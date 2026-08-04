# Railway DP-WP0 Deployment Contract Amendment

| Field | Value |
| --- | --- |
| Amendment status | COMPLETE |
| Date | `2026-08-04` |
| Authorized source baseline | `6ef712134f581a12a18da5c98691884e73388b78` |
| Defect | Governance-status / hash cycle |
| Fresh ratification | PENDING |
| DP-WP1 | NOT AUTHORIZED |

## 1. Defect

The DP-WP0 Deployment Contract was included in the canonical SHA-256 file inventory. The ratification workflow required changing the contract status. Updating that status changed the contract hash and caused:

```text
python scripts/generate_railway_artifact_manifest.py --check
```

to fail without any application or runtime change.

## 2. Corrected Design

1. Deployment-affecting contract content remains integrity-protected and hashed.
2. Contract status is stable: `IMPLEMENTED CONTRACT — RATIFICATION STATUS RECORDED EXTERNALLY`.
3. Ratification status is recorded only in `docs/audit/RAILWAY_DP_WP0_DEPLOYMENT_CONTRACT_RATIFICATION.md`.
4. Mutable governance-status records are excluded from the canonical `files` inventory.
5. Technical changes to the contract or canonical deployment inputs still fail `--check`.
6. `release.gitCommit` is the authorized source baseline, not a future closure-commit self-reference.

## 3. Non-Goals

This amendment does not ratify DP-WP0, authorize DP-WP1, deploy to Railway, mutate Docker/database state, or change application runtime behavior.
