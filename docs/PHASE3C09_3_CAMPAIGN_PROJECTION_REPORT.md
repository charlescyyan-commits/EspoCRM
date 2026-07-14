# Phase3C09.3 — Campaign Projection Report

## Status

**PASS — existing-Lead outreach-preparation projection delivered.**

No commit was created.  No live CRM write was performed.

## Scope Delivered

Implemented `CampaignProjectionAdapter` and an existing-Lead-only client
operation:

```text
EmailDraft
      -> CampaignProjectionAdapter
      -> PUT Lead/{id} (three-field allowlist only)
```

| EmailDraft / projection source | Existing Lead field | Value |
| --- | --- | --- |
| Draft preparation boundary | `peEmailStatus` | `DRAFT_READY` only; no approval or send state. |
| Draft preparation label | `peEmailCampaignName` | Default `C09 Draft Preparation`, with an optional valid caller label. No Campaign record is created. |
| Direct recommendation context | `peRecommendedApproach` | Deterministic evidence-backed first-touch guidance, using an available product only when supplied by the draft. |

The projection result retains `draft_generation_version`, evidence-reference
count, and qualification status as connector audit metadata.  No dedicated,
existing Lead field is available for draft-version metadata, so no schema change
or unrelated field reuse was introduced.

## Safety Boundaries

- The local CRM client rejects every field outside
  `peEmailStatus`, `peEmailCampaignName`, and `peRecommendedApproach` before a
  request is issued.
- Draft `subject`, `body`, personalization values, and evidence text are never
  projected to CRM.
- A missing/malformed draft or invalid source reference is skipped before a CRM
  call.
- Permission denial returns `DENIED` without retrying or invoking another CRM
  operation.
- No email send, approval, campaign creation, Lead creation, Opportunity
  creation, scoring change, Evidence change, or workflow change is present.

## Tests

New coverage:
`chitu-connector/tests/test_phase3c09_campaign_projection.py`

| Scenario | Result |
| --- | --- |
| Projection mapping | PASS — exact three-field mapping plus generation/evidence/qualification audit metadata. |
| Permission boundary | PASS — denial causes no retry, create, send, approval, or workflow event. |
| Unrelated fields | PASS — body, subject, score, research, reply/date, and native status fields are excluded. |

## Validation

| Check | Result |
| --- | --- |
| C09.3 unit tests | PASS — 3 tests |
| C09.3 + C09.2/C09.1 + C08/C07/C06 focused boundary suite | PASS — 74 tests |
| Python compilation | PASS |
| Extension suite | PASS — 57 tests |
| Connector suite | PASS — 86 tests |
| Worker suite | PASS — 31 tests |
| Static suite | PASS — 2 tests |
| Core Regression Gate | PASS — 5/5 required suites |

Regression result:
`temp/test-results/regression-gate-20260714-001956-890.json`

## Explicitly Unchanged

- C06/U03/C07/C08 frozen contracts and behavior
- C09.1 input facts and C09.2 draft generation contract
- canonical scoring and Evidence contracts
- SMTP, Instantly, Brevo, AI provider calls, campaign execution, and all email
  delivery or approval paths
- CRM schema, API, migration, Lead/Opportunity creation, and workflow logic
