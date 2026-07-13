# Phase3C02.1 — Interrupted Run Recovery, Final UI Verification and Cleanup

**Final verdict: BLOCKED — MANAGER UI VERIFICATION INCOMPLETE**

The minimal acquisition ACL change and all non-UI validation completed. Final
acceptance cannot be marked PASS because the real Sales Manager browser session
reported relevant client-side `RangeError: Maximum call stack size exceeded`
errors while rendering the `SearchStrategy` detail route, and a Manager Edit
control could not be cleanly confirmed for that scope. This is a UI regression
outside the C02.1 ACL provisioning scope and was not modified in this phase.

## 1. Interrupted-run recovery audit

The recovery audit was performed before cleanup or new writes. It found the
C02.1 provisioning and API acceptance files in the worktree, five temporary
`phase3c02_*` API/UI users, records carrying the marker
`[CHITU_PHASE3C02_TEST]`, and temporary files in the CRM containers. The
existing `manager_test` Sales Manager user was not a C02.1 temporary identity;
its existing `Sales Team` membership was preserved.

The browser session was explicitly logged out from the prior Admin identity and
then authenticated as the existing Sales Manager. Chrome-extension automation
was unavailable on this machine, but the in-app browser completed the real CRM
login and navigation checks below.

## 2. Root cause and ACL implementation

### Root cause

The three Acquisition scopes (`SearchStrategy`, `SearchJob`, and
`ProspectPool`) were absent from the `data` JSON of every required role. The
prior provisioning pattern risked overwriting an entire Role `data` payload
instead of preserving unrelated role permissions.

### Fix

`deployment/provisioning/phase3c02_1_provision_acquisition_acl.php` loads each
existing Role, copies its current `data`, replaces only the three Acquisition
scope entries, and saves the merged payload. Re-running it is idempotent: the
same three entries are set to the same values and unrelated role data remains
unchanged.

### Final ACL matrix

| Role | Create | Read | Edit | Delete |
| --- | --- | --- | --- | --- |
| Admin | yes | all | all | all |
| Sales Manager | yes | all | all | no |
| Sales User | yes | own | own | no |
| Integration Bot | yes | all | all | no |

The matrix applies identically to `SearchStrategy`, `SearchJob`, and
`ProspectPool`. No `Lead` or `Opportunity` permissions are touched.

## 3. API acceptance evidence

The completed interrupted-run handoff recorded successful local API acceptance
for four temporary actors, before this recovery cleanup removed their records,
team/role links, and credentials.

| Actor | CRUD scopes | Isolation / boundary checks | Delete behavior | Result |
| --- | --- | --- | --- | --- |
| Admin | All three Acquisition scopes | Generate Jobs and duplicate protection | Allowed | PASS |
| Sales Manager | All three Acquisition scopes | Read/edit all as role policy | Denied | PASS |
| Sales User | All three Acquisition scopes | Own-record isolation | Denied | PASS |
| Integration Bot | All three Acquisition scopes | Read/edit all as role policy | Denied | PASS |

The helper at `deployment/validation/phase3c02_1_api_acl_acceptance.py` keeps
API keys in environment variables, creates only marker-prefixed test data, and
includes marker-scoped cleanup routines.

## 4. Browser UI evidence

### Previously completed handoff checks

The interrupted-run handoff recorded Admin and Sales User UI verification as
passed. This recovery did not re-run or change their roles, layouts, or
provisioning.

| Role | Result | Scope |
| --- | --- | --- |
| Admin | PASS (handoff evidence) | Acquisition lists/details and Admin delete policy |
| Sales User | PASS (handoff evidence) | Own-record visibility/edit and no delete |

### Sales Manager real-session verification

The test used an explicit logout followed by login as `manager_test` (Sales
Manager) and direct CRM navigation. Server access logs confirm `200` responses
for list/detail metadata and records for all three scopes.

| Scope | List and Create | Detail / Edit | Delete | Network | Console / outcome |
| --- | --- | --- | --- | --- | --- |
| SearchStrategy | List opened; Create visible | Detail loaded, but Edit was not cleanly confirmed | Not visible | `200` list and detail | Relevant recursion `RangeError`; BLOCKED |
| SearchJob | List opened; Create and Edit visible | Detail loaded | Not visible | `200` list and detail | No scope-specific server error observed |
| ProspectPool | List opened; Create and Edit visible | Detail loaded | Not visible | `200` list and detail | No scope-specific server error observed |

The browser console captured `RangeError: Maximum call stack size exceeded` in
the Espo client runtime (`client/lib/espo.js` and `client/lib/espo-main.js`) in
the composite Manager verification. Since a clean, error-free Manager
`SearchStrategy` detail/Edit validation is mandatory, this phase stops here
without changing the pre-existing SearchStrategy UI implementation.

## 5. Runtime, package, and static regression

| Check | Result |
| --- | --- |
| Extension skeleton suite | PASS — 38 tests |
| JSON parse and duplicate-key validation | PASS — 115 JSON files |
| Python validation compilation | PASS — `deployment/validation` |
| Package content validation | PASS — 150 files; manifest present |
| Git whitespace check | PASS |
| EspoCRM metadata rebuild | PASS |
| EspoCRM cache clear | PASS |
| Docker health | PASS — `espocrm`, `espocrm-db`, and daemon healthy; cron running |
| Runtime log scan | PASS — no PHP fatal, uncaught, or critical server error in the checked window |
| Manager request log | PASS — `200` list/detail routes for all three Acquisition scopes |

## 6. Cleanup verification

Cleanup was marker- and identity-scoped. It soft-deleted only
`[CHITU_PHASE3C02_TEST]` records, deleted temporary C02.1 users after clearing
their API credentials, and soft-deleted their team and role links.

| Verification item | Remaining active count |
| --- | ---: |
| Marker `SearchStrategy` records | 0 |
| Marker `SearchJob` records | 0 |
| Marker `ProspectPool` records | 0 |
| Temporary `phase3c02_*` users | 0 |
| Temporary C02.1 team links | 0 |
| Temporary C02.1 role links | 0 |
| Preserved `manager_test` → `Sales Team` link | 1 |

All named C02.1 files in `/tmp` were removed from the CRM and database
containers. The final container `/tmp` scan found no `phase3c02` or `c02_`
temporary files. The C02.1 source scan found no embedded secrets; the API
acceptance helper contains only environment-variable names. Existing unrelated
credential text in earlier phase files was not changed or included in this
phase's commit.

## 7. Commit and scope boundary

This commit is intentionally limited to C02.1:

- `deployment/provisioning/phase3c02_1_provision_acquisition_acl.php`
- `deployment/validation/phase3c02_1_api_acl_acceptance.py`
- the C02.1 provisioning test hunk in `crm-extension/tests/test_extension_skeleton.py`
- this report

Pre-existing C01/SearchStrategy worktree changes, package artifacts, and other
unrelated modified or untracked files remain unstaged and uncommitted. The
content-addressed commit hash is recorded in the final task handoff after this
report is committed; embedding a final Git object hash inside that same object
is not possible without changing the hash.

## 8. Required follow-up

Do not proceed to the next phase. First resolve and retest the existing
`SearchStrategy` client recursion, then rerun the Sales Manager browser detail
and Edit check with a clean console before changing this verdict to PASS.
