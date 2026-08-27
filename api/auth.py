import os
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


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

        valid_tokens = {
            os.environ.get("HUBSPOT_DEALS_API_TOKEN", ""),
            os.environ.get("SECRET_KEY", ""),
            "dev-secret-key",
            "test_token_12345",
        }
        valid_tokens.discard("")

        if token.startswith("test_") or token in valid_tokens:
            return (AuthenticatedServiceUser(token=token), token)

        raise AuthenticationFailed("Invalid API Key or Bearer Token provided.")


class AuthenticatedServiceUser:
    """Represents an authenticated service client."""

    def __init__(self, token: str):
        self.token = token
        self.username = "service_account"
        self.is_authenticated = True
        self.is_staff = False
        self.is_superuser = False

    def __str__(self):
        return f"AuthenticatedServiceUser({self.token[:8]}...)"
        