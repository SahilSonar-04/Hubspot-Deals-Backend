# HubSpot Deals Data Extraction Service

A robust, enterprise-grade **Django REST Framework (DRF)** backend service designed for extracting, processing, checkpointing, and visualizing HubSpot Deals data.

---

## 🚀 Key Architectural Features

- **Layered Architecture**: Clear separation across Controller (`api/views.py`), Service (`api/services/`), and Data Access (`api/models.py`) layers.
- **Security & Authentication**: HTTP Header Authentication supporting `X-API-Key` and `Authorization: Bearer <token>` with production secret key isolation.
- **Token Security at Rest**: Fernet-encrypted credentials storage for secure scan resumption.
- **Cursor Checkpointing & Resume**: Resilient page-by-page cursor tracking (`last_cursor`) with `/api/v1/scan/pause/{job_id}` and `/api/v1/scan/resume/{job_id}`.
- **Asynchronous Execution**: Background execution support with in-flight cancellation and pause capabilities.
- **Multi-Tenant ETL Metadata**: Every extracted record includes mandatory `_extracted_at`, `_scan_id`, and `_tenant_id` columns.
- **Centralized Logging & Exception Handling**: Structured rotating file logs and standardized JSON error formatting.
- **Rate Limiting & Throttling**: DRF throttling configured across endpoints.
- **Prometheus Observability**: Telemetry and health metrics exposed at `/api/v1/metrics`.
- **Interactive OpenAPI Documentation**: Interactive Swagger UI served at `/docs/` and raw OpenAPI schema at `/api/schema/`.
- **Analytics Dashboard**: Corporate visual telemetry dashboard at `/api/v1/visualizations/dashboard`.

---

## 📖 API Endpoints Reference

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/health` | Service health & database connectivity check | No |
| `GET` | `/api/v1/metrics` | Prometheus observability metrics | No |
| `POST` | `/api/v1/scan/start` | Initiate new data extraction scan job (`async: true` for non-blocking background execution) | Yes |
| `POST` | `/api/v1/scan/resume/{job_id}` | Resume scan from pagination checkpoint | Yes |
| `POST` | `/api/v1/scan/pause/{job_id}` | Pause active background/async extraction scan mid-flight | Yes |
| `GET` | `/api/v1/scan/status/{job_id}` | Get scan lifecycle status & checkpoint data | Yes |
| `GET` | `/api/v1/scan/result/{job_id}` | Fetch extracted deal records (Paginated) | Yes |
| `POST` | `/api/v1/scan/cancel/{job_id}` | Cancel pending or running scan job | Yes |
| `DELETE` | `/api/v1/scan/remove/{job_id}` | Remove scan job and associated records | Yes |
| `GET` | `/api/v1/jobs/jobs` | List extraction jobs with pagination | Yes |
| `GET` | `/api/v1/jobs/statistics` | Summary metrics & average extraction durations | Yes |
| `GET` | `/api/v1/pipeline/info` | Pipeline metadata & dynamic status check | Yes |
| `GET` | `/api/v1/stats` | Overall service and pipeline statistics | Yes |
| `GET` | `/api/v1/visualizations/data` | JSON data endpoint for visualization metrics | Yes |
| `GET` | `/api/v1/visualizations/dashboard` | Visual analytics & telemetry dashboard | Yes |

---

## 🛠️ Quick Start & Local Setup

### 1. Prerequisites
- Python 3.11+
- Virtualenv (`python3 -m venv venv`)
- Docker & Docker Compose (Optional)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/SahilSonar-04/Hubspot-Deals-Backend.git
cd Hubspot-Deals-Backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install runtime dependencies
pip install -r requirements.txt

# Install dev/test dependencies
pip install -r requirements-test.txt

# Configure environment variables
cp .env.example .env

# Run database migrations
python manage.py migrate

# Start the development server
python manage.py runserver 0.0.0.0:8000
```

---

## 🐳 Docker Deployment

### Local Development:
```bash
# Start dev services with automatic reload & Postgres readiness gating
docker compose up --build -d

# View logs
docker compose logs -f web
```

### Production Deployment:
```bash
# Start production Gunicorn cluster with non-root user & secure env
docker compose -f docker-compose.prod.yml up --build -d
```

---

## 🧪 Running Automated Tests

```bash
# Run unit and integration tests with Django test runner
python manage.py test api.tests

# Or run tests using pytest
pytest
```
*Status*: **20 / 20 tests pass in 0.25s**.

---

## 🔒 Configuration & Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `False` |
| `SECRET_KEY` | Django cryptographic signing key | (Required in production) |
| `HUBSPOT_DEALS_API_TOKEN` | HubSpot CRM Private App Access Token | `""` |
| `API_AUTH_TOKEN` | Dedicated API access authentication token | `""` |
| `TOKEN_ENCRYPTION_KEY` | Fernet 32-byte encryption key for token at rest | (Derived from `SECRET_KEY`) |
| `EXTRACTION_MAX_PAGES` | Maximum pagination pages to extract per scan | `10` |
| `EXTRACTION_PAGE_LIMIT` | Records per HubSpot page query | `10` |
| `DB_HOST` | PostgreSQL database host | `""` (SQLite fallback) |
| `DB_NAME` | PostgreSQL database name | `""` |
| `DB_USER` | PostgreSQL user | `""` |
| `DB_PASSWORD` | PostgreSQL password | `""` |
