from django.test import TestCase
from rest_framework import status

AUTH_HEADERS = {'HTTP_AUTHORIZATION': 'Bearer test_token_12345'}

class EdgeCaseTests(TestCase):
    """Tests covering invalid inputs, 404 non-existent jobs, and malformed requests."""

    def test_status_non_existent_job(self):
        """Querying status for non-existent job returns 404."""
        response = self.client.get('/api/v1/scan/status/non-existent-job-999', **AUTH_HEADERS)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.json())

    def test_result_non_existent_job(self):
        """Querying results for non-existent job returns 404."""
        response = self.client.get('/api/v1/scan/result/non-existent-job-999', **AUTH_HEADERS)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.json())

    def test_cancel_non_existent_job(self):
        """Cancelling non-existent job returns 404."""
        response = self.client.post('/api/v1/scan/cancel/non-existent-job-999', **AUTH_HEADERS)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.json())

    def test_remove_non_existent_job(self):
        """Removing non-existent job returns 404."""
        response = self.client.delete('/api/v1/scan/remove/non-existent-job-999', **AUTH_HEADERS)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.json())

    def test_start_scan_missing_auth(self):
        """Malformed scan request missing auth object returns 400 Bad Request."""
        payload = {
            "config": {
                "scanId": "invalid-scan-001"
            }
        }
        response = self.client.post(
            '/api/v1/scan/start', data=payload, content_type='application/json', **AUTH_HEADERS
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['status_code'], 400)

    def test_invalid_pagination_string_param(self):
        """Passing non-integer string in pagination params returns 400 Bad Request."""
        response = self.client.get('/api/v1/jobs/jobs?limit=invalid_string', **AUTH_HEADERS)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())

    def test_invalid_pagination_negative_param(self):
        """Passing negative values in pagination offset returns 400 Bad Request."""
        response = self.client.get('/api/v1/jobs/jobs?offset=-10', **AUTH_HEADERS)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())

    def test_metrics_endpoint_telemetry(self):
        """Metrics endpoint returns 200 OK with Prometheus formatted metrics."""
        response = self.client.get('/api/v1/metrics')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('hubspot_extractions_total', response.content.decode('utf-8'))

    def test_cancel_already_completed_job_returns_400(self):
        """Attempting to cancel an already completed job returns 400 Bad Request."""
        from api.models import ExtractionJob
        job = ExtractionJob.objects.create(
            job_id="edge-completed-job-123",
            status=ExtractionJob.STATUS_COMPLETED
        )
        response = self.client.post(f'/api/v1/scan/cancel/{job.job_id}', **AUTH_HEADERS)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())