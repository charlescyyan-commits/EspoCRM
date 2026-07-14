# Phase G03.7 - Extension Regression Gate Alignment Report

**Date:** 2026-07-14
**Result:** **PASS**

## Scope and evidence

The failing baseline was tag `v1.9.5-alpha` at
`d004397b8c8a28baa4cdc33415899860f127c1f3`. Its clean gate had eight failures
in the Extension suite because `crm-extension/tests/test_extension_skeleton.py`
still encoded earlier release assumptions. Production metadata, runtime code,
ACL behavior, C09/C10/C10.6 source, the release tag, and the release artifact
were not modified.

The eight failure-related assertion updates already present in the working tree
were reviewed against the tagged source and retained. No bypass, skip, or
conditional test behavior was added.

## Assertion alignment record

### 1. `test_manifest_json_valid`

- **Before:** asserted `manifest["version"] == "1.8.0-alpha"` and the former
  feedback/acquisition-workspace description.
- **After:** asserts `"1.9.5-alpha"` and the current deterministic acquisition
  strategy description.
- **Reason:** the tagged `crm-extension/manifest.json` declares `1.9.5-alpha`
  with that current description; the assertion must validate the package that
  is actually released.

### 2. `test_contract_field_consistency`

- **Before:** mapped only `claim_type` and asserted that engine
  `evidence_type` must not appear in ResearchEvidence properties.
- **After:** maps `evidence_type` to `peEvidenceType` and asserts that the
  optional evidence-format classification is present.
- **Reason:** the tagged ResearchEvidence metadata already contains
  `peEvidenceType`; it is an approved optional V1 pass-through and does not
  change required sync fields or runtime behavior.

### 3. `test_only_standard_research_evidence_php_shells_exist`

- **Before:** the exact PHP allow-list omitted the tagged SearchStrategy entity,
  controller, job-generation API, services, and four SearchStrategy filters.
- **After:** the exact allow-list includes those existing files and asserts the
  four-filter SearchStrategy inventory exactly.
- **Reason:** current acquisition strategy metadata requires this bounded PHP
  inventory; keeping the exact set still rejects arbitrary future PHP files.

### 4. `test_phase3b03_connector_routes_and_proposal_model`

- **Before:** expected the exact route set without
  `/Prospecting/search-strategy/generate-jobs`.
- **After:** includes the existing `PostGenerateSearchStrategyJobs` route in
  the exact expected set.
- **Reason:** the tagged routes metadata legitimately includes the approved
  acquisition-job generation endpoint; the connector proposal route assertions
  remain unchanged.

### 5. `test_phase3b06_prospecting_workspace_ui`

- **Before:** asserted manifest version `1.8.0-alpha`.
- **After:** asserts manifest version `1.9.5-alpha`.
- **Reason:** the UI metadata tested by this method is packaged under the
  tagged release version, not the obsolete 1.8 baseline.

### 6. `test_phase3b07_operations_metadata`

- **Before:** asserted only the earlier operations-dashboard markers and
  manifest version `1.8.0-alpha`.
- **After:** also asserts the existing ProspectingSummary and
  ProspectingRecentDiscovery dashboard markers, and version `1.9.5-alpha`.
- **Reason:** current dashboard provisioning includes those approved native
  dashlets; the test now preserves their intended presence without changing
  provisioning behavior.

### 7. `test_phase3c01_acquisition_workspace_foundation`

- **Before:** expected the earlier SearchJob fields, `WAITING` lifecycle,
  shorter filter inventories, and the former acquisition dashboard inventory;
  it also asserted `1.8.0-alpha`.
- **After:** asserts the tagged QUEUED lifecycle, product/priority/fingerprint
  fields, approved SearchJob and ProspectPool filters, current dashlets, and
  version `1.9.5-alpha`.
- **Reason:** the current metadata is the approved acquisition-workspace state.
  The added assertions validate the exact existing inventory and preserve the
  single module authority; no metadata was changed to satisfy the test.

### 8. `test_phase3c02_1_acquisition_acl_provisioning`

- **Before:** asserted manifest version `1.9.0-alpha`.
- **After:** asserts manifest version `1.9.5-alpha`.
- **Reason:** ACL provisioning behavior and policy assertions are unchanged;
  only the stale package-version expectation was corrected.

## Preserved out-of-scope test content

The pre-existing working-tree diff also contains
`test_phase3c02_search_strategy_discovery_jobs`. It was not one of the eight
failed assertions and was not authored or modified by this phase. It was
preserved to avoid overwriting unrelated user work; its passing result is
included in the Extension suite total below.

## Validation

Tests ran against an isolated export of the tagged source commit with only the
reviewed `test_extension_skeleton.py` overlay. The current untracked gate runner
and root-level tests were supplied as external test tooling; no main-workspace
runtime or metadata source was used.

| Check | Command | Timestamp (UTC) | Result |
|---|---|---|---|
| Extension suite | `python -m unittest discover -s crm-extension/tests -p test_*.py -v` | 2026-07-14T08:43:26.6188457Z to 2026-07-14T08:43:27.0802016Z | PASS - 65/65 |
| Full Regression Gate | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/testing/run-regression-gate.ps1 -PythonExecutable <bundled-python>` | 2026-07-14T08:43:27.0802016Z to 2026-07-14T08:43:31.2231522Z | PASS - 7/7, 382/382 tests |

Required gate suites: Extension 65/65, Connector 270/270, Worker 31/31,
Static 2/2, Runtime 11/11, Baseline 3/3, and Runner integrity PASS.

No `v1.9.5-alpha` tag was deleted or changed. No release artifact was modified.
No C11 work was started.
