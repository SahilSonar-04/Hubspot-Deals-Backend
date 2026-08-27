import logging
import uuid
from django.utils import timezone
from api.models import ExtractionJob, DealRecord, PipelineMetadata
from .hubspot_service import HubspotAPIService

logger = logging.getLogger(__name__)

class DataExtractionService:
    """Core service for orchestrating scan jobs, cursor checkpointing, and job resume operations."""

    @staticmethod
    def start_extraction_job(config_data: dict, max_pages: int = 10) -> ExtractionJob:
        """Initialize and execute an extraction job with checkpoint saving after each page."""
        job_id = config_data.get('scanId') or f"hubspot-scan-{uuid.uuid4().hex[:8]}"
        org_id = config_data.get('organizationId', 'org-default')
        scan_types = config_data.get('type', ['data'])
        auth = config_data.get('auth', {})
        filters = config_data.get('filters', {})

        token = auth.get('accessToken', '')

        job, created = ExtractionJob.objects.update_or_create(
            job_id=job_id,
            defaults={
                'organization_id': org_id,
                'scan_type': scan_types,
                'status': ExtractionJob.STATUS_IN_PROGRESS,
                'auth_config': {'token_provided': bool(token), 'accessToken': token},
                'filters': filters,
                'start_time': timezone.now(),
                'end_time': None,
                'error_message': None,
                'record_count': 0,
                'last_cursor': None,
                'pages_processed': 0,
                'checkpoint_data': {}
            }
        )

        try:
            hubspot_service = HubspotAPIService(access_token=token)
            props = filters.get('properties', [])
            include_archived = filters.get('includeArchived', False)

            DealRecord.objects.filter(job=job).delete()

            return DataExtractionService._run_checkpoint_pipeline(job, hubspot_service, props, include_archived, max_pages=max_pages)

        except Exception as e:
            logger.error(f"Extraction job {job_id} failed: {e}")
            job.status = ExtractionJob.STATUS_FAILED
            job.error_message = str(e)
            job.end_time = timezone.now()
            job.save()
            return job

    @staticmethod
    def resume_extraction_job(job_id: str, config_data: dict = None) -> ExtractionJob:
        """Resume an interrupted or paused extraction job from the last saved cursor checkpoint."""
        job = ExtractionJob.objects.get(job_id=job_id)
        if job.status not in [ExtractionJob.STATUS_PAUSED, ExtractionJob.STATUS_IN_PROGRESS, ExtractionJob.STATUS_FAILED]:
            logger.warning(f"Job {job_id} is in status '{job.status}' and cannot be resumed.")
            return job

        token = ""
        if config_data and 'auth' in config_data:
            token = config_data['auth'].get('accessToken', '')
        if not token and job.auth_config:
            token = job.auth_config.get('accessToken', '')

        if token and job.auth_config.get('accessToken') != token:
            job.auth_config = {**job.auth_config, 'token_provided': bool(token), 'accessToken': token}

        hubspot_service = HubspotAPIService(access_token=token)
        props = job.filters.get('properties', []) if job.filters else []
        include_archived = job.filters.get('includeArchived', False) if job.filters else False

        job.status = ExtractionJob.STATUS_IN_PROGRESS
        job.error_message = None
        job.save()

        try:
            return DataExtractionService._run_checkpoint_pipeline(
                job, hubspot_service, props, include_archived, start_cursor=job.last_cursor
            )
        except Exception as e:
            logger.error(f"Resume of job {job_id} failed: {e}")
            job.status = ExtractionJob.STATUS_FAILED
            job.error_message = str(e)
            job.end_time = timezone.now()
            job.save()
            return job

    @staticmethod
    def _run_checkpoint_pipeline(job: ExtractionJob, hubspot_service: HubspotAPIService, props: list, include_archived: bool, max_pages: int = 10, start_cursor: str = None) -> ExtractionJob:
        """Internal pipeline runner processing pages and persisting cursor checkpoints."""
        cursor = start_cursor
        pages_count = job.pages_processed

        while pages_count < max_pages:
            deals_page, next_cursor, has_more = hubspot_service.fetch_deals_page(
                properties=props,
                limit=10,
                after_cursor=cursor,
                include_archived=include_archived
            )

            now_ts = timezone.now()
            deal_records = []
            for deal_item in deals_page:
                record = DealRecord(
                    job=job,
                    deal_id=str(deal_item.get('deal_id')),
                    name=deal_item.get('name', ''),
                    amount=deal_item.get('amount'),
                    stage=deal_item.get('stage', 'qualifiedtobuy'),
                    pipeline=deal_item.get('pipeline', 'default'),
                    close_date=deal_item.get('close_date'),
                    archived=deal_item.get('archived', False),
                    properties=deal_item.get('properties', {}),
                    _extracted_at=now_ts,
                    _scan_id=job.job_id,
                    _tenant_id=job.organization_id or 'default-tenant'
                )
                deal_records.append(record)

            if deal_records:
                DealRecord.objects.bulk_create(deal_records)

            pages_count += 1
            cursor = next_cursor

            job.pages_processed = pages_count
            job.last_cursor = cursor
            job.record_count = DealRecord.objects.filter(job=job).count()
            job.checkpoint_data = {
                "last_checkpoint_at": timezone.now().isoformat(),
                "last_cursor": cursor,
                "pages_processed": pages_count,
                "total_records": job.record_count
            }
            job.save()

            if not has_more or not cursor:
                break

        job.status = ExtractionJob.STATUS_COMPLETED
        job.end_time = timezone.now()
        job.save()

        meta, _ = PipelineMetadata.objects.get_or_create(id=1)
        meta.total_extractions += 1
        meta.save()

        return job

    @staticmethod
    def pause_job(job_id: str) -> ExtractionJob:
        """Pause a running extraction job."""
        job = ExtractionJob.objects.get(job_id=job_id)
        if job.status in [ExtractionJob.STATUS_PENDING, ExtractionJob.STATUS_IN_PROGRESS]:
            job.status = ExtractionJob.STATUS_PAUSED
            job.save()
        return job

    @staticmethod
    def cancel_job(job_id: str) -> ExtractionJob:
        """Cancel a pending or running extraction job."""
        job = ExtractionJob.objects.get(job_id=job_id)
        if job.status in [ExtractionJob.STATUS_PENDING, ExtractionJob.STATUS_IN_PROGRESS, ExtractionJob.STATUS_PAUSED]:
            job.status = ExtractionJob.STATUS_CANCELLED
            job.end_time = timezone.now()
            job.save()
        return job

    @staticmethod
    def remove_job(job_id: str) -> bool:
        """Remove job and associated records from database."""
        job = ExtractionJob.objects.get(job_id=job_id)
        job.delete()
        return True
