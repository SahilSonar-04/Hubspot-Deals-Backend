# HubSpot CRM API Integration Documentation

## Overview
This document details the integration between the **Data Extraction Service** and the **HubSpot CRM API v3 (Deals Endpoint)**.

---

## 1. Authentication
- **Authentication Type**: Bearer Token (Private App Access Token)
- **Header**: `Authorization: Bearer <YOUR_HUBSPOT_PRIVATE_APP_TOKEN>`
- **Required Scopes**: `crm.objects.deals.read`

---

## 2. Target Endpoint
- **Base URL**: `https://api.hubapi.com`
- **Endpoint**: `/crm/v3/objects/deals`
- **HTTP Method**: `GET`

---

## 3. Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | Integer | No | `50` | Number of deal records to return (max 100) |
| `after` | String | No | `None` | Paging cursor for fetching next page of results |
| `properties` | String | No | `dealname,amount,dealstage,pipeline,closedate` | Comma-separated list of deal properties |
| `archived` | Boolean | No | `false` | Whether to include archived deals |

---

## 4. Response Structure Example

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
    }
  ],
  "paging": {
    "next": {
      "after": "NTB="
    }
  }
}
```

---

## 5. Rate Limiting & Error Handling

- **HubSpot Rate Limits**: 150 requests per 10 seconds for standard Private Apps.
- **Handling Strategy**: Exponential backoff with jitter on HTTP `429 Too Many Requests`.
- **Common Status Codes**:
  - `200 OK`: Successful response.
  - `401 Unauthorized`: Invalid or expired Private App access token.
  - `429 Too Many Requests`: Rate limit exceeded.
  - `500 Internal Server Error`: HubSpot server issue.
