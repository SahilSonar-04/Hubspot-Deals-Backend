# HubSpot CRM API Integration Documentation

## Overview
This document details the integration between the **HubSpot Deals Data Extraction Service** and the **HubSpot CRM API v3 (Deals Endpoint)**.

---

## 1. Authentication
- **Authentication Type**: Bearer Token (Private App Access Token)
- **Header**: `Authorization: Bearer <YOUR_HUBSPOT_PRIVATE_APP_TOKEN>`
- **Required Scopes**: `crm.objects.deals.read`
- **Security Storage**: Access tokens are encrypted at rest inside `ExtractionJob.auth_config` using Fernet symmetric encryption with 32-byte key derivation.

---

## 2. Target Endpoint & Method
- **Base URL**: `https://api.hubapi.com` (configurable via `HUBSPOT_DEALS_API_BASE_URL`)
- **Endpoint**: `/crm/v3/objects/deals`
- **HTTP Method**: `GET`

---

## 3. Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | Integer | No | `50` | Number of deal records to return per page (max 100). |
| `after` | String | No | `None` | Paging cursor for fetching the next page of results. |
| `properties` | String | No | `dealname,amount,dealstage,pipeline,closedate` | Comma-separated list of deal properties to fetch. |
| `archived` | Boolean | No | `false` | Whether to include archived/deleted deals. |

---

## 4. Comprehensive HubSpot Deal Properties Reference

### 4.1. Core Deal Properties
| Property Name | Data Type | Description |
|---------------|-----------|-------------|
| `dealname` | String | Name of the deal opportunity |
| `amount` | Number/Decimal | Total monetary value of the deal |
| `dealstage` | String | Current pipeline stage (e.g., `qualifiedtobuy`, `closedwon`, `closedlost`) |
| `pipeline` | String | Associated sales pipeline identifier (default: `default`) |
| `closedate` | ISO-8601 Timestamp | Projected or actual close date |
| `createdate` | ISO-8601 Timestamp | Record creation timestamp in HubSpot CRM |
| `hs_lastmodifieddate` | ISO-8601 Timestamp | Timestamp when the deal was last updated |
| `hubspot_owner_id` | String | Identifier of the CRM deal owner |
| `description` | String | Detailed description and notes about the opportunity |
| `dealtype` | String | Classification of deal (`newbusiness`, `existingbusiness`) |

### 4.2. Forecasting & Stage Probability
| Property Name | Data Type | Description |
|---------------|-----------|-------------|
| `hs_deal_stage_probability` | Number | Probability percentage of winning the deal based on stage |
| `hs_forecast_amount` | Number/Decimal | Forecasted weighted revenue contribution |
| `hs_is_closed` | Boolean | Whether the deal has reached a closed stage |
| `hs_is_closed_won` | Boolean | Flag indicating if the deal was successfully closed won |
| `hs_is_closed_lost` | Boolean | Flag indicating if the deal was marked as closed lost |
| `hs_days_to_close_raw` | Integer | Number of days elapsed between creation and close date |
| `hs_projected_amount` | Number/Decimal | Projected revenue amount calculated across sales cycles |

### 4.3. Financial & Revenue Properties
| Property Name | Data Type | Description |
|---------------|-----------|-------------|
| `hs_acv` | Number/Decimal | Annual Contract Value |
| `hs_arr` | Number/Decimal | Annual Recurring Revenue |
| `hs_mrr` | Number/Decimal | Monthly Recurring Revenue |
| `hs_tcv` | Number/Decimal | Total Contract Value |

### 4.4. Association & Activity Metadata
| Property Name | Data Type | Description |
|---------------|-----------|-------------|
| `num_associated_contacts` | Integer | Count of contacts associated with this deal |
| `num_notes` | Integer | Total number of notes logged against the deal |
| `num_contacted_notes` | Integer | Count of outreach notes |
| `hs_analytics_source` | String | Original marketing channel/source of the deal |

---

## 5. Response Structure Example

```json
{
  "results": [
    {
      "id": "101",
      "properties": {
        "amount": "5000.00",
        "closedate": "2026-03-15T00:00:00Z",
        "createdate": "2026-01-10T12:00:00Z",
        "dealname": "Small Business Starter Package",
        "dealstage": "qualifiedtobuy",
        "pipeline": "default"
      },
      "createdAt": "2026-01-10T12:00:00Z",
      "updatedAt": "2026-02-01T15:30:00Z",
      "archived": false
    },
    {
      "id": "102",
      "properties": {
        "amount": "25000.00",
        "closedate": "2026-04-30T00:00:00Z",
        "createdate": "2026-01-15T10:00:00Z",
        "dealname": "Mid-Market Growth Retainer",
        "dealstage": "presentationscheduled",
        "pipeline": "default"
      },
      "createdAt": "2026-01-15T10:00:00Z",
      "updatedAt": "2026-02-05T11:20:00Z",
      "archived": false
    }
  ],
  "paging": {
    "next": {
      "after": "cursor_page_1"
    }
  }
}
```

---

## 6. Rate Limiting & Error Handling

- **HubSpot Rate Limits**: 150 requests per 10-second sliding window for standard Private Apps (100 req/10s burst limit).
- **Retry Mechanism**: Implemented in `HubspotAPIService._fetch_with_retry` using exponential backoff with random jitter (base delay 1.0s, multiplier 2.0x, max retries 3).
- **HTTP Status Codes Handled**:
  - `200 OK`: Successful page response parsed into internal deal structures.
  - `401 Unauthorized`: Invalid/expired access token (fails closed).
  - `429 Too Many Requests`: Rate limit reached; triggers backoff retry loop.
  - `500/502/503`: Upstream HubSpot CRM server errors; retried up to max retries before raising `HubspotAPIError`.
