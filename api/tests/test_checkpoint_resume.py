from django.test import TestCase
from rest_framework import status
from api.models import ExtractionJob, DealRecord

AUTH_HEADERS = {'HTTP_AUTHORIZATION': 'Bearer test_token_12345'}

class CheckpointResumeTests(TestCase):
    """Test workflow for pagination checkpointing, pausing, and resuming extractions."""

    def test_checkpoint_saving_and_job_resume(self):
        """Test starting a job, pausing, checking checkpoint data, and resuming execution without duplicates."""

        start_payload = {
            "config": {
                "scanId": "checkpoint-job-001",
                "organizationId": "org-corp-checkpoint",
                "type": ["data"],
                "auth": {
                    "accessToken": "test_token_12345"
                }
            }
        }

        response = self.client.post(
            '/api/v1/scan/start', data=start_payload, content_type='application/json', **AUTH_HEADERS
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        job = ExtractionJob.objects.get(job_id="checkpoint-job-001")
        self.assertEqual(job.status, ExtractionJob.STATUS_COMPLETED)
        self.assertGreater(job.pages_processed, 0)
        self.assertIsNotNone(job.checkpoint_data)

        initial_deal_ids = list(DealRecord.objects.filter(job=job).values_list('deal_id', flat=True))
        self.assertEqual(len(initial_deal_ids), len(set(initial_deal_ids)), "Initial deals should have no duplicates")

        # Manually rewind cursor and pause job to simulate resume overlap
        job.status = ExtractionJob.STATUS_PAUSED
        job.last_cursor = "cursor_page_1"
        job.save()

        resume_response = self.client.post(f'/api/v1/scan/resume/{job.job_id}', **AUTH_HEADERS)
        self.assertEqual(resume_response.status_code, status.HTTP_200_OK)

        resumed_job = ExtractionJob.objects.get(job_id="checkpoint-job-001")
        self.assertEqual(resumed_job.status, ExtractionJob.STATUS_COMPLETED)
        self.assertGreater(resumed_job.record_count, 0)

        # Assert no duplicate DealRecords exist after resume
        resumed_deal_ids = list(DealRecord.objects.filter(job=resumed_job).values_list('deal_id', flat=True))
        self.assertEqual(len(resumed_deal_ids), len(set(resumed_deal_ids)), "Resumed deals must not contain duplicates")
