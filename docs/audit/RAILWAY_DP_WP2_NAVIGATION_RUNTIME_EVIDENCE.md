# Railway DP-WP2 Navigation Runtime Evidence

| Field | Value |
| --- | --- |
| Result | **PASS — NAVIGATION PROVISIONING COMPLETE; STATE HOOK_PENDING** |
| Prior fail-closed attempt | 2026-08-05T04:55:31Z — `NAVIGATION_BASELINE_UNRECOGNIZED` (29-item default) |
| Baseline preparation | `docs/audit/RAILWAY_DP_WP2_NAVIGATION_BASELINE_PREPARATION_EVIDENCE.md` — **PASS** |
| Recovery + retry window | 2026-08-05T05:49:46Z / local 2026-08-05T13:50:01+08:00 |
| Staging target | `espocrm-c25-staging-espocrm-1` (EspoCRM `10.0.1`) |
| Governing admissions | `BASELINE_RECOVERY_ADMISSION` (re-entry); `FIRST_RUNTIME_ADMISSION` not applicable after prior failed navigation step |
| Adapter baseline | `phase3c25-dp-wp2-navigation-adapter-complete` (`590a25e4347c24743752939f739cad9eea58d6e1`) |
| Durable ledger | `temp/dp-wp1-registration-evidence/installation-ledger.json` |

## 1. Executive Verdict

After baseline preparation placed the exact `phase3c19-ia-v1` navigation target on
the host, the durable record was recovered through the governed edge
`FAILED → READY → INSTALLING → REGISTERED` (read-only registration
revalidation; no reinstall/AfterInstall). Navigation was then admitted under
`BASELINE_RECOVERY_ADMISSION` (not `FIRST_RUNTIME_ADMISSION`, which requires an
absent navigation step). The reviewed `navigation_provisioning` adapter
revalidated the exact target with **zero writes**, recorded the durable success
step, and the orchestrator advanced `REGISTERED → HOOK_PENDING`.

## 2. Recovery Result

### 2.1 `BASELINE_RECOVERY_ADMISSION` preconditions (verified)

| Check | Observed |
| --- | --- |
| Prior failed navigation step | Present (`failed` @ 2026-08-05T04:55:31.093327+00:00) |
| Successful baseline step | Present (`baseline:navigation_default_to_phase3c19_ia_v1` / `succeeded`) |
| Release identity | Exact pinned DP-WP0/DP-WP1 tuple |
| `installationId` | `installation-501688a00ef4b8e5ee083c1d` |
| Lock-scoped ledger access | Yes (`ProvisioningLedgerInteraction.locked`) |
| Host baseline checksum | `fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0` (exact target) |
| Extension / modules | Registered yes; required modules present (read-only) |

### 2.2 Governed recovery path

```text
FAILED_PRESERVED / FAILED
  -> READY          (governed retry edge)
  -> governed-retry succeeded
  -> INSTALLING
  -> extension-registration succeeded (revalidation marker; no package reinstall)
  -> REGISTERED
```

No synthetic navigation success marker was created during recovery. No direct
ledger JSON edit.

| Field | Before recovery | After recovery |
| --- | --- | --- |
| Disposition | `FAILED_PRESERVED` | `RESUME` |
| State | `FAILED` | `REGISTERED` |
| Event count | 17 | 20 |

## 3. Navigation Runtime Result

| Field | Value |
| --- | --- |
| Admission kind | `BASELINE_RECOVERY_ADMISSION` |
| Adapter | `navigation_provisioning` only |
| Adapter invoked | Yes |
| Host write count | **0** (exact match → `REVALIDATE_AND_NOOP`) |
| Failure code | `null` |
| Final state | **`HOOK_PENDING`** |
| Navigation durable step | `adapter:navigation_provisioning:postcondition:navigation_state_matches_definition` / **succeeded** @ 2026-08-05T05:49:46.481254+00:00 |
| Postcondition evidence | `sha256:fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0` |
| Business data touched | `false` |

Note on admission naming: the operator task referenced `FIRST_RUNTIME_ADMISSION`
for the retry invoke. That classification remains reserved for a virgin
`REGISTERED` record with **no** prior navigation durable step. This retry
correctly used the frozen `BASELINE_RECOVERY_ADMISSION` rule from the baseline
preparation implementation authorization §5.

## 4. Evidence Checksums and Ledger Events

| Checksum | Value |
| --- | --- |
| Baseline / navigation host (before retry) | `fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0` |
| Navigation host (after retry) | `fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0` |
| Target source | `ad0eb26d685be89695551ef968833e81ada660affecd618ed0bd3b39b0056a9e` |
| Canonical definition | `bfd9319e53dfb9e05ac5ef851965fd1853424984853668e51c6e8e344960d9d6` |
| Expected postcondition | `fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0` |

Material navigation-related ledger sequence (abridged):

```text
... REGISTERED (DP-WP1 native registration)
step  adapter:...navigation_state_matches_definition  failed     # first runtime
phase FAILED
step  baseline:navigation_default_to_phase3c19_ia_v1  succeeded  # baseline prep
phase READY / INSTALLING / REGISTERED                            # governed recovery
step  adapter:...navigation_state_matches_definition  succeeded  # recovery retry
phase HOOK_PENDING
```

## 5. Negative Proof

| Forbidden surface | Evidence |
| --- | --- |
| ACL / roles / teams | Not invoked |
| Dashboard / preferences | Not invoked |
| Migration / schema | Not invoked |
| Railway / compose / restart | Not invoked |
| Hooks / AfterInstall | Not invoked |
| CRM business data | `business_data_touched=false` |
| Direct ledger JSON edits | Ledger mutated only via DP-WP1.3 interaction APIs |
| Synthetic navigation success before adapter | Not created |
| Legacy C17 materializer | Not invoked |

## 6. Prior Fail-Closed Attempt (retained)

The first controlled runtime attempt (2026-08-05T04:55:31Z) correctly failed
closed with `NAVIGATION_BASELINE_UNRECOGNIZED` against the default Espo **29-item**
layout, wrote **zero** navigation changes, and preserved `FAILED`. That outcome
remains valid evidence that the adapter permutation gate held before baseline
preparation.

## 7. Authorization State

| Scope | State |
| --- | --- |
| Baseline preparation | **COMPLETE** |
| Governed recovery to `REGISTERED` | **EXECUTED — PASS** |
| Navigation provisioning under `BASELINE_RECOVERY_ADMISSION` | **EXECUTED — PASS** |
| Lifecycle state | **`HOOK_PENDING`** |
| Hooks / migrations / Railway / ACL / dashboard | **NOT AUTHORIZED / NOT EXECUTED** |
| Later DP-WP2 phases (`MIGRATION_PENDING`+) | **NOT AUTHORIZED** |
