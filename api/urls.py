from django.urls import path
from api.views import (
    HealthView,
    StartScanView,
    ScanStatusView,
    ScanResultView,
    ScanResumeView,
    ScanPauseView,
    ScanCancelView,
    ScanRemoveView,
    JobListView,
    JobStatisticsView,
    PipelineInfoView,
    StatsView
)
from api.visualizations import VisualizationDataView, DashboardView

urlpatterns = [
    # Health & System Status
    path('health', HealthView.as_view(), name='health'),
    path('pipeline/info', PipelineInfoView.as_view(), name='pipeline-info'),
    path('stats', StatsView.as_view(), name='stats'),

    # Extraction Scan Workflow
    path('scan/start', StartScanView.as_view(), name='scan-start'),
    
    # Status endpoints (supporting both /scan/status/<job_id> and /scan/<job_id>/status)
    path('scan/status/<str:job_id>', ScanStatusView.as_view(), name='scan-status'),
    path('scan/<str:job_id>/status', ScanStatusView.as_view(), name='scan-status-alt'),
    
    # Result endpoints (supporting /scan/result/<job_id> and /results/<job_id>/result)
    path('scan/result/<str:job_id>', ScanResultView.as_view(), name='scan-result'),
    path('results/<str:job_id>/result', ScanResultView.as_view(), name='scan-result-alt'),
    
    # Resume & Pause Checkpoint endpoints
    path('scan/resume/<str:job_id>', ScanResumeView.as_view(), name='scan-resume'),
    path('scan/<str:job_id>/resume', ScanResumeView.as_view(), name='scan-resume-alt'),
    path('scan/pause/<str:job_id>', ScanPauseView.as_view(), name='scan-pause'),
    path('scan/<str:job_id>/pause', ScanPauseView.as_view(), name='scan-pause-alt'),

    # Cancel endpoints
    path('scan/cancel/<str:job_id>', ScanCancelView.as_view(), name='scan-cancel'),
    path('scan/<str:job_id>/cancel', ScanCancelView.as_view(), name='scan-cancel-alt'),

    # Remove endpoints
    path('scan/remove/<str:job_id>', ScanRemoveView.as_view(), name='scan-remove'),
    path('scan/<str:job_id>/remove', ScanRemoveView.as_view(), name='scan-remove-alt'),

    # Jobs & Statistics
    path('jobs/jobs', JobListView.as_view(), name='job-list'),
    path('scan/list', JobListView.as_view(), name='scan-list'),
    path('jobs/statistics', JobStatisticsView.as_view(), name='job-statistics'),
    path('scan/statistics', JobStatisticsView.as_view(), name='scan-statistics'),

    # Data Visualizations & Analytics Dashboard
    path('visualizations/data', VisualizationDataView.as_view(), name='visualization-data'),
    path('visualizations/dashboard', DashboardView.as_view(), name='visualization-dashboard'),
]
