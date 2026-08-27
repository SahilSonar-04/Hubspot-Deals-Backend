from django.test import TestCase
from rest_framework import status
from api.models import ExtractionJob, DealRecord

AUTH_HEADERS = {'HTTP_AUTHORIZATION': 'Bearer test_token_12345'}

class RealExtractionTests(TestCase):
    """End-to-end workflow tests triggering real/mock extractions via API."""

    def test_start_and_complete_scan_job(self):
        """Test starting a new extraction scan job."""
        payload = {
            "config": {
                "scanId": "real-test-job-1001",
                "organizationId": "org-corp-test",
                "type": ["data"],
                "auth": {
                    "accessToken": "test_token_12345"
                },
                "filters": {
                    "properties": ["dealname", "amount", "dealstage"],
                    "includeArchived": False
                }
            }
        }

        response = self.client.post(
            '/api/v1/scan/start', data=payload, content_type='application/json', **AUTH_HEADERS
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        data = response.json()
        job_id = data['job_id']
        self.assertEqual(job_id, 'real-test-job-1001')

        status_res = self.client.get(f'/api/v1/scan/status/{job_id}', **AUTH_HEADERS)
        self.assertEqual(status_res.status_code, status.HTTP_200_OK)
        job_data = status_res.json()
        self.assertEqual(job_data['status'], 'completed')
        self.assertGreater(job_data['record_count'], 0)

        results_res = self.client.get(f'/api/v1/scan/result/{job_id}', **AUTH_HEADERS)
        self.assertEqual(results_res.status_code, status.HTTP_200_OK)
        res_data = results_res.json()
        self.assertGreaterEqual(len(res_data['results']), 1)
