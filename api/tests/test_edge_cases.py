from django.test import TestCase
from rest_framework import status

class EdgeCaseTests(TestCase):
    """Tests covering invalid inputs, 404 non-existent jobs, and malformed requests."""

    def test_status_non_existent_job(self):
        """Querying status for non-existent job returns 404."""
        response = self.client.get('/api/v1/scan/status/non-existent-job-999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.json())

    def test_result_non_existent_job(self):
        """Querying results for non-existent job returns 404."""
        response = self.client.get('/api/v1/scan/result/non-existent-job-999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.json())

    def test_cancel_non_existent_job(self):
        """Cancelling non-existent job returns 404."""
        response = self.client.post('/api/v1/scan/cancel/non-existent-job-999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.json())

    def test_remove_non_existent_job(self):
        """Removing non-existent job returns 404."""
        response = self.client.delete('/api/v1/scan/remove/non-existent-job-999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.json())

    def test_start_scan_missing_auth(self):
        """Malformed scan request missing auth object returns 400 Bad Request."""
        payload = {
            "config": {
                "scanId": "invalid-scan-001"
            }
        }
        response = self.client.post('/api/v1/scan/start', data=payload, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
