# Phase 3A-2.2-B Auth Precheck Report V1

**Status:** BLOCKED — credential missing on host  
**Date:** 2026-07-10  
**Scope:** Authentication and environment verification only  
**Mutations performed:** NONE

## Purpose

Restore the authentication precondition for Phase 3A-2.2-B Real EspoCRM Test Sync without modifying business code, Sync Contract, or EspoCRM data.

## Code Inspection — `integration/espocrm_sync/real_client.py`

No production code was modified. Current client behavior:

| Item | Value |
|---|---|
| Env gate | `ESPOCRM_TEST_ENV` must equal `true` |
| Base URL | `ESPOCRM_TEST_URL` or default `http://localhost:8080` |
| API key env | `ESPOCRM_TEST_API_KEY` |
| Username env | `ESPOCRM_TEST_USERNAME` or `ESPOCRM_ADMIN_USERNAME` |
| Password env | `ESPOCRM_TEST_PASSWORD` or `ESPOCRM_ADMIN_PASSWORD` |
| API key header | `X-Api-Key: <key>` |
| Basic auth headers | `Espo-Authorization: base64(user:pass)` then fallback `Authorization: Basic ...` |
| Auth probe endpoint | `GET /api/v1/App/user` |
| Safety | Only `http://localhost:8080` is permitted |

Header format matches EspoCRM documentation (`X-Api-Key` for API Users). This is not a code-format defect.

## Environment Variables (host session)

| Variable | Present | Notes |
|---|---|---|
| `ESPOCRM_TEST_ENV` | NO | Required by `from_environment()` |
| `ESPOCRM_TEST_URL` | NO | Defaults to `http://localhost:8080` |
| `ESPOCRM_TEST_API_KEY` | NO | **Missing — not auto-created** |
| `ESPOCRM_TEST_USERNAME` | NO | |
| `ESPOCRM_TEST_PASSWORD` | NO | |
| `ESPOCRM_ADMIN_USERNAME` | NO | |
| `ESPOCRM_ADMIN_PASSWORD` | NO | |

`ESPOCRM_TEST_API_KEY` does not exist in the current host environment. Per instructions, it was not created.

## Docker

| Check | Result |
|---|---|
| Docker available | YES |
| `espocrm` container | Up, healthy, `0.0.0.0:8080->80/tcp` |
| `espocrm-db` | Up, healthy |
| `espocrm-daemon` | Up, healthy |
| Compose target | Local test stack on localhost:8080 |

Container env names include `ESPOCRM_ADMIN_USERNAME` / `ESPOCRM_ADMIN_PASSWORD`, but those values are **not** exported into the current host shell. No API-key-related container env var exists.

## API Reachability

| Request | Result |
|---|---|
| `GET http://localhost:8080/` | HTTP 200 |
| `GET /api/v1/App/user` (no auth) | HTTP 401 (expected) |

EspoCRM HTTP API is reachable. Unauthenticated access is correctly rejected.

## Authentication Attempts

| Attempt | Result |
|---|---|
| `X-Api-Key` via `ESPOCRM_TEST_API_KEY` | SKIPPED — env var missing |
| Username/password Basic / Espo-Authorization | SKIPPED — host credentials missing |

No authenticated `GET /api/v1/App/user` call succeeded because no usable host credential was available.

Prior Phase 3A-2.2-B reports already recorded that container administrator credentials returned HTTP 401 for both Basic header forms. This precheck did not re-extract or retry those secrets, and did not create Leads or write CRM data.

## Failure Analysis

| Candidate cause | Assessment |
|---|---|
| API Key does not exist on host | **YES — primary blocker** |
| API Key wrong | N/A — no key present to test |
| User permission insufficient | Not reachable yet — auth never succeeded |
| Header format error | **NO** — `X-Api-Key` matches EspoCRM docs and `real_client.py` |
| EspoCRM down / unreachable | **NO** — Docker healthy, root HTTP 200 |
| EspoCRM config / no API User | Likely secondary — container has admin env names but no API key env; dedicated API User may not be provisioned |

**Root cause for this session:** host credential absence (`ESPOCRM_TEST_API_KEY` and username/password env vars missing), not a Sync Adapter / Real Client code defect.

## Actions Not Performed

- No POST Lead
- No POST ResearchEvidence
- No relationship writes
- No DELETE / rollback
- No business code changes
- No Sync Contract changes
- No credential auto-creation
- No password reset
- No database modification

## Validation Summary

| Check | Result |
|---|---|
| Environment | FAIL |
| Docker | PASS |
| API reachable | PASS |
| Authentication | FAIL |
| Credential issue | YES |
| Code issue | NO |

## Next Action Recommendation

1. In the local EspoCRM Admin UI (`http://localhost:8080`), create or open an **API User** with API Key auth and a role that can read `App/user` (and later Lead / ResearchEvidence for the real sync phase).
2. Export into the **host** shell only (do not commit secrets):
   - `ESPOCRM_TEST_ENV=true`
   - `ESPOCRM_TEST_URL=http://localhost:8080`
   - `ESPOCRM_TEST_API_KEY=<api-key-from-API-User>`
3. Re-run this auth-only probe: `GET /api/v1/App/user` with `X-Api-Key`.
4. Only after Authentication = PASS, resume Phase 3A-2.2-B metadata preflight and synthetic sync under the existing safety rules.

Do not use production endpoints. Do not modify Sync Contract or scoring. Do not create real customer Leads.
