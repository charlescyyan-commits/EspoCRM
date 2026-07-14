# Changelog Policy

**Status:** Policy document

## Principles

1. **User-visible changes** to extension behavior, connector contracts, or deployment procedures should be recorded.
2. **Phase reports** serve as detailed engineering changelogs; release notes summarize user-facing deltas.
3. Do not retroactively rewrite historical phase report conclusions.

## Where to Record Changes

| Change type | Location |
|-------------|----------|
| Extension release summary | `docs/release/RELEASE_NOTES_<version>.md` |
| Engineering detail | `docs/PHASE3*_*.md` or `docs/phase-reports/` |
| Documentation center | Update relevant `docs/**` page + `docs/README.md` status table |
| Connector-only | Phase report under `docs/` referencing commit SHAs |

## Release Notes Format

```markdown
# Release Notes <version>

## Summary
- Bullet of user-visible changes

## Upgrade
- ZIP path, manifest version, breaking notes

## Verification
- Tests run, runtime environment (disposable only)
```

## Alpha Releases

`-alpha` releases may ship metadata and connector changes without stable API guarantees. Document known **Draft** / **TBD** items explicitly.

## Related Documents

- [VERSION_POLICY.md](VERSION_POLICY.md)
- [RELEASE_PROCESS.md](RELEASE_PROCESS.md)
