"""
HubSpot Deals Data Source & Transformation Module
Implements DLT (Data Load Tool) resource extraction, data type conversions,
and ETL metadata tagging for HubSpot deals data pipelines.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional, Generator
from django.utils import timezone
from api.services.hubspot_service import HubspotAPIService

logger = logging.getLogger(__name__)


def transform_deal_record(
    raw_deal: Dict[str, Any],
    scan_id: str,
    tenant_id: str,
    extracted_at: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Transform raw HubSpot API deal response into the standardized database schema format.
    Handles data type conversions (Decimal amounts, ISO-8601 timestamps) and injects ETL metadata.
    """
    properties = raw_deal.get("properties", {})
    deal_id = str(raw_deal.get("id") or raw_deal.get("deal_id") or "")

    # Parse and convert amount to Decimal
    raw_amount = properties.get("amount") or raw_deal.get("amount") or 0.0
    try:
        amount = Decimal(str(raw_amount))
    except (ValueError, TypeError):
        amount = Decimal("0.00")

    # Extract name/stage/pipeline
    name = str(properties.get("dealname") or raw_deal.get("name") or "Unnamed Deal")
    stage = str(properties.get("dealstage") or raw_deal.get("stage") or "default")
    pipeline = str(properties.get("pipeline") or raw_deal.get("pipeline") or "default")

    # Handle close date conversion
    close_date_raw = properties.get("closedate") or raw_deal.get("close_date")
    close_date = None
    if close_date_raw:
        if isinstance(close_date_raw, datetime):
            close_date = close_date_raw
        elif isinstance(close_date_raw, str):
            try:
                close_date = datetime.fromisoformat(close_date_raw.replace("Z", "+00:00"))
            except ValueError:
                close_date = None

    archived = bool(raw_deal.get("archived", False))
    extracted_timestamp = extracted_at or timezone.now()

    return {
        "deal_id": deal_id,
        "name": name,
        "amount": amount,
        "stage": stage,
        "pipeline": pipeline,
        "close_date": close_date,
        "archived": archived,
        "_extracted_at": extracted_timestamp,
        "_scan_id": scan_id,
        "_tenant_id": tenant_id,
    }


class DealsDataSource:
    """
    Data Source orchestrator responsible for paginated HubSpot data ingestion,
    schema transformation, and checkpoint emission.
    """

    def __init__(self, api_service: Optional[HubspotAPIService] = None):
        self.api_service = api_service or HubspotAPIService()

    def extract_deals_stream(
        self,
        scan_id: str,
        tenant_id: str,
        properties: Optional[List[str]] = None,
        limit_per_page: int = 10,
        start_cursor: Optional[str] = None,
        max_pages: Optional[int] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Yields batches of transformed deal records alongside cursor checkpoints.
        """
        current_cursor = start_cursor
        pages_count = 0
        has_more = True

        while has_more:
            if max_pages and pages_count >= max_pages:
                break

            records_raw, next_cursor, has_more = self.api_service.fetch_deals_page(
                properties=properties,
                limit=limit_per_page,
                after_cursor=current_cursor
            )

            transformed_records = [
                transform_deal_record(r, scan_id=scan_id, tenant_id=tenant_id)
                for r in records_raw
            ]

            pages_count += 1
            current_cursor = next_cursor

            yield {
                "records": transformed_records,
                "cursor": current_cursor,
                "has_more": has_more,
                "page_number": pages_count,
            }


# DLT Integration Resource Definition
try:
    import dlt

    @dlt.resource(name="hubspot_deals", write_disposition="merge", primary_key="deal_id")
    def hubspot_deals_resource(
        access_token: Optional[str] = None,
        properties: Optional[List[str]] = None,
        scan_id: str = "default_scan",
        tenant_id: str = "default_tenant"
    ) -> Generator[Dict[str, Any], None, None]:
        """DLT Resource yielding transformed HubSpot deal records."""
        api = HubspotAPIService(access_token=access_token)
        cursor = None
        has_more = True
        while has_more:
            raw_deals, cursor, has_more = api.fetch_deals_page(properties=properties, after_cursor=cursor)
            for d in raw_deals:
                yield transform_deal_record(d, scan_id=scan_id, tenant_id=tenant_id)

    @dlt.source(name="hubspot_deals_source")
    def hubspot_deals_source(
        access_token: Optional[str] = None,
        properties: Optional[List[str]] = None,
        scan_id: str = "default_scan",
        tenant_id: str = "default_tenant"
    ):
        """DLT Source wrapper for HubSpot Deals."""
        return [hubspot_deals_resource(access_token, properties, scan_id, tenant_id)]

except ImportError:
    hubspot_deals_resource = None
    hubspot_deals_source = None
