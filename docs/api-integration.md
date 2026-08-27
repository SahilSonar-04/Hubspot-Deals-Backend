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
- **Base URL**: `https://api.hubapi.com`
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

## 4. HubSpot Deal Properties Reference

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
| `description` | String | Detailed description/notes of the deal |
| `dealtype` | String | Deal classification (e.g., `newbusiness`, `existingbusiness`) |

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
