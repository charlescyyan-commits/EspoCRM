# Phase3C25 WP2.1A — Audit Storage Decision Package

| Field | Value |
| --- | --- |
| Document Type | Governance Decision Package (documentation only) |
| Work Package | WP2.1A — Audit Storage Decision and ADR Ratification |
| ADR | `docs/adr/ADR-C25-007_COMMERCIAL_BRIEF_AUDIT_STORAGE.md` (**RATIFIED — implementation planning reference only; code implementation not authorized**) |
| Status | **RATIFIED** — Implementation Planning Reference Only; Code Implementation Not Authorized |
| Date | 2026-08-01 |
| Implementation Authorization | **NO** — no code, table, entity, metadata, migration, writer, guard, service, route, or test is authorized |

> **Governance alignment amendment (2026-08-06):** The C20 Dependency Closure
> Amendment is ratified at `b632f1d`. WP2.1A consumes the foundation gate
> **Capability identity + Purpose policy + Boundary evidence**. The former
> D-3 `INV-05…11 ACTIVE` requirement is not required for this foundation
> decision; C20-INV-05…11 remain deferred runtime maturity items. This record
> authorizes no implementation, generation runtime, provider call, or
> deployment.

> **Administrative synchronization note (2026-08-06):** Historical WP2.2
> records exist in the repository (`PHASE3C25_WP2_2_*` and
> `docs/audit/PHASE3C25_WP2_2_*`). They are **HISTORICAL / SUPERSEDED** and
> do not change the state asserted here: WP2.1B remains **NOT AUTHORIZED**,
> WP2.3 remains **NOT AUTHORIZED**, **Any Code** remains **NOT AUTHORIZED**.
> See `docs/PHASE3C25_WP2_AUTHORIZATION_STATE_SYNCHRONIZATION.md`.
>
> **Amendment record (2026-08-06) — WP2.1B Implementation Authorization
> issued:** `docs/PHASE3C25_WP2_1B_IMPLEMENTATION_AUTHORIZATION.md` grants
> WP2.1B implementation **AUTHORIZED WITH CONDITIONS** (CommercialBrief
> persistence only; **no audit**). WP2.1A remains RATIFIED (documentation
> only); WP2.3 audit implementation remains **NOT AUTHORIZED**.

---

## 1. Executive Verdict

**WP2.1A RATIFIED.**

The package evaluated four storage options against the ratified charter
contract and live repository evidence, and selected **Option C — an internal
append-only C25 audit record** implemented as one dedicated Espo entity
`CommercialBriefAuditEvent` (module `CommercialIntelligence`), written only
by `CommercialBriefAuditWriter` under `CommercialBriefSaveOption::
AUDIT_WRITE_AUTHORIZED`, enforced by an append-only hook guard, with zero
ordinary CRUD surface. The artifact is classified as a **first-class
governed artifact (append-only governance ledger), not a business record**;
the entity budget is reconciled by the ADR to one business artifact + one
governance ledger. All seven Go/No-Go checks pass (§15).

WP2.1A is RATIFIED. This package is an Implementation Planning Reference Only.
Code Implementation Not Authorized. WP2.1B remains NOT AUTHORIZED. WP2.3
remains NOT AUTHORIZED. The C20 foundation gate is ratified, but generation
implementation remains NOT AUTHORIZED pending its separate predecessor gates
and authorization. Any code remains NOT AUTHORIZED.

---

## 2. Governing Sources

| Source | Role |
| --- | --- |
| `docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md` | Ratified charter — §13 audit model, §16.1 per-action audit rows, §26 OQ-B |
| `docs/PHASE3C25_WP2_IMPLEMENTATION_PLAN.md` | Ratified Plan — §15 storage decision input, §23.1 WP2.1A scope, §25 WP2.3 default ownership, §28.1-conditional |
| `docs/PHASE3C25_WP2_0_C20_DEPENDENCY_RESOLUTION.md` + `..._ADDENDUM.md` | WP2.0 outcomes; WP2.1A C20-independence basis |
| `docs/audit/ADR-C25-002_AI_COMMERCIAL_BRIEF_GOVERNANCE.md` | Brief governance — acceptance scope, immutability, supersession |
| `docs/audit/ADR-C25-005_CROSS_LAYER_READ_ONLY_ACCESS_CONTRACTS.md` | Cross-layer read-only contracts; provenance chain |
| `docs/audit/ADR-C25-006_AI_CONFIDENCE_AUDIT_FEEDBACK_GOVERNANCE.md` | §4 audit requirements (governance-only), §4.3 audit rules |
| `docs/adr/C25_INVARIANT_REGISTRY.md` | PROV-001, INT-006, HG-001, ADV-001, OWN-001 |
| `docs/PHASE3C24_WP2_IMPLEMENTATION_CHARTER.md` | C24 lifecycle/audit precedent (transitionHistory) |
| `docs/adr/C24_INVARIANT_REGISTRY.md` | SEP-002, LIFE-001 |
| `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` | AIRequestLog model, invariants §8 |
| `docs/adr/C20_INVARIANT_REGISTRY.md` | C20-INV-07/08 (append-only, one-log-per-invocation) |

---

## 3. Repository Evidence

Verified against the **live** extension tree (not archives):

| Evidence | Finding |
| --- | --- |
| Append-only ledger pattern (×3) | `ExecutionLedgerAppendOnlyGuard`, `HumanFeedbackAppendOnlyGuard`, `AIRequestLogAppendOnlyGuard` — all `BeforeSave` reject non-new saves, require a create save-option token; `BeforeRemove` unconditionally `Forbidden`. All three ledgers are Espo entities with `object:false`, `tab:false`, `acl:true`, `aclPortal:false`, `type:Base` scopes and `deleteId: true`. |
| `AIRequestLog` entityDefs | Required-field validation for provider/model/tokens/cost/latency/template; unique indexes `(aiJobId, attemptId, deleteId)` and `(aiJobId, attemptNumber, deleteId)`; `deleteId: true`. |
| `AIRequestLogService` | Create-only; marks the PromptTemplate reference **inside the same transaction** (atomicity precedent). |
| `AIJobService` | `findExistingIdempotencyKey` pre-check + unique `(idempotencyKey, deleteId)` index (idempotent-writer precedent). |
| PromptTemplate immutability | `IMMUTABLE_AFTER_REFERENCE_FIELDS` + hash-equality guard + supersede-only `createNewVersion()` (immutability-by-guard precedent). |
| `OpportunityCandidate` audit | `transitionHistory` JSON field appended by its lifecycle service under a save option — the pattern the WP2 charter explicitly **forbids** for CommercialBrief (mutable JSON history). |
| Espo `audited` flag | Used only by `PromptTemplate` and `SendExecution` (`"audited": true`); it is a field-diff audit, per `docs/audit/00_EspoCRM_Baseline_State.md` and `docs/architecture/ADR_C16_QUOTE_PI_ARCHITECTURE.md` (stream captures state transitions as ActionHistoryRecord). |
| Stream usage | **Zero** `"stream"` metadata and zero stream service usage in custom modules. |
| Scheduled jobs / cleanup | **Zero** `Jobs/`/`ScheduledJob`/cleanup/retention logic in custom modules. Espo core is not vendored here; stream retention behavior is not verifiable in this workspace and is outside C25 control. |
| Table creation conventions | Entity schema via entityDefs + Espo rebuild (universal); `crm-extension/scripts/AfterInstall.php` exists with raw PDO DDL for one non-entity auxiliary table (`numbering_sequence`) — the only raw-DDL precedent. No `Migrations/` directory; a test forbids migration artifacts. |
| Soft delete | `deleteId: true` on ExecutionLedger, HumanFeedback, AIRequestLog, AIJob, SendExecution. |
| ACL precedents | AIPlatform `app/acl.json` uses `mandatory.scopeLevel` force-off + `adminMandatory`; C24 governed scopes avoid force-off after the WP1.2 correction (force-off made role read grants impossible). |

---

## 4. Options Comparison

Full option text in ADR §5. Decisive comparison against the charter's
19-point guarantee list (append-only; actor; timestamp; event type; action
key; from/to reviewStatus; from/to validityDisposition; from/to
retentionDisposition; reason; acceptanceScope; brief ID; anchor; provenance
references; correlation ID; atomic write; no ordinary edit; no ordinary
delete; governance-compatible retention; no evidence-destroying cleanup):

| Guarantee | A — Espo audit/stream | B — JSON history | C — Internal append-only record | D — App log only |
| --- | --- | --- | --- | --- |
| Structured event schema (from/to, reason, actionKey, scope) | ✗ (field-diff / feed) | △ (unstructured JSON) | ✅ | ✗ |
| Append-only with no edit/delete for anyone | ✗ (not enforceable) | ✗ (array rewritable) | ✅ (guard-proven ×3) | ✗ |
| Atomic write with transition | ✗ | △ (same-row save, weak) | ✅ (one transaction) | ✗ |
| Queryable per event (indexes) | △ | ✗ | ✅ | ✗ |
| Retention under C25 control; no cleanup risk | ✗ (core cleanup outside C25 control, unverifiable) | ✅ | ✅ | ✗ (non-persistent) |
| Immutable-projection boundary kept | ✅ | ✗ (mutates brief) | ✅ | ✅ |
| Repository precedent | — | C24 (forbidden for WP2) | ×3 ledgers | — |

Verdict: A rejected (multiple guarantee failures); B rejected (forbidden by
charter §13.1); D rejected as the formal store (telemetry only); **C
selected**.

---

## 5. Selected Decision

One dedicated append-only audit entity `CommercialBriefAuditEvent`:

- **Table**: independent, created by Espo metadata rebuild from entityDefs
  (no migration files; no AfterInstall change; no raw DDL).
- **Entity**: yes — mechanism reuse of the proven ledger pattern; not a
  business entity.
- **Scope**: hardened (`object:false`, `tab:false`, `acl:true`,
  `aclPortal:false`, `aclActionList:["read"]`, `statusField:null`).
- **Navigation / lists / global search**: none.
- **CRUD**: create only via `CommercialBriefAuditWriter` + token; update and
  delete impossible for any actor including admin (guard + ACL).
- **Soft delete**: `deleteId: true` carried per precedent, but deletion is
  permanently forbidden by the guard.
- **`deleteId` boundary**: if retained for framework compatibility, it is not
  event identity, is excluded from all unique constraints, cannot be mutated,
  and cannot permit reinsertion of the same governance event.
- **Writer ownership**: module `CommercialIntelligence`; work package WP2.3.
- **Read**: standard Record read under role-granted ACL; no dedicated API.
- **Portal**: denied (scope + `app/aclPortal.json` mandatory false).

---

## 6. Event Matrix

Closed taxonomy (15 event types). "—" = field left null. All rows:
`eventIdentityKey` + `actorUserId` + `actorType` + `occurredAt` + `requestCorrelationId` +
`metadataVersion` required.

| Event | actionKey | briefId | from→to fields set | reason | provenance refs | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `GENERATION_REQUESTED` | `brief.generate` | yes (after persist intent) / correlates by request key | — → reviewStatus `GENERATED` (on completion) | — | — (pre-dispatch: no AIJob yet) | Records the explicit human request |
| `GENERATION_COMPLETED` | `brief.generate` | yes | — → `GENERATED` | — | `sourceAIJobId`, `sourceAIRequestLogId` | Written with brief persist, same tx |
| `GENERATION_FAILED` | `brief.generate` | — (no brief) | — | `reasonCode` + `reasonText` | `sourceAIJobId` (FAILED job) | Governance-level fact only; runtime facts stay in C20 |
| `PRE_DISPATCH_GATE_FAILURE` | `brief.generate` / `brief.regenerate` | **null** | — | gate `reasonCode` + summary | — (no-AIJob marker) | Approved as first-class by the ADR |
| `GENERATION_REUSED` | `brief.generate` | yes (reused brief) | — | — | reused brief's refs | Cross-request reuse attribution (reusing requester = actor) |
| `REGENERATION_REQUESTED` | `brief.regenerate` | yes (prior brief) | — | required | prior refs; `regenerationRequestId`; `relatedBriefId` | Unique nonce per request |
| `SUPERSESSION_CREATED` | `brief.regenerate` | yes (new revision) | — → `GENERATED` | — | new refs; `relatedBriefId` = prior | Prior brief untouched |
| `REVIEWED` | `brief.review` | yes | `GENERATED → REVIEWED` | — | brief's refs | — |
| `ACCEPTED` | `brief.accept` | yes | `REVIEWED → ACCEPTED` | — | `acceptanceScope` set; brief's refs | Zero side effects; **no AIRequestLog** |
| `DISMISSED` | `brief.dismiss` | yes | `REVIEWED → DISMISSED` | required | brief's refs | `acceptanceScope` forbidden |
| `INVALIDATED` | `brief.invalidate` | yes | validity `NONE → INVALIDATED` | required | brief's refs | reviewStatus unchanged |
| `ARCHIVED` | `brief.archive` | yes | retention `ACTIVE → ARCHIVED` | required | brief's refs | reviewStatus/validity unchanged |
| `GOVERNED_DELETION_REQUESTED` | `brief.delete` | yes | — | required | brief's refs | Hold check happens after |
| `GOVERNED_DELETION_COMPLETED` | `brief.delete` | yes | brief framework `deleteId` set (no from/to fields) | required | brief's refs | Soft delete; audit retained; audit-event `deleteId` remains compatibility-only |
| `GOVERNED_DELETION_DENIED` | `brief.delete` | yes | — | required (denial basis) | brief's refs | e.g., `LEGAL_HOLD` |

---

## 7. Persistence Contract

- Insert-only rows. `eventIdentityKey` is required, immutable,
  server-generated, server-owned, client-writable **no**, `varchar(255)`, and
  the single unique event identity. `CommercialBriefAuditWriter` generates it:

  ```text
  eventIdentityKey = H(eventType | actionKey | requestCorrelationId)
  ```

  The database unique constraint is `eventIdentityKey UNIQUE`. A composite
  unique index is permitted only when exactly equivalent; divergent identities
  are forbidden.
- `deleteId` is a framework-compatibility field only and is excluded from
  event identity and unique constraints. It is immutable, cannot support
  soft-delete reuse, and the guard rejects delete and soft-delete mutation.
- `requestCorrelationId` is immutable and server-owned. Request-level events
  (`GENERATION_REQUESTED`, `GENERATION_REUSED`, `REGENERATION_REQUESTED`,
  `SUPERSESSION_CREATED`, `REVIEWED`, `ACCEPTED`, `DISMISSED`, `INVALIDATED`,
  `ARCHIVED`, all governed-deletion events, and
  `PRE_DISPATCH_GATE_FAILURE`) use `c25-brief-request:{requestId}` or
  `c25-brief-regenerate:{regenerationRequestId}`. A retry with the same
  request ID returns the existing event and repeats neither brief mutation nor
  side effect.
- `GENERATION_COMPLETED` and `GENERATION_FAILED` use attempt-level
  correlation: `c25-brief-attempt:{requestKey}:{attemptNumber}`, or
  `c25-brief-regenerate-attempt:{regenerationRequestId}:{attemptNumber}`.
  One request may have multiple attempts; each attempt has independent
  identity, may have only one terminal event, and retries are idempotent.
  A regeneration request ID without an attempt suffix is invalid for terminal
  attempt events.
- The same request-level correlation can have distinct event types; therefore
  `eventType` participates in identity and the same
  `eventType + actionKey + requestCorrelationId` cannot repeat. `actionKey`
  must come from the closed ratified allowlist:
  `GENERATION_REQUESTED`, `GENERATION_COMPLETED`, `GENERATION_FAILED`, and
  `GENERATION_REUSED` use `brief.generate`; `REGENERATION_REQUESTED` and
  `SUPERSESSION_CREATED` use `brief.regenerate`; `REVIEWED`, `ACCEPTED`,
  `DISMISSED`, `INVALIDATED`, and `ARCHIVED` use respectively `brief.review`,
  `brief.accept`, `brief.dismiss`, `brief.invalidate`, and `brief.archive`;
  all governed-deletion events use `brief.delete`; and
  `PRE_DISPATCH_GATE_FAILURE` permits only `brief.generate` or
  `brief.regenerate`. Provider/runtime facts cannot masquerade as `brief.*`
  actions, and arbitrary strings are forbidden.
- Field contract per ADR §8.2 (including the required/immutable/
  server-owned `eventIdentityKey` and the correlation rules above). No
  arbitrary JSON metadata; `metadataVersion` starts at `1`.
- Query indexes: `(commercialBriefId, occurredAt)`,
  `(opportunityCandidateId, occurredAt)`, `(eventType, occurredAt)`,
  `(actorUserId, occurredAt)`, `sourceAIJobId`, `sourceAIRequestLogId`,
  `regenerationRequestId`, and `requestCorrelationId`.
- Writer idempotency: generate `eventIdentityKey`, then
  `findExisting(eventIdentityKey)` before insert. An existing equivalent event
  is returned with no insert and no additional state mutation; a concurrent
  unique collision rereads and returns that existing event rather than a
  generic internal error. If an identical identity has a non-equivalent
  payload, reject it as an idempotency-context conflict, roll back the
  transition, and never overwrite the existing event. Equivalence compares at
  least `eventType`, `actionKey`, `commercialBriefId`,
  `opportunityCandidateId`, from/to review/validity/retention dispositions,
  `acceptanceScope`, `regenerationRequestId`, and `relatedBriefId`.

---

## 8. Atomicity Model

1. Owning service (`CommercialBriefLifecycleService` /
   `CommercialBriefGenerationService`) opens one transaction per governed
   action.
2. Order: validate transition → insert audit event (writer, token) → save
   brief (save option) → commit.
3. CommercialBriefAuditWriter never owns, opens, commits, or closes an
   independent transaction; it joins the transaction opened or inherited by
   the owning lifecycle, generation, or disposition service. The repository
   must not auto-commit around that transaction.
4. An idempotency collision returns the existing equivalent event and causes
   no insert and no additional state mutation. A collision with a
   non-equivalent payload is an idempotency-context conflict and rolls back
   the whole transaction.
5. Audit write failure ⇒ full rollback (no transition without audit). Brief
   save failure ⇒ audit insert rollback (no orphan success event).
6. From/to values are validated against the brief's actual state inside the
   same transaction.
7. Duplicate transition event is structurally prevented by
   `eventIdentityKey UNIQUE` plus the writer pre-check.
8. `PRE_DISPATCH_GATE_FAILURE` has no brief mutation and may use a single
   insert transaction, but still uses the same writer, guard, token, identity,
   and unique contract. The writer does not manage an independent nested
   transaction, and this event creates neither `AIJob` nor `AIRequestLog`.
9. WP2.3 must provide runtime transaction evidence before any audit ledger is
   implemented.
10. Provider facts never disguise as human events; human events never write
   `AIRequestLog` (ADR §9.9).

---

## 9. Retention Model

| Item | Decision |
| --- | --- |
| Default retention | Permanent |
| Automatic cleanup | None; no job may be introduced for this store |
| Brief soft delete | Audit retained |
| Anchor soft delete / invisibility | Audit retained |
| Legal/audit hold | Brief-level hold: WP2.3/D5 decision; audit events never deleted this phase |
| Privacy deletion request | Out of scope this phase; future retention ADR must assess before any mechanism |
| Physical deletion | Only via a future independent retention ADR (approver + scope + purge mechanism) |
| Current phase rule | **audit deletion = NO** |

---

## 10. Entity Budget Reconciliation

| Before (ratified) | After (this ADR) |
| --- | --- |
| Exactly one persistent C25 artifact type in WP2: `CommercialBrief`; everything else requires an ADR amendment | One **business artifact** (`CommercialBrief`) + one **append-only governance ledger** (`CommercialBriefAuditEvent`), the latter sanctioned by ADR-C25-007 as a non-business, non-user-editable record |

The charter's preconditions are met: not a user-editable second business
entity; ADR amendment executed (this package); not a CRM scope in the
navigation/list/search sense; no ordinary CRUD. Any further persistent type
requires a new ADR.

---

## 11. Conditional Future Allowlist

As ADR §14. Summary: **approved-future (conditional on ADR ratification +
WP2.3 separate authorization; all owned by WP2.3)** — audit entityDefs,
scopes, aclDefs (`{}`), `app/acl.json` append (adminMandatory; no force-off),
`app/aclPortal.json` append, i18n en/zh pair, `Entities/CommercialBriefAuditEvent.php`,
`Services/CommercialBriefAuditWriter.php`,
`Hooks/CommercialBriefAuditEvent/CommercialBriefAuditEventAppendOnlyGuard.php`,
save-token constant on the WP2.1B `CommercialBriefSaveOption` class (no new
file), schema via Espo rebuild, `tests/test_phase3c25_wp2_3_audit_*.py` +
skeleton/namespace inventory updates, verification report.
**Forbidden** — Portal UI, list layout, detail editor, generic controller,
ordinary Record routes, CRM Core files, C20 files, `AIRequestLog`
modification, migration/SQL files, scheduler/job files, stream config.

---

## 12. Work-Package Sequencing

1. **WP2.1A (this package)** — decision + ADR; docs only.
2. **WP2.1A ratification review** — independent sign-off (gate §15).
3. WP2.1B (separately authorized) — CommercialBrief persistence; no audit.
4. WP2.3 (separately authorized, after ADR ratified) — audit implementation
   per §11 + lifecycle/disposition integration + audit tests.
5. WP2.2 remains **NOT AUTHORIZED** until its predecessor gates are met. The
   C20 closure conditions are satisfied for foundation consumption by the WP2.0
   closure addendum; this does not authorize generation runtime.

---

## 13. Test Requirements

Static/contract tests (WP2.3, per allowlist): event taxonomy closed enum;
field contract (required/nullable/lengths/enums); forbidden-content absence;
append-only guard (update rejected, delete rejected incl. admin); create
requires token; unique idempotency index; writer `findExisting` pre-check;
atomicity (audit failure rolls back transition; transition failure leaves no
event); from/to consistency validation; no `AIRequestLog` created by human
events; ACL (role read grant works, default deny, portal denied, admin
edit/delete denied); no navigation/list/search exposure; i18n parity; no
migration artifacts; retention (no cleanup job exists).

---

## 14. Risks

| Risk | Mitigation |
| --- | --- |
| Espo stream later proposed as "good enough" | ADR §5 records the 19-point failure analysis; changing the decision requires ADR amendment |
| JSON-history creep on the brief | Charter-forbidden; schema test asserts no history field |
| Admin edit/delete expectation | Guard is unconditional; adminMandatory edit/delete "no"; tests assert admin denial |
| Orphan events / partial transitions | Single-transaction model (§8) + contract tests |
| Retention pressure | Permanent-by-default; any purge requires independent retention ADR |
| Budget ratchet | Budget line amended exactly once (this ADR); further types need new ADR |
| Privacy erasure conflict | Deferred explicitly to retention ADR; no mechanism this phase |

---

## 15. Go / No-Go

| Decision | Status |
| --- | --- |
| Storage mechanism selected | **PASS** — Option C, single deterministic model (§5) |
| Artifact classification resolved | **PASS** — first-class governance ledger, not a business record (ADR §7) |
| Entity budget reconciled | **PASS** — one business artifact + one ledger, ADR-amended (§10) |
| Append-only contract complete | **PASS** — guard + token + idempotent writer + unique identity (ADR §9) |
| Atomicity model complete | **PASS** — single-transaction, rollback symmetric (§8) |
| Retention boundary complete | **PASS** — permanent default; deletion = NO until retention ADR (§9) |
| Conditional allowlist complete | **PASS** — approved-future / conditional / forbidden enumerated (§11) |

**Final: WP2.1A RATIFIED.**

This package is an Implementation Planning Reference Only. Code Implementation
Not Authorized.

---

## 16. Authorization Boundary

| Item | Status |
|------|--------|
| WP2.1A | RATIFIED |
| WP2.1B | NOT AUTHORIZED |
| WP2.2 Generation | NOT AUTHORIZED — predecessor and implementation gates remain |
| WP2.3 | NOT AUTHORIZED |
| Any Code | NOT AUTHORIZED |

WP2.1A is RATIFIED. This package is an Implementation Planning Reference Only.
Code Implementation Not Authorized. WP2.1B remains NOT AUTHORIZED. WP2.3
remains NOT AUTHORIZED. Generation implementation remains NOT AUTHORIZED.
Any code remains NOT AUTHORIZED.

---

## 17. References

1. `docs/adr/ADR-C25-007_COMMERCIAL_BRIEF_AUDIT_STORAGE.md`
2. `docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md`
3. `docs/PHASE3C25_WP2_IMPLEMENTATION_PLAN.md`
4. `docs/PHASE3C25_WP2_0_C20_DEPENDENCY_RESOLUTION.md` and `..._ADDENDUM.md`
5. `docs/audit/ADR-C25-002_AI_COMMERCIAL_BRIEF_GOVERNANCE.md`
6. `docs/audit/ADR-C25-005_CROSS_LAYER_READ_ONLY_ACCESS_CONTRACTS.md`
7. `docs/audit/ADR-C25-006_AI_CONFIDENCE_AUDIT_FEEDBACK_GOVERNANCE.md`
8. `docs/adr/C25_INVARIANT_REGISTRY.md`
9. `docs/PHASE3C24_WP2_IMPLEMENTATION_CHARTER.md`
10. `docs/adr/C24_INVARIANT_REGISTRY.md`
11. `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md`
12. `docs/adr/C20_INVARIANT_REGISTRY.md`
13. Live precedents: `crm-extension/files/custom/Espo/Modules/{Prospecting,AIPlatform}/` (append-only guards, ledger entityDefs/scopes, services, `app/acl.json` files); `crm-extension/scripts/AfterInstall.php`
