# Phase3C02.1B — Parallel Worktree Commit Separation & Baseline Recovery

## 1. Initial Worktree State

Initial inspection used `git status --short`, `git diff --stat`, `git diff --name-status`, `git diff --cached --name-status`, and `git log --oneline --decorate -20`.

- Starting `HEAD`: `441cb02 Phase3C02.1 add minimal acquisition ACL`.
- Phase3C01 already had an independent commit: `8e185c2 Phase3C01 Acquisition Workspace Foundation`.
- The initial index was empty; the worktree contained 20 tracked changes and 33 untracked files.
- No initial change was discarded, overwritten, reset, restored, or cleaned.

Ownership evidence was read from the C01, C02.1, C02.2A, and C02.2B reports and from the extension, 1A, and 2B regression tests.

## 2. File Ownership Matrix

`Unknown / SearchStrategy foundation` identifies the uncommitted 1.9 SearchStrategy/SearchJob feature. It cannot safely be assigned to C01, the narrow 1A recursion fix, or 2B.

| File | Current Diff Summary | Intended Phase | Confidence | Shared File | Safe Commit Method |
| --- | --- | --- | --- | --- | --- |
| `crm-extension/Resources/entityDefs/SearchJob.json` | Strategy fields/relationship | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/Resources/layouts/SearchJob/detail.json` | Strategy detail layout | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/Resources/layouts/SearchJob/list.json` | Strategy list layout | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/Resources/routes.json` | Generate-jobs route | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Classes/Select/SearchJob/PrimaryFilters/JobsWaiting.php` | Deletes legacy waiting filter | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/Global.json` | Acquisition labels | Unknown / SearchStrategy foundation | Medium | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/SearchJob.json` | Queue/strategy labels | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/layouts/SearchJob/detail.json` | Module strategy detail layout | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/layouts/SearchJob/list.json` | Module strategy list layout | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/app/layouts.json` | Acquisition strategy layout entry | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/clientDefs/SearchJob.json` | Queue-oriented filters | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/dashlets/AcquisitionJobsWaiting.json` | Retargets dashlet to queued jobs | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/SearchJob.json` | Strategy, priority, counters, queue state | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/scopes/ProspectPool.json` | Scope metadata change | Unknown / SearchStrategy foundation | Medium | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/scopes/SearchJob.json` | Scope metadata change | Unknown / SearchStrategy foundation | Medium | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/selectDefs/SearchJob.json` | Replaces waiting filter definition | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/routes.json` | Module generate-jobs route | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/manifest.json` | Version and description to 1.9 | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/tests/test_extension_skeleton.py` | C01, SearchStrategy, and 1A assertions mixed | Shared: C01 / foundation / 1A | High | Yes | Leave unstaged; hunk analysis |
| `deployment/provisioning/phase3c01_provision_acquisition_workspace.php` | Strategy dashlet and queue cleanup | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `chitu-connector/chitu_connector/acquisition/__init__.py` | Package export | Phase3C02.2B | High | No | Explicit add; committed `7db88c4` |
| `chitu-connector/chitu_connector/acquisition/models.py` | Worker data models | Phase3C02.2B | High | No | Explicit add; committed `7db88c4` |
| `chitu-connector/chitu_connector/acquisition/provider.py` | Provider protocol | Phase3C02.2B | High | No | Explicit add; committed `7db88c4` |
| `chitu-connector/chitu_connector/acquisition/fake_provider.py` | Deterministic fake provider | Phase3C02.2B | High | No | Explicit add; committed `7db88c4` |
| `chitu-connector/chitu_connector/acquisition/normalization.py` | Candidate normalization | Phase3C02.2B | High | No | Explicit add; committed `7db88c4` |
| `chitu-connector/chitu_connector/acquisition/worker.py` | Queue-claim worker core | Phase3C02.2B | High | No | Explicit add; committed `7db88c4` |
| `chitu-connector/tests/test_phase3c02_2b_acquisition_worker_core.py` | Ten worker-core regression tests | Phase3C02.2B | High | No | Explicit add; committed `7db88c4` |
| `crm-extension/Resources/acl/SearchStrategy.json` | ACL surface definition | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/Resources/entityDefs/SearchStrategy.json` | Surface entity definition | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/Resources/layouts/SearchStrategy/detail.json` | Surface detail layout | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/Resources/layouts/SearchStrategy/list.json` | Surface list layout | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/client/custom/src/handlers/search-strategy/generate-jobs.js` | Detail action handler | Phase3C02.1A | High | No | Add only with metadata baseline |
| `crm-extension/files/client/custom/src/views/search-strategy/detail.js` | Full detail wrapper | Unknown / SearchStrategy foundation | High | Yes | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Api/PostGenerateSearchStrategyJobs.php` | Generate-jobs API | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Classes/Select/SearchJob/PrimaryFilters/JobsCancelled.php` | Cancelled filter | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Classes/Select/SearchJob/PrimaryFilters/JobsQueued.php` | Queued filter | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Controllers/SearchStrategy.php` | SearchStrategy controller | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Entities/SearchStrategy.php` | SearchStrategy entity | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/SearchStrategy.json` | SearchStrategy labels | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/layouts/SearchStrategy/detail.json` | Module detail layout | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/layouts/SearchStrategy/list.json` | Module list layout | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/aclDefs/SearchStrategy.json` | ACL metadata | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/clientDefs/SearchStrategy.json` | Base client config plus 1A recursion/action fix | Shared: foundation / 1A | High | Yes | Cannot split untracked whole file |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/dashlets/AcquisitionSearchStrategies.json` | Dashlet metadata | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/SearchStrategy.json` | Module entity metadata | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/scopes/SearchStrategy.json` | Module scope metadata | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Services/SearchStrategyService.php` | Strategy job planning service | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Services/SearchStrategyTemplates.php` | Strategy templates | Unknown / SearchStrategy foundation | High | No | Leave unstaged |
| `deployment/prospecting-extension-1.9.0-alpha.zip` | Generated extension archive | Generated / temporary | High | No | Leave untracked |
| `deployment/prospecting-extension-1.9.0-alpha.zip.sha256` | Generated archive checksum | Generated / temporary | High | No | Leave untracked |
| `deployment/validation/test_phase3c02_1a_search_strategy_detail.py` | Two recursion regression tests | Phase3C02.1A | High | No | Add only with metadata baseline |
| `docs/PHASE3C02_2A_ACQUISITION_RUNTIME_BOUNDARY_AUDIT.md` | Standalone boundary audit | Phase3C02.2A | High | No | Explicit add; committed `be4bdab` |
| `docs/PHASE3C02_2B_ACQUISITION_WORKER_CORE_REPORT.md` | Worker-core report | Phase3C02.2B | High | No | Explicit add; committed `7db88c4` |

## 3. Shared File / Hunk Analysis

`crm-extension/tests/test_extension_skeleton.py` presented ten selectable hunks. The first eight concern the uncommitted 1.9 SearchStrategy/SearchJob foundation. The ninth contains the full new SearchStrategy test, including the three 1A assertions for no `recordViews` and the `generateJobs` action handler, but also the model, templates, service, route, and role-boundary assertions.

`git add -p -- crm-extension/tests/test_extension_skeleton.py` was opened and every hunk was explicitly rejected. Git did not provide a safe standalone hunk for only the three recursion assertions. Manual test rewriting was prohibited and was not attempted.

The required `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/clientDefs/SearchStrategy.json` fix is also an untracked whole file. Its 1A changes are inseparable from the base SearchStrategy client configuration unless that foundation is committed first. Staging the full file as 1A would absorb unrelated feature work.

## 4. Phase3C01 Commit Result

No C01 commit was created because `8e185c2 Phase3C01 Acquisition Workspace Foundation` already exists. The current SearchJob and provisioner changes go beyond the C01 report and remain unstaged.

## 5. Phase3C02.1A Commit Result

**COMMIT BLOCKED.** The handler and regression test are identifiable, but the required clientDefs metadata and skeleton-test assertions share uncommitted SearchStrategy foundation work. No partial index construction, blob manipulation, manual test rewrite, or unrelated feature staging was used. The prior runtime validation was not repeated; this phase only performed static verification and Git-boundary work.

## 6. Phase3C02.2B Commit Result

`7db88c4 Phase3C02.2B acquisition worker core` contains only the eight files identified by the 2B report. The staged review confirmed no SearchStrategy UI, ACL, C01, manifest, or unrelated file was included.

## 7. Phase3C02.2A Commit Result

`be4bdab Phase3C02.2A document acquisition runtime boundary` contains only the completed, read-only acquisition runtime-boundary audit. It contains no implementation, provider, manifest, runtime, or parallel-task file.

## 8. Tests Run

| Check | Result |
| --- | --- |
| 2B worker-core regression | 10 passed |
| Complete connector suite | 68 passed |
| Extension skeleton suite | 38 passed |
| 1A static recursion regression | 2 passed |
| JSON syntax and duplicate-key validation | 115 files passed |
| Node syntax: detail wrapper and action handler | passed |

The first connector discovery form using `-s tests -t .` was rejected because `tests` is not importable. It made no repository change; root discovery then completed successfully with 68 tests. No Docker, EspoCRM runtime, browser, rebuild, cache-clear, or provider action was run.

## 9. Final Worktree State

After the 2A commit the index is clean. The remaining 20 tracked and 24 untracked entries listed above are intentionally unstaged. This report is the sole 1B documentation artifact and is reviewed separately.

## 10. Remaining Unclassified Changes

The remaining set is the uncommitted SearchStrategy/SearchJob 1.9 foundation (including the shared test hunk) and the generated 1.9 archive/checksum. A dedicated foundation ownership decision is required; no file was forced into another phase merely to obtain a clean worktree.

## 11. Commit Hashes

| Phase | Result |
| --- | --- |
| Phase3C01 | `8e185c2` (already committed) |
| Phase3C02.1 ACL baseline | `441cb02` (already committed) |
| Phase3C02.1A | COMMIT BLOCKED |
| Phase3C02.2A | `be4bdab` |
| Phase3C02.2B | `7db88c4` |

## 12. Safety Confirmation

- Used explicit-path staging only; never used `git add .` or `git add -A`.
- Inspected and rejected every shared test hunk through `git add -p`.
- Committed the standalone 2A audit independently after a staged full-content review.
- Did not use reset, checkout, restore, clean, blob/index construction, or destructive Git commands.
- Did not modify business logic, runtime state, Docker, browser state, or a real provider.
- No change was discarded or overwritten.

## 13. Readiness for Phase3C02.2C

**NO.** C02.2B is independently committed and test-verified, but the baseline is not clean because the SearchStrategy foundation and C02.1A dependencies still require safe ownership and commit separation.

## Conclusion

**PARTIAL PASS**

- Phase3C01 already committed: `8e185c2`.
- Phase3C02.2A safely committed: `be4bdab`.
- Phase3C02.2B safely committed: `7db88c4`.
- Phase3C02.1A is blocked by exact shared metadata and test hunks.
- Remaining files are preserved and explicitly classified; no changes were lost.
- Phase3C02.2C readiness: **NO**.
