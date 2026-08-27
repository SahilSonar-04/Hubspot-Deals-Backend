import json
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from django.db.models import Count, Sum, Avg, Max
from django.utils import timezone
from api.models import ExtractionJob, DealRecord, PipelineMetadata
from drf_spectacular.utils import extend_schema

class VisualizationDataView(APIView):
    """API endpoint providing aggregated analytics and chart data for deals and extraction performance."""

    @extend_schema(
        summary="Get analytics data for visualizations",
        description="Returns aggregated deal metrics, pipeline statistics, and job statuses formatted for charting UI."
    )
    def get(self, request):
        format_type = request.query_params.get('format', 'json')

        stage_counts = list(
            DealRecord.objects.values('stage')
            .annotate(count=Count('id'), total_amount=Sum('amount'))
            .order_by('-count')
        )

        job_counts = list(
            ExtractionJob.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        total_deals = DealRecord.objects.count()
        total_value = DealRecord.objects.aggregate(total=Sum('amount'))['total'] or 0.0
        avg_deal_value = DealRecord.objects.aggregate(avg=Avg('amount'))['avg'] or 0.0
        max_deal_value = DealRecord.objects.aggregate(max_val=Max('amount'))['max_val'] or 0.0

        data = {
            "summary": {
                "total_deals": total_deals,
                "total_pipeline_value": float(total_value),
                "average_deal_size": float(avg_deal_value),
                "largest_deal_size": float(max_deal_value),
                "generated_at": timezone.now().isoformat()
            },
            "deals_by_stage": stage_counts,
            "jobs_by_status": job_counts,
        }

        if format_type == 'html':
            return render(request, 'visualizations/dashboard.html', {
                'analytics': data,
                'stage_data_json': json.dumps(stage_counts),
                'job_data_json': json.dumps(job_counts),
            })

        return Response(data)


class DashboardView(APIView):
    """HTML Interactive Dashboard View for visual presentation of Hubspot Deals analytics."""

    def get(self, request):
        stage_counts = list(
            DealRecord.objects.values('stage')
            .annotate(count=Count('id'), total_amount=Sum('amount'))
            .order_by('-count')
        )

        # Convert Decimal values to float for JSON serialization
        for item in stage_counts:
            if item.get('total_amount') is not None:
                item['total_amount'] = float(item['total_amount'])

        job_counts = list(
            ExtractionJob.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        total_deals = DealRecord.objects.count()
        total_value = DealRecord.objects.aggregate(total=Sum('amount'))['total'] or 0.0
        avg_deal_value = DealRecord.objects.aggregate(avg=Avg('amount'))['avg'] or 0.0

        context = {
            'total_deals': total_deals,
            'total_value': f"${total_value:,.2f}",
            'avg_value': f"${avg_deal_value:,.2f}",
            'stage_data_json': json.dumps(stage_counts),
            'job_data_json': json.dumps(job_counts),
        }
        return render(request, 'visualizations/dashboard.html', context)
