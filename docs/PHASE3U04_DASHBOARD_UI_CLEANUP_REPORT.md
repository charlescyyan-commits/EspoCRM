# Phase U04 — Prospecting Dashboard UI Cleanup Report

**Date:** 2026-07-14
**Status:** PASS — source metadata and extension static tests

## Scope

This phase changes only native EspoCRM presentation metadata. No PHP backend,
connector, Lead workflow, evidence logic, ACL metadata, entity definition, or
runtime configuration was changed.

## Dashboard: Prospecting Operations

The existing `Prospecting Operations` provisioning layout is a four-column
native EspoCRM grid. Its summary and recent-discovery dashlets occupy the full
first-row width, the four Lead Intelligence dashlets are aligned as one-column
cards, and the two lower queue dashlets occupy matching two-column cards. It
was inspected but not edited because provisioning PHP is outside U04 scope.

The record-list dashlets below previously relied on whichever default list
columns EspoCRM selected. Each now declares a compact native `expandedLayout`,
so fields align in two columns and match the dashlet purpose.

| Dashlet | Display fields |
| --- | --- |
| Search Strategies | Name, Status; Product, Search Jobs Created |
| Search Jobs | Name, Status; Strategy, Result Count |
| Queued Jobs | Name, Strategy; Provider, Created At |
| Running Jobs | Name, Strategy; Provider, Started At |
| Completed Jobs | Name, Strategy; Result Count, Completed At |
| Failed Jobs | Name, Strategy; Failure Reason, Created At |
| Prospect Pool | Company, Website; Country, Research Status |
| Research Queue | Company, Website; Country, Research Status |

All use EspoCRM's built-in `views/dashlets/abstract/record-list`; no React,
SPA, or custom dashboard component was introduced.

## Entity UI Review

| Surface | Result |
| --- | --- |
| SearchStrategy | Native Record controller, strategy labels, status filters, list/detail layouts, and `Generate Search Jobs` action metadata are present. |
| SearchJob | Native list/detail layouts use business labels (Search Job, Provider, Result Count, Failure Reason); internal `queryFingerprint` stays out of the standard sales layout. |
| ProspectPool | Native list/detail layouts show Company, Website, Country, Provider, and Research Status first; pipeline details remain in the record detail view. |
| Lead Intelligence | Existing native Lead layout, labels, relationship panels, Opportunity Proposal display contract, and CRM-owned sales fields remain unchanged. |

## Validation

1. JSON field-reference audit passed: every U04 dashlet field exists in its
   declared entity definition.
2. Extension static suite passed:

   ```text
   C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe \
     -m unittest discover -s crm-extension/tests -p test_*.py -v

   Ran 57 tests — OK
   ```

3. The suite includes the C01 acquisition workspace, C02 SearchStrategy, and
   C06 Prospecting UI contract checks. U04 did not change any C01-C10 source
   boundary: no connector, backend, entity-definition, workflow, evidence,
   or ACL file was edited.

## Files Changed by U04

- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/dashlets/AcquisitionSearchStrategies.json`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/dashlets/AcquisitionDiscoveryJobs.json`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/dashlets/AcquisitionJobsWaiting.json`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/dashlets/AcquisitionJobsRunning.json`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/dashlets/AcquisitionJobsCompleted.json`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/dashlets/AcquisitionJobsFailed.json`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/dashlets/AcquisitionLeadPool.json`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/dashlets/AcquisitionResearchQueue.json`
- `docs/PHASE3U04_DASHBOARD_UI_CLEANUP_REPORT.md`

Browser acceptance remains deferred because U04 is metadata-only and no
extension installation, cache rebuild, or shared-runtime mutation was part of
this task.
