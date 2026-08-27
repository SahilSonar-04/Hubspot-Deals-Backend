# HubSpot Developer Account & Test Data Setup

## Overview
This document records the setup of the HubSpot Developer Account, Private App configuration, and test deal records created for validating the extraction service.

---

## 1. Developer Account & Private App Configuration
- **Developer Portal**: [HubSpot Developer Portal](https://developers.hubspot.com/)
- **App Name**: `DLT Deals Extractor`
- **Authentication Method**: Private App Access Token (Bearer)
- **Assigned Scopes**:
  - `crm.objects.deals.read` (Read deals data)
  - `crm.schemas.deals.read` (Read deals schema definitions)
- **Token Security**: Tokens are configured via `HUBSPOT_DEALS_API_TOKEN` and encrypted at rest in PostgreSQL using Fernet 256-bit symmetric encryption.

---

## 2. Test Deal Records Created

| Deal ID | Deal Name | Amount ($) | Stage | Projected Close Date | Description |
|---------|-----------|------------|-------|----------------------|-------------|
| `101` | Small Business Starter Package | $5,000.00 | `qualifiedtobuy` | 2026-03-15 | Introductory CRM setup and pipeline onboarding. |
| `102` | Mid-Market Growth Retainer | $25,000.00 | `presentationscheduled` | 2026-04-30 | Quarterly consulting and sales enablement retainer. |
| `103` | Enterprise Cloud Migration | $50,000.00 | `decisionmakerboughtin` | 2026-05-15 | Multi-region cloud migration and modernization. |
| `104` | Global Systems Integration | $75,000.00 | `closedlost` | 2026-02-28 | ERP integration. Lost due to client budget realignment. |
| `105` | Annual Enterprise SaaS License | $100,000.00 | `closedwon` | 2026-06-30 | 500-seat enterprise annual subscription. |

*JSON representation saved in `test-results/test_deals.json`.*

---

## 3. Data Extraction & Checkpoint Verification
- All 5 test deals are extracted via the extraction pipeline with transformation into relational `DealRecord` rows.
- Multi-tenant metadata fields (`_extracted_at`, `_scan_id`, `_tenant_id`) are populated on every extracted record.
