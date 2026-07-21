# Phase3C16.2A Quote Workflow Core Report

## Scope

Phase3C16.2A adds the core Quote lifecycle transition service for C16.2. The implementation is limited to Quote state transitions.

Out of scope and not implemented:

- UI buttons or controller actions
- PDF generation
- PI creation or PI workflow
- Approval workflow or Approval record writes
- Notifications
- Connector, worker, queue, or provider integration
- Final quote-number sequence table or sequence implementation

## Files Changed

- `crm-extension/files/custom/Espo/Modules/Prospecting/Services/QuoteTransitionService.php`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Services/QuoteNumberingServiceInterface.php`
- `crm-extension/tests/test_c16_quote_workflow_core.py`
- `crm-extension/tests/test_extension_skeleton.py`
- `deployment/prospecting-extension-1.9.7-alpha.zip`
- `deployment/prospecting-extension-1.9.7-alpha.zip.sha256`
- `docs/PHASE3C16_2A_QUOTE_WORKFLOW_CORE_REPORT.md`

## Service Design

`QuoteTransitionService` follows the existing Prospecting module service pattern:

- Namespace: `Espo\Modules\Prospecting\Services`
- Dependencies: `EntityManager` and `Acl`
- Rejections: Espo core `BadRequest` / `Forbidden`
- Persistence: sets `Quote.status` and saves the entity through `EntityManager`

Public methods:

- `validateTransition(string $currentStatus, string $targetStatus): bool`
- `transition(Entity $quote, string $targetStatus, array $options = []): Entity`

The service includes a protected `afterTransition()` future hook point. C16.2A does not write a separate audit entity, Approval record, EmailEvent, connector record, queue item, or notification.

## Transition Matrix

Allowed in C16.2A:

| From | To | Condition |
|------|----|-----------|
| DRAFT | IN_REVIEW | Allowed; optional numbering boundary invoked if available |
| IN_REVIEW | APPROVED | Allowed |
| APPROVED | SENT | Allowed |
| APPROVED | EXPIRED | Allowed only when `validUntil` has been reached or `adminOverride` is supplied |
| SENT | ACCEPTED | Allowed |
| SENT | REJECTED | Allowed |

Rejected examples covered by tests:

| From | To | Reason |
|------|----|--------|
| SENT | DRAFT | Customer-facing Quote cannot be reset to draft |
| ACCEPTED | DRAFT | Terminal state protection |
| REJECTED | APPROVED | Rejected Quote cannot jump to approved |
| DRAFT | APPROVED | Must pass through review |
| IN_REVIEW | SENT | Must pass through approval |

Terminal states:

- `ACCEPTED`
- `REJECTED`
- `EXPIRED`

## Numbering Boundary

`QuoteNumberingServiceInterface` reserves the ADR boundary for future quote-number assignment:

```php
public function assignQuoteNumber(Entity $quote): string;
```

C16.2A does not implement the final sequence table, `LAST_INSERT_ID`, raw SQL, concurrency strategy, or annual counter. The transition service only calls the optional interface boundary when transitioning from `DRAFT` to `IN_REVIEW` and no `quoteNumber` is already present.

## Tests

Added `test_c16_quote_workflow_core.py` covering:

- Service existence and namespace contract
- Valid transition matrix
- Invalid transition protections
- Terminal state protections
- `APPROVED -> EXPIRED` guard behavior
- Persistence contract
- Numbering interface boundary
- No `DraftApproval`, connector, provider, queue, EmailEvent, PDF, PI, or Approval workflow dependency

Updated `test_extension_skeleton.py` to register the two new approved PHP service files in the existing PHP inventory gate.

## Validation

Commands run:

```powershell
C:\tmp\php-c16\runtime\php.exe -l crm-extension\files\custom\Espo\Modules\Prospecting\Services\QuoteTransitionService.php
C:\tmp\php-c16\runtime\php.exe -l crm-extension\files\custom\Espo\Modules\Prospecting\Services\QuoteNumberingServiceInterface.php
.venv-s01\Scripts\python.exe -m pytest crm-extension\tests\test_c16_quote_workflow_core.py -q
.venv-s01\Scripts\python.exe -m pytest crm-extension\tests\test_c16_entity_contracts.py crm-extension\tests\test_c16_quote_workflow_core.py -q
.venv-s01\Scripts\python.exe -m pytest crm-extension\tests -q
.venv-s01\Scripts\python.exe -c "import json,pathlib; files=list(pathlib.Path('crm-extension').rglob('*.json')); [json.load(open(p, encoding='utf-8')) for p in files]; print(f'JSON PASS {len(files)} files')"
.venv-s01\Scripts\python.exe crm-extension\scripts\build_release_package.py
.venv-s01\Scripts\python.exe crm-extension\scripts\build_release_package.py --check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\testing\run-unified-gate.ps1 -Profile offline -PythonExecutable .venv-s01\Scripts\python.exe -PhpExecutable C:\tmp\php-c16\runtime\php.exe
```

Results:

- PHP lint for new files: PASS
- C16.2A tests: 8 passed
- C16 contract + C16.2A tests: 21 passed
- Extension tests: 96 passed
- JSON validation: 219 files PASS
- Artifact rebuild: PASS
- Artifact SHA-256: `C6D5DD8CE1940852687DEB6F74000051F1002FC00FAF890B09CAF636365CCCB2`
- Artifact `--check`: PASS
- Unified offline gate: PASS

Unified offline gate summary:

- `php-lint`: PASS, 91 passed
- `extension-pytest`: PASS, 96 passed
- `connector-pytest`: PASS, 279 passed
- `root-runtime-pytest`: PASS, 162 passed
- `s01-integrity-pytest`: PASS, 12 passed
- `package-baseline-pytest`: PASS, 5 passed
- `extension-unittest`: PASS, 96 passed
- `artifact-check`: PASS
- `deployment-validation-pytest`: PASS, 2 passed

## Limitations

- No runtime CRM rebuild was executed in this local validation session.
- The final Quote sequence service and `numbering_sequence` table remain deferred.
- The service does not enforce role-specific workflow permissions beyond existing entity edit ACL.
- Approval-driven review consistency is deferred to the Approval workflow phase.
- PDF prerequisites for `APPROVED -> SENT` are not enforced in C16.2A because PDF generation is out of scope.
