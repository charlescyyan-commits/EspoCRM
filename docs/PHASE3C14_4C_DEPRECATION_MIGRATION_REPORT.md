# Phase3C14.4C Phase 1 Deprecation Migration Report

## Result

**PASS WITH RISKS**

Phase 1 adds an explicit deprecation boundary around the two legacy direct
`peEmail*` writers without deleting them or changing their guarded behavior.
The C14.3 CRM bridge remains the preferred internal execution-submission path.

## Pre-Modification Inspection and Migration Plan

The C14.4B reachability audit found zero production callers for both writers.
Their only repository callers are tests, a guarded manual synthetic harness,
and public package re-exports:

| Legacy writer | Public entry point | Repository callers | Phase 1 decision |
|---|---|---|---|
| W-CON-01 | `EmailLifecycleSyncService.sync()` | Compatibility tests and `email_lifecycle_sync.py` test harness. | Keep functional; warn at invocation; retain legacy-specific guard tests. |
| W-CON-02 | `CampaignProjectionAdapter.project()` | C09 compatibility/acceptance tests. | Keep functional; warn at invocation; retain draft-projection compatibility tests. |

No legacy-specific test can be replaced one-for-one by the bridge: W-CON-01
tests guarded direct-summary compatibility, and W-CON-02 tests C09 draft
metadata. Replacing either would remove coverage of the deprecated behavior.
Instead, those tests are explicitly classified as compatibility tests, while a
new connector-local test uses the C14.3 CRM bridge adapter for the applicable
execution-submission path.

## Changes

| File | Change |
|---|---|
| `chitu-connector/chitu_connector/espocrm_sync/email_lifecycle.py` | Marked W-CON-01 as deprecated and emits `DeprecationWarning` from public `sync()`. Message directs callers to the C14.3 CRM SendExecution bridge path. |
| `chitu-connector/chitu_connector/espocrm_sync/campaign_projection.py` | Marked W-CON-02 as deprecated and emits `DeprecationWarning` from public `project()`. Message directs execution submission to the C14.3 bridge where applicable. |
| `chitu-connector/tests/test_espocrm_email_lifecycle.py` | Classified as deprecated compatibility coverage and explicitly asserts the W-CON-01 warning. |
| `chitu-connector/tests/test_phase3c09_campaign_projection.py` | Classified as deprecated compatibility coverage and explicitly asserts the W-CON-02 warning. |
| `chitu-connector/tests/test_phase3c14_4c_deprecation_migration.py` | Added a connector-local C14.3 bridge-preference test that submits a synthetic approved `SendExecution` without any legacy warning. |
| `docs/PHASE3C14_4C_DEPRECATION_MIGRATION_REPORT.md` | Added this report. |

Public re-exports in `chitu_connector.espocrm_sync.__init__` remain unchanged.
Files remain present and both writers still execute their C14.4A rank,
timestamp, terminal, and null guards.

## Migration Behavior

```text
Legacy direct peEmail* call
  -> DeprecationWarning
  -> existing C14.4A guarded compatibility behavior

Preferred execution submission
  -> C14.3 CrmSendExecutionBridgeAdapter
  -> safe BridgeRequest
  -> no legacy writer or deprecation warning
```

The warning is emitted only when a legacy write entry point is invoked; import
and package re-export remain non-breaking during the observation period.

## Tests

| Suite | Result |
|---|---|
| C14.4C bridge-preference test | PASS — 1 test |
| W-CON-01 targeted compatibility tests | PASS — 3 tests; expected deprecation warning observed |
| W-CON-02 targeted compatibility tests | PASS — 3 tests; expected deprecation warning observed |
| C14.3 B-2/B-4 bridge tests | PASS — 14 tests |
| C14.3 A/B-1/B-2/B-3/B-4/C/D focused tests | PASS — 47 tests |
| Full connector regression | PASS — 279 tests; expected legacy deprecation warnings observed only at compatibility call sites |
| Full CRM extension suite | PASS — 75 tests |

All tests use synthetic in-memory records, fixtures, or temporary SQLite
stores. No CRM request, external call, Provider call, Queue processing, or
email send occurred.

## Scope Confirmation

| Question | Result |
|---|---|
| Were legacy files deleted? | No. |
| Are legacy writers still functional? | Yes, subject to their existing C14.4A guards. |
| Were projection service or CRM bridge contract modified? | No. |
| Were Worker, Queue, Provider, Brevo, or retry modified? | No. |
| Was a CRM record written or an external call made? | No. |

## Risks and Next Step

The public exports remain available, so external consumers will receive a
runtime warning only when invoking a legacy writer. The observation window is
still required before removal. The direct-writer compatibility guard also
remains read-then-write rather than atomic.

Next: **C14.4C Phase 2 observation**. Monitor downstream deprecation reports,
confirm the C14.3 bridge covers required execution transitions, and retain the
legacy compatibility tests. Only after that evidence should a separately
approved Option A removal phase remove exports, files, and legacy-only tests.
