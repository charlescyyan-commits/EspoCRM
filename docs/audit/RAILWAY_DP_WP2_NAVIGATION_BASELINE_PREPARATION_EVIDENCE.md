# Railway DP-WP2 Navigation Baseline Preparation Evidence

| Field | Value |
| --- | --- |
| Result | **PASS — BASELINE PREPARATION COMPLETE; LEDGER REMAINS FAILED** |
| Governing authorization | `docs/audit/RAILWAY_DP_WP2_NAVIGATION_BASELINE_PREPARATION_IMPLEMENTATION_AUTHORIZATION.md` |
| Staging target | `espocrm-c25-staging-espocrm-1` (EspoCRM `10.0.1`) |
| Runner | `scripts/dp_wp2_navigation_baseline_preparation.py` |
| Collection window | 2026-08-05T13:46:24+08:00 controlled write + idempotent revalidation |
| Durable ledger | `temp/dp-wp1-registration-evidence/installation-ledger.json` |

## 1. Executive Verdict

The pinned EspoCRM default **29-item** `config.tabList`
(`sha256:cd0179f6d0e0e2964076994197cd956a62ac1d0c7eccc92f051cde1d559bde8d`) was
replaced with the exact approved **19-item** `phase3c19-ia-v1` target
(`sha256:fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0`) under
one durable-ledger lock. Exact read-back matched. Durable step
`baseline:navigation_default_to_phase3c19_ia_v1` was recorded as `succeeded`
while lifecycle state remained `FAILED` / `FAILED_PRESERVED`.

No ledger recovery, navigation adapter invoke, navigation success marker, or
`HOOK_PENDING` transition occurred.

## 2. Identity Binding

| Field | Required | Observed |
| --- | --- | --- |
| `installationId` | `installation-501688a00ef4b8e5ee083c1d` | Exact |
| Extension name | `Chitu Prospecting Integration` | Exact |
| Extension version | `1.9.13-alpha` | Exact |
| Manifest SHA-256 | `9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649` | Exact |
| Source commit | `6ef712134f581a12a18da5c98691884e73388b78` | Exact |
| Pre-state | `FAILED` with prior failed navigation step | Exact |
| Registration | Installed yes (read-only list) | Exact |
| Modules | `ProspectingDashboard`, `ProspectingSearch`, `DraftApproval` present | Exact |

## 3. Checksums

| Checksum | Value | Result |
| --- | --- | --- |
| Before (canonical tabList) | `cd0179f6d0e0e2964076994197cd956a62ac1d0c7eccc92f051cde1d559bde8d` | Matched pin |
| Target source | `ad0eb26d685be89695551ef968833e81ada660affecd618ed0bd3b39b0056a9e` | Matched |
| Target canonical definition | `bfd9319e53dfb9e05ac5ef851965fd1853424984853668e51c6e8e344960d9d6` | Matched |
| After / postcondition | `fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0` | Matched |

Postcondition claim:

```text
name:     navigation_baseline_matches_definition
satisfied: true
evidence: sha256:fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0
```

## 4. Exact Structured Diff (identity/position only)

| Metric | Value |
| --- | --- |
| Before count | 29 |
| After count | 19 |
| Removed | 21 (default Espo dividers/modules outside `phase3c19-ia-v1`) |
| Added | 11 (approved prospecting/commercial/support dividers + `Home` / center modules / `Quote`) |
| Reordered shared | 7 (`Account`, `Contact`, `Lead`, `Opportunity`, `Email`, `Task`, `Calendar`) |
| Write count | 1 |

Removed identities (abridged classes): `$CRM` / `$Activities` / `$Support` /
`$Marketing` / `$Business` / `$Organization` dividers; `Meeting`, `Call`,
`Case`, `Campaign`, `TargetList`, `Document`, `User`, `Team`,
`WorkingTimeCalendar`, `EmailTemplate`, `Template`, `Import`, `_delimiter_`.

Added identities: approved `phase3c17-*` / `phase3c19-*` dividers;
`Home`, `ProspectingDashboard`, `ProspectingSearch`, `DraftApproval`, `Quote`.

## 5. Ledger Evidence

| Field | Value |
| --- | --- |
| State after preparation | `FAILED` |
| Recovery disposition | `FAILED_PRESERVED` |
| Baseline step | `baseline:navigation_default_to_phase3c19_ia_v1` / `succeeded` |
| Navigation adapter success step | **Absent** (prior failed navigation step retained) |
| `HOOK_PENDING` | **Not present** |

## 6. Idempotent Rerun

Second identical invoke after success:

| Field | Value |
| --- | --- |
| `idempotent_noop` | `true` |
| Write count | `0` |
| Before/after checksum | `fe0c9ed6…` / `fe0c9ed6…` |
| State | Remained `FAILED` |

## 7. Negative Proof

| Forbidden surface | Evidence |
| --- | --- |
| ACL / roles / teams | Not invoked |
| Dashboard / preferences | Not invoked |
| Migration / schema | Not invoked |
| Railway / compose / restart | Not invoked |
| Hooks / AfterInstall | Not invoked |
| CRM business data | `business_data_touched=false` |
| Legacy C17 materializer | Not invoked |
| Navigation adapter | Not called |
| Synthetic navigation success marker | Not created |
| Ledger recovery / `HOOK_PENDING` | Not performed |
| DP-WP1 foundation / orchestrator files | Unmodified by this work package |

## 8. Focused Tests

`tests/test_railway_dp_wp2_navigation_baseline_preparation.py` — **7 passed**
(default baseline accepted; checksum mismatch; exact target; read-back mismatch;
idempotent rerun; registration missing; forbidden-scope / no navigation success).

## 9. Authorization State

| Scope | State |
| --- | --- |
| Baseline preparation implementation | **COMPLETE** |
| Controlled host baseline write + evidence | **COMPLETE — PASS** |
| Ledger recovery to `REGISTERED` | **NOT AUTHORIZED / NOT EXECUTED** |
| `BASELINE_RECOVERY_ADMISSION` / navigation re-admission | **NOT AUTHORIZED / NOT EXECUTED** |
| `HOOK_PENDING` / DP-WP2 provisioning success | **NOT CLAIMED** |
