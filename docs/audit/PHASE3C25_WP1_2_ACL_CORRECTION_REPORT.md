# Phase3C25 WP1.2 Governed Source ACL Correction Report

| Field | Value |
| --- | --- |
| Document Type | ACL Correction Verification Report |
| Subject | Phase3C25 WP1.2 — Governed Source Native ACL Registration |
| Date | 2026-07-31 |
| Baseline HEAD (pre-commit) | `44d9ffa` — Railway C25 staging scaffold |
| Branch | `master` |
| Implementation Authorization | Metadata ACL registration correction only |

## 1. Executive Verdict

```text
PASS — native governed source ACL behavior corrected
```

## 2. Preflight and Concurrent HEAD Review

| Item | Value |
| --- | --- |
| Branch | `master` |
| HEAD at report drafting | `44d9ffa` |
| Commit `44d9ffa` classification | Railway staging Dockerfile scaffold only — **no ACL content** |
| Dirty ACL metadata | Present in working tree (uncommitted) |
| Untracked ACL tests / leftovers | Present; formal report previously missing |
| ACL work previously committed? | **NO** — all WP1.2 ACL changes were worktree-only until this commit |

Concurrent / unrelated dirty and untracked files (CommercialIntelligence module, Railway plan, C25 docs, `docs/adr/C24_INVARIANT_REGISTRY.md`, extension skeleton tests, temporary sha256 sidecar, etc.) remain outside the ACL correction commit allowlist.

## 3. Reproduced Runtime Failure

Pre-correction runtime verification (`docs/audit/PHASE3C25_WP1_RUNTIME_VERIFICATION_REPORT.md`) established:

| Observation | Result |
| --- | --- |
| `CommercialIntelligenceWorkspace` permission | Present (`true`) for authorized API user |
| C24 scopes in `App/user` effective ACL | **Absent / missing** for non-admin |
| Authorized non-admin `GET .../CommercialIntelligence/workspace/c25wp1root0000001` | **404** at root `OpportunityCandidate` ACL check |
| Admin workspace | **200** (admin path bypasses the mandatory force-off) |

The workspace boolean alone was insufficient: C25 correctly called native `checkEntityRead` on governed sources, and Espo denied because no effective source ACL existed for the role.

## 4. Root Cause

C24 governed scopes (`OpportunityCandidate`, `ReplySignal`, `RevenueInsight`, `PipelineMetric`) had native ACL-capable scope metadata (`entity: true`, `acl: true`) but were **force-disabled for every non-admin role assignment** by:

```text
metadata/app/acl.json
mandatory.scopeLevel.<scope> = false
```

Consequences:

1. Role UI / role data could not place a usable non-admin read grant into Espo’s effective ACL map for those scopes.
2. `App/user` omitted the scopes for authorized non-admin API users.
3. C25 `VisibilityInheritanceService` / assembly path native `checkEntityRead` correctly failed closed → **404** on the root `OpportunityCandidate`.

This was an Espo **mandatory ACL registration** defect, not a C25 parallel-ACL bug.

## 5. Correction

| Change | Detail |
| --- | --- |
| Remove force-off | Delete the four C24 scopes from `mandatory.scopeLevel = false` |
| Read-only action list | Add `"aclActionList": ["read"]` on each of the four scopes |
| Preserve hidden posture | Keep `object: false`, `tab: false` |
| Preserve portal denial | Keep `aclPortal: false` (and portal mandatory denials unchanged) |
| No C25 ACL rewrite | No change to `VisibilityInheritanceService`; no parallel ACL service |
| No CRUD navigation | Entities remain non-object / non-tab; not ordinary CRM list/detail entities |

Deny-by-default remains: scopes are eligible for **native role read**, but roles without an explicit read grant still deny.

## 6. Files Changed

| File | Purpose |
| --- | --- |
| `.../scopes/OpportunityCandidate.json` | Add `aclActionList: ["read"]` |
| `.../scopes/ReplySignal.json` | Add `aclActionList: ["read"]` |
| `.../scopes/RevenueInsight.json` | Add `aclActionList: ["read"]` |
| `.../scopes/PipelineMetric.json` | Add `aclActionList: ["read"]` |
| `.../metadata/app/acl.json` | Remove four C24 scopes from `mandatory.scopeLevel=false` |
| `tests/test_phase3c25_wp1_2_acl_correction.py` | New WP1.2 offline ACL regression suite |
| `tests/test_phase3c24_wp1_reply_intelligence.py` | Align ReplySignal ACL expectations with WP1.2 |
| `tests/test_phase3c24_wp2_candidate_acl.py` | Align OpportunityCandidate ACL expectations with WP1.2 |
| `tests/test_phase3c24_wp3_entity_foundation.py` | Align WP3 entity ACL expectations with WP1.2 |
| `tests/test_phase3c24_wp3_metadata_acl.py` | Align WP3 metadata ACL expectations with WP1.2 |
| `docs/audit/PHASE3C25_WP1_2_ACL_CORRECTION_REPORT.md` | This report |

## 7. Effective ACL Before and After

### Before (authorized non-admin)

- `CommercialIntelligenceWorkspace = true`
- `OpportunityCandidate` / `ReplySignal` / `RevenueInsight` / `PipelineMetric` **missing from effective ACL table**
- Workspace request → **404**

### After (verified)

```text
CommercialIntelligenceWorkspace = true
OpportunityCandidate = read:all, create:no, edit:no, delete:no
ReplySignal = read:all, create:no, edit:no, delete:no
RevenueInsight = read:no, create:no, edit:no, delete:no
PipelineMetric = read:all, create:no, edit:no, delete:no
```

`RevenueInsight = read:no` is the intentional nested-denial fixture configuration, not a registration failure.

## 8. Runtime ACL Matrix

| Case | Result |
| --- | --- |
| Authorized non-admin | **200** — root OC present; RS + PM present; RI omitted |
| Root denied | **404** |
| Workspace denied | **403** |
| Portal | **rejected** (401) |
| Nested RevenueInsight denied | **omitted** from payload; no RI string leakage |
| Admin | Earlier WP1 runtime verification returned **200**; WP1.2 recovery audit could not retest via API because `phase3c25_wp1_admin_ui` has no API key |

Missing admin API-key retest is **not** a blocker for this correction.

## 9. Mutation Boundary

| Control | Status |
| --- | --- |
| Only read assignable via `aclActionList` | YES — `["read"]` |
| create / edit / delete in effective ACL | `no` |
| `object` | `false` |
| `tab` | `false` |
| `importable` | `false` |
| Generic CRUD navigation introduced | NO |
| Write API added | NO |
| C24 lifecycle authority changed | NO |

## 10. Tests

Commands executed for this documentation/commit task:

```powershell
.\.venv-s01\Scripts\python.exe -m pytest tests/test_phase3c25_wp1_2_acl_correction.py -q -p no:cacheprovider

.\.venv-s01\Scripts\python.exe -m pytest `
  tests/test_phase3c24_wp1_reply_intelligence.py `
  tests/test_phase3c24_wp2_candidate_acl.py `
  tests/test_phase3c24_wp3_entity_foundation.py `
  tests/test_phase3c24_wp3_metadata_acl.py `
  -q -p no:cacheprovider

.\.venv-s01\Scripts\python.exe -m pytest `
  tests/test_phase3c25_wp1_workspace_foundation.py `
  crm-extension/tests/test_espo_php_namespace_contracts.py `
  crm-extension/tests/test_extension_skeleton.py `
  -q -p no:cacheprovider

git diff --check
```

Results are recorded in the commit task execution log (focused suites must pass before commit).

Prior recovery audit also confirmed `tests/test_phase3c25_wp1_2_acl_correction.py` → **12 passed**.

## 11. Remaining Work

- ACL blocker for governed source assembly: **CLOSED**
- Governed source navigation (hash/UI deep-link): **separate WP1 task**
- Focused runtime recheck required after navigation work
- WP1 is **not** yet formally frozen

## 12. Final Recommendation

| Gate | Status |
| --- | --- |
| native source ACL corrected | YES |
| authorized non-admin works | YES |
| nested denial works | YES |
| mutation remains denied | YES |
| portal remains blocked | YES |
| ready for governed source navigation | YES |
| ready for formal freeze | **NO** |

---

*Documentation only for commit packaging of an already-verified ACL metadata correction. Does not authorize production promotion, provider credentials, push, or freeze.*
