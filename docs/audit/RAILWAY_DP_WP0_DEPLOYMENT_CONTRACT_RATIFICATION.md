# Railway DP-WP0 Deployment Contract Ratification

## 1. Ratification Decision

**PASS — DP-WP0 RATIFIED**

The bounded amendment is complete and resolves the prior governance-status/hash cycle. The immutable deployment contract remains a hashed technical release input, while ratification status is carried only by this external governance record, which is excluded from canonical artifact files. The manifest remains current after this record changes.

DP-WP1 is **ELIGIBLE — NOT AUTHORIZED**.

## 2. Ratified Artifacts

- `docs/deployment/RAILWAY_DP_WP0_DEPLOYMENT_CONTRACT.md`
- `deployment/railway/full-application-artifact-manifest.json`
- `scripts/generate_railway_artifact_manifest.py`
- `tests/test_railway_dp_wp0_artifact_manifest.py`
- `docs/audit/RAILWAY_DP_WP0_DEPLOYMENT_CONTRACT_REVIEW.md`
- `docs/audit/RAILWAY_DP_WP0_DEPLOYMENT_CONTRACT_AMENDMENT.md`
- Parent plan: `docs/deployment/RAILWAY_FULL_APPLICATION_DEPLOYMENT_PLAN.md`
- Parent-plan / authorized source baseline: `6ef712134f581a12a18da5c98691884e73388b78`

## 3. Verification Basis

| Check | Result |
| --- | --- |
| Read-only manifest `--check` | PASS; checked-in manifest SHA-256 unchanged during verification. |
| Focused manifest tests | PASS; 14 tests passed in an isolated temporary mirror. |
| Focused keyword query | PASS; 14 tests passed in an isolated temporary mirror. |
| JSON parsing | PASS. |
| Schema/version/model | PASS; schema `1`, `deterministic-overlay`. |
| Release identity | PASS; `Chitu Prospecting Integration` `1.9.13-alpha`, full baseline SHA. |
| Inventory | PASS; 654 files, 1,177,923 bytes, 30 required artifacts, SHA-256 for every entry. |
| Path and forbidden-content review | PASS; normalized, sorted, unique relative paths; no forbidden/runtime/absolute paths. |
| Independent review | PASS — DP-WP0 READY FOR RATIFICATION; zero findings at every severity. |
| Ratification isolation | PASS; an external ratification-status mutation is excluded from canonical files and does not break `--check`. |
| Contract-integrity failure | PASS; a technical contract change makes `--check` fail. |
| Canonical-artifact failure | PASS; a canonical code change makes `--check` fail. |

## 4. Ratified Decisions

- `crm-extension/files/custom` and `crm-extension/files/client/custom` are canonical code roots.
- Extension name/version derive from `crm-extension/manifest.json`; the manifest uses the authorized source baseline and deterministic rendering rules.
- Inventory inclusion never authorizes execution: `AfterInstall.php` remains an input only, and provisioning/navigation files remain DP-WP2 candidates.
- Docker volumes, local/Railway databases, `/var/www/html/data`, user preferences, business data, credentials, caches, logs, and sessions are non-canonical release sources.
- DP-WP1 consumes the contract for deterministic installation; DP-WP2 through DP-WP7 retain their ratified ownership boundaries.
- Ratification status is recorded only in this external record; the deployment contract remains technically immutable for manifest integrity.

## 5. Legacy ZIP Decision

`deployment/prospecting-extension-1.9.13-alpha.zip` is **LEGACY — NOT A DEPLOYMENT SOURCE**.

It has SHA-256 `785affd89f1fcea8372faf3eb2a37e2ae3730169e51aadb4eb02c75f68d96c5a`, 461 entries, 153 missing canonical files, zero extra files, and no C25 Commercial Intelligence content. It is absent from the canonical file list and must not be consumed by DP-WP1 unless regenerated and separately validated.

## 6. Authorization Boundary

DP-WP0 ratification approves only the deployment contract, artifact inventory, release identity, manifest verification rules, legacy-artifact disposition, and downstream ownership boundaries.

It does not authorize DP-WP1 implementation, `AfterInstall.php` execution, migrations, provisioning, navigation application, branding, database changes, Railway changes, browser validation, Provider Integration, Runtime Expansion, invariant activation, or Production Promotion.

## 7. Next Eligible Work Package

**DP-WP1 — Deterministic Extension Installation** is **ELIGIBLE — NOT AUTHORIZED**.

DP-WP0 ratification does not authorize DP-WP1 implementation.

## 8. Ratification Metadata

| Field | Value |
| --- | --- |
| Date | `2026-08-04` |
| Authorized source baseline | `6ef712134f581a12a18da5c98691884e73388b78` |
| Previous attempt | REQUIRED AMENDMENT |
| Amendment | COMPLETE |
| Fresh ratification | PASS — DP-WP0 RATIFIED |
| DP-WP0 implementation | COMPLETE |
| DP-WP0 ratification | COMPLETE |
| Manifest | Current after amendment |
| Deployment contract | Immutable technical contract |
| Ratification state | External governance record |
| DP-WP1 status | ELIGIBLE — NOT AUTHORIZED |
