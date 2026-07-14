# Phase3C08.4 — Score Runtime Acceptance Report

## Status

**PASS — synthetic end-to-end orchestration acceptance.**

No commit was created.  No live EspoCRM write was performed.

## Synthetic Flow Validated

```text
ResearchEvidence (2 synthetic website records)
        -> QualificationDecision (QUALIFIED)
        -> ScoreInput
        -> CanonicalScoreIntegration (one executor invocation)
        -> CanonicalScoreResult (82 / A)
        -> existing Lead score projection
```

The fixture uses only the `[C08_RUNTIME_SYNTHETIC]` marker and synthetic IDs,
URLs, and evidence text.

## Acceptance Evidence

| Stage | Verified result |
| --- | --- |
| ResearchEvidence input | Two valid website records, with public source URLs and confidence values `0.90` and `0.92`. |
| Qualification | C07 gate returned `QUALIFIED` with an evidence count of `2`. |
| Score input | C08.1 retained evidence count, sorted confidence facts, source indicators, and `QUALIFIED` status without computing a score. |
| Canonical score execution | C08.2 invoked its injected canonical executor exactly once and retained its canonical result unchanged: score `82`, tier `A`, product `Resin Printer`, version `canonical-scoring-v4.0`. |
| Evidence traceability | The score trace contains both sorted `peEvidenceId` values and the `QUALIFIED` qualification status. |
| Lead projection | The existing synthetic Lead received only `peOpportunityScoreV4=82.0`, `peScoreTier=A`, `peScoreRulesVersion=canonical-scoring-v4.0`, and `peBestFirstProduct=Resin Printer`. |

The Lead's existing `name` and `status` remained unchanged.

## Safety Assertions

- One canonical executor call was observed for the explicit evaluation; no
  duplicate scorer or fallback scorer was invoked.
- The target began with an existing synthetic Lead; `lead_creations` remained
  empty.
- `opportunity_creations`, `email_sends`, and `workflow_events` all remained
  empty.
- No production data, provider, AI call, email send, Opportunity creation, or
  workflow trigger was used.

## Canonical-Engine Limitation

This repository contains the frozen `CanonicalScoreResult` contract and the
C08.2 executor seam, but no executable canonical V4 scoring engine.  The
runtime test therefore uses a fixed external-owner canonical result fixture to
verify single-path invocation, unchanged result propagation, traceability, and
Lead projection.  Formula-level verification against the external canonical
engine is **DEFERRED** to the owning runtime; this phase does not create a
second scoring implementation to simulate it.

## Validation

| Check | Result |
| --- | --- |
| C08.4 synthetic runtime acceptance | PASS — 1 test |
| C08.3/C08.2/C08.1 + C07 + C06 focused boundary suite | PASS — 62 tests |
| Python compile for C08.4 test | PASS |
| Core Regression Gate | PASS — see result artifact below |

Regression result artifact:
`temp/test-results/regression-gate-20260714-000422-554.json`
