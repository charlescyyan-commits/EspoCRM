# Phase3C16.2D Hotfix — Invalid Core Exception Namespace

**Mode:** surgical hotfix  
**Baseline HEAD:** `8fcd676d378b503a83d689ddfab3b7f87b003012` (`@ phase3c16: add runtime smoke report`)  
**Version:** `1.9.7-alpha`  
**Scope boundary:** no ApprovalService, no QuoteTransition redesign, no ACL/metadata/UI/C16.3 work.

## 1. Original defect

`crm-extension/files/custom/Espo/Modules/Prospecting/Services/QuoteWorkflowActionService.php` imported Espo HTTP exceptions from a non-existent collapsed namespace:

```php
use Espo\CoreExceptions\BadRequest;
use Espo\CoreExceptions\Forbidden;
use Espo\CoreExceptions\NotFound;
```

EspoCRM’s real exception classes live under `Espo\Core\Exceptions\…`. Sibling services already used the correct form (`QuoteTransitionService`, `PostQuoteWorkflowAction`, `ChituSyncService`, etc.).

## 2. Root cause

A typo / namespace collapse: `Espo\Core\Exceptions` was written as `Espo\CoreExceptions`. Static/offline tests that only grepped action strings and ACL behavior did not execute PHP autoload, so C16.2C/C16.2D could pass while a live EspoCRM request to the Quote workflow action would fail at class resolution.

## 3. Files changed

| File | Change |
| --- | --- |
| `…/Services/QuoteWorkflowActionService.php` | Corrected three `use` imports to `Espo\Core\Exceptions\{BadRequest,Forbidden,NotFound}` |
| `crm-extension/tests/test_espo_php_namespace_contracts.py` | New permanent static contract scanning all packaged PHP under `crm-extension/files` |
| `deployment/prospecting-extension-1.9.7-alpha.zip` | Rebuilt to match source |
| `deployment/prospecting-extension-1.9.7-alpha.zip.sha256` | Regenerated sidecar |
| `docs/PHASE3C16_2D_HOTFIX_REPORT.md` | This report |

## 4. Regression protection

`test_espo_php_namespace_contracts.py` now:

1. Scans every `*.php` under `crm-extension/files`.
2. **Rejects** forbidden fragment `Espo\CoreExceptions\`.
3. Asserts every `use` / `namespace` Espo reference starts with a known-valid prefix discovered from this repository: `Espo\Core\`, `Espo\ORM\`, `Espo\Entities\`, `Espo\Modules\Prospecting\`, `Espo\Custom\`.
4. Pin-checks `QuoteWorkflowActionService.php` for the three corrected imports.

Pre-fix, assertion (2)/(4) would fail on the collapsed imports; post-fix all three tests pass.

## 5. Test / gate results

| Gate | Result |
| --- | --- |
| `php -l` on QuoteWorkflowActionService / PostQuoteWorkflowAction / QuoteTransitionService | PASS (no syntax errors) |
| Unified gate `php-lint` (94 packaged PHP files) | PASS |
| Namespace contract pytest | 3 passed |
| Focused C16 pytest (entity + workflow + numbering + UI actions) | 35 passed |
| Extension pytest | 113 passed (+22 subtests) |
| Unified offline gate (post-rebuild) | **PASS** — php-lint, extension, connector (279), root/runtime (162), S01 integrity (12), package baseline (5), extension unittest (113), artifact-check, deployment-validation |

Pre-rebuild, S01 integrity / artifact-check correctly failed because the ZIP still contained the broken imports; that was expected and resolved by rebuilding.

## 6. Artifact verification

- Artifact: `deployment/prospecting-extension-1.9.7-alpha.zip`
- SHA-256: `F8B0CC5315F23299525FA3F3D807826A09EBFDA26C4386AD1DC4A1EF636B90EF`
- Sidecar matches archive hash and filename (case-insensitive hex).
- `build_release_package.py --check`: PASS (source bytes match archive, including corrected `QuoteWorkflowActionService.php`).

## 7. Untouched boundaries

No ApprovalService, QuoteTransitionService logic changes, ACL, metadata, clientDefs, layouts, i18n, or C16.3 work.

## Verdict

**PASS**
