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

    def test_restart_scan_job_with_updated_config(self):
        """Test restarting a scan job with updated organization and filters applies changes."""
        initial_payload = {
            "config": {
                "scanId": "restart-test-job-2001",
                "organizationId": "org-initial",
                "type": ["data"],
                "auth": {"accessToken": "test_token_12345"},
                "filters": {"properties": ["dealname"]}
            }
        }
        res1 = self.client.post(
            '/api/v1/scan/start', data=initial_payload, content_type='application/json', **AUTH_HEADERS
        )
        self.assertEqual(res1.status_code, status.HTTP_202_ACCEPTED)

        # Re-start same job_id with new org and new filters
        updated_payload = {
            "config": {
                "scanId": "restart-test-job-2001",
                "organizationId": "org-updated-new",
                "type": ["data", "analytics"],
                "auth": {"accessToken": "test_token_12345"},
                "filters": {"properties": ["dealname", "amount", "pipeline"]}
            }
        }
        res2 = self.client.post(
            '/api/v1/scan/start', data=updated_payload, content_type='application/json', **AUTH_HEADERS
        )
        self.assertEqual(res2.status_code, status.HTTP_202_ACCEPTED)

        job = ExtractionJob.objects.get(job_id="restart-test-job-2001")
        self.assertEqual(job.organization_id, "org-updated-new")
        self.assertEqual(job.scan_type, ["data", "analytics"])
        self.assertEqual(job.filters.get("properties"), ["dealname", "amount", "pipeline"])
