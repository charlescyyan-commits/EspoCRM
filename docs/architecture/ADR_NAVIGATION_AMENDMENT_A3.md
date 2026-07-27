# ADR Navigation Amendment A3 — Commercial & Intelligence Center Top-Level Separation

**Status:** Accepted

**Date:** 2026-07-27

**Accepted:** 2026-07-27 (docs-only governance review)

**Amends:** `docs/architecture/ADR_C17_NAVIGATION_OPERATIONAL_CENTERS.md`

**Relationship:** Evolution within the authority of ADR-C17. Does not overturn, deprecate, or redesign ADR-C17. Does not modify ADR-C16.

**Decision Owners:**
- Principal Software Architect, EspoCRM Prospecting module.
- Phase3C17 Release Approval Board.
- Phase3C19 Governance Review (docs-only acceptance).

---

## 1. Amendment Motivation

### 1.1 Phase Ownership Ambiguity

ADR-C17 placed five Centers under the single `潜客开发` (Prospecting) divider:

```
潜客开发
├ 潜客运营         (Dashboard)
├ 搜索中心         (Search Center)
├ 触达中心         (Outreach Center)
└ 报价中心         (Quote Center)
```

The frozen ADR-C17 entity classification correctly identifies Quote as **Class A — Primary Center Entry**, owning the commercial workflow: quote drafting → commercial approval → proforma invoice execution. However, Quote is not a "prospecting" (潜客开发 / market development) activity. It is a **commercial execution** activity. Keeping it under the Prospecting divider creates phase ownership ambiguity — the divider label implies a pre-sales discovery scope, but commercial documents belong to a later business phase.

### 1.2 Intelligence Center Entry Gap

The current navigation artifact encodes the Research Center as:

```json
"research": {
  "entry": "Lead",
  "label": "情报中心",
  "placement": "global-native-preserved"
}
```

The Research/Intelligence Center label is acknowledged in the ADR but its physical entry is the global-native `Lead` tab under `客户管理`. There is no explicit Intelligence Center entry under `潜客开发`. This is correct for physical implementation — Lead is a Class E global native scope — but the conceptual IA is incomplete without an Intelligence Center reference under the Prospecting divider.

Phase3C19 delivered the **Intelligence Center Research Workbench** — a composite dashlet aggregating ProspectPool research queues, Lead research gaps, and ResearchEvidence panels. The Intelligence Center is now a substantiated operational surface, not merely a label on the Lead tab.

### 1.3 Support Divider Gap

`KnowledgeBaseArticle` currently sits under `更多` (More). As the product matures, post-sales support resources warrant their own conceptual grouping — the `支持` (Support) divider — even though no Case or Support workflow entities are introduced.

### 1.4 Calendar Re-homing

`Calendar` currently sits under `更多` (More) alongside `Task`. This grouping is acceptable for C17 and is preserved unchanged.

---

## 2. Relationship with Frozen Navigation ADR

| ADR-C17 Decision | A3 Treatment | Status |
|---|---|---|
| Entity visibility classification (A–F) | Preserve | **UNCHANGED** — no entity changes class |
| Quote is Class A, Quote Center entry | Preserve | **UNCHANGED** — Quote remains Class A; only its divider parent changes |
| Lead is Class E, global native | Preserve | **UNCHANGED** |
| ResearchEvidence is Class D, supporting object | Preserve | **UNCHANGED** |
| Governance chain (ADR → artifact → materializer → runtime) | Preserve | **UNCHANGED** |
| Five Centers: Dashboard, Search, Research, Outreach, Quote | Preserve | **UNCHANGED** — Center count unchanged |
| `config.tabList` writer governance | Preserve | **UNCHANGED** |
| Top-level divider membership for Quote | Change | **MODIFIED** — Quote moves from 潜客开发 to new 商务 divider |
| Top-level divider membership for KnowledgeBaseArticle | Change | **MODIFIED** — KnowledgeBaseArticle moves from 更多 to new 支持 divider |
| Research Center physical entry (Lead global-native) | Preserve | **UNCHANGED** — Lead stays under 客户管理; 情报中心 reference added under 潜客开发 |

**This is an evolution, not a redesign.** No entity changes ownership, workflow, ACL, or lifecycle. The change is purely structural: two new dividers (`商务`, `支持`), one entry moves (`Quote`), one entry moves (`KnowledgeBaseArticle`), and one Center reference is explicitly listed (`情报中心`).

---

## 3. Why This Is Evolution Instead of Redesign

| Dimension | Redesign | A3 Evolution |
|---|---|---|
| Entity classification | Would reassign A–F classes | Zero class changes |
| Workflow ownership | Would move lifecycle ownership | Zero ownership changes |
| ACL / permissions | Would change role visibility | Zero ACL changes |
| New entities | Would introduce new scopes | Zero new entities |
| Navigation mechanism | Would change the materializer or governance chain | Same governance chain |
| Divider structure | — | Two new dividers; two entries move |
| Center definitions | Would add/remove Centers | Same five Centers; one entry label made explicit |

The ADR-C17 governance chain (ADR → `phase3c17_navigation.json` → materializer → `config.tabList` → drift validation) is preserved. The desired-state artifact schema version and marker evolve; the governance mechanism does not.

---

## 4. Target Information Architecture

### 4.1 Phase-to-Navigation Ownership Model

| Business Phase | Nav Divider | Owned Entries | Business Meaning |
|---|---|---|---|
| **Market Development** | `潜客开发` | Dashboard, Search Center, Intelligence Center, Outreach Center | Discovery, research, and first-contact outreach |
| **Customer Management** | `客户管理` | Account, Contact, Lead, Opportunity | CRM record ownership (unchanged) |
| **Commercial** | `商务` | Quote Center (Quote, Approval, ProformaInvoice) | Quote drafting, commercial approval, financial execution |
| **Support** | `支持` | KnowledgeBaseArticle | Post-sales resources (no Case in C17) |
| **Activities** | `活动` | Email | Communication timeline (unchanged) |
| **More** | `更多` | Task, Calendar | Productivity tools (Calendar stays) |

### 4.2 Target IA (Physical)

```text
首页

潜客开发
├ 潜客运营              (ProspectingDashboard)
├ 搜索中心              (ProspectingSearch)
├ 情报中心              (Intelligence Center — references Lead + ResearchEvidence + Workbench)
└ 触达中心              (DraftApproval)

客户管理
├ 客户                  (Account)
├ 联系人                (Contact)
├ 潜在客户              (Lead)          ← Class E global native; research record ownership
└ 商机                  (Opportunity)

商务
└ 报价中心              (Quote)         ← Class A; moved from 潜客开发

支持
└ 知识库                (KnowledgeBaseArticle)  ← moved from 更多

活动
└ 邮件                  (Email)

更多
├ 任务                  (Task)
└ 日历                  (Calendar)
```

### 4.3 Intelligence Center Entry Governance

The `情报中心` entry under `潜客开发` is a **composition reference**, not a new entity. It does not introduce:

- a new `tab:true` scope
- a new custom page
- a new entity or persistence layer
- a new ACL scope
- a new workflow owner

The Intelligence Center is physically composed from:

```text
情报中心 composition:
  ├ Lead native list         (Class E — the CRM research record source)
  ├ ResearchEvidence list    (Class D — supporting evidence)
  ├ Intelligence Research Workbench dashlet  (Phase3C19 — composite dashboard)
  └ SalesFeedback / LearningSignal / EmailEvent  (Class D/F — supporting panels)
```

**Frozen rule:** Lead remains the sole CRM research entry ownership. The `情报中心` label under the Prospecting divider navigates to the same Lead list that appears under `客户管理`. No duplicate Lead tab is introduced. No new top-level intelligence tab is introduced.

The Intelligence Center Research Workbench (Phase3C19) remains a **composition layer** — a dashlet aggregating cross-entity research visibility. It is not a navigation entry. It is not a scope. It is not a data owner.

---

## 5. Migration Scope

### 5.1 What Changes

| Artifact | Change | Impact |
|---|---|---|
| `deployment/navigation/phase3c17_navigation.json` | New `商务` divider; new `支持` divider; `Quote` moved; `KnowledgeBaseArticle` moved; `情报中心` entry added under `潜客开发`; `centers.research` updated | Desired-state definition only |
| Navigation materializer | Supports new divider IDs | Already supports arbitrary divider entries |
| `i18n/*/Global.json` | New divider labels: `商务` (Commercial), `支持` (Support) | Two new label keys |
| Navigation contract tests | Updated to reflect new divider membership | Test assertions only |

### 5.2 What Does NOT Change

| Area | Status |
|---|---|
| Entity definitions (entityDefs, scopes, aclDefs, clientDefs) | **Untouched** |
| Services, workflow owners, lifecycle guards | **Untouched** |
| ACL model, role matrices, permission sets | **Untouched** |
| Dashboard composition, dashlet inventory | **Untouched** |
| Lead lifecycle, status fields, formula hooks | **Untouched** |
| ProspectPool status ownership | **Untouched** |
| Quote, Approval, SendExecution, ReplyEvent code | **Untouched** |
| Intelligence Center Research Workbench code | **Untouched** |
| `crm-extension/files/` module code | **Untouched** |
| Provisioning scripts (non-navigation) | **Untouched** |

---

## 6. Non-Goals (Frozen)

The following are explicitly **NOT** in scope for Amendment A3:

- No new business entities (no Case, no Ticket, no SupportTicket)
- No Case implementation
- No Support workflow
- No PI implementation or redesign
- No payment workflow
- No ACL changes
- No scope ownership changes
- No dashboard redesign
- No Lead lifecycle changes
- No ProspectPool status ownership changes
- No new custom Center composition pages
- No new Center entry surfaces beyond the existing five
- No `tab:false` retroactive flips on existing operational entities
- No navigation governance chain changes
- No materializer rewrite

---

## 7. Rollback Considerations

### 7.1 Primary Rollback

Restore the captured pre-migration `config.tabList` snapshot per ADR-C17 rollback governance (§Runtime Effective Navigation):

1. Capture effective runtime `config.tabList` before applying A3.
2. Store with timestamp, environment identifier, source commit, and checksum.
3. Apply the A3 desired state.
4. On rollback, restore the captured pre-migration state.
5. Validate: `config.tabList` matches captured state; ACL filtering functional; all Centers reachable; Quote still navigable.

### 7.2 Fallback

Re-run the pre-A3 materializer against the pre-A3 desired-state artifact (`phase3c17-wp1-4-product-polish-v1`). This is baseline reconstruction, not the primary mechanism.

### 7.3 Impact if Not Applied

If A3 is rejected:

- Quote Center remains under `潜客开发` — phase ownership ambiguity persists but no functional regression.
- `KnowledgeBaseArticle` remains under `更多` — acceptable; this is cosmetic.
- Intelligence Center remains referenced only through the Lead global-native tab — Phase3C19 workbench is still reachable via dashlet picker.

**Zero runtime regression if A3 is deferred.** The amendment is structural clarity, not functional necessity.

---

## 8. Acceptance Criteria

### 8.1 Structural

- [ ] `商务` divider exists in the desired-state artifact with `Quote` as its sole top-level entry.
- [ ] `支持` divider exists in the desired-state artifact with `KnowledgeBaseArticle` as its sole top-level entry.
- [ ] `Quote` is not present under the `潜客开发` divider.
- [ ] `KnowledgeBaseArticle` is not present under the `更多` divider.
- [ ] `情报中心` entry is listed under `潜客开发` in the desired-state artifact.
- [ ] `Lead` remains under `客户管理` as a global native tab (not duplicated).
- [ ] Divider order preserved: 潜客开发 → 客户管理 → 商务 → 支持 → 活动 → 更多.

### 8.2 Governance

- [ ] Desired-state artifact marker is updated (e.g., `phase3c19-a3-commercial-separation-v1`).
- [ ] Materializer reads the updated artifact without modification.
- [ ] Navigation contract tests pass against the updated artifact.
- [ ] No `config.tabList` writer other than the canonical materializer is introduced.

### 8.3 Constraints

- [ ] No entity definition files modified.
- [ ] No service files modified.
- [ ] No ACL files modified.
- [ ] No scope metadata (`tab:true`/`tab:false`) modified.
- [ ] No Lead lifecycle or status fields modified.
- [ ] No ProspectPool status ownership modified.
- [ ] Intelligence Center Research Workbench dashlet unchanged.
- [ ] All 356 existing tests continue to pass (2 pre-existing C19 failures accepted).

### 8.4 Rollback

- [ ] Pre-migration `config.tabList` captured before applying A3.
- [ ] Rollback restoration procedure documented and tested.
- [ ] Post-rollback validation confirms all Centers reachable.

---

## 9. Relationship to Phase3C19

Phase3C19 delivered the Intelligence Center Research Workbench (commit `17d45c5`). That implementation:

- Added schema links: ResearchEvidence ↔ ProspectPool ↔ Lead.
- Added parent-link validation and idempotent promotion inheritance.
- Delivered the IntelligenceResearchWorkbench composite dashlet.
- Did **not** create new entities, navigation tabs, or ACL changes.

Amendment A3 is the **governance acknowledgment** of the Intelligence Center as a named operational surface within the product IA. The code delivered in Phase3C19 does not change as a result of A3. A3 only updates the navigation desired-state artifact to reflect the Intelligence Center as an explicit entry under `潜客开发`.

---

## 10. Decision Summary

- **Is ADR-C17 overturned?** No. A3 is an evolution within its authority.
- **Is ADR-C16 affected?** No. All preserved C16 decisions remain authoritative.
- **Do any entities change ownership?** No.
- **Do any entities change ACL?** No.
- **Is a new Center introduced?** No. The five Centers are unchanged.
- **Is a new entity introduced?** No.
- **What is the substantive change?** Two new dividers (`商务`, `支持`); Quote moves from 潜客开发 to 商务; KnowledgeBaseArticle moves from 更多 to 支持; 情报中心 becomes an explicit entry under 潜客开发.
- **Does Phase3C19 code change?** No. This is a governance/document amendment only.
- **Is rollback safe?** Yes. Pre-migration snapshot restoration. Zero data impact.

---

## 11. Acceptance Record

### 11.1 Governance Validation (2026-07-27)

| Gate | Result | Evidence |
|---|---|---|
| No conflict with ADR-C17 frozen navigation model | **PASS** | Entity classes A–F unchanged; five Centers unchanged; Quote remains Class A; Lead remains Class E with no duplicate tab; governance chain preserved. Divider membership for Quote / KnowledgeBaseArticle and explicit 情报中心 listing are the amended dimensions, authorized by ADR amendment (same mechanism as A1). |
| No conflict with Phase3C19 Charter | **PASS** | C19 Charter §5 still forbids C19 WP1–WP3 from modifying `tabList` / `navigation.json` / materializer. A3 is a C17 navigation evolution. Acceptance does **not** fold A3 materialization into C19 WP scope. |
| Intelligence Center remains composition layer | **PASS** | §4.3: composition reference only; Workbench remains a dashlet; no new scope, page, entity, ACL, or workflow owner. |
| Quote migration is navigation ownership only | **PASS** | Quote Class A retained; lifecycle/ACL/services untouched (§5.2, §6). |
| Support divider is placeholder only | **PASS** | KnowledgeBaseArticle only; no Case / Support workflow / new entities (§1.3, §6). |
| No implementation scope in this acceptance | **PASS** | Docs-only. No `navigation.json`, metadata, code, or test changes in this acceptance task. §8 criteria remain implementation gates for a separately authorized materialization task. |

### 11.2 Acceptance Decision

**Amendment A3 is Accepted** as design authority for the Commercial / Intelligence / Support divider evolution of ADR-C17.

Accepted means:

1. The target IA in §4 is the authorized desired navigation design.
2. Runtime materialization, desired-state artifact edits, i18n keys, and contract-test updates remain **not executed** until a separately authorized implementation task.
3. That implementation task is **outside** Phase3C19 WP1–WP3 and must not weaken C19 Charter §5 for those work packages.
4. Physical materialization of `情报中心` must not duplicate the global native `Lead` tab (ADR-C17 Class E rule remains binding).

### 11.3 Decision Record

| Date | Decision | Authority |
|---|---|---|
| 2026-07-27 | Amendment A3 proposed (Commercial & Intelligence Center top-level separation) | Architecture draft |
| 2026-07-27 | Governance validation gates 1–6 PASS | Docs-only governance review |
| 2026-07-27 | **Amendment A3 Accepted** — design authority only; no runtime/artifact mutation in this task | Phase3C19 Navigation ADR Amendment A3 Acceptance |
| 2026-07-27 | A3 materialization deferred to a separately authorized navigation implementation task (not C19 WP1–WP3) | Acceptance §11.2 |

---

*Amendment A3 accepted 2026-07-27. Status: Accepted. Design authority only — no runtime, artifact, metadata, code, or test changes authorized by this acceptance alone.*
