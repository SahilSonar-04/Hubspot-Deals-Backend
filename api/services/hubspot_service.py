import os
import time
import random
import logging
import requests
from typing import List, Dict, Any, Tuple
from django.conf import settings

from api.exceptions import HubspotAPIError

logger = logging.getLogger(__name__)


class HubspotAPIService:
    """Service to interact with HubSpot CRM API for Deals data with cursor-based pagination."""

    BASE_URL = "https://api.hubapi.com/crm/v3/objects/deals"

    def __init__(self, access_token: str = None, timeout: int = 30, max_retries: int = 3):
        self.access_token = access_token or os.environ.get("HUBSPOT_DEALS_API_TOKEN", "")
        self.timeout = timeout
        self.max_retries = int(os.environ.get("HUBSPOT_DEALS_API_MAX_RETRIES", max_retries))

    def _uses_mock_mode(self) -> bool:
        # Explicit test token is allowed in testing environments
        if self.access_token and self.access_token.startswith("test_"):
            return True

        is_placeholder_or_empty = (
            not self.access_token
            or self.access_token == "your-token-here"
        )
        if is_placeholder_or_empty:
            if not getattr(settings, 'DEBUG', False):
                raise HubspotAPIError("Invalid or missing HubSpot API access token in production environment.")
            return True
        return False

    def fetch_deals_page(self, properties: List[str] = None, limit: int = 10, after_cursor: str = None, include_archived: bool = False) -> Tuple[List[Dict[str, Any]], str, bool]:
        """Fetch a single page of deal records using HubSpot cursor-based pagination."""
        if self._uses_mock_mode():
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

        return self._fetch_with_retry(headers, params)

    def _fetch_with_retry(self, headers: dict, params: dict) -> Tuple[List[Dict[str, Any]], str, bool]:
        attempt = 0
        delay = 1.0
        last_error = None

        while attempt <= self.max_retries:
            try:
                response = requests.get(self.BASE_URL, headers=headers, params=params, timeout=self.timeout)

                if response.status_code == 429 or response.status_code >= 500:
                    last_error = f"HTTP {response.status_code} from HubSpot API"
                    if attempt < self.max_retries:
                        sleep_for = delay + random.uniform(0, 0.5)
                        logger.warning(f"{last_error}, retrying in {sleep_for:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                        time.sleep(sleep_for)
                        delay *= 2
                        attempt += 1
                        continue
                    raise HubspotAPIError(last_error)

                response.raise_for_status()
                return self._parse_deals_response(response.json())

            except requests.exceptions.RequestException as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    sleep_for = delay + random.uniform(0, 0.5)
                    logger.warning(f"HubSpot API request failed ({last_error}), retrying in {sleep_for:.1f}s")
                    time.sleep(sleep_for)
                    delay *= 2
                    attempt += 1
                    continue
                raise HubspotAPIError(f"HubSpot API request failed after {self.max_retries} retries: {last_error}")

        raise HubspotAPIError(last_error or "Unknown HubSpot API error")

    def _parse_deals_response(self, data: dict) -> Tuple[List[Dict[str, Any]], str, bool]:
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

        start_index = 0
        if after_cursor == "cursor_page_1":
            start_index = 2
        elif after_cursor == "cursor_page_2":
            start_index = 4
        elif after_cursor == "cursor_end":
            return [], None, False

        page_items = all_mock_deals[start_index:start_index + limit]

        next_index = start_index + len(page_items)
        if next_index >= len(all_mock_deals):
            next_cursor = None
            has_more = False
        else:
            next_cursor = f"cursor_page_{ (next_index // 2) }"
            has_more = True

        return page_items, next_cursor, has_more
