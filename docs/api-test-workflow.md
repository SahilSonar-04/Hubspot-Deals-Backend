# Data Extraction Service: API Test Workflow Documentation

## Table of Contents
1. [Introduction](#1-introduction)
2. [Test Types Overview](#2-test-types-overview)
3. [Workflow Steps for Seeded Data Tests](#3-workflow-steps-for-seeded-data-tests)
4. [Workflow Steps for Real Extraction Tests](#4-workflow-steps-for-real-extraction-tests)
5. [Common Assertions and Validations](#5-common-assertions-and-validations)
6. [API Endpoints Tested and Their Test Cases](#6-api-endpoints-tested-and-their-test-cases)
7. [Edge Case Tests](#7-edge-case-tests)
   - 7.1. [Description](#71-description)
   - 7.2. [Edge Cases Tested](#72-edge-cases-tested)
8. [Generic Guidelines for Effective API Testing of Extraction Services](#8-generic-guidelines-for-effective-api-testing-of-extraction-services)
   - 8.1. [Understand the API and its Purpose Thoroughly](#81-understand-the-api-and-its-purpose-thoroughly)
   - 8.2. [Define Clear Test Objectives](#82-define-clear-test-objectives)
   - 8.3. [Categorize Your Tests](#83-categorize-your-tests)
   - 8.4. [Design Test Data Strategically](#84-design-test-data-strategically)
   - 8.5. [Prioritize Test Automation](#85-prioritize-test-automation)
   - 8.6. [Implement Robust Assertions and Validations](#86-implement-robust-assertions-and-validations)
   - 8.7. [Handle Dependencies and State](#87-handle-dependencies-and-state)
   - 8.8. [Focus on Observability and Logging](#88-focus-on-observability-and-logging)
   - 8.9. [Documentation and Maintainability](#89-documentation-and-maintainability)
   - 8.10. [Continuous Improvement](#810-continuous-improvement)
9. [Conclusion](#9-conclusion)

---

## 1. Introduction
This document outlines the API testing workflow for the **Data Extraction Service**. The service is designed to extract data from a third-party source (HubSpot CRM). To ensure its reliability, accuracy, and robustness, our testing strategy incorporates two primary types of tests:

- **Seeded Data Tests**: These tests validate core API behavior and internal logic using pre-populated database entries. This approach removes external dependencies, allowing for rapid, controlled, and deterministic testing of internal mechanisms.
- **Real Extraction Tests**: These tests focus on end-to-end functionality by interacting with the third-party API in real-time. They utilize valid API tokens to perform actual data extractions, ensuring seamless integration and data fidelity.
- **Edge Case Tests**: Dedicated tests examining how the service handles invalid inputs, unexpected requests, non-existent entities, and boundary conditions.

---

## 2. Test Types Overview

| Test Type | Description | Primary Use Case |
|-----------|-------------|------------------|
| **Seeded Data Tests** | Utilizes predefined data inserted directly into the test database for controlled, fast, and isolated tests. | Validating internal API logic, data processing, and business rules without external dependencies. |
| **Real Extraction Tests** | Employs actual API tokens for the service provided to trigger live data extractions, validating real-time integration. | Ensuring end-to-end integration, authentication, and data mapping with the external service API. |
| **Edge Case Tests** | Focuses on validating the API's behavior when confronted with invalid inputs, unexpected states, or boundary conditions. | Guaranteeing API robustness, proper error handling, and predictable responses to abnormal scenarios. |

---

## 3. Workflow Steps for Seeded Data Tests

1. **Setup Environment and Data**:
   - Initialize clean test database.
   - Seed database with pre-defined extraction job records (pending, completed, cancelled jobs) and mock deal records (`DealRecord`).
2. **Verify Job Status (`/api/v1/scan/status/<job_id>`)**:
   - Query status endpoint for a seeded job's ID.
   - Assert returned status matches pre-seeded state (`completed`, `pending`).
   - Verify associated metadata (`record_count`, `start_time`, `end_time`).
3. **Fetch Extraction Results (`/api/v1/scan/result/<job_id>`)**:
   - Retrieve extraction results for completed job.
   - Assert returned records match pre-seeded data in content, format, and quantity.
   - Verify pagination (`limit`, `offset`, `total_records`).
4. **List All Jobs (`/api/v1/jobs/jobs`)**:
   - Make GET request to list all extraction jobs.
   - Assert all seeded jobs appear in the response with pagination parity (`has_more`, `next_offset`, `prev_offset`).
5. **Retrieve Job Statistics (`/api/v1/jobs/statistics`)**:
   - Request overall statistics about extraction jobs.
   - Assert metrics (`total_jobs`, `completed_jobs`, `pending_jobs`, `total_records_extracted`) accurately reflect database aggregation.
6. **Health Check (`/api/v1/health`)**:
   - Perform GET request to health endpoint.
   - Assert `{"status": "ok"}` and HTTP 200 OK.
7. **Cancel a Pending Job (`/api/v1/scan/cancel/<job_id>`)**:
   - Send POST request to cancel pre-seeded pending job.
   - Assert HTTP 200 OK and verify status transition to `cancelled`.
8. **Remove Job Data (`/api/v1/scan/remove/<job_id>`)**:
   - Send DELETE request to remove extraction data for seeded job.
   - Assert HTTP 200 OK, then verify subsequent status queries return HTTP 404 Not Found.

---

## 4. Workflow Steps for Real Extraction Tests

1. **Prepare Valid Credentials**:
   - Provide valid API access token (`HUBSPOT_DEALS_API_TOKEN` or `accessToken` in payload).
2. **Start New Extraction (`/api/v1/scan/start`)**:
   - Send POST request with configuration payload.
   - Assert HTTP 202 Accepted status code and extract `job_id`.
3. **Poll Job Status (`/api/v1/scan/status/<job_id>`)**:
   - Query status endpoint until job transitions to `completed` or `failed`.
4. **Retrieve Extracted Results (`/api/v1/scan/result/<job_id>`)**:
   - Fetch extracted deal records and assert HTTP 200 OK.
   - Validate structure of deal records (`deal_id`, `name`, `amount`, `stage`, `pipeline`, `_extracted_at`, `_scan_id`, `_tenant_id`).
5. **Re-start with Updated Configuration**:
   - Re-submit existing `scanId` with modified filters or organization and verify configuration updates dynamically.
6. **Remove Extraction Data (`/api/v1/scan/remove/<job_id>`)**:
   - Send DELETE request to clean up test data and verify 404 on subsequent queries.

---

## 5. Common Assertions and Validations

- **HTTP Status Codes**: Strict matching (200 OK, 202 Accepted, 400 Bad Request, 401 Unauthorized, 404 Not Found, 503 Service Unavailable).
- **Job Status Transitions**: Verification of lifecycle progression (`pending` -> `in_progress` -> `completed` / `cancelled` / `failed`).
- **Response Body Content**: Standardized envelope verification (`{ "error": "...", "status_code": 400 }`), data integrity, and mandatory ETL metadata presence.
- **Pagination & Capping**: Validation of `limit` (capped at 100) and `offset` ranges.

---

## 6. API Endpoints Tested and Their Test Cases

| Endpoint | HTTP Method | Tested In | Description |
|----------|-------------|-----------|-------------|
| `/api/v1/scan/start` | POST | Real Extraction Test, Edge Case Test | Initiates new data extraction job with token authentication. |
| `/api/v1/scan/status/<job_id>` | GET | Both Tests, Edge Case Test | Retrieves status, progress, and checkpoint state. |
| `/api/v1/scan/result/<job_id>` | GET | Both Tests, Edge Case Test | Fetches extracted data for completed job (Paginated). |
| `/api/v1/scan/resume/<job_id>` | POST | Checkpoint Resume Test | Resumes extraction from pagination cursor checkpoint. |
| `/api/v1/scan/pause/<job_id>` | POST | Checkpoint Resume Test | Pauses active background extraction. |
| `/api/v1/scan/cancel/<job_id>` | POST | Seeded Data Test, Edge Case Test | Cancels pending/running extraction job. |
| `/api/v1/scan/remove/<job_id>` | DELETE | Both Tests, Edge Case Test | Deletes all stored extraction records for job. |
| `/api/v1/jobs/jobs` | GET | Seeded Data Test, Edge Case Test | Lists extraction jobs with pagination. |
| `/api/v1/jobs/statistics` | GET | Seeded Data Test | Aggregated job statistics and calculated durations. |
| `/api/v1/pipeline/info` | GET | Seeded Data Test | Dynamic pipeline and system health metrics. |
| `/api/v1/health` | GET | Both Tests | Health and database connectivity check. |
| `/api/v1/metrics` | GET | Edge Case Test | Prometheus telemetry metrics. |
| `/api/v1/visualizations/dashboard` | GET | Auth Test | Interactive visual analytics dashboard. |
| `/api/v1/visualizations/data` | GET | Auth Test | Aggregated analytics chart data. |

---

## 7. Edge Case Tests

### 7.1. Description
Edge case tests verify system behavior when encountering malformed payloads, invalid parameters, unauthorized attempts, and boundary conditions.

### 7.2. Edge Cases Tested
1. **Invalid or Missing Authentication Token**:
   - Unauthorized access attempts return `401 Unauthorized`.
   - Missing required authentication fields return `400 Bad Request` with standardized error envelope.
2. **Non-Existent Job ID**:
   - Querying status, results, cancel, or remove for non-existent `job_id` returns `404 Not Found`.
3. **Cancelling an Already Completed Job**:
   - Attempting to cancel an already completed job returns `400 Bad Request` with a clear message stating the job cannot be cancelled in its completed state.
4. **Invalid Pagination Parameters**:
   - Non-integer string limits (`?limit=invalid_string`) or negative offsets (`?offset=-10`) return `400 Bad Request`.
5. **Pagination Limit Capping**:
   - Excessively large limits are capped to 100 to prevent unbounded memory usage.
6. **Mock Mode Protection**:
   - In production environments (`DEBUG=False`), placeholder and test tokens are rejected rather than returning fabricated mock data.

---

## 8. Generic Guidelines for Effective API Testing of Extraction Services

1. **Understand the API and Its Purpose Thoroughly**: Map extraction fields, filters, authentication schemes, and asynchronous job states.
2. **Define Clear Test Objectives**: Test success paths, negative paths, boundary conditions, and security assertions.
3. **Categorize Your Tests**: Divide tests into Unit, Integration, Seeded Data, Real Extraction, and Edge Case suites.
4. **Design Test Data Strategically**: Utilize isolated test databases and deterministic mock datasets alongside live integration accounts.
5. **Prioritize Test Automation**: Maintain 100% automated test execution via pytest and CI/CD pipelines.
6. **Implement Robust Assertions**: Validate status codes, response schemas, error envelopes, and database state transitions.
7. **Handle Dependencies and State**: Ensure complete test teardown between runs to prevent state pollution.
8. **Focus on Observability and Logging**: Leverage structured JSON logs and Prometheus metrics for diagnostic telemetry.
9. **Documentation and Maintainability**: Keep test workflow documentation synchronized with codebase features.
10. **Continuous Improvement**: Automate regression test suites on every commit via GitHub Actions.

---

## 9. Conclusion
This workflow document outlines the testing architecture for the HubSpot Deals Data Extraction Service. Adherence to these testing workflows guarantees high reliability, complete data fidelity, and resilience across production deployments.
