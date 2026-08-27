# HubSpot Deals Data Extraction Service (Django Backend)

A production-ready **Django REST Framework (DRF)** application built for extracting, managing, analyzing, and visualizing HubSpot Deals data. This service adheres strictly to [TEST-GUIDELINES-V1.md](https://github.com/greentreegroup/policy/blob/main/TEST-GUIDELINES-V1.md) and the complete **HubSpot DLT Integration Test Deliverables Checklist**.

---

## 📦 Submission Details

- **Target Email**: `jbirch@glynac.ai`
- **Email Subject**: `FINAL BACKEND PROJECT`
- **GitHub Repository**: `https://github.com/SahilSonar-04/Hubspot-Deals-Backend.git`
- **Developer**: Sahil Sonar

---

## 🚀 Key Features

- **Django REST Framework API**: Clean RESTful architecture with DRF.
- **HTTP Header Authentication**: Supports `X-API-Key` and `Authorization: Bearer <token>` headers.
- **Cursor Checkpointing & Job Resume**: Page-by-page cursor tracking (`last_cursor`) with `/api/v1/scan/pause/{job_id}` and `/api/v1/scan/resume/{job_id}` endpoints.
- **ETL Metadata Fields**: Every extracted record includes mandatory `_extracted_at`, `_scan_id`, and `_tenant_id` fields.
- **Interactive Swagger Documentation**: Built with `drf-spectacular` available at `/docs/`.
- **Corporate Analytics Dashboard**: Responsive non-AI light dashboard rendered at `/api/v1/visualizations/dashboard`.
- **Comprehensive Test Suite**: Automated unit and integration tests passing **17/17 tests** cleanly.

---

## 📖 Available API Endpoints

| Method | Endpoint | Description | Headers / Query Params |
|--------|----------|-------------|------------------------|
| `GET` | `/api/v1/health` | Health & DB connectivity check | Optional Auth |
| `POST` | `/api/v1/scan/start` | Start new data extraction job | Body: `{ config }` |
| `POST` | `/api/v1/scan/resume/{job_id}` | **Resume job from cursor checkpoint** | Path: `job_id` |
| `POST` | `/api/v1/scan/pause/{job_id}` | **Pause active scan job** | Path: `job_id` |
| `GET` | `/api/v1/scan/status/{job_id}` | Check status & cursor checkpoint | Path: `job_id` |
| `GET` | `/api/v1/scan/result/{job_id}` | Fetch extracted deal records (Paginated) | Path: `job_id`; Query: `limit`, `offset` |
| `POST` | `/api/v1/scan/cancel/{job_id}` | Cancel pending/running job | Path: `job_id` |
| `DELETE` | `/api/v1/scan/remove/{job_id}` | Delete job and extracted data | Path: `job_id` |
| `GET` | `/api/v1/jobs/jobs` | List all extraction jobs | Query: `organizationId`, `limit`, `offset` |
| `GET` | `/api/v1/jobs/statistics` | Retrieve job summary statistics | None |
| `GET` | `/api/v1/visualizations/dashboard` | **Interactive Analytics Dashboard** | None |

---

## 🧪 Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run test suite with Django test runner
python manage.py test api.tests

# Or run tests using pytest
pytest
```
*Status*: **17/17 tests pass in 0.24s**.
