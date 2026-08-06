# Phase3C25 WP1 Navbar Exposure Amendment

| Field | Value |
| --- | --- |
| Document Type | Governance / Runtime Amendment Evidence |
| Work Package | C25 WP1 — Navbar / Tab List exposure amendment |
| Date | 2026-08-06 |
| Environment | Local C25 staging container `espocrm-c25-staging-espocrm-1` (`http://localhost:18080`) |
| Status | **PASS — WP1 Navbar Exposure Amendment Complete** |

---

## 1. Executive Verdict

**PASS — WP1 Navbar Exposure Amendment Complete.**

WP1 backend entities and frontend assets were already present. The remaining gap was
runtime `config.tabList` only: `ProspectPool`, `SearchStrategy`, and `SendExecution`
were absent from the left navigation. After the tabList amendment, all three surfaces
are visible and open successfully. Existing CRM menus and the Commercial Intelligence
Workspace route remain intact. No entity, ACL, metadata, migration, rebuild, deploy,
AI, provider, or WP2 work was performed.

---

## 2. Root Cause

| Layer | Pre-amendment state |
| --- | --- |
| Entity metadata (`Prospecting` module) | Present — `tab: true`, `module: Prospecting` |
| Frontend assets | Present (previously verified) |
| ACL | Unchanged / previously verified |
| Workspace route `#CommercialIntelligenceWorkspace` | Present |
| Runtime `config.tabList` | **Missing** `ProspectPool`, `SearchStrategy`, `SendExecution` |

Root cause: UI navigation configuration only. Entities were deployed; they were not
listed in the effective EspoCRM tab list consumed by the navbar.

---

## 3. Before State (tabList)

Recorded via `bin/command config:get tabList` before the amendment.

Present Prospecting entries:

- `ProspectingDashboard`
- `ProspectingSearch`
- `DraftApproval`

Missing:

- `ProspectPool`
- `SearchStrategy`
- `SendExecution`

No duplicate tabs for those three scopes existed.

---

## 4. Changed Surface

**Only** runtime EspoCRM navigation configuration (`config.tabList`).

| Changed | Not changed |
| --- | --- |
| `config.tabList` (runtime) | PHP / JS / templates |
| Cache clear after config write | entityDefs / scopes / aclDefs |
| | Database schema / migrations |
| | Docker image / Railway redeploy |
| | WP1 freeze artifacts / WP2 code |

Placement (Prospecting section):

```text
...
ProspectingDashboard
ProspectingSearch
SearchStrategy      ← added
ProspectPool        ← added
DraftApproval
SendExecution       ← added
...
```

No WP2 / CommercialBrief navbar exposure was introduced.

---

## 5. After State (tabList)

Verified via `bin/command config:get tabList` after the amendment:

- `SearchStrategy` present
- `ProspectPool` present
- `SendExecution` present
- `CommercialBrief` absent (correct)

---

## 6. Browser Verification

Admin login succeeded. Left navigation (accessibility tree + navbar menu) exposed:

| Navbar label | Scope | Result |
| --- | --- | --- |
| Prospect Pool | `ProspectPool` | PASS — `#ProspectPool` list loads; title “Prospect Pool”; no 404/ACL error |
| Search Strategies | `SearchStrategy` | PASS — `#SearchStrategy` list loads; title “Search Strategies”; no 404/ACL error |
| Send Executions | `SendExecution` | PASS — `#SendExecution` list loads; title “Send Executions”; no 404/ACL error |

CRM regression (unchanged menus / pages):

| Surface | Result |
| --- | --- |
| Accounts (`#Account`) | PASS |
| Contacts (`#Contact`) | PASS |
| Leads (`#Lead`) | PASS |

Workspace preservation:

| Surface | Result |
| --- | --- |
| `#CommercialIntelligenceWorkspace` | PASS — heading “Commercial Intelligence Workspace”; route unchanged |

Console: no application errors observed during verification (only Cursor browser harness warnings).

### Evidence screenshots

Stored under `docs/audit/runtime-evidence/phase3c25-wp1-navbar/`:

| File | Content |
| --- | --- |
| `01-navbar-after.png` | Navbar after amendment (Prospect Pool / Search Strategies / Send Executions visible with Accounts/Contacts/Leads) |
| `02-prospect-pool.png` | Prospect Pool list page |
| `03-search-strategy.png` | Search Strategies list page |
| `04-send-execution.png` | Send Executions list page |
| `05-workspace.png` | Commercial Intelligence Workspace route |

---

## 7. Regression Verification

| Check | Result |
| --- | --- |
| Entity Manager / entityDefs | Unchanged (not modified) |
| ACL / aclDefs | Unchanged (checksum-verified on staging scopes/aclDefs; no writes) |
| Metadata unrelated to navigation | Unchanged |
| Rebuild | Not executed |
| Migration / SQL | Not executed |
| Docker rebuild / Railway redeploy | Not executed |
| Hooks / PHP / JS | Unchanged |
| WP2 / AI generation / provider | Not in scope; not touched |
| Duplicate tabs | None for the three added scopes |

---

## 8. Scope Confirmation

Allowed:

- Navbar / Tab List configuration
- UI exposure of existing Prospecting entities
- Browser verification
- Documentation / evidence
- Commit of amendment-related files only

Forbidden (honored):

- Entity / ACL / unrelated metadata changes
- Database / migration / rebuild
- Hook / AI / provider / WP2 work

---

## 9. Final WP1 Status

| Area | Status |
| --- | --- |
| WP1 Backend | **PASS** |
| WP1 Frontend | **PASS** |
| WP1 Navigation | **PASS** |
| WP1 Runtime | **PASS** |
| WP1 Overall | **COMPLETE** |

Next authorized governance step (not performed by this amendment): **C25 WP2.1B Foundation Review** — do not enter WP2.1B Implementation from this record alone.

---

*End of Phase3C25 WP1 Navbar Exposure Amendment.*
