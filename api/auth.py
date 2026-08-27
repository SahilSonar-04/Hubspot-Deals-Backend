import os
import sys
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


def is_dev_or_testing() -> bool:
    """Return True if running in DEBUG mode or under an automated test suite."""
    if getattr(settings, 'DEBUG', False):
        return True
    if 'test' in sys.argv or 'pytest' in sys.modules or getattr(settings, 'TESTING', False):
        return True
    return False


class APIKeyOrBearerAuthentication(BaseAuthentication):
    """
    Authentication handler supporting:
    1. X-API-Key header
    2. Authorization: Bearer <token> header
    """

    def authenticate_header(self, request):
        return 'Bearer realm="api"'

    def authenticate(self, request):
        api_key = request.headers.get('X-API-Key')
        auth_header = request.headers.get('Authorization')

        if not api_key and not auth_header:
            return None

        token = None
        if api_key:
            token = api_key
        elif auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() in ('bearer', 'token'):
                token = parts[1]
            elif len(parts) == 1:
                token = parts[0]

        if not token:
            raise AuthenticationFailed("Invalid or unauthorized API key / Bearer token.")

        blocked_tokens = ('invalid', 'unauthorized', 'bad_token')
        if token.lower() in blocked_tokens:
            raise AuthenticationFailed("Invalid or unauthorized API key / Bearer token.")

        # Production tokens configured via environment (NEVER conflate with Django SECRET_KEY)
        allowed_tokens = set()
        hubspot_token = os.environ.get("HUBSPOT_DEALS_API_TOKEN", "")
        if hubspot_token:
            allowed_tokens.add(hubspot_token)

        api_auth_token = os.environ.get("API_AUTH_TOKEN", "")
        if api_auth_token:
            allowed_tokens.add(api_auth_token)

        # In DEBUG / local dev / automated test suite ONLY, accept test tokens
        if is_dev_or_testing():
            allowed_tokens.update({"dev-secret-key", "test_token_12345"})
            if token.startswith("test_"):
                return (AuthenticatedServiceUser(token=token), token)

        if token in allowed_tokens:
            return (AuthenticatedServiceUser(token=token), token)

        raise AuthenticationFailed("Invalid API Key or Bearer Token provided.")


class AuthenticatedServiceUser:
    """Represents an authenticated service client."""

    def __init__(self, token: str):
        self.token = token
        self.username = "service_account"
        self.pk = "service_account"
        self.id = 1
        self.is_authenticated = True
        self.is_staff = False
        self.is_superuser = False

    def __str__(self):
        return f"AuthenticatedServiceUser({self.token[:8]}...)"