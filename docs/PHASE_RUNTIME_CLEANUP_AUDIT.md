# Runtime Cleanup Audit

**Date:** 2026-07-14  
**Scope:** Freeze-prep, read-only hygiene audit of the local Docker/EspoCRM runtime and `D:\EspoCRM-Production`.  
**Changes made:** None. No code, database records, cache, packages, or repository files were deleted or modified.

## Verdict

**NOT READY FOR FREEZE - cleanup/reconciliation required.**

The local EspoCRM runtime is healthy and is running the expected installed extension release (`1.9.5-alpha`). Its compiled cache is not accumulating stale metadata. However, the installed dashboard metadata differs from the current workspace in every sampled Phase U04 dashlet. The repository also retains a substantial, ignored `temp/` test-output set and a full ladder of historical deployment packages.

## 1. Docker and EspoCRM runtime

| Check | Result | Evidence |
| --- | --- | --- |
| Container health | PASS | `espocrm` and `espocrm-db` were healthy; `espocrm-daemon` was healthy; `espocrm-cron` was running. The CRM is exposed on local port 8080. |
| Running image | PASS | EspoCRM application, cron, and daemon containers use `espocrm/espocrm:10.0.1`; the database uses `mariadb:11.4`. |
| Cache status | PASS | `data/cache` contained only the current `application/cronLastRunTime.php` (written 2026-07-14 06:52). No cached metadata tree or stale generated metadata was present. |
| Extension loading | PASS | `custom/Espo/Modules/Prospecting` is present in the runtime with entity metadata, layouts, client definitions, dashboard dashlets, and language resources. |
| Installed extension version | PASS | The newest runtime upload archive (`data/upload/extensions/6a54fee0412d79694z`) has SHA-256 prefix `927e0bc6` and suffix `c1c7e4`, matching `deployment/prospecting-extension-1.9.5-alpha.zip`; its manifest is `1.9.5-alpha`. |
| Metadata alignment | FAIL | The seven sampled Phase U04 dashlet metadata files have different hashes in the runtime and current workspace; see below. |

### Workspace/runtime metadata drift

The runtime contains the installed `1.9.5-alpha` archive, but the current workspace contains later/different dashlet definitions. This is a deployment-state mismatch, not a dirty cache condition.

| Dashlet metadata | Runtime hash prefix | Workspace hash prefix | Match |
| --- | --- | --- | --- |
| `AcquisitionDiscoveryJobs.json` | `b8d25c10830f` | `d063955c7818` | No |
| `AcquisitionJobsWaiting.json` | `9777bf89abc8` | `e97ea9bd8e25` | No |
| `AcquisitionJobsRunning.json` | `397cc70d5969` | `170be6176343` | No |
| `AcquisitionJobsCompleted.json` | `1c58c7b80daf` | `905d3f363a1f` | No |
| `AcquisitionJobsFailed.json` | `f7a72e0bea12` | `d33d2564ae73` | No |
| `AcquisitionLeadPool.json` | `f68d249ef069` | `10a588be68b6` | No |
| `AcquisitionResearchQueue.json` | `54eb65c9ae14` | `d7090b08076f` | No |

The runtime upload directory also retains two older archives alongside the latest package:

- `1.3.1-alpha` archive (20,262 bytes, 2026-07-12)
- An older `1.4.0-alpha`-era archive (31,006 bytes, 2026-07-12)
- Current `1.9.5-alpha` archive (104,433 bytes, 2026-07-13)

They do not prevent the currently loaded custom module from existing, but they are stale deployment artifacts and should be handled by an explicitly approved retention/cleanup operation.

## 2. Repository hygiene

### `temp/` artifacts

`temp/` is ignored by Git and contains **202 files / 1,605,220 bytes**:

- 162 `.log` test outputs
- 31 `.json` regression/test-result artifacts
- 5 top-level C06 test transcript `.txt` files
- 4 top-level PHP utility/debug scripts: `check_clientdefs.php`, `_debug_formula.php`, `_verify_formula.php`, and `_verify_metadata.php`
- one dashboard-preferences snapshot: `dashboard_preferences_before_20260714T000000Z.json`

The file names show repeated test executions on 2026-07-13 and 2026-07-14. These files are not part of a clean freeze baseline. No content was inspected beyond file names, types, sizes, and timestamps, and nothing was removed.

### Other generated artifacts

- Git-ignore inspection shows Python `__pycache__/` directories under `chitu-connector`, `crm-extension/tests`, and `deployment/validation`.
- No debug-script or `.log`/`.tmp` candidates were found outside `temp/` by the repository filename scan.
- The worktree also has pre-existing unrelated modified/untracked content. This audit did not alter or attempt to reconcile it; freeze preparation needs a separately defined source baseline.

## 3. Deployment package hygiene

`deployment/` contains **19** EspoCRM extension ZIP packages, covering `1.0.0-alpha` through `1.9.5-alpha`, totaling **1,086,330 bytes**.

| Check | Result | Evidence |
| --- | --- | --- |
| Exact duplicate ZIP contents | PASS | SHA-256 comparison found 19 unique package hashes for 19 ZIP files. |
| Historical-package retention | FINDING | 18 packages predate the current `1.9.5-alpha` package. They are version-history artifacts, not byte-for-byte duplicates. |
| Current runtime package traceability | PASS | Runtime archive hash equals local `prospecting-extension-1.9.5-alpha.zip`. |
| Checksum coverage | FINDING | Only six packages (`1.6.0` through `1.9.0`, with gaps before `1.6.0`) have `.sha256` sidecars. Releases `1.9.1` through `1.9.5`, including the current release, lack a sidecar file. |

## Freeze gate actions (not executed)

1. Decide the intended freeze source: either package/install the current workspace dashlet metadata, or make the workspace match the installed `1.9.5-alpha` runtime.
2. After that decision, run the approved EspoCRM extension installation/cache-rebuild workflow and re-check the seven metadata hashes.
3. Define a retention policy for `temp/`, runtime upload archives, and the 18 historical deployment ZIPs; execute cleanup only under a separate approved change.
4. Define a source-control baseline that excludes unrelated untracked work before freeze.
5. Generate and retain a checksum sidecar for the selected freeze package.

## Audit boundaries

This was a read-only audit. Docker checks used status, directory listing, hash, and manifest-read operations only. No cache clear, extension install/uninstall, database query/update, source edit, package rebuild, staging, or deletion was performed.
