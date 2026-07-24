# Phase3C17 Finalization Report

**Date:** 2026-07-24  
**Role:** Release Engineer — Phase3C17 closure  
**Target release:** `1.9.10-alpha`  
**HEAD (pre-packaging push):** `3837ef655356c6a5bf940a933b033edfd6ea42b8`

## 1. Push status

| Item | Value |
| --- | --- |
| Commit (feature close) | `3837ef6` — `phase3c17: implement center composition dashboard` |
| Prior | `8883e1c` — `phase3c17: harden command center provisioning` |
| Remote | `origin/master` synced at `3837ef6` (`git fetch` verified; `HEAD == origin/master`) |

Untracked pre-existing reports left unmodified (not part of this packaging commit set unless separately requested):

- `docs/PHASE3C17_BROWSER_RUNTIME_SMOKE_REPORT.md`
- `docs/PHASE3C17_LOCAL_PORT_ISOLATION_REPORT.md`

## 2. Runtime Smoke (CC-1)

| Field | Result |
| --- | --- |
| Environment | `http://localhost:8090` — container `espocrm` healthy, host `8090:80` (no port collision) |
| Admin | Login PASS; `销售开发指挥中心` present as first dashboard tab (My Espo preserved) |
| Sales | Login PASS; dashboard loads; Command Center present |
| Queues | All five visible: 我的任务, 待研究客户, 待触达, 待回复, 待审批 |
| Center cards | 搜索中心 / 情报中心 / 触达中心 / 报价中心 routes open for admin + sales |
| Quote boundary | Dashboard does not inline-mutate `Quote.status` / `Approval.status`; Quote route loads |
| ACL | Sales `#Admin` → 403; `/api/v1/Role`, `/Extension`, `/ScheduledJob` → 403 |
| Evidence | `temp/evidence/phase3c17_final/cc1-smoke-results.json` (+ screenshots) |

**Runtime Smoke verdict: PASS WITH RISKS**

Functional composition checks: **21/21 PASS**. Console observed non-blocking queue data errors (titles still render):

- `Controller 'ReplyEvent' does not exist` (待回复 list load)
- `Controller 'Approval' does not exist` (待审批 list load)
- `No primary filter 'c17Pending' for 'DraftApproval'` (待触达 list load)

These are pre-existing scope/controller/filter gaps on the disposable runtime; no ACL, navigation, workflow, or source changes were made in this finalization to address them.

Known documented risk (unchanged): new-user default dashboard still requires provisioner re-run or native Dashboard Templates — no login hook added.

## 3. Release Preparation

| Field | Value |
| --- | --- |
| Version | `1.9.10-alpha` |
| Artifact | `deployment/prospecting-extension-1.9.10-alpha.zip` |
| SHA-256 | `D1F190376F59AE86C64C977D1D9079B2034992AAA302772D6912D8B5117636BC` |
| Sidecar | `deployment/prospecting-extension-1.9.10-alpha.zip.sha256` (exact match) |
| `--check` | PASS (source-to-artifact byte parity + sidecar) |
| Prior artifact | `1.9.9-alpha` **immutable** — SHA `067A89E52EFB35DF7DA4D9437485381D93004063BFC0E81B67EF2C67995871C2` unchanged |

### Tests

| Gate | Result |
| --- | --- |
| C17 focused (`cc1` + `cc0b`) | OK — 18 passed |
| Extension suite (`discover -s crm-extension/tests`) | OK — 260 passed |
| Release integrity + consumers | OK — 26 passed |
| `build_release_package.py --check` | PASS |

Manifest, VERSION_POLICY, deployment docs, release notes index, and `RELEASE_NOTES_1.9.10-alpha.md` aligned to `1.9.10-alpha`.

## 4. Final Verdict

**READY FOR RELEASE** (with documented risks)

### Remaining risks

1. Queue list data for 待触达 / 待回复 / 待审批 may 400/404 until ReplyEvent/Approval controllers and DraftApproval `c17Pending` filter are present on the target CRM (composition titles still show).
2. New-user default Command Center assignment remains out of package scope (documented known risk; no login hook).
3. Runtime smoke used headless Chromium only on the local disposable instance.

### Next step

1. Commit packaging + this report (if not already on `master`).
2. Install `prospecting-extension-1.9.10-alpha.zip` on the target disposable CRM.
3. Re-run `phase3c17_provision_sales_development_command_center.php` for target users.
4. Optional follow-up (separate phase): close ReplyEvent/Approval controller + DraftApproval filter gaps — **not** part of this release closure.
