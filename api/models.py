from django.db import models
from django.utils import timezone

class ExtractionJob(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_PAUSED = 'paused'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_PAUSED, 'Paused'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    job_id = models.CharField(max_length=255, unique=True, db_index=True)
    organization_id = models.CharField(max_length=255, db_index=True, blank=True, null=True)
    scan_type = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_PENDING)
    record_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    filters = models.JSONField(default=dict, blank=True)
    auth_config = models.JSONField(default=dict, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Checkpoint & Resume Fields
    last_cursor = models.CharField(max_length=255, blank=True, null=True, help_text="Cursor token for pagination checkpointing")
    pages_processed = models.IntegerField(default=0, help_text="Total pages fetched during extraction")
    checkpoint_data = models.JSONField(default=dict, blank=True, help_text="Checkpoint state metadata")

    class Meta:
        ordering = ['-start_time']
        verbose_name = 'Extraction Job'
        verbose_name_plural = 'Extraction Jobs'

    def __str__(self):
        return f"Job {self.job_id} ({self.status})"


class DealRecord(models.Model):
    job = models.ForeignKey(ExtractionJob, on_delete=models.CASCADE, related_name='deal_records')
    deal_id = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=500, blank=True, default='')
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    stage = models.CharField(max_length=255, blank=True, default='appointmentscheduled')
    pipeline = models.CharField(max_length=255, blank=True, default='default')
    close_date = models.DateTimeField(null=True, blank=True)
    archived = models.BooleanField(default=False)
    properties = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Mandatory ETL Metadata Fields
    _extracted_at = models.DateTimeField(default=timezone.now)
    _scan_id = models.CharField(max_length=255, blank=True, default='', db_index=True)
    _tenant_id = models.CharField(max_length=255, blank=True, default='default-tenant', db_index=True)

    class Meta:
        ordering = ['created_at', 'id']
        verbose_name = 'Deal Record'
        verbose_name_plural = 'Deal Records'

    def __str__(self):
        return f"Deal {self.deal_id}: {self.name} (${self.amount or 0})"


class PipelineMetadata(models.Model):
    pipeline_name = models.CharField(max_length=255, default='hubspot_deals_pipeline')
    destination_type = models.CharField(max_length=255, default='postgresql')
    active_scanners = models.IntegerField(default=1)
    total_extractions = models.IntegerField(default=0)
    last_sync = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pipeline {self.pipeline_name} ({self.destination_type})"
