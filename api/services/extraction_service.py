import logging
import uuid
import threading
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from api.models import ExtractionJob, DealRecord, PipelineMetadata
from api.services.token_encryption import encrypt_token, decrypt_token
from .hubspot_service import HubspotAPIService

logger = logging.getLogger(__name__)


class DataExtractionService:
    """Core service for orchestrating scan jobs, cursor checkpointing, async execution, and resume operations."""

    @staticmethod
    def start_extraction_job(config_data: dict, max_pages: int = None, run_async: bool = False) -> ExtractionJob:
        """Initialize and execute an extraction job with checkpoint saving after each page."""
        job_id = config_data.get('scanId') or f"hubspot-scan-{uuid.uuid4().hex[:8]}"
        org_id = config_data.get('organizationId', 'org-default')
        scan_types = config_data.get('type', ['data'])
        auth = config_data.get('auth', {})
        filters = config_data.get('filters', {})

        raw_token = auth.get('accessToken', '')
        # Encrypt access token at rest for secure storage
        stored_auth_config = {
            'token_provided': bool(raw_token),
            'accessToken': encrypt_token(raw_token) if raw_token else ''
        }

        job, _ = ExtractionJob.objects.get_or_create(
            job_id=job_id,
            defaults={
                'organization_id': org_id,
                'scan_type': scan_types,
                'status': ExtractionJob.STATUS_IN_PROGRESS,
                'filters': filters,
                'auth_config': stored_auth_config,
                'start_time': timezone.now()
            }
        )

        # Reset records if job previously existed
        DealRecord.objects.filter(job=job).delete()
        job.record_count = 0
        job.pages_processed = 0
        job.last_cursor = None
        job.checkpoint_data = {}
        job.status = ExtractionJob.STATUS_IN_PROGRESS
        job.save()

        if max_pages is None:
            max_pages = getattr(settings, 'EXTRACTION_MAX_PAGES', 10)

        props = filters.get('properties', [])
        include_archived = filters.get('includeArchived', False)

        if run_async:
            thread = threading.Thread(
                target=DataExtractionService._run_async_wrapper,
                args=(job.job_id, raw_token, props, include_archived, max_pages, None),
                daemon=True
            )
            thread.start()
            return job
        else:
            hubspot_service = HubspotAPIService(access_token=raw_token)
            return DataExtractionService._run_checkpoint_pipeline(
                job, hubspot_service, props, include_archived, max_pages=max_pages
            )

    @staticmethod
    def resume_extraction_job(job_id: str, config_data: dict = None, run_async: bool = False) -> ExtractionJob:
        """Resume an interrupted or paused extraction job from the last saved cursor checkpoint."""
        job = ExtractionJob.objects.get(job_id=job_id)
        if job.status not in [ExtractionJob.STATUS_PAUSED, ExtractionJob.STATUS_IN_PROGRESS, ExtractionJob.STATUS_FAILED]:
            logger.warning(f"Job {job_id} is in status '{job.status}' and cannot be resumed.")
            return job

        token = ""
        if config_data and 'auth' in config_data:
            token = config_data['auth'].get('accessToken', '')

        stored_enc = job.auth_config.get('accessToken', '') if job.auth_config else ''
        stored_token = decrypt_token(stored_enc) if stored_enc else ''

        if not token:
            token = stored_token

        if token and token != stored_token:
            job.auth_config = {
                **(job.auth_config or {}),
                'token_provided': bool(token),
                'accessToken': encrypt_token(token)
            }

        max_pages = getattr(settings, 'EXTRACTION_MAX_PAGES', 10)
        props = job.filters.get('properties', []) if job.filters else []
        include_archived = job.filters.get('includeArchived', False) if job.filters else False

        job.status = ExtractionJob.STATUS_IN_PROGRESS
        job.error_message = None
        job.save()

        if run_async:
            thread = threading.Thread(
                target=DataExtractionService._run_async_wrapper,
                args=(job.job_id, token, props, include_archived, max_pages, job.last_cursor),
                daemon=True
            )
            thread.start()
            return job
        else:
            hubspot_service = HubspotAPIService(access_token=token)
            return DataExtractionService._run_checkpoint_pipeline(
                job, hubspot_service, props, include_archived, max_pages=max_pages, start_cursor=job.last_cursor
            )

    @staticmethod
    def _run_async_wrapper(job_id: str, token: str, props: list, include_archived: bool, max_pages: int, start_cursor: str):
        """Worker thread entry point for async background extraction."""
        try:
            job = ExtractionJob.objects.get(job_id=job_id)
            hubspot_service = HubspotAPIService(access_token=token)
            DataExtractionService._run_checkpoint_pipeline(
                job, hubspot_service, props, include_archived, max_pages=max_pages, start_cursor=start_cursor
            )
        except Exception as e:
            logger.error(f"Async extraction worker failed for job {job_id}: {e}")
            try:
                failed_job = ExtractionJob.objects.get(job_id=job_id)
                failed_job.status = ExtractionJob.STATUS_FAILED
                failed_job.error_message = str(e)
                failed_job.end_time = timezone.now()
                failed_job.save(update_fields=['status', 'error_message', 'end_time', 'updated_at'])
            except Exception:
                pass

    @staticmethod
    def _run_checkpoint_pipeline(
        job: ExtractionJob,
        hubspot_service: HubspotAPIService,
        props: list,
        include_archived: bool,
        max_pages: int = 10,
        start_cursor: str = None
    ) -> ExtractionJob:
        """Internal pipeline runner processing pages and persisting cursor checkpoints atomically."""
        cursor = start_cursor
        pages_count = job.pages_processed
        page_size = getattr(settings, 'EXTRACTION_PAGE_LIMIT', 10)

        # Scale-friendly O(n) in-memory tracking of unique deals across pages
        seen_deal_ids = set(DealRecord.objects.filter(job=job).values_list('deal_id', flat=True))

        try:
            while pages_count < max_pages:
                # Atomically check for external pause/cancel request
                with transaction.atomic():
                    fresh_job = ExtractionJob.objects.select_for_update().get(id=job.id)
                    if fresh_job.status in [ExtractionJob.STATUS_PAUSED, ExtractionJob.STATUS_CANCELLED]:
                        logger.info(f"Job {job.job_id} halted due to external status update: {fresh_job.status}")
                        return fresh_job

                deals_page, next_cursor, has_more = hubspot_service.fetch_deals_page(
                    properties=props,
                    limit=page_size,
                    after_cursor=cursor,
                    include_archived=include_archived
                )

                now_ts = timezone.now()
                deal_records = []
                for deal_item in deals_page:
                    d_id = str(deal_item.get('deal_id'))
                    if d_id in seen_deal_ids:
                        continue
                    seen_deal_ids.add(d_id)
                    record = DealRecord(
                        job=job,
                        deal_id=d_id,
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

                # Atomically save checkpoint state without stomping concurrent status changes
                with transaction.atomic():
                    fresh_job = ExtractionJob.objects.select_for_update().get(id=job.id)
                    if fresh_job.status in [ExtractionJob.STATUS_PAUSED, ExtractionJob.STATUS_CANCELLED]:
                        logger.info(f"Job {job.job_id} halted mid-checkpoint due to status update: {fresh_job.status}")
                        return fresh_job

                    fresh_job.pages_processed = pages_count
                    fresh_job.last_cursor = cursor
                    fresh_job.record_count = len(seen_deal_ids)
                    fresh_job.checkpoint_data = {
                        "last_checkpoint_at": timezone.now().isoformat(),
                        "last_cursor": cursor,
                        "pages_processed": pages_count,
                        "total_records": len(seen_deal_ids)
                    }
                    fresh_job.save(update_fields=['pages_processed', 'last_cursor', 'record_count', 'checkpoint_data', 'updated_at'])
                    job = fresh_job

                if not has_more or not cursor:
                    break

            with transaction.atomic():
                fresh_job = ExtractionJob.objects.select_for_update().get(id=job.id)
                if fresh_job.status not in [ExtractionJob.STATUS_PAUSED, ExtractionJob.STATUS_CANCELLED]:
                    fresh_job.status = ExtractionJob.STATUS_COMPLETED
                    fresh_job.end_time = timezone.now()
                    fresh_job.save(update_fields=['status', 'end_time', 'updated_at'])
                    job = fresh_job

            # Update global pipeline telemetry
            meta, _ = PipelineMetadata.objects.get_or_create(id=1)
            meta.total_extractions += 1
            meta.save()

            return job

        except Exception as e:
            logger.error(f"Extraction job {job.job_id} failed in pipeline: {e}")
            with transaction.atomic():
                failed_job = ExtractionJob.objects.select_for_update().get(id=job.id)
                failed_job.status = ExtractionJob.STATUS_FAILED
                failed_job.error_message = str(e)
                failed_job.end_time = timezone.now()
                failed_job.save(update_fields=['status', 'error_message', 'end_time', 'updated_at'])
                job = failed_job
            raise

    @staticmethod
    def pause_job(job_id: str) -> ExtractionJob:
        """Pause a running extraction job."""
        with transaction.atomic():
            job = ExtractionJob.objects.select_for_update().get(job_id=job_id)
            if job.status in [ExtractionJob.STATUS_PENDING, ExtractionJob.STATUS_IN_PROGRESS]:
                job.status = ExtractionJob.STATUS_PAUSED
                job.save(update_fields=['status', 'updated_at'])
        return job

    @staticmethod
    def cancel_job(job_id: str) -> ExtractionJob:
        """Cancel a pending or running extraction job."""
        with transaction.atomic():
            job = ExtractionJob.objects.select_for_update().get(job_id=job_id)
            if job.status in [ExtractionJob.STATUS_PENDING, ExtractionJob.STATUS_IN_PROGRESS, ExtractionJob.STATUS_PAUSED]:
                job.status = ExtractionJob.STATUS_CANCELLED
                job.end_time = timezone.now()
                job.save(update_fields=['status', 'end_time', 'updated_at'])
        return job

    @staticmethod
    def remove_job(job_id: str) -> bool:
        """Remove job records and metadata."""
        job = ExtractionJob.objects.get(job_id=job_id)
        DealRecord.objects.filter(job=job).delete()
        job.delete()
        return True

    delete_job_data = remove_job
