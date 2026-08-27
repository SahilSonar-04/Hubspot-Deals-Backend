from django.test import TestCase
from rest_framework import status

class HeaderAuthenticationTests(TestCase):
    """Test suite for HTTP Header Authentication (X-API-Key and Authorization: Bearer)."""

    def test_valid_api_key_header(self):
        """Request with valid X-API-Key header succeeds."""
        headers = {'HTTP_X_API_KEY': 'dev-secret-key'}
        response = self.client.get('/api/v1/health', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_valid_bearer_token_header(self):
        """Request with valid Authorization Bearer header succeeds."""
        headers = {'HTTP_AUTHORIZATION': 'Bearer test_token_12345'}
        response = self.client.get('/api/v1/health', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_bearer_token_header(self):
        """Request with invalid Authorization Bearer header returns 401 Unauthorized."""
        headers = {'HTTP_AUTHORIZATION': 'Bearer bad_token'}
        response = self.client.get('/api/v1/health', **headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
