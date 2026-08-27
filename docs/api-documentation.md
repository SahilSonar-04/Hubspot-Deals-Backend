# Service API Specification Documentation

## Overview
This document describes the REST API endpoints exposed by the **HubSpot Deals Data Extraction Service**.

---

## Authentication Methods
The service supports two authentication methods for security compliance:
1. **API Key Header**: `X-API-Key: <YOUR_API_KEY>`
2. **Bearer Token Header**: `Authorization: Bearer <YOUR_ACCESS_TOKEN>`

---

## Interactive Swagger UI
Access interactive Swagger UI documentation at **`http://localhost:8000/docs/`** or OpenAPI schema at **`http://localhost:8000/api/schema/`**.

---

## API Endpoints Reference

### 1. Health Check
- **Endpoint**: `GET /api/v1/health`
- **Description**: Verifies service status and database connection health.
- **Response**: `200 OK`

---

### 2. Start Scan Job (with Checkpointing)
- **Endpoint**: `POST /api/v1/scan/start`
- **Headers**: `Authorization: Bearer <token>` or `X-API-Key: <key>`
- **Description**: Initiates a new HubSpot Deals extraction scan.
- **Request Body**:
```json
{
  "config": {
    "scanId": "hubspot-scan-001",
    "organizationId": "org-12345",
    "type": ["data"],
    "auth": {
      "accessToken": "your-hubspot-access-token"
    },
    "filters": {
      "properties": ["dealname", "amount", "dealstage"],
      "includeArchived": false
    }
  }
}
```
- **Response**: `202 Accepted`

---

### 3. Pause & Resume Scan Job (Checkpointing)
- **Pause Endpoint**: `POST /api/v1/scan/pause/<job_id>`
- **Resume Endpoint**: `POST /api/v1/scan/resume/<job_id>`
- **Description**: Pauses an active job or resumes an extraction from the last saved pagination cursor (`last_cursor`).

---

### 4. Get Scan Status & Checkpoints
- **Endpoint**: `GET /api/v1/scan/status/<job_id>`
- **Description**: Returns execution status, pagination cursor, pages processed, and checkpoint metadata.

---

### 5. Fetch Scan Results (Paginated)
- **Endpoint**: `GET /api/v1/scan/result/<job_id>`
- **Query Params**: `limit` (default 10), `offset` (default 0)
- **Description**: Returns extracted deal records with pagination metadata (`total_records`, `has_more`, `next_offset`, `prev_offset`).
