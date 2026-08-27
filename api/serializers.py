from rest_framework import serializers
from api.models import ExtractionJob, DealRecord, PipelineMetadata

class AuthConfigSerializer(serializers.Serializer):
    accessToken = serializers.CharField(required=True, help_text="Hubspot Private App Access Token")

class FiltersConfigSerializer(serializers.Serializer):
    properties = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    includeArchived = serializers.BooleanField(required=False, default=False)

class ScanConfigSerializer(serializers.Serializer):
    scanId = serializers.CharField(required=False, help_text="Unique custom ID for scan job")
    organizationId = serializers.CharField(required=False, default="org-default", help_text="Organization ID")
    type = serializers.ListField(child=serializers.CharField(), required=False, default=lambda: ["data"])
    auth = AuthConfigSerializer(required=True)
    filters = FiltersConfigSerializer(required=False, default=dict)

class StartScanRequestSerializer(serializers.Serializer):
    config = ScanConfigSerializer(required=True)

class StartScanResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()
    job_id = serializers.CharField()

class ExtractionJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractionJob
        fields = [
            'id', 'job_id', 'organization_id', 'scan_type', 'status',
            'record_count', 'error_message', 'filters', 'start_time', 'end_time',
            'updated_at', 'last_cursor', 'pages_processed', 'checkpoint_data'
        ]

class DealRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DealRecord
        fields = [
            'id', 'deal_id', 'name', 'amount', 'stage',
            'pipeline', 'close_date', 'archived', 'properties',
            'created_at', '_extracted_at', '_scan_id', '_tenant_id'
        ]

class JobResultsResponseSerializer(serializers.Serializer):
    job_id = serializers.CharField()
    status = serializers.CharField()
    total_records = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    next_offset = serializers.IntegerField(allow_null=True)
    prev_offset = serializers.IntegerField(allow_null=True)
    has_more = serializers.BooleanField()
    results = DealRecordSerializer(many=True)

class JobStatisticsSerializer(serializers.Serializer):
    total_jobs = serializers.IntegerField()
    completed_jobs = serializers.IntegerField()
    failed_jobs = serializers.IntegerField()
    pending_jobs = serializers.IntegerField()
    cancelled_jobs = serializers.IntegerField()
    total_records_extracted = serializers.IntegerField()
    average_extraction_time_seconds = serializers.FloatField()

class PipelineInfoSerializer(serializers.Serializer):
    pipeline_name = serializers.CharField()
    destination_type = serializers.CharField()
    active_scanners = serializers.IntegerField()
    total_extractions = serializers.IntegerField()
    status = serializers.CharField()
    version = serializers.CharField()

class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()
    version = serializers.CharField()
    database = serializers.CharField()
    timestamp = serializers.CharField()
