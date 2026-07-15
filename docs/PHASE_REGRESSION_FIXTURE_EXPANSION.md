# Phase Regression Fixture Expansion

**Date:** 2026-07-14  
**Result:** PASS

## Scope and boundary

This phase expands regression coverage using fixtures and test code only. No
production PHP or Python code, EspoCRM metadata, database schema, connector
contract, or runtime configuration was changed. The fixtures are deterministic
and contain no credentials, customer data, provider calls, CRM writes, or
database access.

## Added regression assets

| Asset | Purpose |
| --- | --- |
| `tests/fixtures/email_lifecycle_cases.json` | Lifecycle input and expected projection state for Draft, Approved, Queued, Sent, Failed, and Replied. |
| `tests/fixtures/research_evidence_cases.json` | New, duplicate, and invalid ResearchEvidence inputs with expected persistence outcomes. |
| `tests/fixtures/persistence_acl_roles.json` | Expected access matrix for Admin, Integration Bot, Sales User, and Sales Manager. |
| `tests/fixtures/README.md` | Fixture format and safety boundary. |
| `tests/regression/test_prospecting_regression_fixtures.py` | Fixture-driven regression coverage. This is discovered by the existing baseline test discovery. |

## Coverage added

### Email lifecycle

The lifecycle fixture validates the authorized event-to-Lead projection
contract:

| Case | Source state | Expected Lead projection |
| --- | --- | --- |
| Draft | `DraftApproval=PENDING` | `peEmailStatus=DRAFT_PENDING_APPROVAL` |
| Approved | `DraftApproval=APPROVED` | `peEmailStatus=APPROVED` |
| Queued | `SendExecution=CREATED` | `peEmailStatus=PENDING` |
| Sent | `SendExecution=SENT` | `peEmailStatus=SENT` |
| Failed | `SendExecution=FAILED` | `peEmailStatus=FAILED` |
| Replied | `ReplyEvent=REPLIED` after a sent email | Preserves `peEmailStatus=SENT`; sets `peEmailReplyStatus=REPLIED` |

The test also verifies that the production projection service retains the
expected lifecycle maps and touches only the approved Lead projection fields:
`peEmailStatus`, `peLastEmailDate`, and `peEmailReplyStatus`.

### ResearchEvidence

Fixture execution uses an in-memory client around the existing
`ResearchEvidencePersistenceAdapter`:

| Case | Expected result |
| --- | --- |
| New evidence | `CREATED`; exactly one create request |
| Duplicate evidence | first `CREATED`, second `SKIPPED`; exactly one create request |
| Invalid evidence | `REJECTED` with `INVALID_SOURCE_URL`; no create request |

### ACL

The regression test validates the provisioned collection permissions for all
three persistence scopes (`DraftApproval`, `SendExecution`, `ReplyEvent`):

| Role | create | read | edit | delete |
| --- | --- | --- | --- | --- |
| Admin | yes | all | all | all |
| Integration Bot | yes | all | all | no |
| Sales User | no | all | no | no |
| Sales Manager | no | all | no | no |

It also confirms deterministic collection ordering remains present for the
three native entities.

### Projection boundary

The event-to-projection test confirms the allowed event sources are mapped to
the allowed Lead fields only. It rejects scope expansion into scoring,
ResearchEvidence, Opportunity, provider, queue, or worker domains.

## Test execution

| Command / suite | Result |
| --- | --- |
| `python -m unittest tests.regression.test_prospecting_regression_fixtures -v` | PASS — 4/4 |
| `scripts/testing/run-freeze-gate.ps1` | PASS — 386/386 invocations; exit code 0 |
| `python -m unittest discover -s tests -p 'test_phase3c*.py' -v` | PASS — 83/83 |

Freeze Gate breakdown:

| Suite | Result |
| --- | --- |
| Extension | 65/65 PASS |
| Connector | 270/270 PASS |
| Worker | 31/31 PASS |
| Static | 2/2 PASS |
| Runtime | 11/11 PASS |
| Baseline | 7/7 PASS (includes the 4 new fixture tests) |

The gate reported three conditional suites with zero blocking findings. The
machine-readable gate result was emitted to
`temp/test-results/regression-gate-20260714-224318-586.json`.

## Conclusion

**PASS.** The regression gate now has deterministic fixtures for all requested
email lifecycle, ResearchEvidence, ACL, and event-to-Lead projection cases.
The expanded coverage passed both the existing Freeze Gate and the active
C11–C14 contract suite without changing production behavior.
