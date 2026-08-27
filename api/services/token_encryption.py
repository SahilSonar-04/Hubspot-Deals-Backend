import os
import base64
import hashlib
import logging
from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


def _get_fernet_instance() -> Fernet:
    """Generate a deterministic Fernet key using TOKEN_ENCRYPTION_KEY or derived from SECRET_KEY."""
    raw_key = os.environ.get("TOKEN_ENCRYPTION_KEY", "")
    if not raw_key:
        secret = getattr(settings, "SECRET_KEY", "")
        if not secret:
            raise RuntimeError("Cannot initialize token encryptor: neither TOKEN_ENCRYPTION_KEY nor SECRET_KEY is configured.")
        # Derive a 32-byte key via SHA-256 and base64-encode it for Fernet
        derived_32 = hashlib.sha256(secret.encode("utf-8")).digest()
        raw_key = base64.urlsafe_b64encode(derived_32).decode("utf-8")

    try:
        return Fernet(raw_key.encode("utf-8") if isinstance(raw_key, str) else raw_key)
    except Exception as e:
        logger.error(f"Failed to initialize Fernet token encryptor: {e}")
        raise RuntimeError(f"Cryptographic initialization error: invalid encryption key ({e})") from e


def encrypt_token(token: str) -> str:
    """Encrypt a sensitive token string for safe storage at rest in the database."""
    if not token:
        return ""
    fernet = _get_fernet_instance()
    try:
        encrypted_bytes = fernet.encrypt(token.encode("utf-8"))
        return f"enc:{encrypted_bytes.decode('utf-8')}"
    except Exception as e:
        logger.error(f"Error encrypting token: {e}")
        raise RuntimeError(f"Token encryption failed: {e}") from e


def decrypt_token(stored_value: str) -> str:
    """Decrypt an encrypted token string retrieved from the database."""
    if not stored_value:
        return ""
    if not stored_value.startswith("enc:"):
        # Legacy/plaintext token compatibility
        return stored_value
    
    encrypted_payload = stored_value[4:]
    fernet = _get_fernet_instance()
    try:
        decrypted_bytes = fernet.decrypt(encrypted_payload.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except (InvalidToken, Exception) as e:
        logger.error(f"Error decrypting token: {e}")
        return ""
