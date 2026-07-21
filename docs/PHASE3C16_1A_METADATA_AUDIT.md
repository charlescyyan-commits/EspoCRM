# Phase3C16.1A — Metadata Consistency Audit

**Mode:** read-only audit  
**Scope:** `crm-extension/` metadata for `Quote`, `QuoteItem`, `ProformaInvoice`, `Approval`  
**Baseline HEAD:** `8feedaf792c5a41f336a2640af907f08b4cd49ac`  
**Constraint:** no metadata, entityDefs, scopes, ACL, artifact, or script changes were made.

## 1. Inventory checked

| Layer | Quote | QuoteItem | ProformaInvoice | Approval |
| --- | :---: | :---: | :---: | :---: |
| Module `metadata/entityDefs` | yes | yes | yes | yes |
| Surface `Resources/entityDefs` | yes | yes | yes | yes |
| Module `metadata/scopes` | yes | yes | yes | yes |
| Module `metadata/aclDefs` | yes | yes | yes | yes |
| Surface `Resources/acl` | yes | yes | yes | yes |
| Module `clientDefs` | no | no | no | no |
| i18n (`en_US` / `zh_CN`) | no | no | no | no |
| Layouts (`detail` / `list`) | no | no | no | no |
| PHP `Entities/*.php` | no | no | no | no |

Surface `Resources/scopes` does not exist for any Prospecting entity (including pre-C16 peers). Scopes living only under the module is consistent with this extension’s existing pattern.

## 2. Consistency that passes

### 2.1 Module ↔ surface parity

For all four C16 entities:

- module `entityDefs` JSON equals surface `Resources/entityDefs` JSON
- module `aclDefs` JSON equals surface `Resources/acl` JSON

### 2.2 Scopes

| Entity | entity | object | tab | acl | module | type | statusField |
| --- | :---: | :---: | :---: | :---: | --- | --- | --- |
| Quote | true | true | true | true | Prospecting | Base | status |
| QuoteItem | true | true | false | true | Prospecting | Base | *(absent — no status field)* |
| ProformaInvoice | true | true | true | true | Prospecting | Base | status |
| Approval | true | true | true | true | Prospecting | Base | status |

`QuoteItem.tab = false` matches the inline-child intent from C16.1A.

### 2.3 ACL

All four use the Prospecting gate form:

```json
{"Prospecting": {"<Entity>": true}}
```

Naming matches entity names exactly.

### 2.4 Relationship reciprocity (C16-owned links)

| Pair | Reciprocal foreign keys | Result |
| --- | --- | --- |
| Quote.`quoteItems` ↔ QuoteItem.`quote` | quote / quoteItems | OK |
| Quote.`proformaInvoices` ↔ ProformaInvoice.`quote` | quote / proformaInvoices | OK |
| Quote.`approvals` ↔ Approval.`quote` | quote / approvals | OK |
| ProformaInvoice.`approvals` ↔ Approval.`proformaInvoice` | proformaInvoice / approvals | OK |

### 2.5 Required skeleton keys present

Required C16.1A fields and business links for all four entities are present. No missing keys relative to the shipped skeleton contract tests.

### 2.6 Workflow / payment separation

`ProformaInvoice.status` options and `paymentStatus` options are disjoint. Defaults differ (`DRAFT` vs `UNPAID`).

## 3. Findings

Severity legend: **H** = likely to block later C16 work or confuse integrators; **M** = inconsistency / deferred risk; **L** = informational / phase-expected.

### F1 — Lead / Opportunity have no reverse Quote links (M)

`Quote.lead` and `Quote.opportunity` are one-sided `belongsTo` links with **no** `foreign` key and **no** matching `hasMany` on `Lead` or `Opportunity`.

Impact:

- Lead/Opportunity detail relationship panels cannot show Quotes via Espo relationship metadata.
- Acceptable for a metadata-only skeleton if intentional; must be closed before CRM UI relationship navigation is required.

### F2 — Approval polymorphic triple is metadata-unenforced (H for later phases, accepted for 1A)

Approval requires `targetType` + `targetId`, while `quote` / `proformaInvoice` links are both optional. There is no metadata XOR / consistency rule tying:

- `targetType=Quote` → `quote` populated / `proformaInvoice` empty
- `targetType=ProformaInvoice` → reverse

Risk: orphan or contradictory Approval rows until Service-layer guards land.

### F3 — Ownership-field asymmetry (M)

| Entity | createdBy / modifiedBy | assignedUser / teams |
| --- | :---: | :---: |
| Quote | yes | yes |
| ProformaInvoice | yes | yes |
| Approval | no | no |
| QuoteItem | no | no |

Peers such as `DraftApproval` include ownership/team fields. QuoteItem as a non-tab child can omit them. Approval omitting them is a sharper ACL/audit gap for a tab-visible workflow entity.

### F4 — `paymentStatus` not indexed (L/M)

`ProformaInvoice` indexes `status` and `quoteId`, but not `paymentStatus`. Finance filters by payment state will not have a dedicated index until a later schema pass.

### F5 — Nullable unique numbering columns (M)

`quoteNumber` and `piNumber` are nullable (`required: false`, `notNull: false`) with unique indexes on `(number, deleteId)`. Multiple unset rows rely on DB NULL-unique semantics. Numbering ADR defers assignment to later phases; still a data-integrity risk if many blank numbers are created before C16.2/C16.5.

### F6 — Deferred UI/runtime artifacts missing (L — in-scope for 1A)

Absent for all four entities: `clientDefs`, i18n, layouts, PHP Entity classes.  
This matches the C16.1A skeleton report (“no client layouts…”). Recorded here so later phases do not assume install-ready CRM UI.

## 4. Missing keys (relative to ADR full design, not 1A skeleton)

These ADR-described keys are **not** in the 1A metadata. They are not 1A delivery defects if 1A deliberately shipped a minimal skeleton, but they are naming/completeness gaps versus the frozen ADR tables:

| Entity | ADR / prep keys not present in 1A metadata |
| --- | --- |
| Quote | currency, subtotal, tax*, total, notes, terms, pdf* |
| QuoteItem | product, description, discount, **lineTotal**, **sortOrder** |
| ProformaInvoice | paymentDueDate, paidAmount, quoteSnapshot, pdf*, financial totals |
| Approval | ADR names `approvalType` / `entityType` / `entityId` / requestedBy / approver / decision / reason — skeleton uses **`targetType` / `targetId`** plus optional quote/PI links |

## 5. Naming consistency

| Topic | Observation |
| --- | --- |
| Entity names | Consistent PascalCase across entityDefs / scopes / aclDefs / ACL surface |
| Link names | Plural collections (`quoteItems`, `proformaInvoices`, `approvals`) and singular belongsTo (`quote`, `proformaInvoice`) are consistent |
| Status enums | Shared tokens (`DRAFT`, `SENT`, `APPROVED`, `REJECTED`) appear in different machines with different meanings — intentional, but operators must not conflate Quote.status with PI.status or Approval.status |
| Amount naming | Quote and QuoteItem both use `amount`; ADR prefers `lineTotal` on items |
| Approval target naming | Skeleton `targetType`/`targetId` ≠ ADR `entityType`/`entityId` / `approvalType` — docs and code will diverge until one vocabulary is frozen in implementation |
| ACL keys | Match entity names exactly |

## 6. Risks summary

1. **Polymorphic Approval integrity** depends entirely on future Service rules (F2).  
2. **No Lead/Opportunity reverse links** blocks CRM relationship UX until added (F1).  
3. **ADR ↔ skeleton vocabulary drift** (`targetType` vs `entityType`, `amount` vs `lineTotal`) can cause wrong field assumptions in C16.2+ (naming section).  
4. **Approval without teams/assignedUser** may complicate ACL and ownership later (F3).  
5. **Nullable unique numbers** need an explicit numbering strategy before bulk create (F5).  
6. **Missing clientDefs/i18n/layouts/PHP** will fail human install/UX expectations if someone treats 1A as UI-complete (F6).

## 7. Verdict

**AUDIT COMPLETE — NO METADATA CHANGES MADE.**

Core 1A consistency (module/surface parity, scopes, ACL naming, C16 reciprocal relationships, required skeleton fields, PI dual-status separation) is **sound**.

Open items are deferred-structure / ADR-alignment / parent-reverse-link findings. Per task rules: **reported only; not fixed.**
