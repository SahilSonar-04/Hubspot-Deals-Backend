import logging
import time
from django.utils import timezone
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from api.models import ExtractionJob, DealRecord, PipelineMetadata
from api.auth import APIKeyOrBearerAuthentication
from api.serializers import (
    StartScanRequestSerializer,
    StartScanResponseSerializer,
    ExtractionJobSerializer,
    DealRecordSerializer,
    JobResultsResponseSerializer,
    JobStatisticsSerializer,
    PipelineInfoSerializer,
    HealthCheckSerializer
)
from api.services.extraction_service import DataExtractionService

logger = logging.getLogger(__name__)
_START_TIME = time.time()


class BaseAPIView(APIView):
    """Base API View configuring authentication handlers."""
    authentication_classes = [APIKeyOrBearerAuthentication]


class HealthView(BaseAPIView):
    """Health check endpoint confirming basic service availability."""
    permission_classes = []

    @extend_schema(
        summary="Service Health Check",
        responses={200: HealthCheckSerializer}
    )
    def get(self, request):
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            db_ok = False

        data = {
            "status": "ok" if db_ok else "unhealthy",
            "service": "Hubspot Deals Data Extraction Service",
            "version": "1.0.0",
            "database": "connected" if db_ok else "disconnected",
            "timestamp": timezone.now().isoformat()
        }
        return Response(data, status=status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE)


class StartScanView(BaseAPIView):
    """Initiates a new data extraction scan job with checkpoint tracking."""
    throttle_scope = 'scan_start'

    @extend_schema(
        summary="Start New Extraction Scan",
        request=StartScanRequestSerializer,
        responses={202: StartScanResponseSerializer}
    )
    def post(self, request):
        serializer = StartScanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        config_data = serializer.validated_data['config']
        # Support asynchronous extraction execution while allowing sync for deterministic tests
        run_async = request.query_params.get('async', 'false').lower() in ('true', '1')
        job = DataExtractionService.start_extraction_job(config_data, run_async=run_async)

        response_data = {
            "status": job.status,
            "message": f"Scan job '{job.job_id}' initiated successfully.",
            "job_id": job.job_id
        }
        return Response(response_data, status=status.HTTP_202_ACCEPTED)


class ScanResumeView(BaseAPIView):
    """Resumes an interrupted or paused extraction job from the last saved cursor checkpoint."""

    @extend_schema(
        summary="Resume Scan Job",
        responses={200: ExtractionJobSerializer, 404: OpenApiTypes.OBJECT}
    )
    def post(self, request, job_id):
        try:
            config_data = request.data.get('config', {}) if isinstance(request.data, dict) else {}
            run_async = request.query_params.get('async', 'false').lower() in ('true', '1')
            job = DataExtractionService.resume_extraction_job(job_id, config_data, run_async=run_async)
            serializer = ExtractionJobSerializer(job)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ExtractionJob.DoesNotExist:
            return Response(
                {"error": f"Extraction job with ID '{job_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class ScanPauseView(BaseAPIView):
    """Pauses a running extraction job."""

    @extend_schema(
        summary="Pause Scan Job",
        responses={200: ExtractionJobSerializer, 404: OpenApiTypes.OBJECT}
    )
    def post(self, request, job_id):
        try:
            job = DataExtractionService.pause_job(job_id)
            serializer = ExtractionJobSerializer(job)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ExtractionJob.DoesNotExist:
            return Response(
                {"error": f"Extraction job with ID '{job_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class ScanStatusView(BaseAPIView):
    """Retrieves status, pagination metadata, and cursor checkpoint for an extraction job."""

    @extend_schema(
        summary="Get Scan Job Status",
        responses={200: ExtractionJobSerializer, 404: OpenApiTypes.OBJECT}
    )
    def get(self, request, job_id):
        try:
            job = ExtractionJob.objects.get(job_id=job_id)
            serializer = ExtractionJobSerializer(job)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ExtractionJob.DoesNotExist:
            return Response(
                {"error": f"Extraction job with ID '{job_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class ScanResultView(BaseAPIView):
    """Fetches extracted deal records supporting limit/offset and next cursor pagination."""

    @extend_schema(
        summary="Fetch Scan Results",
        parameters=[
            OpenApiParameter("limit", OpenApiTypes.INT, description="Number of results to return", default=10),
            OpenApiParameter("offset", OpenApiTypes.INT, description="Offset index for pagination", default=0),
            OpenApiParameter("tableName", OpenApiTypes.STR, description="Optional table filter", default="deal_records")
        ],
        responses={200: JobResultsResponseSerializer, 404: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
    )
    def get(self, request, job_id):
        try:
            job = ExtractionJob.objects.get(job_id=job_id)
        except ExtractionJob.DoesNotExist:
            return Response(
                {"error": f"Extraction job with ID '{job_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Robust pagination input validation (Task 6)
        try:
            limit_param = request.query_params.get('limit', 10)
            offset_param = request.query_params.get('offset', 0)
            limit = int(limit_param)
            offset = int(offset_param)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid pagination parameters: 'limit' and 'offset' must be valid integers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if limit < 1 or offset < 0:
            return Response(
                {"error": "'limit' must be >= 1 and 'offset' must be >= 0."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cap limit to 100 to prevent unbounded memory queries
        limit = min(limit, 100)

        total_count = DealRecord.objects.filter(job=job).count()
        records_qs = DealRecord.objects.filter(job=job)[offset:offset + limit]

        next_offset = (offset + limit) if (offset + limit) < total_count else None
        prev_offset = (offset - limit) if (offset - limit) >= 0 else None
        has_more = (offset + limit) < total_count

        records_serializer = DealRecordSerializer(records_qs, many=True)
        response_data = {
            "job_id": job.job_id,
            "status": job.status,
            "total_records": total_count,
            "limit": limit,
            "offset": offset,
            "next_offset": next_offset,
            "prev_offset": prev_offset,
            "has_more": has_more,
            "results": records_serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)


class ScanCancelView(BaseAPIView):
    """Cancels a pending or running extraction job."""

    @extend_schema(
        summary="Cancel Pending Scan Job",
        responses={200: ExtractionJobSerializer, 404: OpenApiTypes.OBJECT}
    )
    def post(self, request, job_id):
        try:
            job = DataExtractionService.cancel_job(job_id)
            serializer = ExtractionJobSerializer(job)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ExtractionJob.DoesNotExist:
            return Response(
                {"error": f"Extraction job with ID '{job_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class ScanRemoveView(BaseAPIView):
    """Removes scan job records and associated data from the system."""

    @extend_schema(
        summary="Remove Scan Job Data",
        responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def delete(self, request, job_id):
        try:
            DataExtractionService.remove_job(job_id)
            return Response(
                {"message": f"Scan job '{job_id}' and all associated records removed successfully."},
                status=status.HTTP_200_OK
            )
        except ExtractionJob.DoesNotExist:
            return Response(
                {"error": f"Extraction job with ID '{job_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class JobListView(BaseAPIView):
    """Lists all extraction jobs with optional filtering and pagination parity."""

    @extend_schema(
        summary="List Extraction Jobs",
        parameters=[
            OpenApiParameter("organizationId", OpenApiTypes.STR, description="Filter by organization ID"),
            OpenApiParameter("limit", OpenApiTypes.INT, description="Results limit", default=10),
            OpenApiParameter("offset", OpenApiTypes.INT, description="Pagination offset", default=0)
        ],
        responses={200: ExtractionJobSerializer(many=True), 400: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        qs = ExtractionJob.objects.all()
        org_id = request.query_params.get('organizationId')
        if org_id:
            qs = qs.filter(organization_id=org_id)

        # Robust pagination input validation (Task 6 & Task 11)
        try:
            limit_param = request.query_params.get('limit', 10)
            offset_param = request.query_params.get('offset', 0)
            limit = int(limit_param)
            offset = int(offset_param)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid pagination parameters: 'limit' and 'offset' must be valid integers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if limit < 1 or offset < 0:
            return Response(
                {"error": "'limit' must be >= 1 and 'offset' must be >= 0."},
                status=status.HTTP_400_BAD_REQUEST
            )

        limit = min(limit, 100)
        total_count = qs.count()
        paged_qs = qs[offset:offset + limit]

        next_offset = (offset + limit) if (offset + limit) < total_count else None
        prev_offset = (offset - limit) if (offset - limit) >= 0 else None
        has_more = (offset + limit) < total_count

        serializer = ExtractionJobSerializer(paged_qs, many=True)
        return Response({
            "total_jobs": total_count,
            "limit": limit,
            "offset": offset,
            "next_offset": next_offset,
            "prev_offset": prev_offset,
            "has_more": has_more,
            "jobs": serializer.data
        }, status=status.HTTP_200_OK)


class JobStatisticsView(BaseAPIView):
    """Provides metrics and calculated summary statistics for extraction jobs."""

    @extend_schema(
        summary="Retrieve Extraction Job Statistics",
        responses={200: JobStatisticsSerializer}
    )
    def get(self, request):
        total_jobs = ExtractionJob.objects.count()
        completed_jobs = ExtractionJob.objects.filter(status=ExtractionJob.STATUS_COMPLETED).count()
        failed_jobs = ExtractionJob.objects.filter(status=ExtractionJob.STATUS_FAILED).count()
        pending_jobs = ExtractionJob.objects.filter(status=ExtractionJob.STATUS_PENDING).count()
        cancelled_jobs = ExtractionJob.objects.filter(status=ExtractionJob.STATUS_CANCELLED).count()

        total_records = DealRecord.objects.count()

        # Real DB duration calculation across completed jobs (Task 7)
        completed_qs = ExtractionJob.objects.filter(
            status=ExtractionJob.STATUS_COMPLETED,
            start_time__isnull=False,
            end_time__isnull=False
        )
        durations = [
            (j.end_time - j.start_time).total_seconds()
            for j in completed_qs if j.end_time and j.start_time
        ]
        avg_extraction_time = round(sum(durations) / len(durations), 2) if durations else 0.0

        data = {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "pending_jobs": pending_jobs,
            "cancelled_jobs": cancelled_jobs,
            "total_records_extracted": total_records,
            "average_extraction_time_seconds": avg_extraction_time
        }
        return Response(data, status=status.HTTP_200_OK)


class PipelineInfoView(BaseAPIView):
    """Returns telemetry and technical details about the data extraction pipeline."""

    @extend_schema(
        summary="Get Extraction Pipeline Details",
        responses={200: PipelineInfoSerializer}
    )
    def get(self, request):
        meta, _ = PipelineMetadata.objects.get_or_create(id=1)

        # Dynamic Pipeline Status Derivation (Task 8)
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            db_ok = False

        total_jobs = ExtractionJob.objects.count()
        failed_jobs = ExtractionJob.objects.filter(status=ExtractionJob.STATUS_FAILED).count()

        if not db_ok:
            pipeline_status = "unhealthy"
        elif total_jobs > 0 and (failed_jobs / total_jobs) > 0.5:
            pipeline_status = "degraded"
        else:
            pipeline_status = "healthy"

        data = {
            "pipeline_name": meta.pipeline_name,
            "destination_type": meta.destination_type,
            "active_scanners": meta.active_scanners,
            "total_extractions": meta.total_extractions,
            "status": pipeline_status,
            "version": "1.0.0"
        }
        return Response(data, status=status.HTTP_200_OK)


class StatsView(BaseAPIView):
    """Overall application statistics endpoint."""

    @extend_schema(
        summary="Service-wide Statistics",
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        return Response({
            "total_scans": ExtractionJob.objects.count(),
            "total_deals": DealRecord.objects.count(),
            "active_pipeline": "hubspot_deals_pipeline",
            "uptime_status": "online"
        }, status=status.HTTP_200_OK)


class MetricsView(BaseAPIView):
    """Prometheus-compatible and JSON observability metrics endpoint (Task 15)."""
    permission_classes = []

    @extend_schema(
        summary="Prometheus & Observability Metrics",
        responses={200: OpenApiTypes.STR}
    )
    def get(self, request):
        total_jobs = ExtractionJob.objects.count()
        completed_jobs = ExtractionJob.objects.filter(status=ExtractionJob.STATUS_COMPLETED).count()
        failed_jobs = ExtractionJob.objects.filter(status=ExtractionJob.STATUS_FAILED).count()
        total_records = DealRecord.objects.count()
        uptime_seconds = round(time.time() - _START_TIME, 2)

        format_type = request.query_params.get('format', 'prometheus')

        if format_type == 'json':
            return Response({
                "hubspot_extractions_total": total_jobs,
                "hubspot_extractions_completed_total": completed_jobs,
                "hubspot_extractions_failed_total": failed_jobs,
                "hubspot_deals_extracted_total": total_records,
                "hubspot_service_uptime_seconds": uptime_seconds
            })

        # Standard Prometheus exposition format
        metrics_text = f"""# HELP hubspot_extractions_total Total number of extraction jobs created
# TYPE hubspot_extractions_total counter
hubspot_extractions_total {total_jobs}

# HELP hubspot_extractions_completed_total Total completed extraction jobs
# TYPE hubspot_extractions_completed_total counter
hubspot_extractions_completed_total {completed_jobs}

# HELP hubspot_extractions_failed_total Total failed extraction jobs
# TYPE hubspot_extractions_failed_total counter
hubspot_extractions_failed_total {failed_jobs}

# HELP hubspot_deals_extracted_total Total deals records stored
# TYPE hubspot_deals_extracted_total counter
hubspot_deals_extracted_total {total_records}

# HELP hubspot_service_uptime_seconds Process uptime in seconds
# TYPE hubspot_service_uptime_seconds gauge
hubspot_service_uptime_seconds {uptime_seconds}
"""
        return HttpResponse(metrics_text, content_type="text/plain; version=0.0.4")
