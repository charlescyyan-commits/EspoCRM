# Phase3C25 WP1 Runtime Verification Report

## 1. Executive Verdict

**FAIL — runtime behavior violates WP1 boundaries**

The extension installs, the single read-only route executes, the hardened
parser behaves safely for the exercised runtime inputs, repeated requests
produce no persistence, and the D2 workspace renders after one narrow client
registration fix. The runtime gate is nevertheless **not cleared**:

1. a non-admin user whose role grants the workspace and the governed source
   entities receives `404`, not the required `200`;
2. the nested-denial case therefore cannot preserve a successful root response
   while omitting only the unreadable child;
3. the governed C20–C24 source scopes are deliberately hidden
   (`object: false`) and are omitted from EspoCRM's effective non-admin ACL
   map, even though the fixture role row contains the requested grants;
4. the generated evidence links point to the correct native fragments, but the
   hidden source scopes have no generic record controller, so those record
   surfaces are not navigable.

This is an application-contract conflict, not an environment failure.
Changing the governed scopes to ordinary objects would weaken explicit C20–C24
hidden-record contracts and fail existing boundary tests. A compliant repair
needs a separately reviewed source-authorization and source-navigation design.

## 2. Environment

| Item | Evidence |
| --- | --- |
| Preflight branch | `master` |
| Preflight HEAD | `6e2dcf8f1d354c763c5cac8db23ac3e6c1a657d1` |
| End-of-run branch | `master` |
| End-of-run HEAD | `44d9ffa23ae05f9abd64f49b8d61fbfd78e5c5a0` |
| Concurrent Git movement | Reflog records `44d9ffa` at `2026-07-31 14:15:23 +0800` (`feat(deploy): add Railway C25 staging EspoCRM Dockerfile scaffold`). This verification ran no Git mutation and did not reset the concurrent commit. |
| Worktree | Dirty at preflight and end of run; unrelated modifications and untracked files were preserved |
| Web container | `espocrm`, image `espocrm/espocrm:10.0.1`, port `8090` |
| Database container | `espocrm-db`, MariaDB `11.4.12-MariaDB-ubu2404`; it was stopped at discovery and was started for this verification |
| Background containers | `espocrm-daemon` and `espocrm-cron` remained stopped, preventing background queue/scheduler activity during the gate |
| EspoCRM | `10.0.1` |
| PHP | `8.4.23` inside `espocrm` |
| Runtime URL | `http://localhost:8090` |
| Health | Web root returned HTTP `200`; database became healthy. This Espo version has no `php command.php health-check` command, so web, DB, rebuild, cache and API probes were used instead. |
| Extension before | Active `Chitu Prospecting Integration` `1.9.12-alpha`; modules included `AIPlatform` and `Prospecting`; no `CommercialIntelligence` runtime metadata |
| Extension after | Active `Chitu Prospecting Integration` `1.9.13-alpha`; final install ID `6a6c3ed21014ef34c`; `CommercialIntelligence` route, metadata, PHP and client files present |
| Temporary final package | `phase3c25-wp1-runtime-20260731.zip`, SHA-256 `42D5ECCC6EC7863063B429D51D557E792C7C89015481424D0EC7BBFFD8149469` |

Preflight `git status --short` included these tracked modifications:

- `crm-extension/tests/test_espo_php_namespace_contracts.py`
- `crm-extension/tests/test_extension_skeleton.py`
- `docs/adr/C24_INVARIANT_REGISTRY.md`

It also included extensive pre-existing untracked C22–C25 implementation,
audit and test material, the `EspoCRM/` evidence directory, and the complete
Commercial Intelligence implementation. None was cleaned, reset, stashed or
restored.

### Pre-install runtime evidence baseline

- active extension: `Chitu Prospecting Integration 1.9.12-alpha`
  (`6a676629eb869cf39`); historical inactive/deleted extension rows were left
  untouched;
- installed custom modules: `AIPlatform` and `Prospecting`;
- `CommercialIntelligence` was absent from runtime metadata;
- no C24 table and no CommercialContext-like table/entity existed, so the
  controlled target candidate had no pre-install audit/history state;
- exact relevant table counts (`all rows / non-deleted rows`) were:
  `account 14/3`, `opportunity 13/1`, `reply_event 1/0`,
  `research_evidence 25/0`, `provider_credential 0/0`, `contact 13/2`,
  and `lead 60/7`;
- the web container had just started, the database container was initially
  stopped, and the daemon/cron containers were stopped. The database was
  started solely to perform the requested live gate; daemon/cron remained
  stopped.

## 3. Files Changed

### Pre-existing changes

- the three tracked modifications listed above;
- untracked C22–C25 implementation, governance, audit and test material;
- untracked `EspoCRM/` evidence content;
- untracked Commercial Intelligence PHP, client and metadata files.

### WP1/WP1.1 implementation

- `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Context/ArtifactReferenceParser.php`
  was hardened to an immutable 19-type allowlist and 8–36 character
  alphanumeric IDs;
- `tests/test_phase3c25_wp1_workspace_foundation.py` contains the associated
  parser-boundary regression coverage.

### Runtime fix

- added
  `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/clientDefs/CommercialIntelligenceWorkspace.json`;
- added one regression test proving the scope resolves the packaged
  `custom:controllers/commercial-intelligence-workspace` controller.

### Generated runtime evidence

- `docs/audit/runtime-evidence/phase3c25-wp1/admin-workspace-d2.png`
- `docs/audit/runtime-evidence/phase3c25-wp1/admin-workspace-responsive.png`
- this report.

### Unrelated files

No unrelated file was intentionally edited by this verification. A concurrent
external commit moved `master` from `6e2dcf8` to `44d9ffa`; it was preserved.

## 4. Installation and Rebuild

The repository's existing deterministic package builder was used with a
noncanonical temporary output path. The canonical stale
`deployment/prospecting-extension-1.9.13-alpha.zip` was not rebuilt or
overwritten.

Initial package/install:

```text
.\.venv-s01\Scripts\python.exe crm-extension\scripts\build_release_package.py \
  --output D:\EspoCRM-Production\tmp\phase3c25-wp1-runtime-20260731.zip \
  --allow-noncanonical-output

.\.venv-s01\Scripts\python.exe crm-extension\scripts\build_release_package.py \
  --check \
  --output D:\EspoCRM-Production\tmp\phase3c25-wp1-runtime-20260731.zip \
  --allow-noncanonical-output

docker cp D:\EspoCRM-Production\tmp\phase3c25-wp1-runtime-20260731.zip \
  espocrm:/tmp/phase3c25-wp1-runtime-20260731.zip

docker exec espocrm php command.php extension \
  --file=/tmp/phase3c25-wp1-runtime-20260731.zip
docker exec espocrm php command.php rebuild
docker exec espocrm php command.php clear-cache
```

The initial snapshot installed successfully as `1.9.13-alpha`, install ID
`6a6c3a7e165452076`. Live browser execution then exposed the missing
`clientDefs` registration. After the narrow fix, the same temporary path was
rebuilt and checked, then reinstalled:

```text
D:\EspoCRM-Production\tmp\phase3c25-wp1-runtime-20260731.zip
42D5ECCC6EC7863063B429D51D557E792C7C89015481424D0EC7BBFFD8149469

Installing... Do not close the terminal. This may take a while...
Extension 'Chitu Prospecting Integration' v1.9.13-alpha is installed.
Extension ID: '6a6c3ed21014ef34c'.
Rebuild has been done.
Cache has been cleared.
```

Final package verification:

- 522 file entries;
- zero duplicate entries;
- 24 Commercial Intelligence entries;
- all PHP, client, template, route, module, scope, portal ACL, clientDefs and
  i18n files present;
- all 14 Commercial Intelligence PHP files passed `php -l`.

## 5. Route Verification

Installed route metadata contains exactly one Commercial Intelligence route:

```json
{
  "route": "/CommercialIntelligence/workspace/:candidateId",
  "method": "get",
  "actionClassName": "Espo\\Modules\\CommercialIntelligence\\Api\\GetWorkspaceContext"
}
```

The action reads only `request->getRouteParam('candidateId')`.
`ContextAssemblyService::assembleForCandidate` fixes the root type to
`OpportunityCandidate`; the client cannot supply another root type.

| Method | Status | Response body shape | Verdict |
| --- | ---: | --- | --- |
| GET | 200 | `application/json`, 1,883 bytes, CommercialContext JSON | PASS |
| POST | 404 | `application/json`, empty application body | PASS — rejected |
| PUT | 405 | `text/html;charset=UTF-8`, empty application body | PASS — rejected |
| PATCH | 405 | `text/html;charset=UTF-8`, empty application body | PASS — rejected |
| DELETE | 404 | `application/json`, empty application body | PASS — rejected |

No response leaked a stack trace or internal class name. No second
write-capable Commercial Intelligence route exists.

## 6. ACL Runtime Matrix

Dedicated records were created with the marker `PHASE3C25_WP1_RUNTIME`.
Credentials and API keys are intentionally omitted from this report.

| Case | Setup | Request/result | Leakage assessment | Verdict |
| --- | --- | --- | --- | --- |
| A. Authorized internal | Non-admin API user; workspace `true`; role row grants read-all for `OpportunityCandidate`, `ReplySignal`, `RevenueInsight`, `PipelineMetric` and the other source types | `GET .../c25wp1root0000001` → **404**, empty body | Fails closed; no source leakage, but the required readable workspace is unavailable | **FAIL** |
| B. Workspace denied | Non-admin API user; workspace `false`; source grants present | Existing root → **403**, empty body; nonexistent root → **403**, empty body | Candidate existence is not distinguishable | PASS |
| C. Root denied | Non-admin API user; workspace `true`; `OpportunityCandidate` read `no` | Existing denied root → **404**, empty body; nonexistent root → **404**, empty body | No anchor ID/name, provenance, freshness or nested data leaked | PASS |
| D. Nested denied | Intended role: workspace/root/readable siblings allowed; `RevenueInsight` read `no` | Cannot reach the nested filter because the same effective ACL table rejects the root; no required `200` response is possible | No leak, but omission-with-readable-siblings contract is not demonstrated and does not work | **FAIL** |
| E. Portal | Real portal user linked to portal ID `6a6c3dc28b7b7e58b`; portal authentication itself returned `200` from portal `App/user` | Direct portal workspace request → **403**, empty body | Portal metadata cannot be bypassed | PASS |
| F. Admin | Dedicated admin user | `GET .../c25wp1root0000001` → **200**, full assembly | Uses the same action and assembly service; no write/provider activity | PASS |

Root cause evidence:

- the authorized role's stored `data` includes the expected source grants;
- live `App/user` ACL data includes the workspace boolean but omits the
  governed `OpportunityCandidate`, `ReplySignal`, `RevenueInsight` and
  `PipelineMetric` scopes;
- live `Acl->checkEntityRead` consequently returns false;
- the source scopes deliberately use `object: false`, and C20–C24 boundary
  tests require that hidden-governed-record posture;
- clearing Espo cache did not change the result.

This is not a stale-cache or authentication problem. Admin succeeds; each
dedicated API user authenticates; the failure is the effective non-admin
source ACL.

## 7. Parser Runtime Matrix

The readable fixture root mixes two valid references with malformed and
unsupported text in one `provenanceReference`. The nested `ReplySignal`
references the root again and a `PipelineMetric`; the metric references an
`Account` that would be depth 3.

| Input class | Actual runtime result | Verdict |
| --- | --- | --- |
| Valid `ReplySignal:c25wp1signal00001` | Resolved and presented | PASS |
| Valid `RevenueInsight:c25wp1insight0001` | Resolved and presented for admin | PASS |
| Unsupported `User:Unsupported123` | Absent | PASS |
| Lowercase `account:Lowercase123` | Absent | PASS |
| Namespaced `Espo\Account:Namespace123` | Absent | PASS |
| Path-like `Espo/Account:PathLike123` and `../Account:DotPath123` | Absent | PASS |
| ID shorter than 8 (`Account:short`) | Absent | PASS |
| ID longer than 36 (37 `A` characters) | Absent | PASS |
| Slash, backslash, dot, colon, whitespace, hyphen or underscore in ID | All absent | PASS |
| Control character in ID | Covered by the static parser regression suite but not inserted into the live fixture | PENDING |
| Malformed and valid references in same field | Valid references survived; malformed values were ignored | PASS |
| Duplicate ReplySignal reference | One ReplySignal artifact in the response | PASS |
| Cycle (`root → signal → root`) | Request terminates normally; no duplicate root traversal | PASS |
| Maximum depth 2 | Depth-3 Account ID `6a50948100d49f06c` absent | PASS |
| Parser failure handling | No `500`, stack trace or internal class name | PASS |

The admin result contains exactly the four expected C24 artifacts: the root,
ReplySignal, PipelineMetric and RevenueInsight. No malformed candidate caused
adapter-visible output.

## 8. Response Contract

Actual top-level schema:

```text
anchor
  entityType
  entityId
  displayName
assembledAt
assemblyVersion
advisoryDesignation
assembledMarker
sections
  <layer key>
    []
      entityType
      entityId
      layer
      revision
      freshnessStatus
      validationState
      evidenceReference
      displayName
      stalenessWarning
      warningLabel
freshnessSummary
  CURRENT
  AGING
  STALE
  ARCHIVAL
  UNKNOWN
```

Observed values:

- root: `OpportunityCandidate:c25wp1root0000001`;
- assembly version: `c25-wp1-assembly-v1`;
- marker: `AI_ASSEMBLED_CONTEXT`;
- only populated section: `c24`;
- freshness summary:
  `CURRENT=1, AGING=0, STALE=1, ARCHIVAL=1, UNKNOWN=1`;
- source revisions came from the records' actual `createdAt`/`modifiedAt`
  fields;
- source freshness and validation states were passed through;
- `STALE` and `ARCHIVAL` gained presentation-only warning labels;
- the advisory designation explicitly says the assembly is for human review
  and is not a decision, forecast or commitment;
- no authoritative score, rank, lifecycle transition or CRM truth is created;
- WP2/WP3 placeholders create no JSON artifacts;
- scans found no credential, token, secret, provider configuration, SQL,
  stack trace, service class, `AIJob`, `AIRequestLog`, `ActionGate` or
  `SendExecution`.

The inaccessible-child response contract could not be demonstrated because
the authorized non-admin root request fails before assembly.

## 9. No-Write Evidence

Exact row counts and table checksums were captured immediately before and
after three identical successful admin GET requests. All three returned
HTTP `200`, length 1,883, and the same artifact signature.

| Table | Rows before/after | Checksum before/after |
| --- | ---: | ---: |
| `opportunity_candidate` | 2 / 2 | 4263707323 / 4263707323 |
| `opportunity` | 13 / 13 | 1317717953 / 1317717953 |
| `lead` | 60 / 60 | 3067824367 / 3067824367 |
| `account` | 14 / 14 | 3473379555 / 3473379555 |
| `contact` | 13 / 13 | 1363227309 / 1363227309 |
| `revenue_insight` | 1 / 1 | 338229884 / 338229884 |
| `pipeline_metric` | 1 / 1 | 4074990766 / 4074990766 |
| `reply_signal` | 1 / 1 | 3943328259 / 3943328259 |
| `research_evidence` | 25 / 25 | 390385362 / 390385362 |
| `human_feedback` | 0 / 0 | 0 / 0 |
| `execution_ledger` | 0 / 0 | 0 / 0 |
| `optimization_insight` | 0 / 0 | 0 / 0 |
| `performance_metric` | 0 / 0 | 0 / 0 |
| `feedback_learning_observation` | 0 / 0 | 0 / 0 |
| `reply_event` | 1 / 1 | 2929305455 / 2929305455 |
| `prospect_candidate` | 0 / 0 | 0 / 0 |
| `prospect_run` | 0 / 0 | 0 / 0 |
| `provider_credential` | 0 / 0 | 0 / 0 |
| `note` (history/stream evidence) | 269 / 269 | 3609368523 / 3609368523 |

`ai_qualification_insight`, `ai_job` and `ai_request_log` tables do not exist
in this installed runtime and therefore could not change. No
CommercialContext-like table existed before or after. The C25 module has no
entity definitions, migrations, hooks or ORM entity. Fixture
`transitionHistory` remained `[]`; no lifecycle, review or outcome record was
created.

**No-write verdict: PASS.**

## 10. Provider and Execution Isolation

The request-window container log contains exactly the three expected
Commercial Intelligence GETs. A case-insensitive scan found no
`CompletionProvider`, `ProviderCredential`, credential resolution, `AIJob`,
`AIRequestLog`, `ActionGate`, `SendExecution`, outreach, transition, webhook,
queue, scheduler, curl or Guzzle activity.

Network counters changed only by the local HTTP and DB traffic used for this
verification:

```text
before: espocrm 6.62MB / 26.1MB; espocrm-db 3.69MB / 5.97MB
after:  espocrm 6.68MB / 26.2MB; espocrm-db 3.73MB / 6.01MB
```

No daemon or cron container was running. The WP1 PHP source contains no HTTP
client/provider path. These counters are not a packet capture, but the stopped
workers, exact request-window logs, unchanged AI/provider tables and absence of
egress code collectively show no provider or execution activity.

**Provider/execution isolation verdict: PASS.**

## 11. Browser Verification

Initial browser execution exposed:

```text
404 — The url you requested can't be handled.
Could not load script:
/client/custom/modules/commercial-intelligence/src/controllers/
commercial-intelligence-workspace.js
```

After adding `clientDefs` and reinstalling:

- the controller loaded from
  `/client/custom/src/controllers/commercial-intelligence-workspace.js`;
- the view and template loaded successfully;
- a clean tab rendered the workspace with zero console warnings/errors;
- the browser load issued exactly one
  `GET /api/v1/CommercialIntelligence/workspace/c25wp1root0000001`;
- no Commercial Intelligence POST, PUT, PATCH or DELETE appeared;
- no save or inline-edit control exists;
- all four admin-readable C24 artifacts rendered;
- AI/assembled markers and the red D2 divider are visible;
- the 390 px viewport retains the AI marker, divider and both placeholders;
- the script-like source name is displayed literally, the workspace contains
  zero `<script>` descendants, and `window.C25_XSS` is undefined;
- both WP2/WP3 placeholders are non-link `SPAN` elements with no role/href;
  clicking both leaves the URL and page unchanged and opens no dialog.

Evidence hrefs are correctly formed:

```text
#OpportunityCandidate/view/c25wp1root0000001
#ReplySignal/view/c25wp1signal00001
#PipelineMetric/view/c25wp1metric00001
#RevenueInsight/view/c25wp1insight0001
```

However, direct runtime probes of the hidden governed source scopes return
`404` because no generic record controller exists. Correct href construction
therefore does not satisfy the “links open the correct source records”
criterion. Nested unreadable omission cannot be captured visually because the
authorized non-admin workspace itself returns `404`.

Screenshots:

- `docs/audit/runtime-evidence/phase3c25-wp1/admin-workspace-d2.png`
- `docs/audit/runtime-evidence/phase3c25-wp1/admin-workspace-responsive.png`

**Browser/D2 verdict: partial PASS; overall browser acceptance FAIL because
authorized-user and source-navigation behavior remain broken.**

## 12. Runtime Fixes

### Fix 1 — client controller registration

- **Symptom:** workspace hash route showed 404; browser tried to load the
  controller from the module-specific client path, where it was not packaged.
- **Root cause:** the scope declared module ownership but had no `clientDefs`
  override for the existing `custom:` controller.
- **Files:** added
  `Resources/metadata/clientDefs/CommercialIntelligenceWorkspace.json`;
  updated `tests/test_phase3c25_wp1_workspace_foundation.py`.
- **Why WP1:** it only registers the already-implemented read-only WP1
  controller; it adds no entity, write, provider or later-WP behavior.
- **Regression:** new test asserts the exact controller mapping and packaged
  JS file; targeted WP1 count increased from 32 to 33.
- **Runtime rerun:** package rebuilt at the temporary path, installed, rebuilt,
  cache cleared; clean browser load succeeded.

### Unfixed — hidden source ACL and navigation

A “quick” change to mark C20–C24 governed entities as ordinary objects would
enable generic controllers but violate explicit hidden-record boundary tests
and broaden their public surface. Directly reading raw Role JSON inside C25
would bypass Espo's ACL service conventions. Neither is an acceptable narrow
runtime fix. Remediation requires an approved design for:

1. record-level read checks for hidden governed source entities;
2. a safe read-only source evidence surface or resolver;
3. runtime tests proving authorized root, denied root and denied nested
   behavior without exposing generic mutation controllers.

## 13. Tests

| Command | Result | Classification |
| --- | --- | --- |
| `pytest tests/test_phase3c25_wp1_workspace_foundation.py -q` | **33 passed** | PASS; includes 32 requested tests plus one runtime-fix regression |
| `pytest crm-extension/tests/test_espo_php_namespace_contracts.py -q` | **3 passed** | PASS |
| `pytest crm-extension/tests/test_extension_skeleton.py -q` | **38 passed** | PASS |
| all ten `tests/test_phase3c24_*.py` files | **97 passed** | PASS |
| `pytest -q` | **924 passed, 4 failed, 1591 subtests passed** | Four known pre-existing failures; no newly failing test |
| `git diff --check` | no output, exit `0` | PASS |
| `php -l` over all 14 Commercial Intelligence PHP files | all clean | PASS |
| Espo `rebuild` and `clear-cache` | completed | PASS |

Pytest emitted an environment-specific warning because `.pytest_cache` is not
writable. It did not alter test results.

## 14. Known Pre-existing Failures

The same four failures remain:

1. C17 Chinese global i18n test expects the entire singular-scope map to
   contain only three C17 entries, but later phases have valid additional
   entries.
2. Canonical `1.9.13-alpha` release archive does not match the current source
   tree.
3. Canonical archive lacks newer entity definitions.
4. Canonical archive lacks newer canonical text bytes/files.

The three archive failures are expected because this task explicitly forbids
rebuilding the stale canonical release ZIP. The temporary runtime package
passed its own builder check.

## 15. Freeze Criteria F1–F8

| Criterion | Status | Runtime resolution |
| --- | --- | --- |
| F1 — No entity created | **PASS** | No C25 entity metadata/table/migration; no CommercialContext persistence |
| F2 — No CRM mutation path | **PASS** | Route/method matrix, three-request checksums and audit evidence are clean |
| F3 — ACL inheritance verified | **FAIL** | Authorized internal and nested-denial cases do not work |
| F4 — Provenance visible | **FAIL** | Values render for admin, but non-admin inheritance fails and evidence targets have no navigable governed-record surface |
| F5 — Boundary tests pass | **FAIL** | Static suites pass, but required live W1 visibility/navigation behavior is red |
| F6 — C25 invariants preserved | **PASS** | No ownership, egress, truth creation, mutation or provenance rewriting was observed |
| F7 — D2 demonstrated | **PASS** | Desktop and 390 px screenshots show the AI/assembled marker and CRM boundary |
| F8 — Verification audit signed | **FAIL** | Audit is complete but cannot sign a failed runtime gate |

## 16. Final Recommendation

- Runtime gate cleared: **NO**
- WP1 correction work remains: **YES**
- Freeze documentation may begin: **NO**
- Formal freeze allowed: **NO**
- Repository inventory/commit preparation before freeze: **YES, after the ACL
  and source-navigation correction is implemented and rerun**

Retain the installed local `1.9.13-alpha` extension and the clearly named
runtime fixtures for reproducibility. They contain no customer data and invoked
no lifecycle transitions. Do not treat that installed instance as freeze
evidence until the authorized and nested-denial cases pass.

### Cleanup disposition

- the local temporary fixture source
  `tmp/phase3c25_wp1_runtime_fixture.php` was removed;
- the installed extension, database fixture records, dedicated fixture
  users/roles and screenshots were retained for reproducibility;
- cleanup of the host temporary ZIP and sidecar was attempted only after their
  exact resolved paths were verified, but the environment rejected the
  destructive-action approval because its tool-usage allowance was exhausted;
- no workaround deletion was attempted, so these residual temporary files
  remain:
  - `D:\EspoCRM-Production\tmp\phase3c25-wp1-runtime-20260731.zip`
  - `D:\EspoCRM-Production\tmp\phase3c25-wp1-runtime-20260731.zip.sha256`
  - `/tmp/phase3c25-wp1-runtime-20260731.zip` in `espocrm`
  - `/tmp/phase3c25_wp1_runtime_fixture.php` in `espocrm`

The residual files are temporary build/fixture code only, contain no customer
data, and are not loaded as application module code.
