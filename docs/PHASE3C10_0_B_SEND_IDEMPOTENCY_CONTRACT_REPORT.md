# Phase3C10.0-B — Send Idempotency Contract

Status: **PASS**  
Commit: **not created**

## Scope

Delivered a provider-neutral, in-memory contract for reserving a future email
delivery request before any execution layer exists. It has no SMTP, email
provider, CRM, approval, campaign, or send behavior.

## Contract

`SendRequest` is an immutable request containing:

- `draftId` (`draft_id`)
- `leadId` (`lead_id`)
- `sendRequestId` (`send_request_id`)
- `idempotencyKey` (`idempotency_key`)
- `providerName` (`provider_name`)
- `createdAt` (`created_at`)
- `requestVersion` (`request_version`)

`SendAttemptState` defines only the delivery lifecycle vocabulary:

```text
CREATED -> READY -> PROCESSING -> SENT | FAILED
                 \-> CANCELLED
```

`SENT`, `FAILED`, and `CANCELLED` are terminal in this contract.

## Idempotency Rules

The key is SHA-256 over a canonical, versioned payload:

```text
c10-send-idempotency-v1
+ draftId
+ leadId
+ sendRequestId
+ normalized providerName
```

`createdAt` is deliberately excluded: replaying the same explicitly named
request must derive the same key regardless of wall-clock time.

- Same key: return the existing `SendAttempt`, in its current state; never
  reserve a second attempt.
- New key: reserve one new `CREATED` attempt.
- Retry after `FAILED`: a replay with the same key returns the existing failed
  attempt. A caller must create a new `sendRequestId`, hence a new key, for an
  explicitly authorized retry.
- Concurrent calls: registry reservation is lock-protected; exactly one caller
  receives `RESERVED`, all concurrent duplicates receive `EXISTING`.

The in-memory registry is a test/reference implementation only. A future
durable store must preserve the same atomic uniqueness rule before a provider
can be introduced.

## Tests

`chitu-connector/tests/test_phase3c10_send_idempotency_contract.py`

| Scenario | Result |
|---|---|
| Same request repeated | PASS — existing attempt returned |
| Different request | PASS — separate key and reservation |
| Retry after failure | PASS — same key remains failed; new key reserves |
| Concurrent duplicate attempt | PASS — one reservation, 15 existing results |
| Invalid request | PASS — rejected with no attempt |

## Validation

| Check | Result |
|---|---|
| C10.0-B contract tests | PASS — 5 tests |
| C09 tests | PASS — 13 tests |
| Core Regression Gate | PASS — Extension 57, Connector 86, Worker 31, Static 2, runner integrity 5/5 |

Regression artifact:
`temp/test-results/regression-gate-20260714-140712-565.json`.

## Explicitly Unchanged

- SMTP, SendGrid, Instantly, Brevo, Gmail, and all actual delivery
- Email approval and campaign execution
- CRM writes, Lead mutation, scoring, qualification, and workflow behavior
- C09 `EmailDraft` contract and all frozen upstream contracts
