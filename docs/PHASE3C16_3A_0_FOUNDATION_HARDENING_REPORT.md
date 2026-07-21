# Phase3C16.3A-0 — Foundation Hardening Report

**Mode:** foundation hardening only (not C16.3 implementation)  
**Baseline HEAD:** `ce934b02f76ee28f280cbe616ff8463ef4c4b3ea`  
**Version:** `1.9.7-alpha`

## 1. Findings

### 1.1 i18n scope labels

Entity-level `en_US` / `zh_CN` files for `Quote`, `QuoteItem`, `ProformaInvoice`, and `Approval` already existed with field/link/label/option coverage and locale key parity.

Gap: `Global.json` `scopeNames` / `scopeNamesPlural` omitted all four C16 entities, so tab/menu scope labels would fall back to raw entity names in Chinese UI.

### 1.2 DI fail-fast

`QuoteTransitionService` accepted an optional nullable numbering dependency:

```php
private ?QuoteNumberingServiceInterface $numberingService = null
```

When unresolved, `assignQuoteNumberBoundary()` returned early and DRAFT→IN_REVIEW transitions proceeded **without** assigning a quote number. That is silent business-behavior disablement.

Other C16 services audited:

| Service | Constructor DI | Action |
| --- | --- | --- |
| `QuoteNumberingService` | mandatory `PDO` | none |
| `QuoteWorkflowActionService` | mandatory `QuoteTransitionService` (+ Acl/User/EM) | none |
| `QuoteTransitionService` | nullable numbering interface | **fixed** |

No other confirmed required C16 service dependency used the silent-null pattern.

## 2. Fixes

1. Added C16 entries to `Global.json` (`en_US` + `zh_CN`) for `scopeNames` / `scopeNamesPlural`.
2. Made `QuoteNumberingServiceInterface` a **mandatory** constructor dependency of `QuoteTransitionService`.
3. Removed the `$this->numberingService === null` short-circuit; existing quote numbers still skip reassignment.
4. Updated workflow-core tests to require fail-fast DI and forbid the nullable pattern.
5. Added `test_c16_i18n_foundation.py` for Global scope coverage and C16 locale key parity.
6. Rebuilt `deployment/prospecting-extension-1.9.7-alpha.zip` (+ sidecar) so the artifact matches source.

## 3. Files changed

- `crm-extension/files/.../i18n/en_US/Global.json`
- `crm-extension/files/.../i18n/zh_CN/Global.json`
- `crm-extension/files/.../Services/QuoteTransitionService.php`
- `crm-extension/tests/test_c16_quote_workflow_core.py`
- `crm-extension/tests/test_c16_i18n_foundation.py`
- `deployment/prospecting-extension-1.9.7-alpha.zip`
- `deployment/prospecting-extension-1.9.7-alpha.zip.sha256`
- `docs/PHASE3C16_3A_0_FOUNDATION_HARDENING_REPORT.md`

## 4. Tests

| Check | Result |
| --- | --- |
| `php -l QuoteTransitionService.php` | PASS |
| Focused C16 + namespace + i18n foundation pytest | 41 passed |
| Extension pytest | 116 passed (+22 subtests) |
| Unified offline gate | PASS (php-lint 94, extension 116, connector 279, root/runtime 162, S01 12, baseline 5, unittest 116, artifact-check, deployment-validation) |
| Artifact SHA-256 | `B7423923802FC1BE90A7A9A92BF9F3EA7772183D9A99E8CAAA6DF98DE0AE0BAF` |

## 5. Remaining C16.3A scope

Still required for C16.3A (not done here):

- `ApprovalService` core
- Approval workflow transitions / decision recording
- Quote ↔ Approval propagation rules
- Interface→implementation container binding for `QuoteNumberingServiceInterface` if Espo runtime resolution needs an explicit binding map
- Any Approval UI / API / ACL work

## NOT IMPLEMENTED

- ApprovalService
- Approval workflow
- Quote propagation
- UI
- API route changes
- ACL / metadata / Quote status matrix changes

## Verdict

**PASS**
