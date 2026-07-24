# Phase3C17 WP1.4C Release Closure Report

## 1. Baseline

- Branch: `master`
- Takeover HEAD: `4dfaeacc1af61412dabfa33cd23f87975bfdc8b1` (`phase3c17: polish product navigation and dashboard IA`)
- Takeover time: 2026-07-24 (UTC)

## 2. Working-tree state at takeover

- 25 tracked files modified (WP1.4B fix set), none staged.
- 8 untracked files: 6 WP1.4B outputs (controller, focused test, artifact + sidecar,
  WP1.4B report, release notes) and 2 pre-existing reports (section 3).
- No `.git/index.lock` existed; no active `git`/`ssh`/`git-lfs` processes.
  Git index was verified with an `add --intent-to-add` / `reset` round-trip on
  `Controllers/DraftApproval.php`; final staging content was unaffected.

## 3. Excluded pre-existing untracked reports

Left untracked, unmodified, unstaged (verified in `git status` after push):

- `docs/PHASE3C17_BROWSER_RUNTIME_SMOKE_REPORT.md`
- `docs/PHASE3C17_LOCAL_PORT_ISOLATION_REPORT.md`

## 4. Files committed (commit `6ad99ef`, 31 files)

- New: `crm-extension/files/custom/Espo/Modules/Prospecting/Controllers/DraftApproval.php`
- New: `crm-extension/tests/test_phase3c17_wp1_4b_runtime_fixes.py`
- New: `deployment/prospecting-extension-1.9.9-alpha.zip` (+ `.sha256` sidecar)
- New: `docs/PHASE3C17_WP1_4B_RUNTIME_FIX_REPORT.md`, `docs/release/RELEASE_NOTES_1.9.9-alpha.md`
- Modified: 6 i18n JSON files (`en_US`/`zh_CN` × `ProspectingDashboard`/`ProspectingSearch`/`Quote`),
  2 templates (`dashboard.tpl`, `search.tpl`), 3 client JS files
  (`views/prospecting/dashboard.js`, `views/prospecting/search.js`,
  `handlers/quote/workflow-transition.js`), `manifest.json`,
  4 extension test files, `tests/regression/test_phase3s01_release_integrity.py`,
  `tests/test_phase3c11_2_persistence_entities.py`, `tests/test_phase3c11_5_operational_schema.py`,
  and release/deployment docs (`INSTALL.md`, `PACKAGE.md`, `UPGRADE.md`, `VERSIONING.md`,
  `docs/release/README.md`, `docs/release/VERSION_POLICY.md`).
- No logs, caches, databases, secrets, temp files, or browser profiles were staged.

## 5. DraftApproval controller audit

`Controllers/DraftApproval.php` is a 9-line native EspoCRM `Record` controller
(`Espo\Core\Controllers\Record`), identical in pattern to the existing
`Controllers/Quote.php` in the same module namespace.

- No custom actions, no direct status writes, no ACL override, no exception
  swallowing — Espo's standard record API and ACL apply unchanged.
- Root-cause match: runtime log had repeated `Controller 'DraftApproval' does not
  exist` for `GET /DraftApproval`; the running container's
  `custom/Espo/Modules/Prospecting/Controllers/` lacked `DraftApproval.php`
  (verified pre-deploy). After install, the controller exists and
  `GET /api/v1/DraftApproval*` returns 200 (verified in container access log).
- Cosmetic note: `Quote.php` carries `declare(strict_types=1);`, the new file does
  not; behavior is unaffected (no scalar type coercion surface in an empty subclass).

## 6. i18n audit

- All 6 JSON files parse strictly; `en_US`/`zh_CN` label-key sets are identical per
  scope (enforced by `test_phase3c17_wp1_4b_runtime_fixes.py`).
- Keys match client call sites: `search.js`/`dashboard.js` `buildLabels()` and
  `workflow-transition.js` `translate()` reference exactly the added keys; templates
  use `{{labels.*}}` bindings only. No unrelated translations were overwritten
  (diffs are pure additions plus hard-coded-string removals).
- **Defect found and fixed during this audit:** `dashboard.tpl` referenced
  `{{labels.operationalCenters}}`, but `dashboard.js` `buildLabels()` did not provide
  that key, so the dashboard "Operational Centers" panel heading would have rendered
  blank. Fixed with one line (`operationalCenters: translate('operationalCenters')`)
  and a guarding assertion inside the existing WP1.4B focused test (test count
  unchanged at 32). Browser verification confirms the heading renders as 运营中心.
- zh_CN `Global.json` already carried the `C17Dashboard*` keys; admin UI language is
  `zh_CN` and renders Chinese throughout (screenshots b/c).

## 7. Version consistency (`1.9.9-alpha`)

Aligned and verified: `crm-extension/manifest.json` (`version`, `releaseDate`
2026-07-24), artifact filename, artifact-internal `manifest.json`,
`docs/release/VERSION_POLICY.md`, `docs/deployment/{INSTALL,PACKAGE,UPGRADE,VERSIONING}.md`,
`docs/release/README.md` index, `RELEASE_NOTES_1.9.9-alpha.md`, and all
`RELEASE_VERSION`/canonical-archive constants in the test suite. Remaining
`1.9.8-alpha` references are historical records only (prior release notes, prior
sidecar, prior phase reports).

## 8. PHP lint (container `espocrm`, PHP of EspoCRM 10.0.1 image)

Only one PHP file was added/changed by this task:

- Source copy: `php -l /tmp/DraftApproval.php` → `No syntax errors detected`
- Installed copy: `php -l /var/www/html/custom/Espo/Modules/Prospecting/Controllers/DraftApproval.php`
  → `No syntax errors detected`

JavaScript syntax: `node --check` passed for all 3 modified JS files.

## 9. Test gates (all run in this session)

| Gate | Command | Result |
| --- | --- | --- |
| Focused (WP1.4B + navigation + UI) | `python -m unittest crm-extension.tests.test_phase3c17_wp1_4b_runtime_fixes crm-extension.tests.test_phase3c17_wp1_navigation crm-extension.tests.test_phase3c06_prospecting_ui_foundation` | OK — 32 passed |
| Extension suite | `python -m unittest discover -s crm-extension/tests` | OK — 236 passed |
| Release integrity + package consumers | `python -m unittest tests.regression.test_phase3s01_release_integrity tests.test_phase3c11_2_persistence_entities tests.test_phase3c11_5_operational_schema` | OK — 26 passed (all subtests pass; unittest reports subtests only on failure) |
| Artifact check | `python crm-extension/scripts/build_release_package.py --check` | PASS (exact source-to-artifact byte parity + sidecar match) |
| i18n strict parse | `json.load` on all 6 modified i18n files + `manifest.json` | OK |
| JS syntax | `node --check` × 3 modified JS files | OK |

Counts match the WP1.4B baselines exactly (32 / 236 / 26).

## 10. Artifact

- File: `deployment/prospecting-extension-1.9.9-alpha.zip`
- **SHA-256: `067A89E52EFB35DF7DA4D9437485381D93004063BFC0E81B67EF2C67995871C2`**
- The WP1.4B report records `CDCD1130…2A47`. That hash is superseded: the
  `operationalCenters` one-line source fix (section 6) changed source bytes, so the
  artifact was deterministically rebuilt with
  `python crm-extension/scripts/build_release_package.py`, which regenerated the
  sidecar. `--check` passes against the new hash. ZIP contains 284 entries,
  including `Controllers/DraftApproval.php` and the fixed `dashboard.js`;
  internal manifest version is `1.9.9-alpha`.

## 11. Commit

- `6ad99ef3058f8dd59dca5f4b31201e06e95a6bd0` — `phase3c17: close navigation runtime defects`
- This closure report is committed as the immediately following documentation commit.

## 12. Remote verification

- After push: `git rev-parse HEAD` == `git rev-parse @{u}` ==
  `6ad99ef3058f8dd59dca5f4b31201e06e95a6bd0` (`origin/master`, `git fetch` verified).
- Working tree clean except the two excluded untracked reports (section 3).
  `.gitignore` was not modified to fake cleanliness.

## 13. Deployment

Containers are plain `docker run` instances (no compose file; verified via
`docker inspect` — no compose labels): `espocrm`, `espocrm-daemon`, `espocrm-cron`,
`espocrm-db` (mariadb:11.4).

Commands executed:

```powershell
docker cp deployment/prospecting-extension-1.9.9-alpha.zip espocrm:/tmp/prospecting-extension-1.9.9-alpha.zip
docker exec espocrm php /var/www/html/command.php extension --file=/tmp/prospecting-extension-1.9.9-alpha.zip
# → Extension 'Chitu Prospecting Integration' v1.9.9-alpha is installed. ID: 6a62d05f854a6d1e6
docker exec espocrm php /var/www/html/command.php clear-cache   # → Cache has been cleared.
docker exec espocrm php /var/www/html/command.php rebuild       # → Rebuild has been done.
docker exec espocrm php /var/www/html/command.php extension --list  # → 1.9.9-alpha Installed: yes
docker restart espocrm
curl http://localhost:8090/   # → HTTP 200
```

Post-deploy state: all four containers up; `espocrm-db` and `espocrm-daemon`
healthy. Container log scan (last 200 lines + post-smoke window): no PHP
fatal/parse errors, no `controller class not found`, no metadata/JSON failures, no
permission denied, no `DraftApproval` 404, no Quote 5xx. All
`GET /api/v1/DraftApproval*` requests return 200.

## 14. Browser smoke matrix (headless Chromium 149 via Playwright, `http://localhost:8090`, 2026-07-24T02:49–02:53Z)

Roles: `admin` (UI language zh_CN) and `sales_test` (regular user). Passwords were
reset for the disposable local runtime via the official
`php command.php set-password` CLI (precedented local-only practice); no
credentials, tokens, or cookies appear in evidence or in this report.

| Section | Checks | Result |
| --- | --- | --- |
| A. Touch Center `#DraftApproval` | route reached; list container rendered; no 404 text; zh header 触达中心; full page refresh re-verified | PASS |
| B. Search Center `#ProspectingSearch` | 搜索中心/创建搜索任务/国家/关键词/提供方/策略/结果数量上限/开始搜索 + 8 nav labels all present in zh; zero English fallback strings | PASS |
| C. Operations Dashboard `#ProspectingDashboard` | 潜客运营/运营中心/工作流/潜客汇总/最近发现活动 + 5 metric labels in zh; zero English fallback; zero empty panel headings (operationalCenters fix confirmed); dashlets render | PASS |
| D. Quote stability | 5 consecutive load/refresh cycles of `#Quote` list — all ok; opened record `#Quote/view/6a6033ab8e6e6dbd9`; back to list; reopened — all ok; actions menu shows 批准/驳回审核 in zh | PASS — no intermittent failure observed |
| E. Roles | admin: `DraftApproval`/`Quote` API 200, Quote actions visible. sales_test: module APIs 200 per its role; admin-only surfaces `/api/v1/Role`, `/api/v1/Extension`, `/api/v1/ScheduledJob` → 403; SPA `#Admin` route renders "403 You don't have access to this area." — Forbidden stays Forbidden, never 404/blank | PASS |
| F. Evidence | `temp/evidence/wp1_4c/`: `a1-touch-center.png`, `a2-touch-center-after-refresh.png`, `b-search-center-zh.png`, `c-dashboard-zh.png`, `d1-quote-list.png`, `d2-quote-detail.png`, `e-sales-home.png`, `wp1_4c-smoke-results.json`, `e-sales-forbidden-probe.json` | saved, credential-free |

## 15. Console and Network

During the full authenticated smoke run: **0 console errors, 0 page errors,
0 failed requests, 0 HTTP ≥ 400 responses** (`wp1_4c-smoke-results.json`). The only
403s observed were the intentional forbidden-surface probes in section E, captured
separately (`e-sales-forbidden-probe.json`).

## 16. Remaining risks

- The WP1.4B report's recorded artifact hash (`CDCD1130…`) is superseded by
  `067A89E5…` (section 10); kept as historical record, not edited.
- Two core-EspoCRM admin-only menu items on the Quote detail page display in
  English (`View Audit Log`, `View User Access`) — these are core platform labels,
  not extension scope; workflow actions themselves are localized (批准/驳回审核).
- `sales_test` holds read access to all probed prospecting scopes; that role design
  predates this task and was not altered. ACL boundaries verified intact (section E).
- Quote stability was verified over 5 cycles in one session; longer soak was out of
  scope. No intermittent failure reproduced.
- Smoke used headless Chromium only; no other browser engines were exercised.

## 17. Final verdict

**PASS**

All closure criteria met: changes committed and pushed with remote SHA verified;
PHP lint, all test gates, and artifact `--check` green; artifact hash verified;
redeployment clean; Touch Center serves `DraftApproval` without 404; Search
Center, Operations Dashboard, and Quote actions render correct zh_CN/en_US labels;
Quote repeated-load test showed no intermittent failure; console and network are
clean; ACL forbidden semantics intact.
