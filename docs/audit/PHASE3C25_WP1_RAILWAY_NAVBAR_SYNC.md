# Phase3C25 WP1 Railway Navbar Runtime Sync

| Field | Value |
| --- | --- |
| Document Type | Runtime configuration sync evidence |
| Work Package | C25 WP1 — Railway staging navbar / Tab List sync |
| Date | 2026-08-06 |
| Environment | Railway staging `espocrm-c25-staging` |
| URL | `https://espocrm-c25-staging-staging.up.railway.app` |
| Deployment | `1dd8584c-f23a-45ba-89b6-51f2da95c2b1` |
| Image digest | `sha256:59d3c93b5eb67e5260b82664c0bfa460707d919da5b5119474826eed3559f819` |
| Status | **PASS — WP1 Railway Navbar Runtime Sync Complete** |

```text
Runtime config.tabList sync only.
No PHP, metadata, ACL, entity, migration, rebuild, restart, or redeploy.
```

---

## 1. Executive Verdict

**PASS — WP1 Railway Navbar Runtime Sync Complete.**

Railway staging already had Prospecting / CommercialIntelligence modules loaded and
WP1 entity APIs healthy. The stock EspoCRM UI was caused only by a default
`config.tabList` on the Layer-A data volume. After syncing Tab List to expose
`SearchStrategy`, `ProspectPool`, and `SendExecution`, the navbar shows those
surfaces and the list routes load normally. Standard CRM tabs remain intact.
`CommercialIntelligenceWorkspace` was not added as a normal entity tab.

---

## 2. Cause

| Layer | Pre-sync Railway state |
| --- | --- |
| Extension modules | Loaded (metadata + ACL scopes present) |
| Entity APIs | `ProspectPool` / `SearchStrategy` / `SendExecution` → HTTP 200 |
| Runtime `config.tabList` | **Stock EspoCRM defaults** (no WP1 tabs) |

**Cause:** runtime `config.tabList` mismatch vs local WP1 navbar amendment
(`docs/audit/PHASE3C25_WP1_NAVBAR_EXPOSURE_AMENDMENT.md`). Local had the
amendment; Railway volume retained Layer-A stock Tab List.

---

## 3. Local vs Railway Difference (before sync)

| Surface | Local C25 (`localhost:18080`) | Railway (before) |
| --- | --- | --- |
| Modules / metadata | Present | Present |
| Entity APIs | Reachable | Reachable |
| `tabList` WP1 entries | Present | **Absent** |
| Visible navbar | WP1 + CRM | Stock CRM only |

---

## 4. Runtime Configuration Changed

**Only** EspoCRM runtime UI configuration equivalent to:

Administration → User Interface → Tab List

Applied via Settings API (`PUT /api/v1/Settings` with `tabList`) — the same
persisted field the Admin UI edits.

### Before (names only)

Account, Contact, Lead, Opportunity, Email, Meeting, Call, Task, Calendar, …

WP1 absent: SearchStrategy / ProspectPool / SendExecution = false

### After (inserted section)

```text
$CRM
Account
Contact
Lead
Opportunity
Prospecting          ← divider added
SearchStrategy       ← added
ProspectPool         ← added
SendExecution        ← added
$Activities
Email
...
```

Preserved: Account, Contact, Lead, Opportunity, and remaining stock tabs.  
Not added: `CommercialIntelligenceWorkspace` (workspace design unchanged; `tab: false`).

### Not changed

| Surface | Result |
| --- | --- |
| PHP / JS / templates | Unchanged |
| entityDefs / scopes / aclDefs | Unchanged |
| Database schema / migrations | Not run |
| Docker image / Railway redeploy / restart | Not performed |
| Manual metadata rebuild | Not performed |

---

## 5. Verification Results

| Check | Result |
| --- | --- |
| Navbar: Prospect Pool | **PASS** |
| Navbar: Search Strategies | **PASS** |
| Navbar: Send Executions | **PASS** |
| `#ProspectPool` list page | **PASS** — title “Prospect Pool” |
| `#SearchStrategy` list page | **PASS** — title “Search Strategies” |
| `#SendExecution` list page | **PASS** — title “Send Executions” |
| `#Account` | **PASS** — title “Accounts” |
| `#Contact` | **PASS** — title “Contacts” |
| `#Lead` | **PASS** — title “Leads” |
| `#CommercialIntelligenceWorkspace` | **PASS** — heading “Commercial Intelligence Workspace”; not converted to entity tab |
| Settings after-state WP1 flags | SearchStrategy / ProspectPool / SendExecution = true |

---

## 6. Screenshots / Evidence Paths

Stored under `docs/audit/runtime-evidence/phase3c25-wp1-railway-navbar/`:

| File | Content |
| --- | --- |
| `01-navbar-after.png` | Post-sync Prospect Pool surface (route active) |
| `02-prospect-pool.png` | Prospect Pool list + navbar including WP1 + CRM tabs |
| `03-search-strategy.png` | Search Strategies list + navbar |
| `04-send-execution.png` | Send Executions list + navbar |

---

## 7. Scope Confirmation

Allowed (performed):

- Railway runtime Tab List / `config.tabList` sync
- Browser verification
- Documentation / screenshots
- Documentation-only git commit (if created)

Forbidden (honored):

- PHP / metadata / entity / ACL code changes
- Migrations / reinstall / restart / redeploy / Dockerfile changes
- Schema changes
- Application code commits

Do not continue to WP2.2 from this record.

---

*End of Phase3C25 WP1 Railway Navbar Runtime Sync.*
