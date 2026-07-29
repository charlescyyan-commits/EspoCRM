# Phase3C21 WP1 ResearchEvidence Governance Design

## Status

**FROZEN — design only. No implementation in this increment.**

## Purpose

WP1 hardens the existing `ProspectPool` and `ResearchEvidence` contracts for
C21 intelligence governance. It does not create a second evidence entity or a
`ProspectCandidate` identity.

---

## 1. Existing Model Audit

### 1.1 ProspectPool

The existing model already satisfies the C21 identity decision:

| Requirement | Finding | Result |
| --- | --- | --- |
| Pre-CRM identity | Dedicated `ProspectPool` entity exists with external identity/source fields | Met |
| Lead separation | Optional `lead` belongs-to link preserves distinct ProspectPool and Lead records | Met |
| Candidate aggregation | Links to SearchJob, ResearchEvidence, assigned user, teams, and Lead exist | Met |
| Evidence relationship | `researchEvidences` has-many relation targets existing ResearchEvidence | Met |
| Promotion preservation | Existing PromotionInheritanceService attaches evidence to Lead without replacing ProspectPool identity | Met |
| C21 authority boundary | Existing queue/status fields predate C21 and remain owned by frozen workflows | Preserve; C21 must not add ownership |

No `ProspectPool` schema change is required for the WP1 evidence-governance
foundation. C21 must not create `ProspectCandidate` or change ProspectPool/Lead
conversion and lifecycle ownership.

### 1.2 ResearchEvidence

The existing entity is mature and already used by production-facing C10/C19
contracts. Its current capabilities are:

| Governance concept | Existing surface | Finding |
| --- | --- | --- |
| Parent identity | `lead`, `prospectPool` | Present; service requires at least one |
| External evidence identity | `peEvidenceId` | Present |
| Claim/content | `peClaim`, `peEvidenceText`, `peContentSummary` | Present |
| Source | `peSourceUrl`, `peCanonicalUrl` | Present |
| Source taxonomy | `peClaimType`, `peEvidenceType`, `peEvidenceTypeNormalized` | Present but unconstrained varchar semantics |
| Confidence | `peConfidence` float 0..1 | Present |
| Capture time | `peCapturedAt` | Present |
| Provenance helpers | `peSchemaVersion`, `peSnapshotHash`, `peClaimHash` | Partial connector provenance |
| Deduplication | Unique indexes for Lead and ProspectPool evidence identity | Present |
| C20 provenance | AIRequestLog / AIJob links | Missing |
| C21 evidence classification | FACT / OBSERVATION / AI_INFERENCE enum | Missing |
| Verification | validationState | Missing |
| Correction history | supersedes relation | Missing |
| Core immutability | Persistence guard | Missing |
| Delete protection | Guard and mandatory ACL denial | Missing |

`ResearchEvidenceService` currently validates parent presence on create and
update. It does not enforce classification, immutability, validation
separation, provenance consistency, supersession, or deletion denial.

---

## 2. Gap Analysis and Target Contract

### 2.1 Reuse before addition

WP1 must retain the existing `pe*` fields and their connector compatibility.
New governance fields may be added only where the existing model has no
equivalent authority.

| Target concept | Decision |
| --- | --- |
| Content | Govern existing `peClaim`, `peEvidenceText`, and `peContentSummary`; do not add duplicate content storage |
| Source reference | Govern existing `peSourceUrl` and `peCanonicalUrl`; do not add a duplicate raw source field |
| Capture time | Reuse `peCapturedAt` |
| Confidence | Reuse `peConfidence` and keep it independent from validation |
| External provenance | Preserve `peEvidenceId`, schema/snapshot hashes, and parent links |
| Governed evidence classification | Add a bounded `evidenceType` enum; legacy `peEvidenceType*` remains source taxonomy input, not governance authority |
| Validation | Add service-owned `validationState` enum |
| Correction | Add self-reference `supersedes` / `supersedesId` |
| C20 provenance | Add reference-only `sourceAIRequestLog` and optional consistent `sourceAIJob` links |

The target governed evidence classification contains exactly:

```text
FACT
OBSERVATION
AI_INFERENCE
```

Legacy `peEvidenceType` values must not be treated as governed classification
without an explicit deterministic mapping. Unknown legacy values must never be
guessed or promoted to `FACT`.

### 2.2 Validation model

`validationState` contains exactly:

```text
UNVALIDATED
VERIFIED
REJECTED
SUPERSEDED
```

Allowed transitions are:

| Current | Allowed target |
| --- | --- |
| UNVALIDATED | VERIFIED, REJECTED, SUPERSEDED |
| VERIFIED | SUPERSEDED |
| REJECTED | SUPERSEDED |
| SUPERSEDED | none |

Validation transitions are explicit service actions. Neither confidence nor
evidence classification can trigger them automatically.

```text
confidence != validationState
high confidence != VERIFIED
AI_INFERENCE != FACT
```

---

## 3. Immutability and Correction Model

### 3.1 Immutable core

After creation, the persistence guard must reject changes to:

- governed `evidenceType`;
- `peClaim`, `peEvidenceText`, and `peContentSummary`;
- `peSourceUrl` and `peCanonicalUrl`;
- `peCapturedAt`;
- `peEvidenceId`, `peSchemaVersion`, `peSnapshotHash`, and `peClaimHash`;
- `peConfidence` as captured intelligence context;
- `sourceAIRequestLogId` and `sourceAIJobId`; and
- the original `supersedesId` relation.

The existing `leadId` attachment performed by the frozen promotion-inheritance
workflow is not an evidence-fact rewrite. It may remain an authorized service
operation while all core facts stay immutable. `prospectPoolId` must remain
preserved during that attachment.

### 3.2 Correction and supersession

A correction creates a new ResearchEvidence record. The new record may set
`supersedesId` to the prior evidence. In the same transaction, an authorized
service may move the prior record to `SUPERSEDED`.

Original evidence remains preserved. No operation overwrites content, source,
classification, capture time, confidence, or provenance on the prior record.

Rules:

- an evidence record cannot supersede itself;
- a supersession chain cannot contain a cycle;
- a record may have at most one direct predecessor;
- a superseded record is terminal;
- “current” is derived from supersession ordering, not mutable `isCurrent`;
- DELETE is forbidden for every role and internal normal path.

---

## 4. C20 Provenance Design

The reference direction is:

```text
ResearchEvidence
        ↓ references
AIRequestLog
        ↓ belongs to
AIJob
```

This is provenance only. ResearchEvidence cannot create or modify C20 records.

For AI-produced evidence:

- `sourceAIRequestLogId` is required;
- `sourceAIJobId` is optional, but if stored it must equal the AIJob referenced
  by the source AIRequestLog;
- no raw prompt, response, provider payload, or credential is copied into
  ResearchEvidence; and
- provider/model/attempt facts remain owned by AIRequestLog.

FACT or OBSERVATION records created without AI execution may omit C20
provenance only when their attributable non-AI source is present. An
`AI_INFERENCE` cannot omit `sourceAIRequestLogId`.

---

## 5. Service, Guard, and ACL Design

### 5.1 Service responsibilities

The existing ResearchEvidenceService will be hardened rather than replaced. It
will own:

- create-time parent validation;
- governed classification validation;
- FACT source requirement;
- AI_INFERENCE C20 provenance requirement;
- AIRequestLog / AIJob consistency validation;
- explicit validation transitions;
- correction/supersession creation in a transaction; and
- controlled Lead attachment compatibility.

It will not execute AI, resolve providers, write scores, mutate lifecycle state,
send email, or schedule automation.

### 5.2 Persistence guard

A ResearchEvidence hook will:

- reject mutation of immutable core facts;
- reject direct validationState changes without a service authorization option;
- reject direct supersession-state changes;
- reject evidenceType promotion or reclassification; and
- reject every remove/delete operation.

The guard supplements the service and protects direct repository/entity-manager
paths.

### 5.3 ACL

- CREATE and READ remain subject to existing scope permissions.
- Generic EDIT must not permit evidence-core changes.
- Validation, supersession, and controlled parent attachment occur only through
  authorized service paths.
- DELETE is mandatory `no`, including administrators and portals.
- New governance/provenance fields are read-only or internal as appropriate.

---

## 6. Compatibility and Migration Design

WP1 implementation must be additive and migration-aware:

1. Inventory actual legacy `peEvidenceType*` values using approved non-customer
   fixtures or schema-safe diagnostics; do not import real customer data.
2. Map only deterministic known values to FACT, OBSERVATION, or AI_INFERENCE.
3. Unknown values remain unclassified legacy rows until explicit review; they
   are never defaulted to FACT.
4. New records require governed evidenceType at create time.
5. Existing rows receive `UNVALIDATED` without deriving verification from
   `peConfidence`.
6. Migration/backfill uses a one-time authorized path; the normal guard blocks
   later classification mutation.
7. Existing unique indexes, parent validation, layouts, and promotion
   inheritance must remain compatible.

No release artifact is rebuilt by the governance-hardening implementation
unless separately authorized.

---

## 7. Future Test Strategy

### 7.1 Existing-contract preservation

- ProspectPool remains the pre-Lead intelligence subject.
- Lead and ProspectPool parent links remain valid.
- Existing deduplication indexes remain intact.
- Promotion inheritance remains idempotent and preserves prospectPoolId.

### 7.2 Evidence governance

- create succeeds with valid classification and source/provenance;
- immutable core update fails;
- delete fails;
- correction creates a new record and preserves the original;
- supersession cycles/self-reference fail;
- AI_INFERENCE cannot be promoted to FACT;
- confidence cannot set or imply validationState;
- validation transitions follow the frozen matrix.

### 7.3 C20 provenance

- AI_INFERENCE requires sourceAIRequestLogId;
- optional sourceAIJobId matches the log's AIJob;
- mismatched or missing references fail;
- C21 cannot write AIJob, AIRequestLog, or PromptTemplate.

### 7.4 Boundary tests

The C21 implementation tree must contain no:

- provider runtime, routing, adapter, or credentials;
- AIScore, canonical-score writer, or qualification verdict;
- Lead/Opportunity lifecycle mutation;
- email, outreach, agent, ActionLedger, or AutomationRule; or
- ProspectCandidate entity or naming variant.

---

## 8. Planned Implementation Surface

The next implementation gate may modify only the existing ResearchEvidence
governance surface and related tests/configuration required for compatibility:

- existing ResearchEvidence entity metadata;
- existing ResearchEvidenceService;
- additive guard/save-option support;
- ACL and field protection;
- controlled migration/backfill if separately reviewed; and
- focused C21 plus regression tests.

It must not redesign ProspectPool, create ResearchEvidence again, modify C20,
or implement AIQualificationInsight/HumanFeedback prematurely.

## 9. Readiness Decision

**READY WITH IMPLEMENTATION CONDITIONS** for Phase3C21 WP1 Governance
Hardening Implementation.

The implementation must first freeze deterministic legacy classification
mappings and migration behaviour. If safe mapping cannot be proven, legacy
rows remain unclassified and no automatic FACT assignment is allowed.
