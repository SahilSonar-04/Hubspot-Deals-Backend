# Database Schema Design Documentation

## Overview
This document details the PostgreSQL / Django database schema design for storing extracted **HubSpot Deals** data, extraction jobs, and pipeline execution telemetry.

---

## 1. Relational Schema Diagram & Models

### `api_extractionjob` Table
Stores scan metadata, status lifecycle, and pagination checkpoint state.

```sql
CREATE TABLE api_extractionjob (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    organization_id VARCHAR(255),
    scan_type JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending | in_progress | paused | completed | failed | cancelled
    record_count INT NOT NULL DEFAULT 0,
    error_message TEXT,
    filters JSONB NOT NULL DEFAULT '{}'::jsonb,
    auth_config JSONB NOT NULL DEFAULT '{}'::jsonb, -- stores token_provided flag and accessToken (plaintext, required for resume)
    start_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_cursor VARCHAR(255),
    pages_processed INT NOT NULL DEFAULT 0,
    checkpoint_data JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_extractionjob_job_id ON api_extractionjob(job_id);
CREATE INDEX idx_extractionjob_org_id ON api_extractionjob(organization_id);
CREATE INDEX idx_extractionjob_status ON api_extractionjob(status);
```

`auth_config.accessToken` is stored so `/scan/resume/{job_id}` can continue extraction without the caller resupplying credentials. This is plaintext in the current implementation and is never returned by the API (`ExtractionJobSerializer` omits `auth_config`); a production deployment should move this to a proper secrets store.

---

### `api_dealrecord` Table
Stores extracted deal properties along with mandatory ETL metadata fields for multi-tenant data isolation.

```sql
CREATE TABLE api_dealrecord (
    id BIGSERIAL PRIMARY KEY,
    job_id BIGINT NOT NULL REFERENCES api_extractionjob(id) ON DELETE CASCADE,
    deal_id VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL DEFAULT '',
    amount NUMERIC(15, 2),
    stage VARCHAR(255) NOT NULL DEFAULT 'appointmentscheduled',
    pipeline VARCHAR(255) NOT NULL DEFAULT 'default',
    close_date TIMESTAMPTZ,
    archived BOOLEAN NOT NULL DEFAULT FALSE,
    properties JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    _extracted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    _scan_id VARCHAR(255) NOT NULL DEFAULT '',
    _tenant_id VARCHAR(255) NOT NULL DEFAULT 'default-tenant'
);

CREATE INDEX idx_dealrecord_deal_id ON api_dealrecord(deal_id);
CREATE INDEX idx_dealrecord_stage ON api_dealrecord(stage);
CREATE INDEX idx_dealrecord_tenant ON api_dealrecord(_tenant_id);
CREATE INDEX idx_dealrecord_scan ON api_dealrecord(_scan_id);
```

---

## 2. Mandatory ETL Metadata Fields

| Field Name | Type | Description |
|------------|------|-------------|
| `_extracted_at` | TIMESTAMPTZ | Timestamp when the record was extracted from HubSpot |
| `_scan_id` | VARCHAR(255) | Identifier of the extraction job scan |
| `_tenant_id` | VARCHAR(255) | Organization / Tenant ID for multi-tenant isolation |

---

## 3. Checkpoint & Resume Fields

| Field Name | Type | Description |
|------------|------|-------------|
| `last_cursor` | VARCHAR(255) | HubSpot pagination cursor to resume from |
| `pages_processed` | INT | Number of pages fetched so far |
| `checkpoint_data` | JSONB | Snapshot of checkpoint state (cursor, page count, record count, timestamp) |
| `auth_config.accessToken` | JSONB field | Real access token retained for resume; not exposed via API |

---

## 4. Data Type Mapping

| HubSpot CRM Property | HubSpot Type | PostgreSQL / Django Field | Notes |
|----------------------|--------------|---------------------------|-------|
| `id` | String | `VARCHAR(255)` / `CharField` | Primary deal identifier |
| `dealname` | String | `VARCHAR(500)` / `CharField` | Name of the deal |
| `amount` | Number/String | `NUMERIC(15, 2)` / `DecimalField` | Deal monetary value |
| `dealstage` | String | `VARCHAR(255)` / `CharField` | Pipeline stage |
| `pipeline` | String | `VARCHAR(255)` / `CharField` | Associated pipeline ID |
| `closedate` | ISO Timestamp | `TIMESTAMPTZ` / `DateTimeField` | Target or actual close date |
| `archived` | Boolean | `BOOLEAN` / `BooleanField` | Deletion/archive status |
