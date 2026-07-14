# Coding Guidelines

**Status:** Derived from workspace rules and existing code patterns

## Boundary Rules (Mandatory)

From `AGENTS.md` / `CLAUDE.md`:

- **Do not** modify Chitu scoring logic, AI research logic, or email-generation engine.
- **Do not** modify unrelated Chitu application code.
- Connector imports **only** `chitu_connector` and `chitu_connector/vendored/` stable interfaces.

## Extension (`crm-extension`)

### Metadata Parity

- Entity defs in `Resources/entityDefs/` must match `files/custom/.../Resources/metadata/entityDefs/`.
- Routes in `Resources/routes.json` must match module `Resources/routes.json`.
- `test_extension_skeleton.py` enforces parity — run after metadata edits.

### PHP Conventions

- API actions: thin `Api\Post*` classes delegating to `Services\*`.
- Controllers: extend `Espo\Core\Controllers\Record` when no custom logic needed.
- ACL checks in services via injected `Espo\Core\Acl`.
- Use `BadRequest`, `Forbidden`, `NotFound`, `Conflict` exceptions consistently.

### Prohibited in Sync Path

- `getEntity('Opportunity')` in `ChituSyncService` — tests enforce `NO_AUTOMATIC_OPPORTUNITY`.
- Full email body fields on Lead — `peEmailSubject` / `peEmailBody` must remain absent.
- External HTTP from `SearchStrategyService` — planning only, no provider calls.

## Connector (`chitu-connector`)

### Acquisition Worker

- Worker (`worker.py`) must not perform unconditional status transitions; use `AcquisitionStore.claim_search_job`.
- `EspoAcquisitionRepository` documents GET-then-PUT MVP; do not assume atomic CRM claim API exists.
- Runner supports `--provider fake` only until real providers are explicitly added.

### Sync Client

- Validate contract before HTTP (`validate_sync_contract`, `evaluate_sync_gate`).
- Never log API keys or full auth headers.

## Tests

- Extension: offline `unittest` only for skeleton acceptance.
- Connector: mock HTTP or use test doubles; live CRM tests gated by env vars.
- No side effects: tests must not require production CRM or external APIs by default.

## Phase Reports

When completing a phase:

1. Record verdict, scope, files changed, and verification commands.
2. Place report under `docs/` or `docs/phase-reports/` per existing convention.
3. Do not mark runtime-verified unless actually executed.

## Parallel Worktrees

If `git status` shows unstaged changes outside your task:

- Do not revert or clean other work.
- Treat `manifest.json` and tests as authority over stale docs.

## Related Documents

- [TESTING.md](TESTING.md)
- [../architecture/BOUNDARIES.md](../architecture/BOUNDARIES.md)
