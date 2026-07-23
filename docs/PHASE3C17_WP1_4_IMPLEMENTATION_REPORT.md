# Phase3C17 WP1.4 — Navigation Product Polish Implementation Report

**Date:** 2026-07-23
**Release baseline:** `1.9.8-alpha`
**Runtime:** local disposable EspoCRM 10.0.1 at `http://localhost:8090`

## Verdict

**PASS WITH DOCUMENTED BROWSER-SESSION LIMITATION**

The approved navigation IA, localization, release promotion, artifact checks,
offline gates, container installation, cache rebuild, and provisioner
idempotency checks passed. The browser reached the real local EspoCRM login
page, but the historical `sales_test` test password was rejected. No password
was guessed, reset, logged, or bypassed. Browser role-session acceptance is
therefore a follow-up credential-availability check rather than a product
failure.

## Implemented Product IA

The only global navigation writer remains
`phase3c17_provision_operational_centers_navigation.php`.

The governed order is:

```text
Home (native)
潜客开发: 潜客运营, 搜索中心, 触达中心, 报价中心
客户管理: Account, Contact, Lead, Opportunity
活动: Email
更多: Task, Calendar, KnowledgeBaseArticle
```

`Lead` occurs once. Supporting C17 objects (`ResearchEvidence`, `Approval`,
`ProformaInvoice`, `QuoteItem`, `EmailEvent`, and `LearningSignal`) have no
top-level entry. Existing unmanaged native tools remain after the product
order; they were not disabled or deleted.

## Dashboard Consolidation

`phase3c17_provision_sales_development_command_center.php` replaces the
historical phase-managed `Prospecting Operations`, `Acquisition`, and
`Prospecting Home` tabs with one primary `销售开发指挥中心` tab while preserving
`My Espo` and any non-phase dashlets.

It uses only existing extension dashlets plus EspoCRM's built-in `Records`
dashlet:

- Top: `ProspectingSummary`, `AcquisitionOverview`.
- Daily queues: my active Tasks, research queue, pending outreach, awaiting
  customer reply, and pending quote approvals.
- Bottom: prospect pool, new-discovery activity, completed jobs, and recent
  research evidence.

The queue definitions are presentation-only client filters:

- `DraftApproval.status = PENDING`
- `ReplyEvent.replyStatus = SENT` (awaiting a customer reply)
- `Approval.status = PENDING`

No PHP service, workflow, ACL, entity definition, scope tab flag, relationship,
schema, connector, provider, worker, or C16 behavior changed.

## Localization

- `ProspectingDashboard` is `潜客运营` in `zh_CN`.
- Added parity-safe scope labels for Send Execution, Customer Reply, Email
  Event, Sales Feedback, and Learning Signal.
- Added singular labels for Outreach Approval, Quote, and Quote Approval.
- The four operational-center card names, descriptions, and entry labels now
  resolve through `Global.labels` with exact `en_US`/`zh_CN` key parity.

## Release and Artifact

`1.9.7-alpha` remains unchanged. This source/presentation change was promoted
as a new canonical `1.9.8-alpha` package.

| Check | Result |
| --- | --- |
| Artifact | `deployment/prospecting-extension-1.9.8-alpha.zip` |
| SHA-256 | `0CF9682A61CFC51A98831515F85A6AB67CD1AE316172C64CCC98045BD9BA5074` |
| Python builder | PASS |
| `build_release_package.py --check` | PASS |
| Source/artifact parity | PASS through S01 integrity and package-baseline gates |

## Validation

| Gate | Result |
| --- | --- |
| JSON validation | PASS |
| PHP lint (105 packaged PHP files, EspoCRM 10.0.1 container) | PASS |
| C17 focused tests | PASS (23 tests) |
| Extension test suite | PASS (232 tests) |
| Unified offline gate | PASS: extension 232, connector 279, root/runtime 162, S01 12, package baseline 5, deployment 2 |
| Container extension install, rebuild, cache clear | PASS |
| Navigation provisioner second run | PASS; snapshot retained and output unchanged |
| Dashboard provisioner second run | PASS; one command-center tab per admin/manager/sales user |

## Runtime Evidence

System-side runtime inspection after installation confirmed for `admin`,
`manager_test`, and `sales_test`:

- Dashboard tabs are exactly `My Espo` plus one `销售开发指挥中心`.
- The command-center tab contains the eleven expected dashlet instances.
- `Records` queue options point to the approved Task/DraftApproval/ReplyEvent/
  Approval entities and filters.
- Navigation dividers are `潜客开发`, `客户管理`, `活动`, and `更多`; governed entries
  match the expected prefix and `Lead` count is one.

Browser automation at `http://localhost:8090` reached the healthy real login
page. The documented historical `sales_test` password returned “Wrong
username/password”; the browser acceptance step intentionally stopped there.

## Remaining Risk / Next Step

Provide an authorized reusable session or current disposable-runtime credentials
for `admin`, `manager_test`, and `sales_test`, then run a browser-only visual
acceptance pass. Do not reset or create credentials as part of that follow-up.
