# Phase3C07.4 — Runtime Acceptance Report

Status: **PASS — synthetic in-process acceptance**  
Live EspoCRM evidence write: **DEFERRED safely**  
Commit: **not created**

## Acceptance Flow

The acceptance fixture is explicitly marked `[C07_RUNTIME_SYNTHETIC]` and uses
no customer data, external provider, Apify, DeepSeek, email service, or batch
execution.

`WebsiteResearchPipelineResult.to_dict()` → C07.1 extractor → C07.2 persistence adapter → C07.3 enrichment gate

The runtime target is an in-memory implementation of the exact C07.2
`ResearchEvidencePersistenceClient` interface. It permits only evidence lookup
and creation and exposes empty Lead, Opportunity, email, and workflow stores
for side-effect assertions.

Acceptance implementation: `chitu-connector/tests/test_phase3c07_runtime_acceptance.py`.

## Evidence Persistence Acceptance

The synthetic page produces three website EvidenceItems: title, meta
description, and visible text. The first persistence run creates exactly three
ResearchEvidence-shaped records for synthetic lead ID
`synthetic-c07-runtime-lead`.

| Verification | Result |
|---|---|
| Source URL retained | PASS |
| Claim retained | PASS |
| Evidence text retained | PASS |
| Deterministic confidence retained | PASS |
| Shared snapshot hash retained on every record | PASS |
| Second persistence run | PASS — `SKIPPED` |
| Evidence record count after second run | PASS — remains 3 |

## Qualification Acceptance

| Input | Expected decision | Result |
|---|---|---|
| No evidence | `NOT_READY` | PASS |
| One high-confidence website record | `RESEARCH_COMPLETE` | PASS |
| Three extracted valid records | `QUALIFIED` | PASS |
| Low-confidence record | `REVIEW_REQUIRED` | PASS |
| Mixed high/low confidence records | `REVIEW_REQUIRED` | PASS |
| Reordered repeated evaluation | identical decision | PASS |

## No-Side-Effect Acceptance

The synthetic runtime explicitly verified all of the following remain empty:

- Lead records
- Opportunity records
- Email records
- Workflow events

No network transport, CRM batch, provider, AI, or email sender is instantiated
by the acceptance flow.

## Local EspoCRM Readiness Check

The configured local EspoCRM test client completed read-only authentication and
metadata preflight successfully. It found no existing synthetic Lead. Since the
task forbids Lead creation, no live ResearchEvidence write was attempted and no
CRM record was changed. A live write acceptance can be run later only against
an already-provisioned, explicitly marked synthetic Lead with cleanup authority.

## Validation

| Check | Result |
|---|---|
| C07.4 synthetic acceptance | PASS — 2 tests |
| C07.1–C07.3 + C06 boundary combined tests | PASS — 49 tests |
| Connector suite | PASS — 86 tests |
| Extension suite | PASS — 57 tests |
| Worker suite | PASS — 31 tests |
| Static suite | PASS — 2 tests |
| Core Regression Gate | PASS — required suites 5/5 |

Regression result: `temp/test-results/regression-gate-20260713-234329-914.json`.
