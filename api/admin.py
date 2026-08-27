from django.contrib import admin
from .models import ExtractionJob, DealRecord, PipelineMetadata

@admin.register(ExtractionJob)
class ExtractionJobAdmin(admin.ModelAdmin):
    list_display = ('job_id', 'organization_id', 'status', 'record_count', 'start_time', 'end_time')
    list_filter = ('status', 'organization_id')
    search_fields = ('job_id', 'organization_id', 'error_message')

@admin.register(DealRecord)
class DealRecordAdmin(admin.ModelAdmin):
    list_display = ('deal_id', 'name', 'amount', 'stage', 'pipeline', 'job', 'created_at')
    list_filter = ('stage', 'pipeline', 'archived')
    search_fields = ('deal_id', 'name')

@admin.register(PipelineMetadata)
class PipelineMetadataAdmin(admin.ModelAdmin):
    list_display = ('pipeline_name', 'destination_type', 'active_scanners', 'total_extractions', 'last_sync')
