# Phase 3A-2.2-B Real Sync Test Report V1

## Offline Tests

| Suite | Tests | Pass | Fail |
|---|---:|---:|---:|
| Real-client safety tests | 9 | 9 | 0 |
| Existing sync-adapter tests | 20 | 20 | 0 |
| Existing Prospecting Engine tests | 219 | 219 | 0 |

The real-client tests cover local-only URL enforcement, explicit test environment flag, environment credential loading, token authentication path, metadata preflight success/failure handling, synthetic Lead/evidence body field limits, marker injection, and external path rejection.

## Local Read-Only Test

| Check | Result |
|---|---|
| Target static identity | PASS - Docker Compose project `espocrm-test`, local port 8080 |
| Remote/Railway target used | NO |
| Authentication with raw `Espo-Authorization` | FAIL - HTTP 401 |
| Authentication with standard `Authorization: Basic` | FAIL - HTTP 401 |
| Metadata preflight | NOT RUN - authentication gate denied |
| Lead creation | NOT RUN |
| ResearchEvidence creation | NOT RUN |
| Relationship link | NOT RUN |
| Idempotency/duplicate test | NOT RUN |
| Rollback call | NOT REQUIRED - no records were created |

## Side-Effect Inventory

- Local HTTP requests: authentication only, both read-only `GET /api/v1/App/user` calls.
- Database writes: zero.
- Lead/Evidence/relationship writes: zero.
- Production/Railway calls: zero.
- Email, SMTP, DeepSeek, Apify, and Playwright: zero.

`pytest` is unavailable in the local Python runtime; repository `unittest` suites were run directly.
