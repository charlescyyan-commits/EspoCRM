# Freeze Archive

This directory contains recoverable files moved during Phase G03 repository-freeze preparation. Nothing in this directory is an active deployment input.

## Retention layout

- `runtime-backups/` - retained runtime snapshots, including the C10.6 backup and its SQL dump.
- `audit-artifacts/` - archived test results, C06 transcripts, and dashboard-preference evidence.
- `debug-scripts/` - obsolete one-off diagnostic scripts retained for traceability; not release code.
- `deployment/historical-packages/` - historical extension ZIPs and their legacy sidecars. `SHA256SUMS.txt` records all archived ZIP hashes.

The active deployable artifact remains in `../deployment/`. Restore or reuse an archived file only through an approved rollback or investigation procedure.
