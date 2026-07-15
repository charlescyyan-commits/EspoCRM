# Phase3C14.2A.2 Recipient Guard Implementation

## Result

PASS WITH RISKS

## Implemented Boundary

The acceptance recipient guard is implemented only in:

`chitu-connector/chitu_connector/espocrm_sync/brevo_provider.py`

`BrevoConfiguration` now reads these process-environment values:

- `BREVO_ACCEPTANCE_MODE`
- `BREVO_TEST_RECIPIENT`

The mode is enabled only when `BREVO_ACCEPTANCE_MODE` is the case-insensitive string `true`. It is disabled when unset, empty, `false`, or any other value.

## Guard Behavior

| Runtime configuration | Result | HTTP |
|---|---|---|
| acceptance mode enabled; test recipient present | The transactional payload uses only the configured test recipient. The request's original recipient is not used for delivery. | One mock call in test |
| acceptance mode enabled; test recipient absent | `PERMANENT_FAILURE`, `VALIDATION_ERROR`, `ACCEPTANCE_RECIPIENT_NOT_CONFIGURED` | Not called |
| acceptance mode disabled or unset | Payload preserves `SendRequest.recipient` unchanged. | Existing behavior |

The guard is evaluated by `BrevoProviderAdapter.send()` before idempotency caching and before `_send_once()`; the missing-recipient failure therefore cannot reach `BrevoHttpClient.post_json()`.

## Data-Minimization Decision

The C14.2A.1 design suggested an HTTP header carrying the original recipient for audit. This implementation intentionally omits that non-mandatory header: transmitting the original customer recipient to Brevo is unnecessary to enforce the guard and conflicts with the existing boundary that avoids recipient-sensitive diagnostic output. The original recipient remains only in the in-memory request object; acceptance-mode payloads contain the controlled test recipient.

## Files Changed

- `chitu-connector/chitu_connector/espocrm_sync/brevo_provider.py`
- `tests/test_phase3c12_2_brevo_adapter.py`
- `docs/PHASE3C14_2A_2_RECIPIENT_GUARD_IMPLEMENTATION.md`

No Queue, Worker, provider contract, HTTP client, CRM entity, migration, or runtime secret file was changed.

## Tests

Mock-only verification completed:

- C12.2 focused adapter suite: 11/11 PASS.
- C12 provider regression suites (C12.1, C12.2, C12.3): 23/23 PASS.

New coverage verifies:

1. acceptance mode rewrites the payload recipient to the controlled test mailbox;
2. acceptance mode without a test recipient returns a permanent validation failure with zero HTTP calls;
3. production mode preserves the original request recipient;
4. existing provider success, error mapping, configuration, idempotency, security, and C10 freeze tests continue to pass.

No real Brevo API call or email occurred.

## Remaining Risks

- Live C14.1 acceptance remains skipped and runtime credentials are still externally controlled.
- Acceptance mode protects the recipient only when the adapter is used with `BREVO_ACCEPTANCE_MODE=true`; it is not a general production-recipient policy.
- The CRM SendExecution to C13 Worker bridge remains intentionally absent and out of this change.
- No automatic retry, daemon, scheduler, batch, campaign, or production deployment was introduced.

## Stop Condition

C14.2A.2 stops after guard implementation and Mock-HTTP validation. C14.2B was not started.

