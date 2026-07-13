# Phase3B06 — Prospecting Workspace / Sales Intelligence UI Report

**Date:** 2026-07-13  
**Workspace:** `D:\EspoCRM-Production`  
**Extension:** Chitu Prospecting Integration `1.6.0-alpha`  
**Runtime:** local EspoCRM-Test Docker stack  
**Status:** **PASS**

**Boundary:** Native EspoCRM Extension UI only (layouts, dashlets, panels, filters, relationships, ACL). No React CRM frontend. No second CRM UI. No data-model or connector/Brevo/Feedback contract changes. Does not authorize Phase3B07.

---

## 1. UI Architecture

Prospecting Workspace is delivered entirely through EspoCRM native extension mechanisms:

| Layer | Mechanism |
|---|---|
| Lead detail workspace | Prospecting-owned `layouts/Lead/detail.json` panels |
| Lead list | Prospecting-owned `layouts/Lead/list.json` + primary filters |
| Evidence relationship | `clientDefs.Lead.bottomPanels` + `relationshipPanels.researchEvidences` |
| Activity / timeline | Native Lead Stream + Activities/History/Tasks side panels + Email Events / Sales Feedback / Tasks relationship panels (no custom Timeline entity) |
| Dashboard | Native dashlet metadata `dashlets/ProspectingIntelligence.json` (`views/dashlets/abstract/record-list`) |
| Role visibility | Field ACL + Sync Information panel for technical fields |

```text
Sales User → Lead Intelligence Summary / Proposal / Email Status / Evidence panels
           → Prospecting Intelligence dashlet (Top 10 by score)
Research  → Evidence + research fields
Admin     → all panels including Sync Information
```

---

## 2. Components Added

### Extension (`1.6.0-alpha`)

| Component | Path / note |
|---|---|
| Primary filter `PeTierA` | score `>= 80` (updated rule) |
| Primary filter `PeRecentlyResearched` | `peResearchStatus=COMPLETED` + `peLastResearchedAt` within 14 days |
| Primary filter `PeContactReady` | `outreachStatus=CONTACT_READY` |
| Dashlet `ProspectingIntelligence` | Top 10 Leads by `peOpportunityScoreV4` DESC |
| i18n | Lead filters + Global dashlet label; panel label “AI Research Evidence” |
| ResearchEvidence `listSmall` | Title / Source URL / Summary / Confidence / Captured At |
| Lead bottom panels | Explicit `__APPEND__` for researchEvidences, emailEvents, salesFeedbacks, learningSignals |

### Deployment

- `deployment/prospecting-extension-1.6.0-alpha.zip`
- `deployment/provisioning/phase3b06_provision_workspace_roles.php`
- `deployment/provisioning/phase3b06_provision_synthetic_lead.php`
- `deployment/provisioning/phase3b06_cleanup_validation_records.php`

---

## 3. Layout Changes

### Lead Detail panels

1. **Intelligence Summary** — Company (`name`), Website, Country/State, Source, Opportunity Score, Score Tier, Recommended Product, Research Status, Priority, company classifiers  
2. **Pipeline** — outreachStatus, priority, follow-up dates  
3. **Opportunity Proposal** — `peProposal*` + product/score  
4. **Sales Activity** / **Email Status** / **AI Research Information**  
5. **Sync Information** — technical sync fields (hidden from Sales via ACL)  
6. **Contact & Ownership**

Technical fields (`peCandidateId`, `peSourceBatchId`, `peSourceSystem`, engine/score versions, etc.) remain in Sync Information only (not Intelligence Summary).

### ResearchEvidence

- List / listSmall oriented to Title, Source URL, Content Summary, Confidence.

---

## 4. Filters

| Filter key | Label | Rule |
|---|---|---|
| `peTierA` | A Tier Leads | `peOpportunityScoreV4 >= 80` |
| `peRecentlyResearched` | Recently Researched | research COMPLETED + last researched ≤ 14 days |
| `peContactReady` | Ready for Outreach | `outreachStatus = CONTACT_READY` |
| `peRecentlySynced` | Recently Synced | retained (prior filter) |

---

## 5. Dashlets

| Name | Type | Defaults |
|---|---|---|
| **Prospecting Intelligence** | Native `record-list` dashlet, `aclScope=Lead` | Top 10; sort `peOpportunityScoreV4` DESC; columns Company / Score / Product / Research Status |

Provisioned onto `admin` and `sales_test` Preferences dashboards by `phase3b06_provision_workspace_roles.php`.

---

## 6. Role Visibility

| Role | Sees | Hidden |
|---|---|---|
| Sales User | Intelligence, proposal, email status, research summary/evidence (read), feedback | Technical sync identifiers (`peCandidateId`, `peSourceSystem`, `peSourceBatchId`, sync/engine versions, …) |
| Research User | Evidence + research fields | Same technical sync hide policy on Lead |
| Admin | All panels including Sync Information | — |

Sales Sync Information panel in browser showed only non-hidden fields (e.g. Qualification Status) — ACL hide verified.

---

## 7. Browser Validation

Authenticated as `sales_test` against `http://localhost:8080` with synthetic Lead `PHASE3B06-TEST Workspace Co`.

| Check | Result |
|---|---|
| Lead Detail — Intelligence Summary | **PASS** (score 88.5, Tier A, product, research Completed) |
| Opportunity Proposal / Email Status / AI Research | **PASS** |
| AI Research Evidence panel | **PASS** (Title, Source URL, Summary, Confidence) |
| Email Events / Sales Feedback / Learning Signals panels | **PASS** |
| Stream + Tasks (native activity) | **PASS** |
| Lead List primary filters (`peTierA`, …) | **PASS** (`peTierA` → 1 matching lead) |
| Prospecting Intelligence dashlet | **PASS** (Top lead 88.5 / product / Completed) |
| Sales technical field hide | **PASS** |

**Note:** Narrow viewport list headers may still emphasize Name/Status/Email visually; LayoutProvider resolves Prospecting list columns (Company, Country, Score, Tier, Product, Research Status, Email Status, Priority). Filter behavior verified.

---

## 8. Regression Results

| Suite | Result |
|---|---|
| Extension `tests.test_extension_skeleton` | **PASS** — 33 tests |
| Connector `unittest discover -s tests` | **PASS** — 47 tests |
| Sync / Workflow / Email / Feedback contracts | Unchanged (no connector contract edits in this phase) |

Package: `deployment/prospecting-extension-1.6.0-alpha.zip`  
SHA-256: `AC432C945EE6F407F602CF90C6D883BD80C8A8EDBEFB8CCCD13FD2A8EACAA45D`

---

## 9. Limitations

1. Filter dropdown may show technical keys (`peTierA`) until client language cache fully refreshes; i18n labels are packaged under Lead `filters`.
2. List column chrome on very narrow viewports can look like core Status/Email; server LayoutProvider returns Prospecting list.json.
3. Timeline uses native Stream + Tasks + Email Events / Feedback panels — no custom Timeline entity.
4. Dashlet deployment is Preferences-based for local validation users; production may attach via Dashboard Template / admin Add Dashlet.
5. Validated on local EspoCRM-Test only.

---

## 10. Cleanup

Synthetic Lead / Evidence / EmailEvent / Feedback / LearningSignal / related Tasks / disposable `research_test` user removed via `phase3b06_cleanup_validation_records.php`.

Temporary debug scripts (`temp/_phase3b06_*.php` and matching `/tmp` copies) removed at finalization.

---

**Phase3B06 complete. Status: PASS.**

Do **not** enter Phase3B07 without explicit authorization.
