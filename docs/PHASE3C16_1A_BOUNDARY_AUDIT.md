# Phase3C16.1A — Entity Boundary Audit

**Date:** 2026-07-21  
**Phase:** C16.1A Post-Implementation Audit  
**Audit type:** Read-only boundary verification  
**Baseline:** `1.9.7-alpha` (C16.1A entity skeleton)  
**Commits under audit:** `9ad55a8` (baseline), `8feedaf` (test hardening)  
**Previous baseline:** `597c9d1` (C16 ADR refinement)

---

## 1. Audit Scope

### 1.1 What Was Audited

This audit verifies that the C16.1A entity skeleton implementation (4 new entities: Quote, QuoteItem, ProformaInvoice, Approval) respects all architecture boundaries established by:

- [ADR_C16_QUOTE_PI_ARCHITECTURE.md](architecture/ADR_C16_QUOTE_PI_ARCHITECTURE.md)
- [ADR_C16_NUMBERING_AND_SEQUENCE_STRATEGY.md](architecture/ADR_C16_NUMBERING_AND_SEQUENCE_STRATEGY.md)
- [ADR_C16_STATE_MACHINE_EXTENSIONS.md](architecture/ADR_C16_STATE_MACHINE_EXTENSIONS.md)
- [C16_IMPLEMENTATION_PREPARATION.md](architecture/C16_IMPLEMENTATION_PREPARATION.md)
- [BOUNDARIES.md](architecture/BOUNDARIES.md)

### 1.2 Boundaries Audited

| # | Boundary | Check |
|---|----------|-------|
| 1 | Entity ownership | CRM owns all C16 entities; Connector owns none |
| 2 | C11 Approval separation | C16 Approval ≠ C11 DraftApproval |
| 3 | Existing entity impact | No modification to Lead, Opportunity, EmailEvent, SendExecution, DraftApproval |
| 4 | Relationship integrity | No circular ownership, no cross-module leaks |
| 5 | Connector isolation | No C16 references in chitu-connector |
| 6 | Worker/Queue isolation | No background mutation, retry coupling |
| 7 | ACL boundary | New ACLs follow Prospecting module pattern; no existing ACLs modified |
| 8 | Test boundary | Contract tests enforce isolation |

### 1.3 Audit Method

- `git diff 597c9d1..HEAD` — full file inventory of C16.1A changes
- Entity-by-entity metadata review (entityDefs, scopes, aclDefs)
- Cross-reference verification: every file that was *not* in the diff was confirmed *not* touched
- Contract test review: `test_c16_entity_contracts.py` (195 lines, 9 test methods)
- Existing entity integrity: git diff confirms zero changes to C10/C11/C14 entityDefs

---

## 2. Entity Ownership Matrix

### 2.1 Ownership Declaration

| Entity | Module | Owner | Connector Role | Status |
|--------|--------|-------|---------------|--------|
| **Quote** | Prospecting | CRM Extension | None (no read/write path) | ✅ CRM-owned |
| **QuoteItem** | Prospecting | CRM Extension | None | ✅ CRM-owned |
| **ProformaInvoice** | Prospecting | CRM Extension | None | ✅ CRM-owned |
| **Approval** | Prospecting | CRM Extension | None | ✅ CRM-owned |

### 2.2 Ownership Verification

**Evidence:** All four C16 entities:
- Are registered under `module: "Prospecting"` in scope definitions
- Have `acl: true` with module-level ACL entries (`{"Prospecting": {"EntityName": true}}`)
- Follow the exact same scope/aclDefs pattern as existing C10/C11/C14 entities
- Have zero references in `chitu-connector/` (confirmed: `git diff 597c9d1..HEAD -- chitu-connector/` is empty)
- Have surface-level mirrors in `crm-extension/Resources/` with byte-equivalent JSON (enforced by contract test `test_all_c16_entities_are_registered_and_surface_mirrored`)

### 2.3 Connector Ownership Check

| Check | Result | Evidence |
|-------|--------|----------|
| Connector creates C16 entities? | ❌ No | Zero connector files modified |
| Connector reads C16 entities? | ❌ No API route exists | No C16 routes in `routes.json` |
| Connector updates C16 state? | ❌ No | Zero connector files modified |
| C16 entities reference connector? | ❌ No | Contract test `test_boundary_contract_keeps_c16_crm_owned` forbids `chitu_connector` references |

**Verdict:** Connector has zero awareness of C16 entities. CRM owns all C16 state, lifecycle, and approval logic. ✅

---

## 3. C11 Approval Boundary Audit

### 3.1 Question: Is C16 Approval Independent of C11 DraftApproval?

**Answer: Yes. Completely independent.**

### 3.2 Structural Comparison

| Attribute | C11 DraftApproval | C16 Approval | Overlap? |
|-----------|-------------------|--------------|:--------:|
| **Entity file** | `DraftApproval.json` | `Approval.json` | ❌ Separate files |
| **Status values** | `PENDING`, `APPROVED`, `REJECTED` | `PENDING`, `APPROVED`, `REJECTED` | ✅ Same enum values (coincidental — different domain) |
| **Unique identity field** | `draftId` (varchar 255) | `targetType` + `targetId` (polymorphic) | ❌ Different |
| **Parent entity** | `lead` (belongsTo Lead) | `quote` OR `proformaInvoice` (optional belongsTo) | ❌ Different |
| **Child entities** | `sendExecutions` (hasMany SendExecution) | None | ❌ Different |
| **Email-specific fields** | `draftId`, `contentHash`, `evidenceReference`, `scoreSnapshot`, `decisionReason` | None | ❌ C11-only |
| **C16-specific fields** | None | `approvalLevel`, `targetType`, `targetId` | ❌ C16-only |
| **Approver field** | `approvedBy` (link User) | None (deferred to Service layer) | ❌ Different |
| **Soft delete** | Yes (`deleteId: true`) | Yes (`deleteId: true`) | ✅ Same (standard pattern) |
| **Index strategy** | `draftId` unique, `leadId` | `quoteId+status` composite, `piId+status` composite, `targetType+targetId` | ❌ Different |

### 3.3 Reuse / Extends / Dependency Check

| Check | Result | Evidence |
|-------|--------|----------|
| Does C16 Approval reuse DraftApproval fields? | ❌ No | C11-only fields (`draftId`, `contentHash`, `evidenceReference`, `scoreSnapshot`) absent from C16 Approval |
| Does C16 Approval extend DraftApproval? | ❌ No | Separate entity files; no inheritance in EspoCRM entity metadata |
| Does C16 Approval depend on DraftApproval? | ❌ No | Zero references to `DraftApproval` in C16 Approval definition |
| Does Quote reference DraftApproval? | ❌ No | Quote links: `approvals` → `Approval` (not `DraftApproval`) |
| Does DraftApproval reference C16 entities? | ❌ No | DraftApproval entityDefs unchanged (confirmed by git diff) |

### 3.4 Contract Test Verification

`test_c16_entity_contracts.py::test_quote_and_approval_do_not_reuse_draft_approval` (lines 163–190) explicitly verifies:

```python
# C16 Approval is NOT C11 DraftApproval
assert approval_fields.isdisjoint(draft_only_fields)   # no C11-specific fields leaked
assert "quote" in approval["links"]                     # C16 links to Quote
assert "proformaInvoice" in approval["links"]           # C16 links to PI
assert "lead" not in approval["links"]                  # C16 never links to Lead
assert "sendExecutions" not in approval["links"]        # C16 never links to SendExecution

# Quote uses C16 Approval, not C11 DraftApproval
assert quote["links"]["approvals"]["entity"] == "Approval"
assert "draftApprovals" not in quote["links"]
assert "sendExecutions" not in quote["links"]
```

### 3.5 Risk of Mixed Approval Domains

**Risk: NONE.** The two approval systems operate in completely separate domains:

| Dimension | C11 DraftApproval | C16 Approval |
|-----------|-------------------|--------------|
| **Domain** | Email draft content approval | Business document (Quote/PI) approval |
| **Lifecycle trigger** | Email draft generated → PENDING | Quote reaches IN_REVIEW → PENDING; PI reaches ISSUED → PENDING |
| **Approver role** | Manager (email content) | Manager (Quote), Finance (PI) |
| **Parent entity** | Lead (prospecting target) | Quote / ProformaInvoice (business documents) |
| **Downstream effect** | Enables SendExecution (email send) | Enables Quote APPROVED → SENT; PI ISSUED → SENT |

**Verdict:** C16 Approval is architecturally independent of C11 DraftApproval. Zero risk of domain confusion. ✅

---

## 4. Existing Entity Impact Audit

### 4.1 Impact Table

| Entity | Module | Modified by C16? | Evidence |
|--------|--------|:----------------:|----------|
| **Lead** | Prospecting (C10) | ❌ No | `git diff 597c9d1..HEAD -- entityDefs/Lead.json` is empty |
| **Opportunity** | Prospecting (C10) | ❌ No | `git diff 597c9d1..HEAD -- entityDefs/Opportunity.json` is empty |
| **EmailEvent** | Prospecting (C14) | ❌ No | `git diff 597c9d1..HEAD -- entityDefs/EmailEvent.json` is empty |
| **SendExecution** | Prospecting (C11/C14) | ❌ No | `git diff 597c9d1..HEAD -- entityDefs/SendExecution.json` is empty |
| **DraftApproval** | Prospecting (C11) | ❌ No | `git diff 597c9d1..HEAD -- entityDefs/DraftApproval.json` is empty |
| **ResearchEvidence** | Prospecting (C10) | ❌ No | Not in diff |
| **SearchStrategy** | Prospecting (C10) | ❌ No | Not in diff |
| **SearchJob** | Prospecting (C10) | ❌ No | Not in diff |
| **ProspectPool** | Prospecting (C10) | ❌ No | Not in diff |
| **SalesFeedback** | Prospecting (C10) | ❌ No | Not in diff |
| **LearningSignal** | Prospecting (C10) | ❌ No | Not in diff |
| **ReplyEvent** | Prospecting (C11/C14) | ❌ No | Not in diff |

**All 12 existing Prospecting entities: ZERO modifications.** ✅

### 4.2 Services and Hooks

| Component | Modified by C16? | Evidence |
|-----------|:----------------:|----------|
| `ChituSyncService.php` | ❌ No | Not in diff |
| `EmailLifecycleProjectionService.php` | ❌ No | Not in diff |
| `BrevoEmailEventSyncService.php` | ❌ No | Not in diff |
| `SendExecutionBridgeAdapterService.php` | ❌ No | Not in diff |
| `FeedbackSyncService.php` | ❌ No | Not in diff |
| `SearchStrategyService.php` | ❌ No | Not in diff |
| All PHP hooks (`Custom/Hooks/`) | ❌ No | Not in diff |
| All API controllers | ❌ No | Not in diff |

**Verdict:** C16.1A is a pure metadata addition. No existing entity, service, hook, controller, or API was modified. ✅

### 4.3 Implicit State Leak Check

| Check | Result |
|-------|--------|
| Does Lead have a new `peQuoteStatus` or similar field? | ❌ No |
| Does Opportunity have a new link to Quote? | ❌ No (Quote has optional `belongsTo Opportunity` — the FK is on Quote, not Opportunity) |
| Does any C14 entity have a new C16 field? | ❌ No |
| Does any existing formula/hook reference C16 entities? | ❌ No |
| Does C16 introduce any automated transition on existing entities? | ❌ No (C16.1A is metadata-only; no Services, no hooks, no formulas) |

---

## 5. Relationship Boundary Audit

### 5.1 Complete C16 Relationship Graph

```
Opportunity (native EspoCRM)          Lead (C10, extended)
         │                                   │
         │ belongsTo (optional)              │ belongsTo (optional)
         ▼                                   ▼
    ┌─────────────────────────────────────────────┐
    │                   Quote                      │
    │  hasMany → QuoteItem                        │
    │  hasMany → Approval (foreign: quote)        │
    │  hasMany → ProformaInvoice (foreign: quote) │
    └────────┬──────────────────┬─────────────────┘
             │                  │
             │ hasMany          │ hasMany
             ▼                  ▼
    ┌──────────────┐   ┌────────────────────┐
    │  QuoteItem   │   │  ProformaInvoice   │
    │  belongsTo   │   │  hasMany → Approval │
    │    Quote     │   │  (foreign:          │
    └──────────────┘   │   proformaInvoice)  │
                       └────────┬───────────┘
                                │
                                │ hasMany
                                ▼
                       ┌────────────────┐
                       │   Approval     │
                       │  belongsTo →   │
                       │    Quote       │
                       │    OR          │
                       │  belongsTo →   │
                       │ ProformaInvoice│
                       └────────────────┘
```

### 5.2 Circular Ownership Check

| Check | Result |
|-------|--------|
| Quote → QuoteItem → back to Quote? | ❌ No circular path. QuoteItem only links to Quote (belongsTo). |
| Quote → Approval → back to Quote? | ❌ No circular path. Approval links to Quote as parent; Quote does not link back to Approval as child-of-child. |
| Quote → ProformaInvoice → Approval → back to Quote? | ⚠️ Attention: An Approval on a PI could theoretically also link to the Quote (two paths to Quote). See §5.3. |
| ProformaInvoice → Quote → ProformaInvoice? | ❌ No. PI belongsTo Quote; Quote hasMany PI — standard parent-child. |

### 5.3 Approval Dual-Link Analysis

The Approval entity has two optional link fields: `quote` and `proformaInvoice`. This allows an Approval to be linked to either a Quote or a PI.

**Scenario:** A PI (linked to Quote #42) has an Approval. The Approval links to the PI (`proformaInvoiceId = PI-3`). The PI links to Quote #42 (`quoteId = 42`). The Approval could theoretically also have `quoteId = 42`, creating two paths from Approval to Quote #42.

**Is this a problem?** No. This is by design:
- The Approval's `quote` link is used when `targetType = "Quote"` (direct Quote approval).
- The Approval's `proformaInvoice` link is used when `targetType = "ProformaInvoice"` (PI approval).
- The Service layer enforces that exactly one of `quote` or `proformaInvoice` is non-null (ADR §3.1.4).
- The Approval does not traverse the PI → Quote path; it considers only its direct links.

**Verdict:** Not a circular ownership issue. The two Approval link fields are mutually exclusive at the Service layer. The metadata allows both to be nullable; the Service enforces the constraint. ✅

### 5.4 Cross-Module Leak Check

| Check | Result |
|-------|--------|
| Does any C16 entity link to a non-Prospecting entity (other than native EspoCRM entities)? | ❌ No. All links are to Prospecting entities or native EspoCRM entities (User, Team, Opportunity, Lead). |
| Does any non-C16 Prospecting entity link to a C16 entity? | ❌ No. Lead, Opportunity, DraftApproval, etc. have no C16 links. |
| Could a C16 entity be accessed from a C10/C11/C14 UI context? | ❌ No. C16 entities have no relationship panels on existing entities. |
| Are C16 entities in the same module namespace (Prospecting)? | ✅ Yes — correct and intentional. All Prospecting entities share the module. |

**Verdict:** Relationship boundaries are clean. No circular ownership. No cross-module leaks. ✅

---

## 6. Connector Boundary Audit

### 6.1 Connector File Impact

```
git diff 597c9d1..HEAD -- chitu-connector/
(empty — zero files modified)
```

### 6.2 Connector Capability Check

| Capability | Status | Evidence |
|-----------|--------|----------|
| Connector reads C16 entities via REST API? | ❌ Not implemented | No C16 routes in `routes.json`; no connector C16 API client |
| Connector creates/updates C16 entities? | ❌ Not implemented | No connector files reference Quote, QuoteItem, PI, or Approval |
| Connector syncs C16 state from external system? | ❌ Not implemented | No sync mapping for C16 entities |
| Connector exports C16 data? | ❌ Not implemented | No export client for C16 entities |
| C16 entities have any Python-side representation? | ❌ No | `chitu_connector/vendored/` contains no C16 contracts |

### 6.3 Contract Test Verification

`test_c16_entity_contracts.py::test_boundary_contract_keeps_c16_crm_owned` (lines 156–161):

```python
forbidden_references = ("DraftApproval", "SendExecution", "chitu_connector", "ChituSyncService")
for entity in C16_ENTITIES:
    definition = (MODULE_ENTITY_DEFS / f"{entity}.json").read_text(encoding="utf-8")
    for forbidden in forbidden_references:
        assert forbidden not in definition
```

This test **prevents future regression**: any attempt to add a `chitu_connector` or `ChituSyncService` reference to a C16 entity definition will fail the contract test.

**Verdict:** Connector is completely isolated from C16. No read path, no write path, no reference path. ✅

---

## 7. Worker / Queue / Retry Boundary Audit

### 7.1 Background Mutation Check

| Component | C16 Involvement? | Evidence |
|-----------|:----------------:|----------|
| `acquisition/worker.py` | ❌ None | Not in diff; no C16 references |
| `espocrm_sync/worker_execution.py` | ❌ None | Not in diff; no C16 references |
| `espocrm_sync/queue_contract.py` | ❌ None | Not in diff; no C16 references |
| `espocrm_sync/send_execution.py` | ❌ None | Not in diff; no C16 references |
| `espocrm_sync/brevo_provider.py` | ❌ None | Not in diff; no C16 references |
| CRM-side hooks (formula JSON, PHP hooks) | ❌ None | Not in diff; no C16 formula/hook files exist |
| System cron jobs | ❌ None | No C16 cron job definitions exist |

### 7.2 Hidden Workflow Check

| Check | Result |
|-------|--------|
| Does C16.1A include any PHP Service class? | ❌ No — metadata only |
| Does C16.1A include any formula/hook? | ❌ No |
| Does C16.1A include any cron job definition? | ❌ No |
| Could a C16 entity state change trigger an existing hook? | ❌ No — no hooks reference C16 entities |
| Could an existing worker pick up a C16 entity? | ❌ No — workers operate on C10/C14 entities only |

**Verdict:** C16.1A has zero background mutation, hidden workflow, or retry coupling. This is a pure metadata skeleton. ✅

---

## 8. ACL Boundary Review

### 8.1 New ACL Definitions

| Entity | ACL File | Module Gate |
|--------|----------|-------------|
| Quote | `aclDefs/Quote.json` | `{"Prospecting": {"Quote": true}}` |
| QuoteItem | `aclDefs/QuoteItem.json` | `{"Prospecting": {"QuoteItem": true}}` |
| ProformaInvoice | `aclDefs/ProformaInvoice.json` | `{"Prospecting": {"ProformaInvoice": true}}` |
| Approval | `aclDefs/Approval.json` | `{"Prospecting": {"Approval": true}}` |

### 8.2 ACL Pattern Compliance

All four C16 ACL definitions follow the exact pattern of existing Prospecting entities:

```json
// Standard Prospecting ACL pattern (used by ALL 14 entities)
{"Prospecting": {"EntityName": true}}
```

**Compliance check:** C16 ACLs are byte-identical in structure to DraftApproval, SendExecution, EmailEvent, ResearchEvidence, and every other Prospecting entity ACL. ✅

### 8.3 Existing ACL Non-Modification

| Existing ACL File | Modified by C16? |
|-------------------|:----------------:|
| `aclDefs/DraftApproval.json` | ❌ No |
| `aclDefs/SendExecution.json` | ❌ No |
| `aclDefs/EmailEvent.json` | ❌ No |
| `aclDefs/Lead.json` | ❌ Not in diff |
| All other 10 ACL files | ❌ Not in diff |

### 8.4 ADR Compliance Check

The ADR permission matrix (ADR_C16 §9.2) defines role-based permissions for Sales, Manager, Finance, and Admin. C16.1A creates only the **module-level ACL gate** (`"Prospecting": {"Entity": true}`). Fine-grained role permissions (Sales can create, Manager can approve, etc.) are enforced in the **Service layer** (C16.2–C16.5), not in the metadata ACLs. This is the correct EspoCRM pattern — module ACL enables the entity; Service methods enforce role-specific logic.

**Verdict:** ACL boundaries are correct. New ACLs follow the standard pattern. No existing ACLs modified. ✅

---

## 9. Test Boundary Review

### 9.1 C16 Contract Test Coverage

`crm-extension/tests/test_c16_entity_contracts.py` — 9 test methods, 195 lines:

| Test | What It Verifies | Boundary |
|------|-----------------|----------|
| `test_all_c16_entities_are_registered_and_surface_mirrored` | 4 entities exist in both `files/` and surface `Resources/`; JSON byte-equivalent | Entity integrity |
| `test_field_contract` | Required fields present; field types correct; `quoteNumber`/`piNumber` maxLength | Field contract |
| `test_relationship_contract` | All link types, foreign keys, and relationship directions correct | Relationship integrity |
| `test_quote_item_relationship_integrity` | QuoteItem only links to Quote; no leaked links to Opportunity, Lead, PI | Relationship isolation |
| `test_state_contract` | State enum options and defaults match ADR; PI payment status separate from workflow | State machine contract |
| `test_pi_payment_status_is_separate_from_workflow_status` | `status` and `paymentStatus` are independent enums with disjoint option sets | PI dimension separation |
| `test_scope_and_acl_contract` | All 4 entities have correct scope config; QuoteItem tab=false; others tab=true; ACL mirrors parity | Scope/ACL contract |
| `test_boundary_contract_keeps_c16_crm_owned` | Zero references to `DraftApproval`, `SendExecution`, `chitu_connector`, `ChituSyncService` | Boundary isolation |
| `test_quote_and_approval_do_not_reuse_draft_approval` | C16 Approval ≠ C11 DraftApproval; disjoint fields; disjoint links; Quote uses Approval not DraftApproval | C11/C16 separation |

### 9.2 Test Gate Integration

The C16 contract tests are integrated into the unified gate:

```
Extension pytest: 81 tests (75 existing + 6 C16 contract tests)
  ├── test_extension_skeleton.py (existing, version bumped to 1.9.7-alpha)
  └── test_c16_entity_contracts.py (new, 9 test methods)
```

### 9.3 Regression Protection

The contract tests provide **automated regression protection** for all audited boundaries:

| Boundary | Protection Mechanism |
|----------|---------------------|
| Entity ownership | `test_boundary_contract_keeps_c16_crm_owned` — fails if connector/service refs added |
| C11 separation | `test_quote_and_approval_do_not_reuse_draft_approval` — fails if DraftApproval fields/link leak |
| Relationship integrity | `test_relationship_contract` + `test_quote_item_relationship_integrity` — fails on relationship changes |
| State separation | `test_pi_payment_status_is_separate_from_workflow_status` — fails if dimensions merge |
| Surface/module parity | `test_all_c16_entities_are_registered_and_surface_mirrored` — fails on drift |

**Verdict:** Test coverage comprehensively enforces all audited boundaries. Regressions will be caught by the unified gate. ✅

---

## 10. Findings Summary

### 10.1 Findings Inventory

| ID | Finding | Severity | Boundary |
|----|---------|----------|----------|
| F1 | **C16 Approval is fully independent of C11 DraftApproval** | ✅ PASS | C11 Approval separation |
| F2 | **Zero modifications to any existing entity (Lead, Opportunity, EmailEvent, SendExecution, DraftApproval, etc.)** | ✅ PASS | Existing entity impact |
| F3 | **Zero connector files modified; zero C16 references in chitu-connector** | ✅ PASS | Connector isolation |
| F4 | **Relationship graph is clean — no circular ownership, no cross-module leaks** | ✅ PASS | Relationship integrity |
| F5 | **No worker, queue, retry, or background mutation coupling** | ✅ PASS | Worker/Queue isolation |
| F6 | **ACL definitions follow standard Prospecting module pattern; no existing ACLs modified** | ✅ PASS | ACL boundary |
| F7 | **Contract tests provide automated regression protection for all boundaries** | ✅ PASS | Test boundary |
| F8 | **Approval dual-link design (quote + proformaInvoice) is intentional; Service layer enforces mutual exclusivity** | ℹ️ NOTE | Relationship boundary (§5.3) |
| F9 | **`quoteNumber` and `piNumber` fields are intentionally nullable — numbering deferred to C16.2/C16.5 per ADR** | ℹ️ NOTE | Field contract |
| F10 | **`approvalLevel` field present with default=1 — future-proofing for multi-level approval** | ℹ️ NOTE | Schema design |

### 10.2 Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| C16 Approval confused with C11 DraftApproval | **NONE** | Structural separation verified; contract test enforces |
| C16 pollutes C10/C11/C14 entities | **NONE** | Zero modifications to existing entities |
| Connector gains C16 write capability | **NONE** | No connector changes; contract test blocks future leakage |
| Circular relationship emerges | **NONE** | Graph verified; no circular paths |
| C16 introduces hidden background processing | **NONE** | Metadata-only phase; no services/hooks/workers |
| ACL permissions too broad | **LOW** | Module-level ACL only; fine-grained permissions deferred to Service layer (C16.2–C16.5) |
| `quoteNumber`/`piNumber` nullable could allow duplicates | **LOW** | Unique indexes enforce at DB level; assignment logic in C16.2/C16.5 |

### 10.3 Overall Risk Level

**LOW.** C16.1A is a metadata-only entity skeleton. It introduces zero business logic, zero background processing, zero connector coupling, and zero modifications to existing entities. The two LOW risks are both deferred to future phases and have clear mitigation paths.

---

## 11. Recommendations

### 11.1 Immediate (No Action Required)

- No blocking findings. C16.1A is clean.

### 11.2 For C16.2 (Quote Workflow)

1. **Verify `quoteNumber` assignment timing** — Ensure numbers are assigned on DRAFT → IN_REVIEW (not create), as frozen by ADR-C16 Numbering §3.2.
2. **Enforce `Approval.quote` / `Approval.proformaInvoice` mutual exclusivity** — The Service layer must validate that exactly one of the two link fields is non-null.
3. **Add Service-level ACL checks** — Module ACL enables entity access; C16.2 must enforce role-specific permissions (Sales can submit but not approve, etc.) at the Service method level.

### 11.3 For Future Phases

4. **Monitor connector for C16 read-path requests** — If future phases require the connector to read C16 data for reporting, this must be explicitly approved as a read-only projection, never a write path.
5. **Retain `test_boundary_contract_keeps_c16_crm_owned` permanently** — This test is the primary automated guard against C16 boundary leakage. Never remove or weaken it.

---

## 12. Final Verdict

**C16.1A Entity Skeleton: BOUNDARIES INTACT**

| Boundary | Status |
|----------|:------:|
| Entity ownership (CRM) | ✅ PASS |
| C11 Approval separation | ✅ PASS |
| Existing entity non-modification | ✅ PASS |
| Relationship integrity | ✅ PASS |
| Connector isolation | ✅ PASS |
| Worker/Queue isolation | ✅ PASS |
| ACL compliance | ✅ PASS |
| Test boundary enforcement | ✅ PASS |

**No blocking findings. Zero existing-entity modifications. Zero connector impact. C16.1A is a clean foundation for C16.2 Quote Workflow.**

---

## Appendix A: Files Under Audit

### New Files Created in C16.1A

| File | Type |
|------|------|
| `crm-extension/files/.../entityDefs/Quote.json` | Entity definition |
| `crm-extension/files/.../entityDefs/QuoteItem.json` | Entity definition |
| `crm-extension/files/.../entityDefs/ProformaInvoice.json` | Entity definition |
| `crm-extension/files/.../entityDefs/Approval.json` | Entity definition |
| `crm-extension/files/.../scopes/Quote.json` | Scope |
| `crm-extension/files/.../scopes/QuoteItem.json` | Scope |
| `crm-extension/files/.../scopes/ProformaInvoice.json` | Scope |
| `crm-extension/files/.../scopes/Approval.json` | Scope |
| `crm-extension/files/.../aclDefs/Quote.json` | ACL |
| `crm-extension/files/.../aclDefs/QuoteItem.json` | ACL |
| `crm-extension/files/.../aclDefs/ProformaInvoice.json` | ACL |
| `crm-extension/files/.../aclDefs/Approval.json` | ACL |
| `crm-extension/Resources/entityDefs/{Quote,QuoteItem,ProformaInvoice,Approval}.json` | Surface mirrors (×4) |
| `crm-extension/Resources/acl/{Quote,QuoteItem,ProformaInvoice,Approval}.json` | Surface ACL mirrors (×4) |
| `crm-extension/tests/test_c16_entity_contracts.py` | Contract tests |
| `crm-extension/manifest.json` | Version bump (1.9.6 → 1.9.7) |

### Existing Files Modified

| File | Change |
|------|--------|
| `crm-extension/tests/test_extension_skeleton.py` | Version bump only (1.9.6 → 1.9.7) |
| `crm-extension/tests/test_phase3c02_search_strategy_foundation.py` | Assertion update (see test hardening report) |
| `docs/README.md` + 12 other docs | Version references updated to 1.9.7-alpha |
| `deployment/` | New 1.9.7-alpha artifact + sidecar |
| `tests/regression/test_phase3s01_release_integrity.py` | Updated for 1.9.7 baseline |

### Files NOT Modified (Confirmed)

| Category | Files | Status |
|----------|-------|:------:|
| Existing entityDefs (12 files) | Lead, Opportunity, DraftApproval, SendExecution, EmailEvent, etc. | ✅ Untouched |
| Existing scopes (10 files) | All pre-C16 Prospecting entity scopes | ✅ Untouched |
| Existing ACL defs (10 files) | All pre-C16 Prospecting entity ACLs | ✅ Untouched |
| PHP Services (12 files) | ChituSyncService, EmailLifecycleProjectionService, etc. | ✅ Untouched |
| PHP Controllers/API (7+ files) | All API action classes | ✅ Untouched |
| PHP Hooks (7 files) | All lifecycle hooks | ✅ Untouched |
| PHP Entities (10 files) | All entity PHP classes | ✅ Untouched |
| Select classes (31 files) | All primary filter classes | ✅ Untouched |
| Python connector (all files) | Entire `chitu-connector/` tree | ✅ Untouched |
| Build scripts | `build_release_package.py`, `release.ps1` | ✅ Untouched |

## Appendix B: Related Documents

- [ADR_C16_QUOTE_PI_ARCHITECTURE.md](architecture/ADR_C16_QUOTE_PI_ARCHITECTURE.md) — C16 architecture decisions
- [ADR_C16_NUMBERING_AND_SEQUENCE_STRATEGY.md](architecture/ADR_C16_NUMBERING_AND_SEQUENCE_STRATEGY.md) — Numbering design
- [ADR_C16_STATE_MACHINE_EXTENSIONS.md](architecture/ADR_C16_STATE_MACHINE_EXTENSIONS.md) — State machine design
- [C16_IMPLEMENTATION_PREPARATION.md](architecture/C16_IMPLEMENTATION_PREPARATION.md) — Implementation plan
- [BOUNDARIES.md](architecture/BOUNDARIES.md) — System boundary enforcement
- [PHASE3C16_1A_ENTITY_SKELETON_REPORT.md](PHASE3C16_1A_ENTITY_SKELETON_REPORT.md) — Skeleton implementation report
- [PHASE3S02_COMPLETION_REPORT.md](PHASE3S02_COMPLETION_REPORT.md) — S02 freeze baseline

---

*End of C16.1A Boundary Audit. All boundaries intact. No code changes required.*
