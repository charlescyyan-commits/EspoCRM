# Phase3C17 WP1 Navigation Implementation Report

## Executive Result

**PASS — the Phase3C17 WP1 Operational Centers navigation is implemented and
validated in the EspoCRM 10.0.1 development runtime.**

The implementation establishes one version-controlled desired-navigation artifact,
one idempotent runtime materializer, and a deprecated U04 compatibility wrapper.
It does not change entity ownership, workflow services, lifecycle states, ACL data,
database schema, or business records.

The runtime now has one `Prospecting` section containing Dashboard, Search Center,
Outreach Center, and Quote Center. The existing native global `Lead` entry is preserved
exactly once and is the Research Center operational record source. This avoids the
unsupported and ambiguous alternative of duplicating `Lead` in `config.tabList`.

Browser-visible validation is **NOT VERIFIED** because the current Docker instance has
no effective host port publication and host port 8080 is owned by another local process.
The supported fallback validation passed through container-internal HTTP, effective
runtime configuration, metadata bootstrap, deployed client-module resolution,
repository queries, and container/application logs.

## Repository Baseline

| Item | Result |
| --- | --- |
| Repository | `D:\EspoCRM-Production` |
| Branch | `master` |
| HEAD before implementation | `827c396eb92cf4a2b45a5483c13529396be4bce6` |
| `origin/master` before implementation | `827c396eb92cf4a2b45a5483c13529396be4bce6` |
| Tag at baseline | `phase3c17-wp0-exit` |
| Release | `1.9.7-alpha` |
| Initial working tree | Clean |
| Development runtime | Docker Compose project `espocrm-test` from `D:\EspoCRM-Test` |
| Runtime version | EspoCRM `10.0.1` |

The required historical input
`docs/PHASE3C17_WP1_NAVIGATION_IA_AUDIT.md` is absent and no renamed equivalent exists.
That repository discrepancy was already recorded by the prior C17 architecture work.
The supplied independent WP0 exit verdict explicitly grants
`READY_FOR_C17_IMPLEMENTATION`; the missing historical filename was therefore retained
as an evidence observation rather than silently fabricated.

## ADR Created

`docs/architecture/ADR_C17_NAVIGATION_OPERATIONAL_CENTERS.md`

Status: **Accepted**

The ADR freezes C17 as an evolution and partial supersession of ADR-C16. It preserves
native scopes, entity/workflow ownership, ACL enforcement, record security, native
lists, dashboards, and related panels while replacing the flat Prospecting tab list
with workflow-oriented Operational Centers.

## Navigation Source-of-Truth Decision

The governance chain is:

```text
Accepted C17 ADR
  -> deployment/navigation/phase3c17_navigation.json
  -> phase3c17_provision_operational_centers_navigation.php
  -> runtime config.tabList
```

Scope metadata remains a capability declaration only. It does not define final runtime
visibility or ordering.

`deployment/provisioning/phase3u04_provision_navbar_tab_order.php` is now a deprecated
compatibility wrapper that delegates to the C17 materializer. It no longer contains an
independent `tabList` definition or an equal `ConfigWriter` path.

The C17 materializer:

- preserves unrelated non-Prospecting entries;
- removes governed stale Prospecting entries and legacy divider IDs;
- requires exactly one preserved global `Lead`;
- appends one deterministic C17 group;
- requires a pre-mutation snapshot;
- retains, validates, and does not overwrite an existing snapshot;
- supports `--dry-run` and `--restore`;
- prints before/after state and the explicit
  `phase3c17-wp1-operational-centers-v1` marker;
- does not read or write entity data or ACL.

## Files Changed

### Navigation authority and deployment

- `deployment/navigation/phase3c17_navigation.json`
- `deployment/provisioning/phase3c17_provision_operational_centers_navigation.php`
- `deployment/provisioning/phase3u04_provision_navbar_tab_order.php`
- `deployment/prospecting-extension-1.9.7-alpha.zip`
- `deployment/prospecting-extension-1.9.7-alpha.zip.sha256`

### Native Center composition and labels

- `crm-extension/files/client/custom/src/views/prospecting/dashboard.js`
- `crm-extension/files/client/custom/res/templates/prospecting/dashboard.tpl`
- `crm-extension/files/client/custom/res/templates/prospecting/search.tpl`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/Global.json`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/zh_CN/Global.json`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/Approval.json`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/zh_CN/Approval.json`

### Contracts and canonical-tree regression alignment

- `crm-extension/tests/test_phase3c17_wp1_navigation.py`
- `crm-extension/tests/test_phase3c06_prospecting_ui_foundation.py`
- `tests/test_phase3c11_2_persistence_entities.py`
- `tests/test_phase3c11_5_operational_schema.py`
- `scripts/runtime/runtime_gate.py`

The three regression-path changes above replace references to the removed duplicate
`crm-extension/Resources` mirror with the singular canonical package tree. They do not
weaken assertions; package-byte parity and canonical-tree absence remain asserted.

### Architecture and evidence

- `docs/architecture/ADR_C17_NAVIGATION_OPERATIONAL_CENTERS.md`
- `docs/PHASE3C17_WP1_NAVIGATION_IMPLEMENTATION_REPORT.md`

## Physical Navigation Implemented

Effective physical behavior:

```text
CRM
  Lead                     <- preserved native global entry; Research Center source

Prospecting
  ProspectingDashboard     -> Dashboard
  ProspectingSearch        -> Search Center
  DraftApproval            -> Outreach Center
  Quote                    -> Quote Center
```

The group intentionally does not add a second `Lead`. Dashboard and Search Center
provide a clearly labelled Research Center link to the single native `Lead` route.

No entity/scope identifier was renamed. User-facing labels are supplied through
`en_US` and `zh_CN` translations. Draft Approval/Outreach Center and Quote Approval are
distinct labels.

## Entity Visibility Result

| Surface | Final placement |
| --- | --- |
| `ProspectingDashboard` | Prospecting top-level Center entry |
| `ProspectingSearch` | Prospecting top-level Center entry |
| `Lead` | Preserved global native entry; Research Center source |
| `DraftApproval` | Prospecting top-level Outreach Center entry |
| `Quote` | Prospecting top-level Quote Center entry |
| `SearchStrategy`, `SearchJob`, `ProspectPool` | Search Center access |
| `ResearchEvidence`, `SalesFeedback`, `LearningSignal`, `EmailEvent` | Research/Lead drill-down and Center links |
| `SendExecution`, `ReplyEvent` | Outreach Center queues |
| `Approval`, `ProformaInvoice` | Quote Center queues |
| `QuoteItem` | Quote child/relationship only |

All twelve supporting objects are absent from the effective top-level `tabList`.
`QuoteItem`, `EmailEvent`, `SalesFeedback`, and `LearningSignal` remain `tab:false`.

## Supporting Object Access Paths

| Center | Verified access paths |
| --- | --- |
| Search Center | Native list links to `SearchStrategy`, `SearchJob`, and `ProspectPool` in both Dashboard and Prospecting Search |
| Research Center | Native `Lead` list; existing relationship panels and Center drill-downs for `ResearchEvidence`, `SalesFeedback`, `LearningSignal`, and `EmailEvent` |
| Outreach Center | Native `DraftApproval` list plus Dashboard links to `SendExecution`, `ReplyEvent`, and `EmailEvent` |
| Quote Center | Native `Quote` list plus Dashboard links to `Approval` and `ProformaInvoice`; existing Quote relationship panels retain `QuoteItem` child access |

Runtime repository construction and a read-only one-row query succeeded for all twelve
supporting entity types. All expected scope metadata objects were present. The deployed
controller/view/template modules for Dashboard and Search Center returned HTTP 200 from
the container's Apache server.

## Provisioning Idempotence

The materializer was first run with `--dry-run`, then applied twice against the same
runtime and snapshot path.

| Check | Result |
| --- | --- |
| First apply | PASS |
| Second-run BEFORE equals first-run AFTER | PASS |
| Second-run BEFORE equals second-run AFTER | PASS |
| Existing snapshot retained rather than overwritten | PASS |
| Snapshot SHA-256 | `452ddc225c066f502264739adc05728fdd59da2014fd9ed8e22374fc18113344` |

The final effective C17 group is exactly:

```json
[
  "ProspectingDashboard",
  "ProspectingSearch",
  "DraftApproval",
  "Quote"
]
```

There is exactly one `Lead` in the full runtime list. All unrelated CRM, Activities,
Support, Marketing, Business, and Organization entries remained in their prior order.

## Offline Test Evidence

All commands used the repository-local
`.venv-s01\Scripts\python.exe`.

| Gate | Result |
| --- | --- |
| Focused C17 + UI-foundation contracts | `25 passed` |
| Full extension pytest suite | `226 passed, 22 subtests passed` |
| Connector pytest suite | `279 passed, 92 subtests passed` |
| Root + runtime regression suite | `162 passed, 1117 subtests passed` |
| S01 integrity | `12 passed, 304 subtests passed` |
| Package baseline | `5 passed, 603 subtests passed` |
| Deployment validation | `2 passed` |
| Extension unittest suite | `226 tests, OK` |
| PHP lint | PASS for all packaged PHP and the C17 materializer |
| Final unified offline gate | PASS — all nine stages |
| Builder `--check` | PASS |
| Deterministic consecutive rebuild | PASS; identical bytes |
| Artifact SHA-256 | `559779080645A158D87D2D9A7678E25A52BD6FDA101A03D9DC84EAD54E12F5A0` |
| `git diff --check` | PASS |

The initial unified run found four `scripts/runtime` tests still reading the deleted
duplicate metadata mirror. The runtime gate was corrected to the canonical package tree,
the exact root/runtime component was rerun successfully (`162 passed`), and the complete
unified offline gate was then rerun from the beginning. Its final summary reports PASS
for PHP lint, extension pytest, connector pytest, root/runtime pytest, S01 integrity,
package baseline, extension unittest, artifact check, and deployment validation. No
failing result is represented as a pass.

## Development Runtime Evidence

| Check | Result |
| --- | --- |
| Environment identity | Compose project `espocrm-test`, working directory `D:\EspoCRM-Test` |
| EspoCRM | `10.0.1` |
| Extension installation | `Chitu Prospecting Integration` `1.9.7-alpha`, PASS |
| Metadata rebuild | PASS |
| Cache clear | PASS |
| Effective `config.tabList` | C17 group exact; one global `Lead`; no stale managed top-level entity |
| Canonical source/runtime parity | PASS for all seven changed packaged client/i18n files |
| Container health | `espocrm`, daemon, and DB healthy; cron running |
| Container-internal `/` | HTTP 200 |
| Container-internal unauthenticated `/api/v1/App/user` | HTTP 401 as expected |
| Dashboard/Search controller, view, and template assets | HTTP 200 |
| New PHP/application fatal after final apply | None |

The current Docker container has no effective published host port in `docker ps`; host
port 8080 is served by another local listener and is not the EspoCRM container.
Accordingly, browser-visible navigation and role-specific page rendering are
**NOT VERIFIED**. This is an environment exposure limitation, not an EspoCRM bootstrap
failure: container-internal application and asset requests pass.

## Role Validation

Runtime inspection found the existing `Admin`, `Sales Manager`, and `Sales User` role
records and active `admin`, `manager_test`, and `sales_test` users. Their stored ACL
maps were read without mutation and retain the prior entity-level policies. No
navigation or extension source change touches role data, ACL metadata, or role
provisioning.

Neither `Finance` nor `Finance Officer` exists in this development baseline. The task
requires inspection only if such a commercial role is present, so no role was created
or redesigned.

Role-specific browser visibility is **NOT VERIFIED** because of the host-port condition
described above. The Admin/system runtime could construct and query every supporting
entity repository, and Sales Manager/Sales User ACL records were inspected. A later
environment smoke should repeat visible navigation with those three existing users
after restoring a usable host mapping.

## Status Mutation Safety

- Runtime `Quote.status.readOnly` is `true`.
- Runtime `Approval.status.readOnly` is `true`.
- Focused contracts prohibit navigation files from writing status.
- No direct status-edit, mass-edit, inline-edit, or drag-and-drop implementation was
  added.
- `QuoteTransitionService` remains the Quote status owner.
- `ApprovalService` remains the Approval status owner.
- No workflow service or lifecycle definition changed.

## Rollback

Before extension deployment and navigation mutation, the implementation captured:

- effective pre-C17 `config.tabList`;
- installed-extension output and runtime metadata state;
- the deployed Prospecting server module;
- deployed Prospecting client views and templates.

The canonical restore command is:

```text
php deployment/provisioning/phase3c17_provision_operational_centers_navigation.php \
  --restore=/safe/path/phase3c17-pre-navigation.json
```

A controlled runtime rollback restored the pre-C17 list exactly. The list was compared
with the original snapshot, after which C17 was re-applied and metadata rebuilt/cache
cleared. The final runtime is on the C17 desired state. The snapshot's local and
container SHA-256 values matched after the complete exercise. Rollback changes only
`config.tabList`; it deletes no records and changes no entity or ACL data.

## Remaining Risks

1. Browser-visible and role-specific rendering remains unverified until the DEV
   container receives a usable host port. Runtime configuration, modules, repositories,
   HTTP bootstrap, and ACL records are verified.
2. A Finance/commercial approval role is absent in this DEV data set. This was not
   introduced or repaired because C17 navigation must not redesign ACL.
3. Analytics remains intentionally
   `DEFERRED — Dashboard aggregation first`; no incomplete KPI or metrics store was
   fabricated.
4. The historical WP1 audit filename remains absent. The Accepted ADR, focused
   contracts, runtime evidence, and this report provide the current implementation
   evidence without rewriting a nonexistent audit.

## Next Step

After this WP1 implementation is merged, restore or assign a non-conflicting host port
for the DEV container and run a short visible smoke as Admin, Sales Manager, and Sales
User. Confirm the five user-facing Center labels and their secondary list links. Do not
change workflow, ACL, entity design, or begin an unrelated C17 work package as part of
that environment-only follow-up.
