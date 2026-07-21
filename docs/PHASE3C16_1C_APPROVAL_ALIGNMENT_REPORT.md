# Phase3C16.1C Approval Audit Metadata Alignment Report

## Scope

Phase3C16.1C-3 aligns the C16 `Approval` metadata with the architecture audit finding that Approval lacked audit ownership fields.

References reviewed:

- `docs/architecture/ADR_C16_QUOTE_PI_ARCHITECTURE.md`
- `docs/architecture/ADR_C16_STATE_MACHINE_EXTENSIONS.md`

No Approval workflow, hook, service, PDF, connector, worker, provider, or business PHP implementation was added.

## Fields Added

Approval now includes the ADR-required audit fields:

- `requestedBy`: required User link identifying who requested approval.
- `approver`: optional User link identifying who made the decision.
- `decision`: optional enum with `APPROVED` and `REJECTED`.
- `reason`: optional text field for decision rationale.
- `decidedAt`: optional datetime for decision timestamp.

Preserved fields:

- `targetType`
- `targetId`
- `approvalLevel`

Preserved state contract:

- `status`: `PENDING`, `APPROVED`, `REJECTED`
- `decision`: `APPROVED`, `REJECTED` only; it records the terminal decision and does not replace `status`.

## Metadata Surface

Updated metadata surfaces:

- Module entity definition and surface mirror.
- Approval detail and list layouts.
- `en_US` and `zh_CN` Approval i18n.

The new fields use existing EspoCRM metadata patterns:

- User ownership fields use `link` fields with `belongsTo User` links.
- Decision state uses an enum with label styling.
- Audit timestamp uses `datetime`.

## ACL Check

The current extension metadata contains module-level `aclDefs` scaffolding for C16 entities, including Approval. No repository-owned role-level JSON definitions for Sales, Manager, Finance, or Admin were found in the extension metadata surface.

No ACL redesign was performed. The added fields are schema-compatible with the planned role responsibilities:

- Sales: can be represented by `requestedBy`.
- Manager: can be represented by `approver` and `decision` for Quote approvals.
- Finance: can be represented by `approver` and `decision` for PI approvals.
- Admin: remains covered by the existing full-access administrative model.

Field-level write restrictions remain deferred to the future Approval workflow implementation phase.

## Tests

Updated contract tests:

- Field existence for all five audit fields.
- User link contract for `requestedBy` and `approver`.
- Decision enum contract.
- State compatibility between `status` and `decision`.
- Preservation of `targetType`, `targetId`, and `approvalLevel`.
- i18n key coverage for the new fields and decision options.

## Validation

Commands run:

```powershell
.venv-s01\Scripts\python.exe -c "import json,pathlib; files=list(pathlib.Path('crm-extension').rglob('*.json')); [json.load(open(p, encoding='utf-8')) for p in files]; print(f'JSON PASS {len(files)} files')"
.venv-s01\Scripts\python.exe -m pytest crm-extension\tests\test_c16_entity_contracts.py -q
.venv-s01\Scripts\python.exe -m pytest crm-extension\tests -q
.venv-s01\Scripts\python.exe crm-extension\scripts\build_release_package.py
.venv-s01\Scripts\python.exe crm-extension\scripts\build_release_package.py --check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\testing\run-unified-gate.ps1 -Profile offline -PythonExecutable .venv-s01\Scripts\python.exe -PhpExecutable C:\tmp\php-c16\runtime\php.exe
```

Results:

- JSON validation: PASS, 219 files.
- C16 contract tests: PASS, 13 passed.
- Extension tests: PASS, 88 passed.
- Artifact rebuild: PASS.
- Artifact SHA-256: `975384B8AED718980A65DCDBB935687CE316A91674A62C57DCF274DAE3CC5A31`.
- Artifact `--check`: PASS.
- Unified offline gate: PASS.

Unified offline gate summary:

- `php-lint`: PASS, 89 passed.
- `extension-pytest`: PASS, 88 passed.
- `connector-pytest`: PASS, 279 passed.
- `root-runtime-pytest`: PASS, 162 passed.
- `s01-integrity-pytest`: PASS, 12 passed.
- `package-baseline-pytest`: PASS, 5 passed.
- `extension-unittest`: PASS, 88 passed.
- `artifact-check`: PASS.
- `deployment-validation-pytest`: PASS, 2 passed.

## Limitations

- The change is metadata-only. It does not implement ApprovalService, hooks, state transitions, role enforcement, or field-level immutability.
- Runtime CRM rebuild was not executed in this local validation session.
- Role-level Sales/Manager/Finance/Admin ACL provisioning remains outside this metadata alignment task.
