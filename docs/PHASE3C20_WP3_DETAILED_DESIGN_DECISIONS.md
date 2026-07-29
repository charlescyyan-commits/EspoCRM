# Phase3C20 WP3 Detailed Design Decisions

**Status:** FROZEN — implementation design decisions
**Date:** 2026-07-29
**Baseline:** WP2 Capability Registry freeze (`a78727c`) and WP3 AI Execution
Charter (`4be1561`)
**Governing ADR:** `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md`
**Related invariants:** `docs/adr/C20_INVARIANT_REGISTRY.md`

This is an implementation-design freeze for WP3. It implements and clarifies
ADR-C20 for the WP3 delivery sequence; it is not an ADR, and it does not amend
or supersede ADR-C20.

## 1. Purpose

WP3 establishes the AI Execution Governance Layer. Its purpose is controlled,
attributable AI execution with:

- AI execution tracking;
- execution evidence;
- prompt governance;
- cost visibility;
- controlled retry; and
- auditability.

WP3 is not an AI Sales Agent, autonomous SDR, lead-qualification engine,
email-automation engine, or Prospecting lifecycle engine. EspoCRM owns
governance and workflow controls; Chitu remains the intelligence authority.

## 2. Architecture Flow

The governed execution flow is:

```text
Business Request
        |
        v
AIJob
        |
        v
Capability Registry Resolution
        |
        v
Provider Adapter
        |
        v
External Provider
        |
        v
AIRequestLog
```

`AIJob` does not select a provider. Provider resolution always remains the
responsibility of the frozen WP2 Capability Registry, evaluated from
CRM-authorized `ProviderBinding` data. The resolution result is governance
evidence; it is not a business decision, qualification result, or lifecycle
instruction.

## 3. AIJob Contract

### Purpose

`AIJob` represents **one controlled AI execution**. It is an execution and
governance record, not a business object and not a substitute for a
Prospecting entity.

### Required fields

The WP3 `AIJob` contract contains the following fields:

```text
id
capability
purpose
requested_by
policy_version
status
attempt_count
idempotency_key
failure_category
last_error
started_at
completed_at
execution_mode
result_reference
created_at
```

`failure_category` is the normalized category for the current or most recent
failure. In retry discussions, `last_failure_category` means this same stored
value; WP3 does not create two competing failure-category fields.

`result_reference` is a reference to a permitted result or evidence object. It
does not make `AIJob` a score, qualification, Lead, Opportunity, or lifecycle
owner.

## 4. AIJob Status Model

WP3 strictly adopts ADR-C20 section 7. No additional state is authorized.

```text
QUEUED
RUNNING
SUCCEEDED
FAILED
CANCELLED
```

The following are explicitly forbidden:

```text
CREATED
WAITING_RETRY
```

Creation enters `QUEUED` directly. An authorized retry returns a failed job to
`QUEUED`; it does not introduce a retry-only status. `SUCCEEDED` and
`CANCELLED` remain terminal according to the ADR transition matrix.

## 5. AIJob State Ownership

`AIJob` owns:

- execution state;
- attempt count;
- execution timestamps; and
- normalized failure classification.

`AIJob` does not own:

- the retry algorithm;
- backoff calculation;
- provider selection; or
- a business, scoring, qualification, or lifecycle decision.

All status mutation remains subject to the ADR-C20 `AIJobService` and guard
requirements. Direct writes are not an alternative execution path.

## 6. Retry Design

`AIJob` stores the evidence required for a controlled retry:

```text
attempt_count
failure_category (the last_failure_category)
last_error
next_retry_at (only if scheduling requires it)
```

The execution service owns retry eligibility, retry limits, backoff,
dispatching, and the cost gate. Eligibility uses the established BridgeError /
provider error taxonomy; it does not create a parallel taxonomy.

No `RetryPolicy` entity is created. A retry returns the same logical job to
`QUEUED` and reuses its persisted `idempotency_key`.

## 7. Idempotency Design

`AIJob.idempotency_key` prevents duplicate logical execution and supports safe
retry. It is persisted before dispatch and remains identical for every retry
of that logical invocation.

`AIRequestLog.attempt_id` identifies an individual provider invocation
attempt. The cardinality is:

```text
One AIJob
   |
   +-- many AIRequestLog attempts
```

An `attempt_id` never replaces the logical job idempotency key.

## 8. AIRequestLog Contract

`AIRequestLog` is append-only AI execution evidence. It records one governed
provider invocation attempt without becoming a mutable work queue or business
decision record.

Required fields:

```text
id
ai_job_id
attempt_id
capability
provider
model
prompt_template_id
prompt_template_version
tokens_in
tokens_out
cost_amount
cost_currency
latency_ms
status
error_class
created_at
```

No update or delete path is authorized for any role. Corrections are recorded
as new evidence where a correction is permitted; prior evidence remains
preserved.

## 9. Payload Storage Decision

WP3 selects **Option B: References + Metadata Only**.

The default persistence model must not store:

```text
raw prompt
raw response
request body
response body
credential payload
api key
```

It may store only safe traceability material:

```text
template reference
template version
template hash
input digest
output digest
sanitized metadata
```

Traceability is not full replay. A future need for payload retention requires a
separate design for an encrypted payload store, retention, access controls,
and disclosure controls; it is not introduced by WP3.

## 10. PromptTemplate Design

`PromptTemplate` provides prompt governance, versioning, and reproducibility.
Its lifecycle is limited to:

```text
DRAFT
ACTIVE
RETIRED
```

An `ACTIVE` version that is referenced by an `AIRequestLog` cannot be edited.
More generally, a version referenced by execution evidence is immutable.
Changes create a new version and preserve the old version for auditability.

`AIJob` and `AIRequestLog` reference prompt provenance through:

```text
template_id
template_version
template_hash
```

## 11. Provider Boundary

Provider authority remains singular:

```text
ProviderBinding
        |
        v
Capability Registry
        |
        v
Resolution Result
```

`AIJob` must not contain provider-routing rules, API URLs, API keys, or model
selection logic. WP3 does not create a `ProviderRoute` entity: that would
duplicate the authoritative `ProviderBinding` plus Capability Registry path
and create two routing authorities.

The resolution result supplies safe provider, adapter, credential-reference,
policy, and candidate-evaluation metadata for execution evidence. It never
supplies a secret value.

## 12. Provider Health Boundary

CRM retains governance configuration: policy and enabled/disabled state.
The connector retains runtime health knowledge: latency, failure rate, and
temporary availability.

WP3 does not create a `ProviderHealth` entity. Health signals may inform the
existing Capability Registry resolution input, but this increment does not
introduce a CRM health store, health-routing authority, or a second provider
selection mechanism.

## 13. AIPlatform / Prospecting Boundary

AIPlatform must not depend on Prospecting entities. In particular, `AIJob`
must not relate to:

```text
ProspectCandidate
ResearchEvidence
QualificationInsight
Lead
Opportunity
```

The permitted direction is outward from a business evidence entity to
execution provenance, for example:

```text
ResearchEvidence -> source_ai_job_id
```

This reference provides provenance only. It grants neither scoring authority
nor lifecycle authority to AIPlatform.

## 14. Cost Governance

WP3 captures governance metadata for tokens, estimated or reported cost,
currency, and provider-usage metadata. This supports visibility and a
pre-attempt cost gate; it does not create a billing system.

WP3 excludes billing, subscriptions, payments, finance reconciliation, and a
per-user budget system. `AIProviderUsage` is deferred and is not created.

## 15. Error Governance

WP3 reuses the existing BridgeError and provider error taxonomy. An
`AIRequestLog` stores only the normalized error class and safe error summary.

The following must not be persisted in an `AIJob` or `AIRequestLog`:

- raw exception objects;
- stack traces;
- raw HTTP bodies; or
- credential information.

This preserves consistent retry decisions while preventing secret or payload
disclosure through governance records.

## 16. Dry Run Design

WP3 supports two execution modes:

```text
LIVE
DRY_RUN
```

`DRY_RUN` may create an `AIJob`, create `AIRequestLog` evidence, and validate
the governance chain. It must make zero external provider calls. Tests use
fixture-backed transport for dry-run evidence and must prove no network egress.

## 17. C21/C22 Exclusion

The following are outside WP3.

**C21 excluded:**

- `ProspectCandidate` creation;
- `QualificationInsight` creation;
- `ResearchEvidence` creation;
- `CandidateScore`; and
- `HumanFeedback`.

**C22 excluded:**

- `ActionLedger`;
- `ActionGate`;
- `AutomationRule`;
- `HumanHandoff`; and
- email sending.

WP3 also does not modify existing Prospecting, Reply, SendExecution, Quote,
Approval, or lifecycle behavior.

## 18. Invariant Mapping

WP3 implementation activates and verifies:

- C20-INV-05 — AIJob execution ownership;
- C20-INV-06 — lifecycle isolation;
- C20-INV-07 — AIRequestLog append-only;
- C20-INV-08 — execution evidence;
- C20-INV-09 — PromptTemplate immutability;
- C20-INV-10 — retry eligibility from the normalized taxonomy; and
- C20-INV-11 — idempotency persistence across retries.

C20-INV-14 (no EspoCRM scoring authority) remains ACTIVE from WP0 and is a
standing boundary for every WP3 implementation; it is not renumbered or
re-owned by this document.

The registry remains the source of status and activation triggers. This design
document neither changes invariant status nor alters ownership outside the WP3
implementation gate.

## 19. Implementation Gate

Completion of this decision freeze authorizes planning and bounded
implementation of:

```text
WP3.1 AIJob Implementation
WP3.2 AIRequestLog Implementation
WP3.3 PromptTemplate Implementation
```

Each work package must preserve the frozen WP2 Capability Registry contract,
the ProviderCredential custody boundary, Chitu intelligence authority, and the
ADR-C20 state and invariant requirements. This document does not authorize an
artifact rebuild, provider execution redesign, autonomous action, scoring,
qualification, email sending, or a change to ADR-C20.
