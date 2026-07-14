# Phase R01 — Final Runtime Alignment Report

**Date:** 2026-07-14  
**Mode:** read-only verification. No code, connector, Evidence logic, ACL, cache, runtime configuration, package, or test data was changed.  
**Conclusion:** **FAIL** — C10.6 Evidence metadata and PHP writer are aligned, but the runtime is not completely aligned with the current workspace UI metadata. The available deployment package also cannot serve as a reproducible final baseline.

## Executive result

| Verification | Result | Evidence |
|---|---|---|
| Workspace/runtime extension version | PASS | Workspace `crm-extension/manifest.json` and installed runtime extension both report `1.9.5-alpha`. |
| C10.6 PHP writer | PASS | `ChituSyncService.php` SHA-256 matches exactly: `0d9acf07cf53d45fed1145f0d30a3c55c99a21ba81a2ca57e4ad2a640466fcc6`. |
| clientDefs metadata | PASS | 10 workspace files / 10 runtime files; all hashes match. |
| entityDefs metadata | PASS | 9 workspace files / 9 runtime files; all hashes match, including `ResearchEvidence`. |
| layouts metadata | FAIL | 21 / 21 files exist, but `layouts/Lead/detail.json` differs. |
| dashlet metadata | FAIL | 14 / 14 files exist, but 8 hashes differ. |
| language metadata | FAIL | 24 / 24 files exist, but 11 hashes differ. |
| Lead primary filters | PASS | Workspace and runtime both contain 26 primary filters; the prior `workspace 26 / runtime 2` drift is no longer present. |
| Docker health and loaded modules | PASS | `espocrm` and `espocrm-db` are healthy; EspoCRM image is `10.0.1`; runtime config lists Prospecting Dashboard/Search, SearchStrategy, SearchJob, ProspectPool, and ResearchEvidence. |
| Package consistency | FAIL | Current package manifest version matches, but its contents differ from the workspace and the latest ZIP has no `.sha256` sidecar. |

## 1. Runtime version and deployment state

Runtime extension listing reports one installed extension:

```
Chitu Prospecting Integration
Version: 1.9.5-alpha
Installed: yes
```

This equals the workspace manifest version. The runtime is hosted by `espocrm/espocrm:10.0.1`. Container state at verification time:

| Container | State |
|---|---|
| `espocrm` | Up, healthy |
| `espocrm-daemon` | Up, healthy |
| `espocrm-cron` | Up |
| `espocrm-db` | Up, healthy |

The C10.6 writer comparison is an exact byte-level match, so the deployed `ChituSyncService.php` is the same as the workspace copy.

## 2. Workspace-to-runtime metadata hashes

The comparison used SHA-256 for each file under the active runtime overlay:

`/var/www/html/custom/Espo/Modules/Prospecting/Resources`

| Group | Workspace | Runtime | Exact matches | Missing/extra | Hash differences |
|---|---:|---:|---:|---:|---:|
| `metadata/clientDefs` | 10 | 10 | 10 | 0 / 0 | 0 |
| `layouts` | 21 | 21 | 20 | 0 / 0 | 1 |
| `metadata/dashlets` | 14 | 14 | 6 | 0 / 0 | 8 |
| `i18n` | 24 | 24 | 13 | 0 / 0 | 11 |
| `metadata/entityDefs` | 9 | 9 | 9 | 0 / 0 | 0 |

No metadata file is missing on either side. The failure is content drift, not an absent module directory.

### Differing layouts

- `layouts/Lead/detail.json`

### Differing dashlets

- `metadata/dashlets/AcquisitionDiscoveryJobs.json`
- `metadata/dashlets/AcquisitionJobsCompleted.json`
- `metadata/dashlets/AcquisitionJobsFailed.json`
- `metadata/dashlets/AcquisitionJobsRunning.json`
- `metadata/dashlets/AcquisitionJobsWaiting.json`
- `metadata/dashlets/AcquisitionLeadPool.json`
- `metadata/dashlets/AcquisitionResearchQueue.json`
- `metadata/dashlets/AcquisitionSearchStrategies.json`

### Differing language files

- `i18n/en_US/Global.json`
- `i18n/zh_CN/EmailEvent.json`
- `i18n/zh_CN/Global.json`
- `i18n/zh_CN/Lead.json`
- `i18n/zh_CN/LearningSignal.json`
- `i18n/zh_CN/Opportunity.json`
- `i18n/zh_CN/ProspectPool.json`
- `i18n/zh_CN/ResearchEvidence.json`
- `i18n/zh_CN/SalesFeedback.json`
- `i18n/zh_CN/SearchJob.json`
- `i18n/zh_CN/SearchStrategy.json`

Every differing workspace file is currently either modified or untracked in Git. This is evidence that the workspace is ahead of (or otherwise different from) the deployed UI metadata; it is not evidence that the runtime has an untracked-only metadata file.

## 3. Docker, cache, and loaded-module state

The runtime overlay is present and readable. The installed-extension list confirms `Chitu Prospecting Integration` is active. `data/config.php` includes the Prospecting module entries named above.

The on-disk cache is near-empty after the reported clear-cache operation: one file is present beneath `data/cache`, and no cached file containing `Prospecting` was found. This is consistent with a cleared cache, but it does not override the direct source-file hash differences above. No rebuild or cache-clear command was run by Phase R01.

## 4. Lead filters drift revalidation

The workspace `metadata/selectDefs/Lead.json` maps **26** `primaryFilterClassNameMap` entries. The runtime file maps the same **26** filters, including `peTierA`–`peTierD`, outreach/research filters, proposal filters, and `peContactReadyWithoutContactMethod`.

**Result: PASS.** The historic `26 vs 2` discrepancy is resolved.

## 5. Package consistency

The newest package is `deployment/prospecting-extension-1.9.5-alpha.zip`.

| Item | Result |
|---|---|
| Package manifest version | `1.9.5-alpha` |
| Workspace manifest version | `1.9.5-alpha` |
| Version match | Yes |
| Computed package SHA-256 | `927e0bc67e670c66625ab2631aa7b361bccd3ff20b25d8502e0df7218cf1c7e4` |
| Adjacent `.sha256` sidecar | No |

Package-to-workspace resource comparison:

| Group | Exact matches | Missing from package | Content differences |
|---|---:|---:|---:|
| clientDefs | 10 | 0 | 0 |
| layouts | 17 | 3 | 1 |
| dashlets | 6 | 0 | 8 |
| language | 11 | 12 | 1 |
| entityDefs | 8 | 0 | 1 |

Therefore the `1.9.5-alpha` ZIP has a matching version label but is not a byte-consistent package of the current workspace. It must not be used as final freeze/package proof for the current state. No new C10.6 package or checksum sidecar was found.

## Required resolution before a PASS verdict

1. Choose the intended UI metadata baseline, then deploy that exact scoped layout/dashlet/language set to the runtime overlay.
2. Run the approved rebuild and cache-clear procedure after deployment.
3. Build one immutable package from the selected workspace commit; keep its manifest version and produce a `.sha256` sidecar (or release manifest).
4. Re-run this read-only hash comparison and confirm zero mismatches across all five metadata groups.

These are recommendations only. Phase R01 did not perform any of them.
