from django.test import TestCase
from rest_framework import status
from api.models import ExtractionJob, DealRecord

class CheckpointResumeTests(TestCase):
    """Test workflow for pagination checkpointing, pausing, and resuming extractions."""

    def test_checkpoint_saving_and_job_resume(self):
        """Test starting a job, pausing, checking checkpoint data, and resuming execution."""

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

        # 1. Start job
        response = self.client.post('/api/v1/scan/start', data=start_payload, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        
        job = ExtractionJob.objects.get(job_id="checkpoint-job-001")
        self.assertEqual(job.status, ExtractionJob.STATUS_COMPLETED)
        self.assertGreater(job.pages_processed, 0)
        self.assertIsNotNone(job.checkpoint_data)

        # 2. Pause job manually for testing
        job.status = ExtractionJob.STATUS_PAUSED
        job.last_cursor = "cursor_page_1"
        job.save()

        # 3. Resume job
        resume_response = self.client.post(f'/api/v1/scan/resume/{job.job_id}')
        self.assertEqual(resume_response.status_code, status.HTTP_200_OK)

        resumed_job = ExtractionJob.objects.get(job_id="checkpoint-job-001")
        self.assertEqual(resumed_job.status, ExtractionJob.STATUS_COMPLETED)
        self.assertGreater(resumed_job.record_count, 0)
