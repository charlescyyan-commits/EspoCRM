# Phase3C25 WP1.3 Governed Source Navigation Report

## 1. Executive Verdict

PASS — governed source navigation works safely

The Commercial Intelligence workspace now opens hidden C20–C24 governed
records through one bounded, GET-only evidence-review surface. The route
requires both Commercial Intelligence workspace permission and native Espo
entity read permission. It exposes no generic governed-entity CRUD surface.

## 2. Preflight

- Branch: `master`
- HEAD before and after implementation:
  `48d3837be53eac5adb7a2cf6f35d7137d28dd31f`
  (`phase3c25: correct governed source ACL registration`)
- Concurrent HEAD movement: none
- Worktree: already heavily dirty/untracked with unrelated C22–C25,
  Railway, runtime-evidence, `EspoCRM/`, temporary checksum, and audit files;
  none was cleaned, reset, stashed, restored, or deleted
- Installed extension before implementation: active
  `Chitu Prospecting Integration 1.9.13-alpha`, ID
  `6a6c4fb90c4b9a372`; installed module, route, and ACL hashes matched the
  source tree
- Installed extension after runtime validation: active
  `Chitu Prospecting Integration 1.9.13-alpha`, ID
  `6a6c6b2f09cf0dadc`
- Temporary noncanonical package:
  `D:\EspoCRM-Production\tmp\phase3c25-wp13-navigation-20260731.zip`
- Temporary package SHA-256:
  `4F2A8F33FC7BBEF45A484A810329758EE8A73DD29C2238E7A643EE2416854B9B`

Prior link behavior was reproduced before editing:

- the authorized API workspace returned `200`;
- generated C24 links were:
  `#OpportunityCandidate/view/c25wp1root0000001`,
  `#ReplySignal/view/c25wp1signal00001`,
  `#PipelineMetric/view/c25wp1metric00001`, and, for admin,
  `#RevenueInsight/view/c25wp1insight0001`;
- all four generic record APIs returned `404`;
- all four browser hashes rendered Espo's 404 page;
- the browser console reported missing
  `opportunity-candidate.js`, `reply-signal.js`,
  `pipeline-metric.js`, and `revenue-insight.js` controllers.

## 3. Navigation Design

### Route model

Hidden governed records use:

```text
#CommercialIntelligenceWorkspace/source/entityType=<type>&entityId=<id>&candidateId=<anchor>
GET /api/v1/CommercialIntelligence/source/:entityType/:entityId
```

The existing `CommercialIntelligenceWorkspace` controller dispatches the
`source` action to a dedicated source-detail view. The server exposes exactly
one additional GET route and no sibling write route.

### Supported entity allowlist

The server, source-detail client, workspace link presenter, and focused tests
are bound to the same 16 governed source types:

- C20: `AIJob`, `AIRequestLog`
- C21: `ResearchEvidence`, `AIQualificationInsight`, `HumanFeedback`
- C22: `ProspectCandidate`, `ProspectRun`, `ExecutionLedger`, `ReplyEvent`
- C23: `OptimizationInsight`, `PerformanceMetric`,
  `FeedbackLearningObservation`
- C24: `OpportunityCandidate`, `ReplySignal`, `RevenueInsight`,
  `PipelineMetric`

Arbitrary types and malformed IDs fail closed with `404` before repository
lookup. `Account`, `Contact`, and `Opportunity` continue to use their native
Espo record routes. Any other source type is rendered as non-clickable
provenance text.

### ACL path

The API action applies checks in this order:

1. `VisibilityInheritanceService::assertWorkspaceAccess()`;
2. exact governed entity-type and alphanumeric 8–36 character ID validation;
3. `EntityManager::getEntity`;
4. `VisibilityInheritanceService::canReadSource`;
5. native `Acl::checkEntityRead`.

Missing and unreadable records both return `404` without record fields.

### Workspace permission requirement

Workspace permission remains mandatory in addition to source read ACL. A
source-readable user without `CommercialIntelligenceWorkspace` permission
receives `403` before type or record resolution.

### Portal behavior

Portal access remains denied by `assertWorkspaceAccess`. A real portal
session's direct source URL returned `403`.

### CRM Core and unsupported handling

Safe CRM Core references keep native routes. Hidden C20–C24 records use the
governed surface. Unsupported types receive no anchor, avoiding broken links
and arbitrary client-supplied entity routing.

## 4. Files Changed

- `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Api/GetGovernedSourceDetail.php`
  - closed entity/field registry, workspace gate, native source read check,
    safe not-found behavior, and scalar-only presentation
  - installed in the validated runtime
- `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/routes.json`
  - adds the single GET-only source route
  - installed in the validated runtime
- `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/ProvenancePresenter.php`
  - emits governed hashes for C20–C24, native hashes for CRM Core, and no
    route for unsupported types
  - installed in the validated runtime
- `crm-extension/files/client/custom/src/controllers/commercial-intelligence-workspace.js`
  - dispatches the bounded `source` action
  - installed in the validated runtime
- `crm-extension/files/client/custom/src/views/commercial-intelligence/workspace.js`
  - validates and classifies governed, CRM Core, and unsupported references
  - installed in the validated runtime
- `crm-extension/files/client/custom/res/templates/commercial-intelligence/workspace.tpl`
  - renders a link only when a safe navigation target exists
  - installed in the validated runtime
- `crm-extension/files/client/custom/src/views/commercial-intelligence/source-detail.js`
  - allowlisted GET-only source loader and safe workspace back route
  - installed in the validated runtime
- `crm-extension/files/client/custom/res/templates/commercial-intelligence/source-detail.tpl`
  - escaped read-only evidence rendering, D2/truth markers, and no mutation
    controls
  - installed in the validated runtime
- `tests/test_phase3c25_wp1_3_governed_source_navigation.py`
  - 12 focused navigation, ACL, route, mutation, escaping, and D2 tests
  - host test artifact only
- `tests/test_phase3c25_wp1_workspace_foundation.py`
  - aligns the WP1 route/provenance inventory with the bounded WP1.3 surface
  - host test artifact only
- `crm-extension/tests/test_extension_skeleton.py`
  - adds the new read-only API action to the exact extension inventory
  - host test artifact only
- `docs/audit/PHASE3C25_WP1_3_GOVERNED_SOURCE_NAVIGATION_REPORT.md`
  - this report
  - host documentation only

## 5. Runtime Matrix

- Readable governed source:
  - authorized `OpportunityCandidate`: `200`, 6 bounded review fields
  - authorized `ReplySignal`: `200`
  - authorized `PipelineMetric`: `200`
- Unreadable governed source:
  - authorized user's denied `RevenueInsight`: `404`
  - browser displayed only “unavailable or not visible”; no record fields
- Workspace denied, source otherwise readable:
  - `403` before source resolution
- Portal:
  - authenticated portal direct route: `403`
- Admin:
  - the same source route rendered the `RevenueInsight` record with `200`;
    no special route or rendering path exists
- Unsupported source:
  - direct `Account` injection into the governed API: `404`
  - unsupported workspace references are non-clickable

## 6. Mutation Boundary

- No create route: confirmed
- No edit route: confirmed
- No delete route: confirmed
- No mass action: confirmed
- No import/export control: confirmed
- No lifecycle or workflow action: confirmed
- No generic list/tab exposure: confirmed
- C24 scopes remain `object: false`, `tab: false`, and
  `aclActionList: ["read"]`
- POST to the source route returned `405`
- Browser source-detail traffic contained only GET requests

## 7. Browser Evidence

Durable browser screenshots were captured in a follow-up evidence-only task
after the original background runner failed to resume with
`OPENSSL_internal:BAD_DECRYPT`. The runner error affected result recovery
only. No implementation, runtime installation, ACL behavior or test result
changed.

Evidence directory:

```text
docs/audit/runtime-evidence/phase3c25-wp1-3/
```

### Screenshots

- `docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-desktop.png`
  - Readable `ReplySignal` `c25wp1signal00001` governed source page.
  - Shows read-only / truth-boundary badges, entity type, record ID,
    evidence fields, back link, and no Edit/Save/Delete/lifecycle controls.
  - Also proves script-like name escaping (see below).
- `docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-responsive.png`
  - Same governed source page captured at the available browser-panel
    viewport (616×925). The panel remained mobile-narrow throughout; a
    distinct wider desktop plane was not available from the retained
    browser host, so this file is byte-identical to the desktop capture
    and documents the responsive/narrow layout of the same surface.
- `docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-escaped-script.png`
  - Same durable image as the desktop capture. Kept as an explicit alias
    because the desktop screenshot already shows
    `<script>window.C25_XSS=true</script>` rendered literally in both the
    heading and the Name evidence field.
- `docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-denied.png`
  - Authorized user’s denied `RevenueInsight` direct governed-source route.
  - Shows safe “Not found” toast plus
    “unavailable or is not visible to you”; no record name, fields,
    provenance, timestamps, stack trace, or mutation controls.
- `docs/audit/runtime-evidence/phase3c25-wp1-3/governed-source-workspace-back.png`
  - Back link restored
    `#CommercialIntelligenceWorkspace/view/c25wp1root0000001`.
  - Workspace shows D2 “AI / Assembled” designation, C24 revenue evidence,
    boundary divider, upcoming WP2/WP3 slots, and no mutation controls.
  - Escaped ReplySignal script-like name remains literal in the workspace
    list.

### Capture checks during evidence recovery

```text
Console errors: 0
Navigation write requests: 0
Back navigation: PASS
Escaping: PASS
```

- Authorized workspace rendered the three readable C24 sources; denied
  `RevenueInsight` remained omitted.
- Clicking `ReplySignal` resolved to:

```text
#CommercialIntelligenceWorkspace/source/entityType=ReplySignal&entityId=c25wp1signal00001&candidateId=c25wp1root0000001
```

- Source XHR:
  `GET /api/v1/CommercialIntelligence/source/ReplySignal/c25wp1signal00001`
  returned `200`.
- Denied source XHR:
  `GET /api/v1/CommercialIntelligence/source/RevenueInsight/c25wp1insight0001`
  returned `404` with no field leakage.
- Navigation traffic observed during capture was GET-only (source detail,
  workspace reload, controller/view/template assets, and normal Espo
  notification polling). No POST, PUT, PATCH or DELETE occurred.
- The page displayed “Read-only governed source” and
  “Source evidence — not assembled CRM truth”.
- No save, edit, delete, dropdown mutation, mass action, or lifecycle control
  appeared.
- The script-like name
  `<script>window.C25_XSS=true</script>` rendered as literal text in both the
  workspace and source-detail page.
- The back link restored
  `#CommercialIntelligenceWorkspace/view/c25wp1root0000001`.
- The readable browser tab produced no application console errors (only
  CursorBrowser native-dialog harness warnings).
- Portal denial produced the expected server-side rejection only and was not
  re-probed in this evidence-only follow-up.

Evidence-only files added by the recovery task (not part of the original
WP1.3 implementation allowlist): the five PNGs under
`docs/audit/runtime-evidence/phase3c25-wp1-3/` and this Browser Evidence
section update.

## 8. Tests

Commands and results:

```powershell
.\.venv-s01\Scripts\python.exe -m pytest `
  tests/test_phase3c25_wp1_3_governed_source_navigation.py `
  -q -p no:cacheprovider
# 12 passed

.\.venv-s01\Scripts\python.exe -m pytest `
  tests/test_phase3c25_wp1_3_governed_source_navigation.py `
  tests/test_phase3c25_wp1_workspace_foundation.py `
  tests/test_phase3c25_wp1_2_acl_correction.py `
  crm-extension/tests/test_espo_php_namespace_contracts.py `
  crm-extension/tests/test_extension_skeleton.py `
  -q -p no:cacheprovider
# 98 passed

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

docker exec espocrm php -l /tmp/GetGovernedSourceDetail.php
# no syntax errors

git diff --check
# exit 0, no output

.\.venv-s01\Scripts\python.exe -m pytest -q -p no:cacheprovider
# 948 passed, 4 failed, 1594 subtests passed
```

The temporary package builder and `--check` both returned the same SHA-256
listed in the preflight section.

## 9. Full-Suite Classification

Four failures remain, all pre-existing and not introduced by WP1.3:

1. C17 Chinese global i18n test expects the whole singular-scope map to
   contain only three C17 entries, but later valid phases added entries.
2. The canonical `1.9.13-alpha` release archive does not match the current
   source tree.
3. The canonical archive lacks later entity definitions.
4. The canonical archive lacks later canonical text files/bytes, now
   including the WP1.3 files.

This task explicitly forbids rebuilding the canonical archive. The
noncanonical runtime package passed its own integrity check.

## 10. Git Hygiene

Exact WP1.3 file allowlist:

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
```

Excluded: Railway files, canonical archive, temporary package/checksum,
runtime screenshots, unrelated C25/C24 documents, `EspoCRM/`, prior untouched
WP1 files, and all other dirty/untracked material.

No commit, push, tag, stash, reset, clean, restore, or freeze operation was
performed.

## 11. Remaining Work

There is no remaining WP1.3 implementation blocker. Only an independent final
runtime recheck and subsequently authorized freeze preparation remain.
Freeze preparation was not performed by this task.

## 12. Final Recommendation

- governed source navigation corrected: YES
- read ACL preserved: YES
- mutation boundary preserved: YES
- portal blocked: YES
- ready for final runtime recheck: YES
- ready for freeze preparation: NO
