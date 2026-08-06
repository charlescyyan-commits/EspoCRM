# Phase3C25 WP1 Railway Navbar Sync Closure

| Field | Value |
| --- | --- |
| Document Type | Governance Closure Record (documentation only) |
| Work Package | C25 WP1 — Railway staging navbar runtime synchronization |
| Date | 2026-08-06 |
| Environment | Railway staging `espocrm-c25-staging` |
| URL | `https://espocrm-c25-staging-staging.up.railway.app` |
| Deployment | `1dd8584c-f23a-45ba-89b6-51f2da95c2b1` |
| Sync evidence | `docs/audit/PHASE3C25_WP1_RAILWAY_NAVBAR_SYNC.md` |
| Local precedent | `docs/audit/PHASE3C25_WP1_NAVBAR_EXPOSURE_AMENDMENT.md` |
| Status | **CLOSED — PASS** |

```text
This record closes the Railway staging WP1 navbar runtime sync.

It does NOT authorize WP2.2, WP2.3, implementation expansion, metadata
rebuild, migration, redeploy, or production promotion.
```

---

## 1. Executive Verdict

**CLOSED — PASS**

Railway staging navbar runtime synchronization is complete and closed.
WP1 Prospecting surfaces are exposed in the Railway Tab List. Standard CRM
tabs and the Commercial Intelligence Workspace route design are preserved.
No code, metadata, ACL, entity, migration, rebuild, deployment, or restart
action was part of this sync or this closure.

---

## 2. Root Cause

Railway staging data volume retained the default EspoCRM `config.tabList`
from Layer-A installation.

| Fact | State before sync |
| --- | --- |
| Deployment | `1dd8584c-f23a-45ba-89b6-51f2da95c2b1` (healthy) |
| Prospecting / CommercialIntelligence modules | Already loaded |
| WP1 entity APIs | Already healthy |
| `config.tabList` | Stock CRM only — missing WP1 tabs |

Local WP1 navbar amendment had already corrected local staging Tab List.
That runtime configuration had not been synchronized to Railway.

---

## 3. Runtime Change

**Changed surface only:** EspoCRM runtime UI configuration —
Administration → User Interface → Tab List (`config.tabList`).

### Added

- `ProspectPool`
- `SearchStrategy`
- `SendExecution`

### Preserved

- `Account`
- `Contact`
- `Lead`
- `Opportunity`
- Existing CRM / Activities / Support / Marketing / Organization tabs

### Not added

- `CommercialIntelligenceWorkspace` as a normal entity tab

Workspace remains the workspace route (`#CommercialIntelligenceWorkspace`),
not a list-entity navbar tab.

### Explicit non-actions (honored)

| Action | Performed? |
| --- | --- |
| Code changes (PHP / JS / templates) | **No** |
| Metadata changes | **No** |
| Entity changes | **No** |
| ACL changes | **No** |
| Migration | **No** |
| Metadata rebuild | **No** |
| Deployment / image rebuild | **No** |
| Service restart | **No** |

---

## 4. Verification Evidence

Source verification record:
`docs/audit/PHASE3C25_WP1_RAILWAY_NAVBAR_SYNC.md`

Screenshots:
`docs/audit/runtime-evidence/phase3c25-wp1-railway-navbar/`

| Check | Result |
| --- | --- |
| Navbar displays Prospect Pool | **PASS** |
| Navbar displays Search Strategies | **PASS** |
| Navbar displays Send Executions | **PASS** |
| `#ProspectPool` | **PASS** |
| `#SearchStrategy` | **PASS** |
| `#SendExecution` | **PASS** |
| `#Account` | **PASS** |
| `#Contact` | **PASS** |
| `#Lead` | **PASS** |
| `#CommercialIntelligenceWorkspace` | **PASS** (workspace route; not entity tab) |

---

## 5. Final WP1 Status

| Area | Status |
| --- | --- |
| WP1 Backend (local + Railway modules/API) | **PASS** |
| WP1 Frontend assets | **PASS** |
| WP1 Local navbar amendment | **PASS / COMPLETE** |
| WP1 Railway navbar runtime sync | **PASS / CLOSED** |
| WP1 Overall | **COMPLETE** for navbar exposure on local and Railway staging |

### Authorization boundary (unchanged)

| Scope | Status |
| --- | --- |
| WP2.2 | **NOT AUTHORIZED** by this closure |
| WP2.3 | **NOT AUTHORIZED** by this closure |
| Implementation authorization | **None issued** |
| Production promotion | **NOT AUTHORIZED** |

No WP2.2 work follows from this record.

---

*End of Phase3C25 WP1 Railway Navbar Sync Closure.*
