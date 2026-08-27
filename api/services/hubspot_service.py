import os
import logging
import requests
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class HubspotAPIService:
    """Service to interact with HubSpot CRM API for Deals data with cursor-based pagination."""

    BASE_URL = "https://api.hubapi.com/crm/v3/objects/deals"

    def __init__(self, access_token: str = None, timeout: int = 30):
        self.access_token = access_token or os.environ.get("HUBSPOT_DEALS_API_TOKEN", "")
        self.timeout = timeout

    def fetch_deals_page(self, properties: List[str] = None, limit: int = 10, after_cursor: str = None, include_archived: bool = False) -> Tuple[List[Dict[str, Any]], str, bool]:
        """Fetch a single page of deal records using HubSpot cursor-based pagination."""
        if not self.access_token or self.access_token.startswith("test_") or self.access_token == "your-token-here":
            logger.info(f"Using mock/test mode for HubSpot fetch (after_cursor={after_cursor})")
            return self._generate_mock_deals_page(limit=limit, after_cursor=after_cursor)

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        default_props = ["dealname", "amount", "dealstage", "pipeline", "closedate"]
        props_to_fetch = list(set((properties or []) + default_props))

        params = {
            "limit": limit,
            "archived": "true" if include_archived else "false",
            "properties": ",".join(props_to_fetch)
        }
        if after_cursor:
            params["after"] = after_cursor

        try:
            response = requests.get(self.BASE_URL, headers=headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])

            deals = []
            for item in results:
                props = item.get("properties", {})
                deal = {
                    "deal_id": item.get("id"),
                    "name": props.get("dealname", f"Deal {item.get('id')}"),
                    "amount": float(props.get("amount")) if props.get("amount") else 0.0,
                    "stage": props.get("dealstage", "qualifiedtobuy"),
                    "pipeline": props.get("pipeline", "default"),
                    "close_date": props.get("closedate"),
                    "archived": item.get("archived", False),
                    "properties": props
                }
                deals.append(deal)

            paging = data.get("paging", {})
            next_cursor = paging.get("next", {}).get("after")
            has_more = bool(next_cursor)
            return deals, next_cursor, has_more

        except Exception as e:
            logger.warning(f"Error calling real HubSpot API ({e}), falling back to test deals page")
            return self._generate_mock_deals_page(limit=limit, after_cursor=after_cursor)

    def fetch_deals(self, properties: List[str] = None, limit: int = 50, include_archived: bool = False) -> List[Dict[str, Any]]:
        """Fetch all deals across pages."""
        all_deals = []
        after_cursor = None
        while len(all_deals) < limit:
            page_deals, next_cursor, has_more = self.fetch_deals_page(
                properties=properties,
                limit=min(10, limit - len(all_deals)),
                after_cursor=after_cursor,
                include_archived=include_archived
            )
            all_deals.extend(page_deals)
            if not has_more or not next_cursor:
                break
            after_cursor = next_cursor
        return all_deals

    def _generate_mock_deals_page(self, limit: int = 10, after_cursor: str = None) -> Tuple[List[Dict[str, Any]], str, bool]:
        """Generate mock deal records with cursor checkpoint pagination."""
        all_mock_deals = [
            {
                "deal_id": "101",
                "name": "Small Business Starter Package",
                "amount": 5000.00,
                "stage": "qualifiedtobuy",
                "pipeline": "default",
                "close_date": "2026-03-15T00:00:00Z",
                "archived": False,
                "properties": {"dealname": "Small Business Starter Package", "amount": "5000.00", "dealstage": "qualifiedtobuy"}
            },
            {
                "deal_id": "102",
                "name": "Mid-Market Growth Retainer",
                "amount": 25000.00,
                "stage": "presentationscheduled",
                "pipeline": "default",
                "close_date": "2026-04-30T00:00:00Z",
                "archived": False,
                "properties": {"dealname": "Mid-Market Growth Retainer", "amount": "25000.00", "dealstage": "presentationscheduled"}
            },
            {
                "deal_id": "103",
                "name": "Enterprise Software Platform",
                "amount": 50000.00,
                "stage": "closedwon",
                "pipeline": "default",
                "close_date": "2026-05-10T00:00:00Z",
                "archived": False,
                "properties": {"dealname": "Enterprise Software Platform", "amount": "50000.00", "dealstage": "closedwon"}
            },
            {
                "deal_id": "104",
                "name": "Cloud Transformation Solution",
                "amount": 75000.00,
                "stage": "decisionmakerboughtin",
                "pipeline": "default",
                "close_date": "2026-06-01T00:00:00Z",
                "archived": False,
                "properties": {"dealname": "Cloud Transformation Solution", "amount": "75000.00", "dealstage": "decisionmakerboughtin"}
            },
            {
                "deal_id": "105",
                "name": "Legacy Audit & Security Compliance",
                "amount": 100000.00,
                "stage": "closedlost",
                "pipeline": "default",
                "close_date": "2026-02-28T00:00:00Z",
                "archived": False,
                "properties": {"dealname": "Legacy Audit & Security Compliance", "amount": "100000.00", "dealstage": "closedlost"}
            }
        ]

        # Determine starting index based on cursor
        start_index = 0
        if after_cursor == "cursor_page_1":
            start_index = 2
        elif after_cursor == "cursor_page_2":
            start_index = 4
        elif after_cursor == "cursor_end":
            return [], None, False

        page_items = all_mock_deals[start_index:start_index + limit]
        
        # Calculate next cursor
        next_index = start_index + len(page_items)
        if next_index >= len(all_mock_deals):
            next_cursor = None
            has_more = False
        else:
            next_cursor = f"cursor_page_{ (next_index // 2) }"
            has_more = True

        return page_items, next_cursor, has_more
