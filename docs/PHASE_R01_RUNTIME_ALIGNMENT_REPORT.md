# Phase R01 — Runtime Metadata Alignment Verification

**Date:** 2026-07-14  
**Target:** isolated EspoCRM Docker runtime at `http://localhost:8080`  
**Scope:** environment metadata alignment only. No PHP, Python, connector, evidence logic, business metadata source, or test data was changed.

## Verdict

**BLOCKED — runtime does not load the workspace's latest UI metadata.**

The requested metadata rebuild and cache clear completed successfully, but the post-refresh runtime UI-metadata hash still differs from the workspace hash. The mismatch is content-level, not a missing-file condition: both sides contain the same 101 relative JSON paths, with 20 differing file contents. The active metadata service also exposes only two Lead filter-list entries while the workspace Lead client definition declares 26.

Rebuild and cache clear can regenerate metadata only from the extension payload already installed in the container. They cannot transfer the newer workspace files into the Docker volume. A correctly built, approved deployment artifact must be installed before this alignment can be completed.

## 1. Runtime baseline

| Item | Observed state |
| --- | --- |
| EspoCRM image | `espocrm/espocrm:10.0.1` |
| Runtime containers | `espocrm`, `espocrm-db`, and `espocrm-daemon` healthy; cron running |
| Installed extension | Chitu Prospecting Integration `1.9.5-alpha`, ID `6a54fee0412d79694`, `Installed: yes` |
| Earlier extension record | `1.3.1-alpha`, `Installed: no` |
| Workspace manifest | `crm-extension/manifest.json` reports `1.9.5-alpha` |
| Runtime storage | named Docker volumes for `/var/www/html/custom` and `/var/www/html/client/custom`; no workspace bind mount |

The identical version label is not sufficient to establish content identity. The running extension payload and workspace candidate content differ.

## 2. Metadata comparison method

The comparison set contains all JSON files under the same three roots on both sides:

- `Resources/metadata/**`
- `Resources/layouts/**`
- `Resources/i18n/**`

For each file, the verifier generated `relative-path|file-SHA-256`, sorted all records, joined them with LF line endings, and calculated one aggregate SHA-256. This makes the result independent of file enumeration order and distinguishes missing paths from changed content.

| State | Files | Aggregate SHA-256 |
| --- | ---: | --- |
| Workspace before refresh | 101 | `fca254ed5427b05a2f4f1a03017c2018ab25d189e89d34bbe1d98dc852ab4de8` |
| Runtime before refresh | 101 | `f119c4a2cd6ea803ea3b1644835a4a83f80d769377dc2bb69c5b43a95553cb09` |
| Runtime after rebuild + cache clear | 101 | `1c63b3c872e2d07cef32af55094f2862775bc97f1fcc10f7cb4d554a06adaddc` |

Post-refresh path comparison: **0 missing in runtime, 0 extra in runtime, 20 content differences**.

## 3. Environment actions performed

The following requested environment-only commands completed successfully:

```text
docker exec espocrm php command.php rebuild
Rebuild has been done.

docker exec espocrm php command.php clear-cache
Cache has been cleared.
```

No files were copied into the container, no extension was installed or uninstalled, and no business record/API write was performed.

## 4. Files still out of alignment

| Area | Differing files |
| --- | --- |
| English localization | `i18n/en_US/Global.json` |
| Chinese localization | `i18n/zh_CN/EmailEvent.json`, `Global.json`, `Lead.json`, `LearningSignal.json`, `Opportunity.json`, `ProspectPool.json`, `ResearchEvidence.json`, `SalesFeedback.json`, `SearchJob.json`, `SearchStrategy.json` |
| Lead UI layout | `layouts/Lead/detail.json` |
| Acquisition dashlets | `metadata/dashlets/AcquisitionDiscoveryJobs.json`, `AcquisitionJobsCompleted.json`, `AcquisitionJobsFailed.json`, `AcquisitionJobsRunning.json`, `AcquisitionJobsWaiting.json`, `AcquisitionLeadPool.json`, `AcquisitionResearchQueue.json`, `AcquisitionSearchStrategies.json` |

## 5. Active metadata state

After the refresh, a direct read from the EspoCRM metadata service confirmed that runtime metadata is available; it loaded Lead client definitions, the `AcquisitionLeadPool` dashlet, and the `SearchStrategy` scope. It did **not** match the workspace Lead UI definition:

| Check | Runtime | Workspace | Result |
| --- | ---: | ---: | --- |
| Lead `clientDefs.filterList` entries | 2 | 26 | MISMATCH |
| `AcquisitionLeadPool` dashlet metadata | loaded | present | loaded, but aggregate file hash differs |
| `SearchStrategy` scope metadata | loaded | present | loaded |

This confirms that cache regeneration completed, but the effective runtime metadata remains from a payload that is not the current workspace UI candidate.

## 6. Deployment-artifact observation

The checked-in deployment artifact `deployment/prospecting-extension-1.9.5-alpha.zip` is also not an alignment artifact for the current workspace:

| Artifact | UI metadata files | Aggregate SHA-256 |
| --- | ---: | --- |
| Current workspace | 101 | `fca254ed5427b05a2f4f1a03017c2018ab25d189e89d34bbe1d98dc852ab4de8` |
| `prospecting-extension-1.9.5-alpha.zip` | 86 | `42da4d8c86a62bcc238a5cd73ce2b432f6cee517aa301312d13505e52161ec38` |

Therefore, reinstalling that existing ZIP would not prove alignment and was intentionally not performed.

## 7. Required next step

Produce or identify an approved extension package whose UI metadata manifest exactly matches the 101-file workspace manifest above, then install that artifact into the isolated runtime and run rebuild plus cache clear. Re-run this report's comparison afterward; completion requires:

```text
workspace aggregate SHA-256 == runtime aggregate SHA-256
missing paths = 0
extra paths = 0
changed content paths = 0
```

No source edit is required for this next step, but package creation/selection and extension installation are separate deployment actions and were not assumed by this verification task.

## 8. Non-changes

- No PHP, Python, connector, or Evidence logic was modified.
- No workspace business file was modified.
- No customer or synthetic data was created, updated, or deleted.
- No extension was installed, uninstalled, or copied into Docker.
- The only repository artifact created by this phase is this report.
