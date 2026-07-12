# Phase 3A-2.2-B Real Sync Implementation Report V1

## Implemented

- `integration/espocrm_sync/real_client.py`: localhost-only REST client, environment-only credentials, token/basic authentication support, redirect denial, metadata preflight, synthetic Lead/evidence creation, relationship linking, verification, duplicate lookup, and delete-only rollback.
- `integration/espocrm_sync/real_sync.py`: one-shot synthetic `OUTREACH_READY` source and controlled test workflow.
- `tests/test_espocrm_real_client.py`: offline safety and client behavior tests.

## Safety Controls

- The client rejects every base URL other than local HTTP port 8080 and rejects absolute request paths.
- Credentials are sourced only from `ESPOCRM_TEST_API_KEY`, `ESPOCRM_TEST_*`, or local-container `ESPOCRM_ADMIN_*` environment variables; they are never hard-coded, printed, or persisted.
- The client authenticates and reads metadata before any write. Required Lead fields, `ResearchEvidence`, and `researchEvidences` relation must all exist.
- The only writable Lead body is named `Synthetic 3D Dealer Test GmbH` and includes `is_test=true`, `data_type=synthetic`, and a deterministic sync key in `description`.
- The client accepts no Account, Opportunity, email, activity, real customer, provider, or non-local target operation.

## Authentication Compatibility Fix

The first local read-only call showed that `Espo-Authorization` must carry the raw Base64 credential value, not a `Basic` prefix. The client was corrected to that official format and also safely falls back to standard `Authorization: Basic` for local regular-user authentication.

## Real Execution Result

The local target was statically confirmed as Docker Compose project `espocrm-test` at `http://localhost:8080`. Both official authentication forms returned HTTP 401 using the container environment's administrator variables. The client stopped before metadata preflight and before any create, link, query-for-duplicate, or delete mutation.

## Required Recovery Condition

Provide a valid local `ESPOCRM_TEST_API_KEY`, local test API user, or valid local test administrator credential through the host environment, then rerun the read-only authentication and metadata preflight. Do not reset passwords, modify the CRM database, install metadata, or use any remote/production endpoint as part of this phase.
