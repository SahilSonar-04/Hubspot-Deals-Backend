"""
URL configuration for hubspot_project.
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from django.http import JsonResponse

def root_index(request):
    """Root endpoint detailing API overview and documentation URLs."""
    return JsonResponse({
        "service": "Hubspot Deals Data Extraction Service",
        "version": "1.0.0",
        "documentation": "/docs/",
        "openapi_schema": "/api/schema/",
        "health": "/api/v1/health",
        "endpoints": {
            "start_scan": "POST /api/v1/scan/start",
            "scan_status": "GET /api/v1/scan/status/<job_id>",
            "scan_result": "GET /api/v1/scan/result/<job_id>",
            "cancel_scan": "POST /api/v1/scan/cancel/<job_id>",
            "remove_scan": "DELETE /api/v1/scan/remove/<job_id>",
            "list_jobs": "GET /api/v1/jobs/jobs",
            "job_statistics": "GET /api/v1/jobs/statistics",
            "pipeline_info": "GET /api/v1/pipeline/info",
            "visualizations": "GET /api/v1/visualizations/dashboard"
        }
    })

urlpatterns = [
    path('', root_index, name='root-index'),
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/', include('api.urls')),
]
