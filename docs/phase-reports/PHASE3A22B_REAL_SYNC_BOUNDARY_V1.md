# Phase 3A-2.2-B Real Sync Boundary V1

**Status:** BLOCKED - LOCAL AUTHENTICATION DENIED  
**Target:** `http://localhost:8080` only

## Environment Confirmation Method

Before any HTTP request, confirm through local process/container metadata and non-secret environment-variable names that the target is a local disposable EspoCRM test environment. A listening port alone is insufficient. Required confirmation is: loopback-only target, EspoCRM process/container identity, explicit test/non-production marker, and an environment-supplied local test account.

## Account Type

The currently available credential source is the local EspoCRM test administrator account supplied by the `espocrm` container environment; no separate integration account is configured in the local compose metadata. The client also supports a dedicated `ESPOCRM_TEST_API_KEY` for the recovery run. Credentials are read only from environment variables during the local test, never hard-coded, printed, or persisted.

## Test Environment Verdict

The target itself is confirmed local: `localhost:8080` is Docker-published by `espocrm/espocrm:10.0.1` under Compose project `espocrm-test`, with working directory `D:\EspoCRM-Test`; no Railway or remote target is involved. The local container's environment-supplied administrator credentials were rejected with HTTP 401 by both supported Basic-authentication header forms. Authentication, metadata preflight, all writes, and rollback are therefore blocked.

## Allowed Write Scope After Confirmation

- Exactly one synthetic Lead named `Synthetic 3D Dealer Test GmbH`.
- Synthetic evidence records belonging only to that Lead.
- Required visible markers: `is_test = true` and `data_type = synthetic`.
- A second identical run may query/return the existing synthetic record but must not create a second Lead.

## Forbidden Writes

- Railway, production, remote, or non-loopback EspoCRM.
- Any real customer, contact, opportunity, account, email, activity, queue, provider, or historical record.
- More than one synthetic Lead, bulk actions, score/contract changes, or non-test database data.

## Synthetic Test Data

The sole candidate is `synthetic_test_dealer_v1`, with website `synthetic-dealer.example`, direct test-only evidence `test-ev-001`, `OUTREACH_READY`, Canonical Scoring V4, and engine version `prospecting-engine-test`.

## Rollback Method

On any partial or successful test import, delete the synthetic evidence records first and then the synthetic Lead by recorded IDs. Verify that the named synthetic Lead and its evidence no longer exist. No rollback action is attempted until the environment is confirmed safe.

## Acceptance Criteria

Environment safety is proved before connection; one synthetic Lead and linked evidence can be created, verified, de-duplicated, and deleted; all calls remain local; no production, customer, email, SMTP, DeepSeek, Apify, or Playwright activity occurs.
