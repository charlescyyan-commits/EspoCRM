# Release / Validation Checklist

**Status:** Static Verified template

## Documentation-Only Tasks (e.g. Phase D01)

- [ ] All edits under `docs/**` only
- [ ] No source, test, or deployment file changes
- [ ] No git commit/push
- [ ] Link audit passed
- [ ] `DOCUMENTATION_CENTER_REPORT.md` completed

## Extension Release Checklist

### Pre-build

- [ ] `crm-extension/manifest.json` version bumped intentionally
- [ ] `Resources/` ↔ module metadata parity tests pass
- [ ] No accidental PHP files outside expected set (`test_only_standard_research_evidence_php_shells_exist`)
- [ ] Routes.json surface/module parity

### Build

- [ ] `build_release_package.ps1` produces ZIP with only `manifest.json` + `files/`
- [ ] ZIP entry paths use forward slashes
- [ ] SHA-256 recorded in `deployment/*.sha256`

### Offline tests

- [ ] `test_extension_skeleton` — all pass
- [ ] `test_phase3c02_search_strategy_foundation` — pass

### Connector tests

- [ ] `discover chitu-connector/tests` — all pass
- [ ] `test_phase3c02_2c_job_runner` — pass

### Runtime (disposable CRM)

- [ ] Extension install + rebuild
- [ ] Integration Bot sync smoke
- [ ] SearchStrategy generate-jobs UI
- [ ] Optional: runner fake job end-to-end
- [ ] ACL scripts if roles changed

### Safety

- [ ] No secrets in reports or logs
- [ ] No production CRM targeted without approval
- [ ] Rollback ZIP and DB backup available

## Related Documents

- [../release/RELEASE_PROCESS.md](../release/RELEASE_PROCESS.md)
- [REGRESSION.md](REGRESSION.md)
