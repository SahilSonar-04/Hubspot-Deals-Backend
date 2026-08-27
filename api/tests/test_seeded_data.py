from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from api.models import ExtractionJob, DealRecord, PipelineMetadata

class SeededDataTests(TestCase):
    """Test workflow using pre-populated/seeded database records."""

    def setUp(self):
        # 1. Seed completed job with records
        self.completed_job = ExtractionJob.objects.create(
            job_id="seeded-completed-job-001",
            organization_id="org-test-1",
            status=ExtractionJob.STATUS_COMPLETED,
            record_count=2,
            scan_type=["data"]
        )
        DealRecord.objects.create(
            job=self.completed_job,
            deal_id="deal-1",
            name="Seeded Deal Alpha",
            amount=50000.00,
            stage="closedwon"
        )
        DealRecord.objects.create(
            job=self.completed_job,
            deal_id="deal-2",
            name="Seeded Deal Beta",
            amount=25000.00,
            stage="qualifiedtobuy"
        )

        # 2. Seed pending job
        self.pending_job = ExtractionJob.objects.create(
            job_id="seeded-pending-job-002",
            organization_id="org-test-1",
            status=ExtractionJob.STATUS_PENDING,
            record_count=0
        )

    def test_health_check(self):
        """Verify service health endpoint returns HTTP 200 OK."""
        response = self.client.get('/api/v1/health')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], 'ok')

    def test_verify_job_status(self):
        """Verify job status endpoint for seeded job."""
        response = self.client.get(f'/api/v1/scan/status/{self.completed_job.job_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(data['record_count'], 2)

    def test_fetch_extraction_results(self):
        """Verify fetching extraction results for completed job."""
        response = self.client.get(f'/api/v1/scan/result/{self.completed_job.job_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_records'], 2)
        self.assertEqual(len(data['results']), 2)
        self.assertEqual(data['results'][0]['name'], 'Seeded Deal Alpha')

    def test_list_all_jobs(self):
        """Verify listing all jobs endpoint."""
        response = self.client.get('/api/v1/jobs/jobs')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_jobs'], 2)

    def test_retrieve_job_statistics(self):
        """Verify retrieve job statistics endpoint."""
        response = self.client.get('/api/v1/jobs/statistics')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_jobs'], 2)
        self.assertEqual(data['completed_jobs'], 1)
        self.assertEqual(data['pending_jobs'], 1)
        self.assertEqual(data['total_records_extracted'], 2)

    def test_cancel_pending_job(self):
        """Verify cancelling a pending job."""
        response = self.client.post(f'/api/v1/scan/cancel/{self.pending_job.job_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], 'cancelled')
        
        # Subsequent status check
        status_res = self.client.get(f'/api/v1/scan/status/{self.pending_job.job_id}')
        self.assertEqual(status_res.json()['status'], 'cancelled')

    def test_remove_job_data(self):
        """Verify removing job data and subsequent 404 response."""
        remove_res = self.client.delete(f'/api/v1/scan/remove/{self.completed_job.job_id}')
        self.assertEqual(remove_res.status_code, status.HTTP_200_OK)

        # Check status after removal returns 404
        status_res = self.client.get(f'/api/v1/scan/status/{self.completed_job.job_id}')
        self.assertEqual(status_res.status_code, status.HTTP_404_NOT_FOUND)
