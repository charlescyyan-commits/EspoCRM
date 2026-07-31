# Phase3C25 WP1 Final Runtime Recheck

## 1. Executive Verdict

PASS WITH CONDITIONS — WP1 final combined runtime state is ready for commit preparation

Conditions:

- retained admin API credential (`smoke-test`) currently returns HTTP 401, so admin control is `NOT TESTABLE FROM CURRENT STATE`;
- WP1.3 durable desktop/responsive/escaped screenshots remain byte-identical at the constrained browser-panel viewport (already documented; non-blocking);
- canonical release archive remains intentionally stale (rebuild forbidden); four pre-existing full-suite failures remain.

No runtime ACL, navigation, mutation-boundary, or no-write regression was observed against the combined WP1/WP1.1/WP1.2/WP1.3 state.

## 2. Repository State

- Branch: `master`
- HEAD: `48d3837be53eac5adb7a2cf6f35d7137d28dd31f`
- Committed WP1.2 SHA: `48d3837` — `phase3c25: correct governed source ACL registration`
- Ahead of `origin/master` (`44d9ffa`); not pushed
- Dirty/untracked summary:
  - modified tracked: `crm-extension/tests/test_espo_php_namespace_contracts.py`, `crm-extension/tests/test_extension_skeleton.py`, `docs/adr/C24_INVARIANT_REGISTRY.md`
  - large untracked set: CommercialIntelligence module/client, WP1/WP1.3 tests and reports, runtime evidence, C22–C25 audit docs, Railway plan, `EspoCRM/`, temporary checksum artifact
- Concurrency assessment: no concurrent HEAD movement during this recheck; HEAD remains `48d3837`

## 3. Runtime Environment

- EspoCRM container image: `espocrm/espocrm:10.0.1`
- PHP: `8.4.23`
- Installed extension: `Chitu Prospecting Integration 1.9.13-alpha` (ID `6a6c6b2f09cf0dadc`, temporary/noncanonical package; installed: yes)
- Inactive older package listed: `1.3.1-alpha` (not installed)
- Container state at recheck:
  - `espocrm`: Up on `0.0.0.0:8090->80/tcp`
  - `espocrm-db`: Up (healthy)
  - `espocrm-cron`: Exited (137) — left stopped per task rules
  - `espocrm-daemon`: Exited (137) — left stopped per task rules
  - Railway staging containers: exited; not used
- Site reachability: `http://localhost:8090` → HTTP 200
- Repository vs runtime SHA-256 match for WP1/WP1.3 key files: YES (all compared paths matched)

## 4. Final Runtime Matrix

| Case | Expected | Actual | Verdict |
| --- | --- | --- | --- |
| A. Workspace authorized non-admin | 200; root + ReplySignal + PipelineMetric present; RevenueInsight absent; no leak | 200; types=`OpportunityCandidate,ReplySignal,PipelineMetric`; RI absent; no denied-name/sensitive leakage | PASS |
| B. Workspace root denied | safe 404; no candidate fields | HTTP 404; empty body | PASS |
| C. Workspace permission denied | 403 or safe rejection | HTTP 403; empty body | PASS |
| D. Portal | 401/403 safe rejection; no source data | HTTP 401; empty body | PASS |
| E. Governed source readable | 200; read-only payload; no mutation metadata | 200; designation=`Read-only governed source`; `ReplySignal`/`c25wp1signal00001`; 8 fields; no mutation metadata | PASS |
| F. Governed source denied | RevenueInsight 404; no leakage | HTTP 404; empty body; no name/status/stack leak | PASS |
| G. Admin control | 200 via same path if credential available | retained `smoke-test` API key → HTTP 401 for workspace and source | NOT TESTABLE FROM CURRENT STATE |

## 5. No-Write Check

Before GETs:

```text
opportunity_candidate=2
reply_signal=1
revenue_insight=1
pipeline_metric=1
note_all=250
note_root(OpportunityCandidate:c25wp1root0000001)=0
fixture identity/created_at snapshot captured
```

After GETs: identical counts and identical fixture identity/`created_at` snapshot.

These governed entities have no `modified_at` column; identity + `created_at` + note counts were used instead.

Verdict: PASS — GET matrix produced no row-count change and no new note/history for the test candidate.

## 6. Browser Evidence Integrity

All five WP1.3 durable screenshots exist, are non-empty, and open successfully:

| Path | Bytes | Open |
| --- | ---: | --- |
| `docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-desktop.png` | 87180 | OK |
| `docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-responsive.png` | 87180 | OK |
| `docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-escaped-script.png` | 87180 | OK |
| `docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-denied.png` | 37618 | OK |
| `docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-workspace-back.png` | 75024 | OK |

`docs/audit/PHASE3C25_WP1_3_GOVERNED_SOURCE_NAVIGATION_REPORT.md` references these exact paths. Desktop/responsive/escaped remain byte-identical by documented panel-width constraint; not a blocker. No recapture performed.

Earlier WP1 screenshots under `docs/audit/runtime-evidence/phase3c25-wp1/` remain historical and are not attributed to WP1.3.

## 7. Boundary Confirmation

Static and runtime confirmation for the CommercialIntelligence module:

- no persistence: no `Entities/`, `entityDefs/`, migrations — PASS
- no write path: no `saveEntity`/`createEntity`/`deleteEntity`; routes GET-only — PASS
- no lifecycle authority: no `transition(` / lifecycle service ownership — PASS
- no scoring/ranking authority: assembly remains read-model presentation — PASS
- no provider egress: no curl/guzzle/http client usage — PASS
- no credential access: no credential/token provider path — PASS
- native root and nested ACL: authorized assembly omits denied RI; denied source 404 — PASS
- portal denial: retained portal API → 401 empty — PASS
- read-only governed navigation: source detail 200 with designation; no mutation metadata — PASS
- no generic CRUD: no object/tab enabling in this recheck; source surface remains dedicated — PASS
- WP2/WP3 inertness: workspace placeholders remain upcoming labels only — PASS

All 15 CommercialIntelligence PHP files passed `php -l`.

## 8. Tests

Focused WP1 / WP1.1 / WP1.2 / WP1.3 + extension integrity:

```powershell
.\.venv-s01\Scripts\python.exe -m pytest `
  tests/test_phase3c25_wp1_workspace_foundation.py `
  tests/test_phase3c25_wp1_2_acl_correction.py `
  tests/test_phase3c25_wp1_3_governed_source_navigation.py `
  crm-extension/tests/test_espo_php_namespace_contracts.py `
  crm-extension/tests/test_extension_skeleton.py `
  -q -p no:cacheprovider
# 98 passed
```

C24 boundary regression:

```powershell
.\.venv-s01\Scripts\python.exe -m pytest `
  tests/test_phase3c24_wp1_reply_intelligence.py `
  tests/test_phase3c24_wp2_boundary_security.py `
  tests/test_phase3c24_wp2_candidate_acl.py `
  tests/test_phase3c24_wp2_candidate_entity.py `
  tests/test_phase3c24_wp2_lifecycle.py `
  tests/test_phase3c24_wp3_boundary_security.py `
  tests/test_phase3c24_wp3_entity_foundation.py `
  tests/test_phase3c24_wp3_guards.py `
  tests/test_phase3c24_wp3_metadata_acl.py `
  tests/test_phase3c24_wp3_services.py `
  -q -p no:cacheprovider
# 97 passed
```

Whitespace:

```powershell
git diff --check
# exit 0
```

Full suite (once):

```powershell
.\.venv-s01\Scripts\python.exe -m pytest -q -p no:cacheprovider
# 948 passed, 4 failed, 1594 subtests passed
```

## 9. Failure Classification

| Failure | Classification |
| --- | --- |
| C17 `test_global_i18n_has_en_zh_key_parity_and_c17_product_names` expects only three singular scopes | pre-existing |
| Release integrity archive entries differ vs current source tree | pre-existing (canonical archive stale; rebuild forbidden) |
| Release integrity archive missing current entity definitions | pre-existing |
| Release integrity archive missing current text/bytes including WP1/WP1.3 files | pre-existing |

No introduced failures. No environment-specific or inconclusive failures in the suite.

## 10. Commit Inventory

### Group A — WP1 Foundation

Untracked/modified foundation implementation and reports (final tree also embeds WP1.1 parser bounds):

```text
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Api/GetWorkspaceContext.php
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Context/ArtifactReferenceParser.php
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Context/CommercialContext.php
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Context/SourceArtifactReference.php
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/module.json
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/i18n/en_US/CommercialIntelligenceWorkspace.json
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/i18n/zh_CN/CommercialIntelligenceWorkspace.json
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/app/aclPortal.json
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/clientDefs/CommercialIntelligenceWorkspace.json
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/scopes/CommercialIntelligenceWorkspace.json
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/ContextAssemblyService.php
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/FreshnessPresenter.php
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/VisibilityInheritanceService.php
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/Adapters/C20ProvenanceReadAdapter.php
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/Adapters/C21IntelligenceReadAdapter.php
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/Adapters/C22ExecutionReadAdapter.php
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/Adapters/C23OptimizationReadAdapter.php
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/Adapters/C24RevenueReadAdapter.php
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/Adapters/CrmCoreAnchorReadAdapter.php
crm-extension/tests/test_espo_php_namespace_contracts.py
docs/PHASE3C25_WP1_IMPLEMENTATION_PLAN.md
docs/audit/PHASE3C25_WP1_VERIFICATION_REPORT.md
docs/audit/PHASE3C25_WP1_RUNTIME_VERIFICATION_REPORT.md
docs/audit/PHASE3C25_WP1_IMPLEMENTATION_PLAN_REVIEW.md
docs/audit/runtime-evidence/phase3c25-wp1/admin-workspace-d2.png
docs/audit/runtime-evidence/phase3c25-wp1/admin-workspace-responsive.png
```

Foundation file count above (implementation + tests/docs/evidence listed): 27 paths.

Shared files that currently hold WP1 Foundation + WP1.1 + WP1.3 final state (cannot be honestly split without rewriting intermediate content):

```text
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/routes.json
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/ProvenancePresenter.php
crm-extension/files/client/custom/src/controllers/commercial-intelligence-workspace.js
crm-extension/files/client/custom/src/views/commercial-intelligence/workspace.js
crm-extension/files/client/custom/res/templates/commercial-intelligence/workspace.tpl
crm-extension/tests/test_extension_skeleton.py
tests/test_phase3c25_wp1_workspace_foundation.py
```

Mark: `WP1 Foundation file containing WP1.1/WP1.3 final state`.

### Group B — WP1.1 Parser Hardening

No separate untracked parser-only file remains. Parser hardening final state lives in:

```text
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Context/ArtifactReferenceParser.php
tests/test_phase3c25_wp1_workspace_foundation.py
```

Mark both as: `WP1 Foundation file containing WP1.1 final state`.

### Group C — WP1.2 ACL (already committed in `48d3837`)

Do not stage or recommit:

```text
crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/app/acl.json
crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/scopes/OpportunityCandidate.json
crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/scopes/PipelineMetric.json
crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/scopes/ReplySignal.json
crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/scopes/RevenueInsight.json
docs/audit/PHASE3C25_WP1_2_ACL_CORRECTION_REPORT.md
tests/test_phase3c24_wp1_reply_intelligence.py
tests/test_phase3c24_wp2_candidate_acl.py
tests/test_phase3c24_wp3_entity_foundation.py
tests/test_phase3c24_wp3_metadata_acl.py
tests/test_phase3c25_wp1_2_acl_correction.py
```

Exact committed file count: 11.

### Group D — WP1.3 Navigation + durable evidence

Implementation / tests / report allowlist (12) plus evidence PNGs (5) = 17 paths:

```text
crm-extension/files/client/custom/res/templates/commercial-intelligence/source-detail.tpl
crm-extension/files/client/custom/res/templates/commercial-intelligence/workspace.tpl
crm-extension/files/client/custom/src/controllers/commercial-intelligence-workspace.js
crm-extension/files/client/custom/src/views/commercial-intelligence/source-detail.js
crm-extension/files/client/custom/src/views/commercial-intelligence/workspace.js
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Api/GetGovernedSourceDetail.php
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/routes.json
crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/ProvenancePresenter.php
crm-extension/tests/test_extension_skeleton.py
tests/test_phase3c25_wp1_3_governed_source_navigation.py
tests/test_phase3c25_wp1_workspace_foundation.py
docs/audit/PHASE3C25_WP1_3_GOVERNED_SOURCE_NAVIGATION_REPORT.md
docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-desktop.png
docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-responsive.png
docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-escaped-script.png
docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-denied.png
docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-workspace-back.png
```

Distinction:

- source implementation: GetGovernedSourceDetail, routes, ProvenancePresenter, controller, workspace/source client+templates
- tests: WP1.3 navigation test, foundation inventory alignment, skeleton inventory
- report: WP1.3 navigation report
- durable browser evidence: five PNGs

### Group E — Final runtime evidence/report reconciliation

New report (this file):

```text
docs/audit/PHASE3C25_WP1_FINAL_RUNTIME_RECHECK.md
```

Historical FAIL report retained unchanged:

```text
docs/audit/PHASE3C25_WP1_RUNTIME_VERIFICATION_REPORT.md
```

## 11. Exclusions

| Group / item | Reason |
| --- | --- |
| `docs/deployment/RAILWAY_C25_STAGING_PLAN.md` and Railway staging containers | unrelated / belongs to deploy track (`44d9ffa`) |
| `docs/adr/C24_INVARIANT_REGISTRY.md` | unrelated / belongs to another phase |
| `tmp/phase3c25-wp13-navigation-20260731.zip` and other temp ZIPs | temporary |
| `EspoCRM-Productiontmpphase3c25-wp12-acl-20260731.zip.sha256` | temporary checksum sidecar / malformed path artifact |
| `EspoCRM/` copied tree and p3c18 evidence | malformed path artifact / historical unrelated |
| pytest `__pycache__` / `.pyc` | generated |
| canonical `deployment/prospecting-extension-1.9.13-alpha.zip` | stale release ZIP; rebuild forbidden |
| C22/C23/C24 audit/charter docs not required by WP1 runtime commit | belongs to another phase |
| Broader C25 ADR/charter/foundation docs beyond WP1 reports | belongs to governance packaging, not remaining WP1 runtime commit unless separately authorized |
| Group C files already in `48d3837` | already committed |
| WP1.2 temporary package artifacts | temporary / already committed ACL result |
| Unrelated modified C24 registry | unrelated |

Do not delete any excluded file.

## 12. Final Recommendation

### Commit structure recommendation

Recommend **one combined remaining WP1 commit**, not a two-commit split.

Reason: shared untracked files (`routes.json`, `ProvenancePresenter.php`, workspace client/controller/template, foundation tests, skeleton inventory) already contain the final WP1.3 state. Staging a “foundation-only” commit would either omit a runnable surface or require inventing intermediate file versions that do not exist in the worktree. Group C remains already committed and must not be restaged.

Suggested single remaining commit message:

```text
phase3c25: add commercial intelligence workspace and governed source navigation
```

Exact staging allowlist for that combined remaining commit (explicit paths only; do not execute here):

```powershell
git add -- `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Api/GetWorkspaceContext.php `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Api/GetGovernedSourceDetail.php `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Context/ArtifactReferenceParser.php `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Context/CommercialContext.php `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Context/SourceArtifactReference.php `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/module.json `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/routes.json `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/i18n/en_US/CommercialIntelligenceWorkspace.json `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/i18n/zh_CN/CommercialIntelligenceWorkspace.json `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/app/aclPortal.json `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/clientDefs/CommercialIntelligenceWorkspace.json `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/scopes/CommercialIntelligenceWorkspace.json `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/ContextAssemblyService.php `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/FreshnessPresenter.php `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/ProvenancePresenter.php `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/VisibilityInheritanceService.php `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/Adapters/C20ProvenanceReadAdapter.php `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/Adapters/C21IntelligenceReadAdapter.php `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/Adapters/C22ExecutionReadAdapter.php `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/Adapters/C23OptimizationReadAdapter.php `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/Adapters/C24RevenueReadAdapter.php `
  crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/Adapters/CrmCoreAnchorReadAdapter.php `
  crm-extension/files/client/custom/src/controllers/commercial-intelligence-workspace.js `
  crm-extension/files/client/custom/src/views/commercial-intelligence/workspace.js `
  crm-extension/files/client/custom/src/views/commercial-intelligence/source-detail.js `
  crm-extension/files/client/custom/res/templates/commercial-intelligence/workspace.tpl `
  crm-extension/files/client/custom/res/templates/commercial-intelligence/source-detail.tpl `
  crm-extension/tests/test_espo_php_namespace_contracts.py `
  crm-extension/tests/test_extension_skeleton.py `
  tests/test_phase3c25_wp1_workspace_foundation.py `
  tests/test_phase3c25_wp1_3_governed_source_navigation.py `
  docs/PHASE3C25_WP1_IMPLEMENTATION_PLAN.md `
  docs/audit/PHASE3C25_WP1_VERIFICATION_REPORT.md `
  docs/audit/PHASE3C25_WP1_RUNTIME_VERIFICATION_REPORT.md `
  docs/audit/PHASE3C25_WP1_IMPLEMENTATION_PLAN_REVIEW.md `
  docs/audit/PHASE3C25_WP1_3_GOVERNED_SOURCE_NAVIGATION_REPORT.md `
  docs/audit/PHASE3C25_WP1_FINAL_RUNTIME_RECHECK.md `
  docs/audit/runtime-evidence/phase3c25-wp1/admin-workspace-d2.png `
  docs/audit/runtime-evidence/phase3c25-wp1/admin-workspace-responsive.png `
  docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-desktop.png `
  docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-responsive.png `
  docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-escaped-script.png `
  docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-denied.png `
  docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-workspace-back.png
```

Exact staged-path count in the allowlist above: **44**.

Post-staging verification (do not execute in this task unless a later commit task authorizes it):

```powershell
git diff --cached --name-status
git diff --cached --stat
git diff --cached --check

$expected = @(
  # paste the same 44 paths
)
$staged = git diff --cached --name-only
$extra = $staged | Where-Object { $_ -notin $expected }
$missing = $expected | Where-Object { $_ -notin $staged }
if ($extra -or $missing) { throw "Allowlist mismatch" } else { "Allowlist match: $($staged.Count) files" }
```

Optional historical two-commit structure remains conceptually documented in Groups A/D, but is **not recommended** for actual staging because shared files already contain WP1.3 final state.

### Gate summary

- final runtime gate cleared: YES
- implementation correction remains: NO
- ready for exact staging: YES
- ready for freeze preparation: YES
- ready for formal freeze: NO

Formal freeze remains disallowed until the remaining commit is created, pushed, and independently reviewed.
