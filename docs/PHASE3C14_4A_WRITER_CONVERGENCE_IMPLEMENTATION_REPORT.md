# Phase3C14.4A Writer Convergence Implementation Report

## Result

**PASS WITH RISKS**

C14.4A implements Option C guarded compatibility for W-CON-01
`EmailLifecycleSyncService` and W-CON-02 `CampaignProjectionAdapter`.
Neither writer was deleted. Each now reads the current CRM email summary before
writing and skips any change that could regress the C14.3 lifecycle state.

## Changed Files

| File | Change |
|---|---|
| `chitu-connector/chitu_connector/espocrm_sync/email_projection_guard.py` | Added one connector-side C14.3-compatible status-rank, timestamp, terminal, and empty-field guard shared by both writers. |
| `chitu-connector/chitu_connector/espocrm_sync/email_lifecycle.py` | Added W-CON-01 read-before-write guards, empty-field exclusion, safe conflict logging, and optional skip reason. |
| `chitu-connector/chitu_connector/espocrm_sync/campaign_projection.py` | Added W-CON-02 Lead state guard and safe conflict logging. |
| `chitu-connector/tests/test_espocrm_email_lifecycle.py` | Added the existing client read seam to its test double. |
| `chitu-connector/tests/test_phase3c09_campaign_projection.py` | Added the existing client read seam to its test double. |
| `chitu-connector/tests/test_phase3c09_outreach_runtime_acceptance.py` | Added the synthetic existing-Lead read seam. |
| `chitu-connector/tests/test_phase3c14_4a_writer_convergence.py` | Added focused convergence, logging, rank-contract, and downgrade-regression tests. |
| `docs/PHASE3C14_4A_WRITER_CONVERGENCE_IMPLEMENTATION_REPORT.md` | Added this report. |

`LocalEspoCRMClient` already had `read_record`, so no CRM transport, schema,
PHP extension, or C14.3 source was changed.

## Before / After Writer Behavior

| Writer | Before | After |
|---|---|---|
| W-CON-01 | Directly updated Lead and optional Opportunity with four email summary fields. | Reads all intended targets first. Older timestamps, lower rank, terminal regression, unknown current state, invalid timestamp, or unavailable current state skip the entire write. Empty optional fields are excluded. |
| W-CON-02 | Unconditionally wrote `DRAFT_READY` and campaign metadata to Lead. | Reads Lead first. If `DRAFT_READY` is lower rank than the current state, skips the entire update. Non-conflicting calls retain the existing three-field payload. |

The full W-CON-02 skip is intentional: this phase requires a lower target
status to skip the update, rather than write metadata after a status conflict.

## Guard Implementation

The shared `C14_3_EMAIL_STATUS_RANK` exactly represents the PHP
`EmailLifecycleProjectionService::STATUS_RANK` contract:

```text
NONE 0 -> DRAFT_READY 10 -> DRAFT_PENDING_APPROVAL 20
-> APPROVED/REJECTED 30 -> PENDING 40 -> READY_TO_SEND 50
-> SENT/FAILED/CANCELLED 60 -> REPLIED/BOUNCED 70
```

PHP cannot be imported by the connector. Instead of maintaining two writer
rank systems, both writers use this one guard and a focused test asserts every
entry against the frozen PHP declaration.

The guard enforces:

- lower-rank proposed status: skip;
- W-CON-01 older `peLastEmailDate`: skip;
- `SENT`, `FAILED`, `CANCELLED`, `REPLIED`, and `BOUNCED` lower-rank
  regression: skip;
- unknown current state, including a future `CONTACTED`: fail closed;
- `None` and blank optional fields: excluded before W-CON-01 update; and
- conflict logging: reason code only, with no recipient or content.

W-CON-01 evaluates Lead and optional Opportunity before writing either target,
so a conflict cannot create a partial cross-record lifecycle update.

## Tests

| Suite | Result |
|---|---|
| C14.4A focused convergence tests | PASS — 8 tests |
| Existing W-CON-01 lifecycle tests | PASS — 3 tests |
| Existing W-CON-02 campaign projection tests | PASS — 3 tests |
| Existing C09 synthetic outreach acceptance | PASS — 1 test |
| C11 + C14.3A/C/D projection/result hardening tests | PASS — 27 tests |
| Full connector regression | PASS — 278 tests |
| Full CRM extension suite | PASS — 75 tests |
| `py_compile` changed connector modules/tests | PASS |

Focused coverage proves W-CON-01 `SENT -> APPROVED` and `REPLIED -> SENT`
are blocked, empty optional values cannot clear existing summaries, and an
older timestamp is blocked. It also proves W-CON-02 cannot replace `SENT` with
`DRAFT_READY`, non-conflicting legacy updates still use the allowlist, every
rank matches C14.3 PHP, and requested terminal direct downgrades are rejected.

## Compatibility Impact

| Boundary | Result | Evidence |
|---|---|---|
| C09 | PASS WITH RISKS | Three-field interface remains; unsafe draft projection now returns `SKIPPED`. No-conflict synthetic acceptance remains `PROJECTED`. |
| C10 | PASS WITH RISKS | The callable lifecycle interface remains; only unsafe legacy display updates are refused. No send, approval, or idempotency behavior changed. |
| C11 | PASS | CRM projection source and hooks are untouched; projection tests pass. |
| C12/C13 | PASS | No Provider, Brevo, Queue, Worker, failure classification, or retry source changed. |
| C14.3 | PASS | Bridge, snapshot, invocation, result adapter, and PHP projection contracts are untouched; C14.3A/C/D tests pass. |

## Scope Confirmation

| Question | Result |
|---|---|
| Were W-CON-01/W-CON-02 deleted? | No. |
| Were C14.3 contracts touched? | No. |
| Were Worker, Queue, Provider, Brevo, or retry touched? | No. |
| Was CRM schema/entity or PHP projection contract changed? | No. |
| Was a real CRM record changed or a real email sent? | No. |

## Remaining Migration Path: Option A

The guard is an interim barrier, not global single-writer ownership. Its
read-then-write operation is not atomic, and external callers remain unknown.

For C14.4B:

1. verify production call sites for both legacy writers;
2. migrate or formally retire valid callers;
3. demonstrate no direct connector `peEmail*` write is required;
4. remove legacy email-summary writes while preserving separately authorized
   non-email fields; and
5. rerun C09/C10/C11/C14 regressions plus CRM Test runtime acceptance.

## Next Recommendation

Proceed to **C14.4B production call-site verification and Option A removal design**.
Do not add a new CRM endpoint, queue/result inbox, automatic retry, Worker CRM write,
Provider change, or real send in that work.
