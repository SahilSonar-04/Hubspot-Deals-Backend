# Service API Specification Documentation

## Overview
This document describes the complete REST API interface exposed by the **HubSpot Deals Data Extraction Service**.

---

## 1. Authentication Methods
The service supports two authentication methods for security compliance:
1. **API Key Header**: `X-API-Key: <YOUR_API_KEY>`
2. **Bearer Token Header**: `Authorization: Bearer <YOUR_ACCESS_TOKEN>`

---

## 2. Interactive Swagger UI & OpenAPI Specification
- **Interactive Swagger UI**: `http://localhost:8000/docs/`
- **Raw OpenAPI Schema**: `http://localhost:8000/api/schema/`

---

## 3. Complete API Endpoints Reference

### 3.1. Health Check
- **Endpoint**: `GET /api/v1/health`
- **Auth Required**: No
- **Description**: Verifies service status and database connectivity.
- **Response**: `200 OK`
```json
{
  "status": "ok",
  "service": "hubspot_deals_extraction_service",
  "version": "1.0.0",
  "database": "connected"
}
```

---

### 3.2. Start Scan Job
- **Endpoint**: `POST /api/v1/scan/start`
- **Query Params**: `?async=true` (for non-blocking background worker execution)
- **Auth Required**: Yes
- **Request Body**:
```json
{
  "config": {
    "scanId": "hubspot-scan-001",
    "organizationId": "org-corp-01",
    "type": ["data"],
    "auth": {
      "accessToken": "your-hubspot-access-token"
    },
    "filters": {
      "properties": ["dealname", "amount", "dealstage", "pipeline", "closedate"],
      "includeArchived": false
    }
  }
}
```
- **Response**: `202 Accepted`
```json
{
  "status": "in_progress",
  "message": "Scan job 'hubspot-scan-001' initiated successfully.",
  "job_id": "hubspot-scan-001"
}
```

---

### 3.3. Check Scan Status & Checkpoints
- **Endpoint**: `GET /api/v1/scan/status/<job_id>`
- **Auth Required**: Yes
- **Response**: `200 OK`
```json
{
  "job_id": "hubspot-scan-001",
  "organization_id": "org-corp-01",
  "status": "completed",
  "record_count": 5,
  "pages_processed": 3,
  "last_cursor": null,
  "checkpoint_data": {
    "last_checkpoint_at": "2026-08-27T23:55:00.000Z",
    "last_cursor": null,
    "pages_processed": 3,
    "total_records": 5
  },
  "start_time": "2026-08-27T23:54:55.000Z",
  "end_time": "2026-08-27T23:55:00.000Z"
}
```

---

### 3.4. Fetch Scan Results (Paginated)
- **Endpoint**: `GET /api/v1/scan/result/<job_id>`
- **Auth Required**: Yes
- **Query Params**: `limit` (default 10, max 100), `offset` (default 0), `tableName` (`deal_records`)
- **Response**: `200 OK`
```json
{
  "job_id": "hubspot-scan-001",
  "total_records": 5,
  "limit": 10,
  "offset": 0,
  "next_offset": null,
  "prev_offset": null,
  "has_more": false,
  "results": [
    {
      "deal_id": "101",
      "name": "Small Business Starter Package",
      "amount": "5000.00",
      "stage": "qualifiedtobuy",
      "pipeline": "default",
      "close_date": "2026-03-15T00:00:00Z",
      "archived": false,
      "_extracted_at": "2026-08-27T23:55:00.000Z",
      "_scan_id": "hubspot-scan-001",
      "_tenant_id": "org-corp-01"
    }
  ]
}
```

---

### 3.5. Pause Scan Job
- **Endpoint**: `POST /api/v1/scan/pause/<job_id>`
- **Auth Required**: Yes
- **Description**: Atomically halts an active asynchronous extraction job and saves checkpoint.
- **Response**: `200 OK`

---

### 3.6. Resume Scan Job
- **Endpoint**: `POST /api/v1/scan/resume/<job_id>`
- **Auth Required**: Yes
- **Description**: Continues extraction starting from `last_cursor` without duplicating stored records.
- **Response**: `200 OK`

---

### 3.7. Cancel Scan Job
- **Endpoint**: `POST /api/v1/scan/cancel/<job_id>`
- **Auth Required**: Yes
- **Description**: Cancels pending or running extraction job. Returns `400 Bad Request` if already completed.
- **Response**: `200 OK`

---

### 3.8. Remove Scan Job Data
- **Endpoint**: `DELETE /api/v1/scan/remove/<job_id>`
- **Auth Required**: Yes
- **Description**: Deletes all stored deals and metadata for the job.
- **Response**: `200 OK`

---

### 3.9. List All Jobs
- **Endpoint**: `GET /api/v1/jobs/jobs`
- **Auth Required**: Yes
- **Query Params**: `limit`, `offset`, `status`
- **Response**: `200 OK`

---

### 3.10. Job Statistics
- **Endpoint**: `GET /api/v1/jobs/statistics`
- **Auth Required**: Yes
- **Response**: `200 OK` (Summary counts and dynamically calculated extraction durations)

---

### 3.11. Observability Metrics
- **Endpoint**: `GET /api/v1/metrics`
- **Auth Required**: No
- **Response**: `200 OK` (Prometheus exposition format)

---

### 3.12. Analytics Dashboard & Data
- **Dashboard UI**: `GET /api/v1/visualizations/dashboard` (HTML UI, Auth Required)
- **Dashboard JSON Data**: `GET /api/v1/visualizations/data` (JSON analytics, Auth Required)
