# ADR-C25-007: Commercial Brief Audit Storage

| Field | Value |
| --- | --- |
| Status | **RATIFIED — implementation planning reference only; code implementation not authorized** |
| Date | 2026-08-01 |
| Work Package | Phase3C25 WP2.1A — Audit Storage Decision and ADR Ratification |
| Decision Package | `docs/PHASE3C25_WP2_1A_AUDIT_STORAGE_DECISION.md` |
| Depends On | WP2 Charter (RATIFIED); WP2 Implementation Plan (RATIFIED WITH NON-BLOCKING NOTES); WP2.0 (READY WITH EXTERNAL C20 DEPENDENCIES); ADR-C25-002; ADR-C25-005; ADR-C25-006; C25 Invariant Registry |
| Related Invariants | `C25-INV-PROV-001`, `C25-INV-INT-006`, `C25-INV-HG-001`, `C25-INV-ADV-001`, `C25-INV-OWN-001` |
| Implementation Authorization | **None** — this ADR authorizes no code, table, entity, metadata, migration, writer, guard, service, route, or test |

---

## 1. Status

RATIFIED. This ADR is an implementation planning reference only; code
implementation is not authorized. WP2.1B remains NOT AUTHORIZED. WP2.3
remains NOT AUTHORIZED. Generation implementation remains NO GO. Any code
remains NOT AUTHORIZED. It does not amend the WP2 Charter or the WP2
Implementation Plan text; it records the audit-storage judgment those
documents explicitly reserved for an ADR (charter §13.1, OQ-B; Plan §15.4,
§23.1).

> **Amendment record (2026-08-06) — WP2.1B Implementation Authorization
> issued:** `docs/PHASE3C25_WP2_1B_IMPLEMENTATION_AUTHORIZATION.md` grants
> WP2.1B implementation **AUTHORIZED WITH CONDITIONS** (CommercialBrief
> persistence only). This ADR remains RATIFIED (documentation only) and
> assigns the audit writer to **WP2.3**. The save token
> `CommercialBriefSaveOption::AUDIT_WRITE_AUTHORIZED` is a constant on the
> WP2.1B save-option class (delivered by WP2.1B), but **no audit writer is
> authorized** in WP2.1B. WP2.3 audit implementation remains **NOT
> AUTHORIZED**.

## 2. Context

WP2 (`CommercialBrief`) requires an append-only audit trail for generation
governance events, human review events, and disposition events. The ratified
charter fixed the boundary conditions:

- mutable JSON history on `CommercialBrief` is **forbidden** (charter §13.1);
- appending audit through an ordinary entity update is **forbidden**;
- human accept/dismiss must never create an `AIRequestLog` (no provider
  invocation occurs on review);
- a user-editable second business entity requires an ADR amendment;
- the priority order is: (1) reuse Espo audit/stream **if** it can guarantee
  the full structured append-only contract; (2) otherwise an internal
  append-only store — not a CRM scope, no navigation/list/search, no
  ordinary CRUD, written atomically by the transition service — with an ADR
  judgment on first-class-entity status **before implementation**.

The ratified Plan deferred the mechanism decision to WP2.1A (this package).
This ADR makes that decision deterministically so that no core storage
question remains for the implementation phase.

## 3. Decision

**Selected storage model: Option C — an internal append-only C25 audit
record, implemented as one dedicated Espo entity `CommercialBriefAuditEvent`
(module `CommercialIntelligence`), written only by
`CommercialBriefAuditWriter` under an internal save token, enforced by an
append-only hook guard, with zero ordinary CRUD surface.**

This follows the repository's proven append-only ledger pattern
(`ExecutionLedger`, `HumanFeedback`, `AIRequestLog`), not a new persistence
invention:

- schema via entityDefs + Espo metadata rebuild (no migration files, no raw
  DDL — the repo's `AfterInstall` raw-DDL precedent covers only a non-entity
  auxiliary table and is not used here);
- scopes: `entity: true`, `object: false`, `tab: false`, `acl: true`,
  `aclPortal: false`, `customizable: false`, `importable: false`,
  `type: Base`, `statusField: null`, `aclActionList: ["read"]`;
- no navigation, no standard lists, no global search exposure, no layouts,
  no clientDefs, no dedicated routes, no Portal access;
- append-only forever: no update, no delete, for any actor including admin.

## 4. Decision Drivers

1. The charter's structured event contract (action key, from/to
   `reviewStatus`/dispositions, reason, `acceptanceScope`, brief ID,
   `AIJob`/`AIRequestLog` provenance references) exceeds what Espo's
   field-diff audit and user-facing stream can guarantee.
2. Governance audit evidence must not be subject to any cleanup or
   retention mechanism outside C25 control.
3. The audit write must commit atomically with its transition — a service
   transaction concern, not a log concern.
4. The repository already proves the entity+guard+token ledger pattern
   three times; deviating would add risk without benefit.
5. The entity budget (`exactly one persistent C25 artifact`) requires an
   explicit, ADR-recorded reconciliation before any second persistent type.

## 5. Options Considered

| Option | Verdict | Decisive reason |
| --- | --- | --- |
| **A — Reuse Espo audit/stream** | **REJECTED** | Espo's `audited: true` is a field-diff mechanism (used only by `PromptTemplate` and `SendExecution` in this repo); stream is a user-facing activity feed. Neither carries the required structured event schema, neither offers an atomic-with-transition write contract, and stream retention depends on core cleanup configuration outside C25 control and unverifiable in this workspace. Any one of these failures is disqualifying; all hold. |
| **B — JSON history field on `CommercialBrief`** | **REJECTED (forbidden)** | Mutates the immutable projection; weak concurrency/atomicity; unqueryable per event; append-only guard is bypassable by rewriting the array; conflicts with the immutable-projection boundary and the action-level ledger direction (charter §13.1). |
| **C — Internal append-only audit record (selected)** | **SELECTED** | Only option satisfying the full contract; matches three live precedents. |
| **D — Application log / telemetry only** | **REJECTED as the formal store** | Admissible solely for pre-ADR pre-dispatch-gate-failure diagnostics and non-persistent telemetry; not a governance audit record. |

## 6. Selected Storage Model

| Aspect | Decision |
| --- | --- |
| Formal audit storage | One dedicated append-only table backing the `CommercialBriefAuditEvent` entity |
| Independent database table | **Yes** (via entityDefs + rebuild) |
| Espo entity | **Yes** — mechanism reuse of the proven ledger pattern |
| Entity scope metadata | **Yes** — required by any entity; hardened per §10 |
| First-class governed artifact | **Yes** — an append-only governance ledger, **not** a business record; this ADR is the required first-class judgment (charter OQ-B) |
| Ordinary Record API | **No** — `aclActionList: ["read"]`; create/edit/delete denied by ACL and by the guard |
| Navigation / lists / global search | **No** (`object: false`, `tab: false`; no layouts, no clientDefs, no search-enable metadata) |
| Ordinary user read | Only roles explicitly granted read (operator/reviewer/provenance-viewer governance roles); denied by default |
| Admin modify/delete | **Never** — guard rejects all non-new saves and all removals unconditionally; adminMandatory `edit: "no"`, `delete: "no"` |
| Soft delete | `deleteId: true` may be retained solely as a framework-compatibility field. It is excluded from event identity and unique constraints, cannot be mutated, and cannot enable reinsertion of the same governance event. Deletion remains **permanently forbidden** by the guard; no purge path exists |
| Permanently append-only | **Yes** — corrections are new events; updates/deletes have no path |
| Atomic transition + audit | Single transaction in the owning service: validate → insert event → save brief; any failure rolls back both |
| Audit writer module | `Espo\Modules\CommercialIntelligence\Services` |
| Audit writer work package | **WP2.3** (default per Plan §25) |
| Guard | **Yes** — `CommercialBriefAuditEventAppendOnlyGuard` (`BeforeSave`, `BeforeRemove`) |
| Save option / internal token | **Yes** — `CommercialBriefSaveOption::AUDIT_WRITE_AUTHORIZED` (constant on the WP2.1B save-option class) |
| Retention | **Permanent**; no automatic deletion in this phase (§11) |
| Legal/audit hold effect | Audit events are never deleted in this phase; hold representation for brief records is a WP2.3/D5 decision |
| Audit survives brief deletion | **Yes** — brief soft delete never cascades to audit events |
| Audit survives anchor deletion | **Yes** — `OpportunityCandidate` soft delete/invisibility never cascades |
| Provenance reference loss tolerance | `sourceAIJobId`/`sourceAIRequestLogId` are immutable historical references; if C20 records later become unreadable, the references and copied provider/model scalars on the brief remain; audit is never rewritten |
| Pre-dispatch gate failure events | **Yes — approved by this ADR** as first-class `PRE_DISPATCH_GATE_FAILURE` events (resolves the Plan §15.3 conditional) |
| Dedupe reuse events | **Yes** — `GENERATION_REUSED` records cross-request reuse with actor attribution |
| Failed provider invocation facts | Owned by **C20** (`AIJob` FAILED + `AIRequestLog` FAILED + `failureCategory`); C25 audit records only the governance-level `GENERATION_FAILED` event referencing the AIJob — never runtime facts |
| Portal | **Denied** — `aclPortal: false` + `app/aclPortal.json` mandatory false |
| Dedicated API | **No** — reads via standard Record read under ACL; workspace audit display uses internal service calls under existing checks |

## 7. Artifact Classification

| Term | Classification for this ADR |
| --- | --- |
| CRM entity | Yes — `CommercialBriefAuditEvent` is an Espo entity **for mechanism reuse only**; it is not a business entity |
| Entity scope | Yes, hardened (`object:false`, `tab:false`, `aclActionList:["read"]`, `aclPortal:false`) |
| Internal persistent record | Each row is one immutable audit event |
| Database table | One dedicated table, created by Espo rebuild from entityDefs |
| Audit event | The semantic unit: one governed action/observation, recorded once |
| First-class governed artifact | **Yes** — sanctioned by this ADR as a non-business append-only ledger |

**Entity budget reconciliation.** The ratified budget ("exactly one
persistent C25 artifact type in WP2") is reconciled by this ADR to: **one
business artifact (`CommercialBrief`) + one append-only governance ledger
(`CommercialBriefAuditEvent`)**. The ledger is not user-editable, is not a
review/business entity, and is created only under this ADR amendment — the
charter's ADR-amendment precondition (OQ-B; Foundation Plan §7.5 "everything
else requires an explicit ADR amendment") is satisfied by this document.

## 8. Event Contract

### 8.1 Event taxonomy (closed enum `eventType`)

Generation governance: `GENERATION_REQUESTED`, `GENERATION_COMPLETED`,
`GENERATION_FAILED`, `PRE_DISPATCH_GATE_FAILURE`, `GENERATION_REUSED`,
`REGENERATION_REQUESTED`, `SUPERSESSION_CREATED`.
Human review: `REVIEWED`, `ACCEPTED`, `DISMISSED`.
Disposition: `INVALIDATED`, `ARCHIVED`, `GOVERNED_DELETION_REQUESTED`,
`GOVERNED_DELETION_COMPLETED`, `GOVERNED_DELETION_DENIED`.

**Never recorded as C25 audit events:** provider invocation attempts,
provider tokens/cost/latency, model execution results, or any C20 runtime
fact owned by `AIRequestLog`. Human accept/dismiss/invalidate/archive never
creates an `AIRequestLog`.

### 8.2 Field contract

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `id` | system id | yes | system record identifier; not the idempotency contract |
| `eventIdentityKey` | varchar(255) | yes | immutable, server-generated, server-owned, client-writable **no**, unique; generated by `CommercialBriefAuditWriter` per §8.3 |
| `eventType` | enum (§8.1) | yes | closed allowlist |
| `commercialBriefId` | link `CommercialBrief` | nullable | null only for `PRE_DISPATCH_GATE_FAILURE` |
| `opportunityCandidateId` | link `OpportunityCandidate` | yes | read-only anchor reference |
| `actorUserId` | link `User` | yes | actor always recorded |
| `actorType` | enum `USER`/`SYSTEM` | yes | default `USER`; `SYSTEM` reserved, unused this phase |
| `actionKey` | enum (8 `brief.*` keys) | yes | initiating action context |
| `occurredAt` | datetime | yes | server-owned, set at write |
| `requestCorrelationId` | varchar(128) | yes | immutable server-owned correlation key; assigned under the deterministic rules in §8.3 |
| `fromReviewStatus` / `toReviewStatus` | enum (`GENERATED`/`REVIEWED`/`ACCEPTED`/`DISMISSED`) | nullable | null when not a reviewStatus transition |
| `fromValidityDisposition` / `toValidityDisposition` | enum (`NONE`/`INVALIDATED`) | nullable | null when not a validity change |
| `fromRetentionDisposition` / `toRetentionDisposition` | enum (`ACTIVE`/`ARCHIVED`) | nullable | null when not a retention change |
| `acceptanceScope` | enum (`DECISION_SUPPORT_MATERIAL_ONLY`) | nullable | set only on `ACCEPTED` |
| `reasonCode` | enum (`SOURCE_ERROR`, `SOURCE_WITHDRAWN`, `GENERATION_ERROR`, `INSUFFICIENT_EVIDENCE`, `POLICY`, `RETENTION`, `LEGAL_HOLD`, `OTHER`) | nullable | required for dismiss/invalidate/archive/delete and gate-failure events |
| `reasonText` | text (≤ 2000 chars, plain text) | nullable | required whenever `reasonCode` is present |
| `sourceAIJobId` | link `AIJob` | nullable | absent for pre-dispatch events (no-AIJob marker) |
| `sourceAIRequestLogId` | link `AIRequestLog` | nullable | reference only; human events never create one |
| `regenerationRequestId` | varchar(128) | nullable | regeneration events only |
| `relatedBriefId` | link `CommercialBrief` | nullable | prior revision for supersession events |
| `metadataVersion` | int | yes | event contract version; starts at `1` |
| `createdAt` | system datetime | yes | system-owned |

**No arbitrary JSON metadata field** — the contract is fully structured;
schema evolution is handled by `metadataVersion`. **Forbidden content in
every field:** raw prompts, completion payloads, provider credentials,
source original content, secrets, PII beyond the actor reference.

### 8.3 Event identity and correlation assignment

`eventIdentityKey` is the single authoritative event identity. It is required,
immutable, server-generated by `CommercialBriefAuditWriter`, never accepted
directly from a client, and has a maximum length of 255. Its deterministic
generation rule is:

```text
eventIdentityKey = H(eventType | actionKey | requestCorrelationId)
```

The database unique constraint is `eventIdentityKey UNIQUE`. A database
composite unique index is permitted only when it is exactly equivalent to this
rule; two potentially divergent idempotency identities are forbidden.

`requestCorrelationId` is assigned as follows:

- **Request-level correlation** applies to `GENERATION_REQUESTED`,
  `GENERATION_REUSED`, `REGENERATION_REQUESTED`, `SUPERSESSION_CREATED`,
  `REVIEWED`, `ACCEPTED`, `DISMISSED`, `INVALIDATED`, `ARCHIVED`,
  `GOVERNED_DELETION_REQUESTED`, `GOVERNED_DELETION_COMPLETED`,
  `GOVERNED_DELETION_DENIED`, and `PRE_DISPATCH_GATE_FAILURE`. Use
  `c25-brief-request:{requestId}`, or for regeneration,
  `c25-brief-regenerate:{regenerationRequestId}`. Every manual
  transition, disposition, or deletion request has a unique request ID. A
  retry with the same request ID returns the existing event and performs no
  duplicate brief mutation or side effect.
- **Attempt-level correlation** applies only to `GENERATION_COMPLETED` and
  `GENERATION_FAILED`. Use
  `c25-brief-attempt:{requestKey}:{attemptNumber}`, or for regeneration,
  `c25-brief-regenerate-attempt:{regenerationRequestId}:{attemptNumber}`.
  One generation request may have multiple attempts; each attempt has its own
  identity, may produce only one terminal event (completed or failed), and a
  retry of that same attempt is idempotent. Different attempt numbers must not
  collide. A regeneration request ID alone is never sufficient for a terminal
  attempt event.
- A request-level correlation may legitimately produce different event types,
  such as `GENERATION_REQUESTED` and `GENERATION_REUSED`, or
  `REGENERATION_REQUESTED` and `SUPERSESSION_CREATED`; `eventType` therefore
  participates in the identity. The same `eventType + actionKey +
  requestCorrelationId` must never repeat.
- Each `eventType` accepts only its ratified action key from the closed
  allowlist: `GENERATION_REQUESTED`, `GENERATION_COMPLETED`,
  `GENERATION_FAILED`, and `GENERATION_REUSED` use `brief.generate`;
  `REGENERATION_REQUESTED` and `SUPERSESSION_CREATED` use
  `brief.regenerate`; `REVIEWED`, `ACCEPTED`, `DISMISSED`, `INVALIDATED`, and
  `ARCHIVED` use respectively `brief.review`, `brief.accept`, `brief.dismiss`,
  `brief.invalidate`, and `brief.archive`; all governed-deletion events use
  `brief.delete`; and `PRE_DISPATCH_GATE_FAILURE` accepts only
  `brief.generate` or `brief.regenerate`. Provider/runtime-only facts cannot
  be represented as `brief.*` actions, and arbitrary action strings are
  forbidden.

If the Espo framework mechanism retains `deleted` or `deleteId`, it is a
framework-compatibility field only: it is excluded from event identity and all
unique constraints, cannot be modified, cannot support soft-delete reuse, and
the guard rejects every delete or soft-delete mutation.

### 8.4 Indexes

- **unique:** `eventIdentityKey`;
- `(commercialBriefId, occurredAt)` — per-brief history;
- `(opportunityCandidateId, occurredAt)` — per-anchor history;
- `(eventType, occurredAt)` — event-type history;
- `(actorUserId, occurredAt)` — actor history;
- `sourceAIJobId`, `sourceAIRequestLogId`, `regenerationRequestId`, and
  `requestCorrelationId` — provenance and correlation lookup.

## 9. Append-Only and Atomicity Contract

1. **Insert-only.** No update, no delete, no merge, no ordinary save, no
   generic create/edit/delete API — for any role, including admin.
2. **Guard enforcement.** `BeforeSave`: reject any non-new save; reject any
   create lacking `CommercialBriefSaveOption::AUDIT_WRITE_AUTHORIZED === true`.
   `BeforeRemove`: unconditional `Forbidden`. (Live precedent:
   `ExecutionLedgerAppendOnlyGuard`, `AIRequestLogAppendOnlyGuard`.)
3. **Unique event identity** — `eventIdentityKey` plus the §8.4 unique
   constraint; `deleteId` is not part of either identity or uniqueness.
4. **Idempotent writer** — `CommercialBriefAuditWriter` generates
   `eventIdentityKey`, calls `findExisting(eventIdentityKey)` before insert,
   and returns the existing equivalent event without an insert or any
   additional state mutation. The database unique constraint is the final
   concurrency defense: on a unique collision, the writer rereads and returns
   the existing equivalent event rather than converting it to a generic
   internal error.
5. **Actor required; timestamp server-owned** — never client-supplied.
6. **Action-key allowlist** — only the 8 ratified `brief.*` keys.
7. **State consistency** — the writer validates from/to values against the
   brief being transitioned, inside the same transaction.
8. **Payload-equivalence conflict** — if the same identity is associated
   with a non-equivalent payload, the writer rejects it as an
   idempotency-context conflict, rolls back the transition, and never
   overwrites the original event. At minimum, equivalence compares
   `eventType`, `actionKey`, `commercialBriefId`, `opportunityCandidateId`,
   from/to `reviewStatus`, from/to `validityDisposition`, from/to
   `retentionDisposition`, `acceptanceScope`, `regenerationRequestId`, and
   `relatedBriefId`.
9. **Atomicity** — CommercialBriefAuditWriter never owns, opens, commits,
   or closes an independent transaction. It joins the transaction opened or
   inherited by the owning lifecycle, generation, or disposition service.
   Event insert and brief save commit together; an audit write failure rolls
   back the brief mutation, a brief-save failure rolls back the audit insert,
   and a payload-conflict collision rolls back the whole transaction. The
   repository must not auto-commit around the owning transaction. WP2.3 must
   provide runtime transaction evidence before the ledger is implemented.
   `PRE_DISPATCH_GATE_FAILURE`, which has no brief mutation, may be a single
   insert transaction but still uses this writer, guard, token, identity, and
   unique contract; the writer still does not manage an independent nested
   transaction and no `AIJob` or `AIRequestLog` is created. (Precedent:
   `AIRequestLogService` marks the PromptTemplate reference inside the same
   transaction.)
10. **No disguise** — provider invocation facts never appear as human
   governance events; human governance events never write `AIRequestLog`.

## 10. ACL and Visibility

- Scope ACL: `acl: true`, `aclActionList: ["read"]`; `aclDefs` = `{}`.
- `app/acl.json` (append): **no** `mandatory.scopeLevel` force-off (the
  WP1.2 lesson: force-off makes role read grants impossible);
  `adminMandatory.scopeLevel.CommercialBriefAuditEvent` =
  `{create: "no", read: "all", edit: "no", delete: "no"}`.
- `app/aclPortal.json` (append): `mandatory.scopeLevel.CommercialBriefAuditEvent: false` —
  Portal fully denied.
- Read is granted per role via the Role UI (operator/reviewer/
  provenance-viewer governance roles); default deny.
- No dedicated read API, routes, layouts, clientDefs, dashlets, or UI.

## 11. Retention and Deletion

| Question | Decision |
| --- | --- |
| Default retention | **Permanent** — audit evidence is governance history |
| Automatic cleanup | **None** — no job exists in the extension (verified: no `Jobs/`/`ScheduledJob` anywhere in custom modules) and none may be added for this store |
| Deleted with the brief? | **No** — brief soft delete never cascades |
| Deleted with the anchor? | **No** |
| Legal hold / audit hold | Brief-level hold representation is a WP2.3/D5 decision; audit events themselves are never deleted in this phase |
| Privacy deletion request | Out of scope this phase; a future retention ADR must assess actor-reference and `reasonText` handling before any mechanism exists |
| Governed deletion of audit events | **Not permitted in this phase** |
| Physical deletion ever? | Only via a **future independent retention ADR** defining approver, scope, and a dedicated purge mechanism |
| Until a retention policy is ratified | **audit deletion = NO** |

## 12. Cross-Phase Boundaries

- **C20:** no `AIJob`/`AIRequestLog`/`PromptTemplate` modification; no new
  `AIRequestLog` for human events; C20 runtime facts remain C20-owned
  (C20-INV-07/08). References are read-only.
- **C24:** no `OpportunityCandidate` mutation or lifecycle interaction;
  anchor is a read-only reference (C24-INV-SEP-002, LIFE-001).
- **C22:** no ActionGate/execution interaction (C22-INV-EX-001).
- **CRM Core:** no FK and no write path (ADR-C25-005 §3.6).
- **C25:** audit records are governance metadata, not business facts
  (C25-INV-INT-006); they never substitute for C24's immutable transition
  records (ADR-C25-006 §4.3).

## 13. Work-Package Ownership

| WP | Owns | Does not own |
| --- | --- | --- |
| **WP2.1A** | This ADR; the decision package; storage contract; artifact classification; entity/artifact budget reconciliation; conditional allowlist; independent review; ratification | Any code, table, entity, metadata, migration, writer, guard, service, route, test |
| **WP2.1B** | `CommercialBrief` entity/persistence (separately authorized) | Audit storage (not by default) |
| **WP2.3** | Audit entityDefs/scopes/metadata, `CommercialBriefAuditWriter`, append-only guard, transaction integration, audit tests, lifecycle/disposition integration, verification report | Anything before this ADR is ratified and WP2.3 is separately authorized |

This is the default ownership from the ratified Plan (§23.2, §25); no
deviation is requested.

## 14. Conditional Allowlist

**Approved future files (conditional on this ADR's ratification + separate
WP2.3 authorization; owning WP = WP2.3 unless noted):**

- `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/entityDefs/CommercialBriefAuditEvent.json`
- `.../Resources/metadata/scopes/CommercialBriefAuditEvent.json`
- `.../Resources/metadata/aclDefs/CommercialBriefAuditEvent.json` (`{}`)
- `.../Resources/metadata/app/acl.json` (append `adminMandatory` entry; no force-off)
- `.../Resources/metadata/app/aclPortal.json` (append mandatory false)
- `.../Resources/i18n/en_US/CommercialBriefAuditEvent.json` and `.../zh_CN/CommercialBriefAuditEvent.json` (key parity)
- `.../Entities/CommercialBriefAuditEvent.php`
- `.../Services/CommercialBriefAuditWriter.php`
- `.../Hooks/CommercialBriefAuditEvent/CommercialBriefAuditEventAppendOnlyGuard.php`
- Save token: `AUDIT_WRITE_AUTHORIZED` constant on the WP2.1B `CommercialBriefSaveOption` class (no new file)
- Schema mechanism: Espo metadata rebuild (no migration files; no AfterInstall change)
- `tests/test_phase3c25_wp2_3_audit_*.py` plus `crm-extension/tests/test_extension_skeleton.py` / `test_espo_php_namespace_contracts.py` inventory updates
- `docs/audit/` ADR implementation verification report

**Forbidden files/surfaces:** Portal UI; list layout; detail editor;
generic controller; ordinary Record routes; CRM Core files; C20 files;
`AIRequestLog` modification; migration/SQL files; scheduler/job files;
stream configuration.

## 15. Consequences

- WP2.3 receives a fully-determined audit implementation contract; no
  storage decision remains at code time.
- The entity budget is explicitly reconciled to one business artifact + one
  governance ledger; any further persistent type requires a new ADR.
- `PRE_DISPATCH_GATE_FAILURE` becomes a first-class event (the Plan's
  conditional approval is hereby granted).
- Review/disposition implementation (WP2.3) depends on this ADR's
  ratification; generation implementation (WP2.2) remains blocked by C20
  dependencies independently of this ADR.

## 16. Rejected Alternatives

See §5: Espo audit/stream (A), JSON history (B), application-log-only (D).
A non-entity raw-DDL table was also considered and rejected: the repo's only
raw-DDL precedent (`AfterInstall` `numbering_sequence`) covers an auxiliary
non-entity table, while three governed ledgers prove the entity+guard
pattern this ADR selects; inventing a second persistence style would add
risk with no governance benefit.

## 17. Ratification Gates

1. Independent review of this ADR and the decision package.
2. WP2.1A ratification sign-off (storage model, artifact classification,
   entity budget reconciliation, event contract, retention boundary,
   conditional allowlist).
3. WP2.3 separate authorization before any conditional-allowlist file is
   created.
4. Any future retention/purge mechanism requires an independent retention
   ADR.

## 18. References

- `docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md` (§13, §16.1, §26 OQ-B)
- `docs/PHASE3C25_WP2_IMPLEMENTATION_PLAN.md` (§15, §23.1, §25, §28.1-conditional)
- `docs/PHASE3C25_WP2_1A_AUDIT_STORAGE_DECISION.md`
- `docs/audit/ADR-C25-002_AI_COMMERCIAL_BRIEF_GOVERNANCE.md`
- `docs/audit/ADR-C25-005_CROSS_LAYER_READ_ONLY_ACCESS_CONTRACTS.md`
- `docs/audit/ADR-C25-006_AI_CONFIDENCE_AUDIT_FEEDBACK_GOVERNANCE.md`
- `docs/adr/C25_INVARIANT_REGISTRY.md`
- `docs/adr/C20_INVARIANT_REGISTRY.md` (INV-07/08)
- `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md`
- `docs/PHASE3C24_WP2_IMPLEMENTATION_CHARTER.md`
- `docs/adr/C24_INVARIANT_REGISTRY.md`
- Live precedents: `crm-extension/files/custom/Espo/Modules/Prospecting/Hooks/ExecutionLedger/ExecutionLedgerAppendOnlyGuard.php`; `.../Hooks/HumanFeedback/HumanFeedbackAppendOnlyGuard.php`; `.../AIPlatform/Hooks/AIRequestLog/AIRequestLogAppendOnlyGuard.php`; `.../AIPlatform/Services/AIRequestLogService.php`; `.../AIPlatform/Resources/metadata/entityDefs/{AIRequestLog,AIJob}.json`; `.../Prospecting/Resources/metadata/entityDefs/ExecutionLedger.json`; `crm-extension/scripts/AfterInstall.php`

## 19. Ratification Record

Final Ratification Review completed.

| Item | Result |
| --- | --- |
| Review Type | Final Ratification Review |
| Verdict | RATIFIED WITH NON-BLOCKING NOTES |
| Date | 2026-08-02 |
| Storage Model | PASS |
| Artifact Classification | PASS |
| Read Surface | PASS |
| Event Contract | PASS |
| Event Identity | PASS |
| Atomicity | PASS |
| Entity Budget | PASS |
| Conditional Allowlist | PASS |
| Remaining Blockers | None |
| WP2.1A | RATIFIED |
| WP2.1B | AUTHORIZED WITH CONDITIONS (2026-08-06) |
| WP2.3 | NOT AUTHORIZED |
| Any Code | NOT AUTHORIZED (outside the WP2.1B scope) |

> **Amendment record (2026-08-06):** Per
> `docs/PHASE3C25_WP2_1B_IMPLEMENTATION_AUTHORIZATION.md`, WP2.1B =
> **AUTHORIZED WITH CONDITIONS**; WP2.3 / Any Code (outside the WP2.1B
> scope) remain **NOT AUTHORIZED**.
