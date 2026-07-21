# Phase3C16.1A — Chinese Localization Preparation Audit

**Mode:** read-only audit  
**Version context:** `1.9.7-alpha`  
**Baseline HEAD (pre-report commit):** `8feedaf792c5a41f336a2640af907f08b4cd49ac`  
**Constraint:** no entityDefs, clientDefs, layouts, ACL, workflows, or i18n content were modified. No Chinese translations were authored.

## 1. Localization structure

### 1.1 Canonical location

Prospecting i18n lives only under the packaged module:

```text
crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/
  en_US/
  zh_CN/
```

There is **no** surface mirror at `crm-extension/Resources/i18n/` (unlike entityDefs/ACL). Future C16 i18n must follow this module path — do not invent a new surface-i18n pattern.

### 1.2 Locale pair

| Locale | Role |
| --- | --- |
| `en_US` | Source / primary labels |
| `zh_CN` | Chinese UI labels |

Existing entity files always appear as a matched pair (`en_US/<Entity>.json` + `zh_CN/<Entity>.json`). File-set parity across locales is currently complete for pre-C16 entities (15/15).

### 1.3 Key / document shape (do not invent a new mode)

Observed patterns from Prospecting peers:

| Pattern source | Top-level keys | Used for |
| --- | --- | --- |
| `EmailEvent`, `DraftApproval` | `fields`, `links`, `labels`, `options` (+ optional `tooltips`) | Dedicated CRM entities |
| `Lead`, `Opportunity` | Extension overlays (`fields`, `options`, `tooltips`, …) | Core CRM entities extended by Prospecting |
| `Global.json` | `scopeNames`, `scopeNamesPlural`, `dashlets` | Selected tab/dashboard scopes (acquisition/research center) — **not** used for every entity |

Reference shape for a new C16 entity (match `DraftApproval` / `EmailEvent`):

```json
{
  "fields": { "<fieldName>": "<label>" },
  "links": { "<linkName>": "<label>" },
  "labels": {
    "Create <Entity>": "<create label>",
    "<Entity>s": "<plural label>"
  },
  "options": {
    "<enumField>": { "<OPTION>": "<label>" }
  }
}
```

Notes:

- Enum option keys must match entityDefs option tokens exactly (e.g. `IN_REVIEW`, not `In Review`).
- `labels.Create <Entity>` uses the entity class name with no space (e.g. `Create DraftApproval`).
- Plural label key is typically `<Entity>s` (`DraftApprovals`, `EmailEvents`).
- `tooltips` are optional; several peers already have en_US tooltips missing in zh_CN (pre-existing drift, not C16).

### 1.4 Global scopeNames

`Global.json` currently names acquisition/dashboard scopes only. It does **not** list `DraftApproval`, `EmailEvent`, `SendExecution`, `Lead`, or `Opportunity`.  
Therefore absence of C16 entries in `Global.json` is consistent with many existing entities; tab labels can initially come from entity `labels` / Espo defaults. Adding `scopeNames` / `scopeNamesPlural` for `Quote`, `ProformaInvoice`, and `Approval` is a **recommended later UI step**, not a 1A blocker pattern break.

## 2. C16 coverage

| Entity | `en_US/<Entity>.json` | `zh_CN/<Entity>.json` | `Global.scopeNames` |
| --- | :---: | :---: | :---: |
| Quote | missing | missing | missing |
| QuoteItem | missing | missing | missing |
| ProformaInvoice | missing | missing | missing |
| Approval | missing | missing | missing |

**Coverage verdict:** C16 has **zero** localization files today. Chinese UI readiness for Quote / QuoteItem / ProformaInvoice / Approval is **not started**.

This matches the C16.1A skeleton scope (metadata/ACL only; no client layouts / i18n delivery).

## 3. Missing translations (preparation list)

No en_US stubs exist either. Every required key below is **待翻译** for both locales. Values must be authored later following the existing JSON shape; this audit does not supply Chinese (or English) copy.

### 3.1 Quote

| Key | Status |
| --- | --- |
| `fields.name` | 待翻译 |
| `fields.status` | 待翻译 |
| `fields.quoteNumber` | 待翻译 |
| `fields.validUntil` | 待翻译 |
| `fields.amount` | 待翻译 |
| `fields.opportunity` | 待翻译 |
| `fields.lead` | 待翻译 |
| `links.opportunity` | 待翻译 |
| `links.lead` | 待翻译 |
| `links.quoteItems` | 待翻译 |
| `links.approvals` | 待翻译 |
| `links.proformaInvoices` | 待翻译 |
| `labels.Create Quote` | 待翻译 |
| `labels.Quotes` | 待翻译 |
| `options.status.DRAFT` | 待翻译 |
| `options.status.IN_REVIEW` | 待翻译 |
| `options.status.APPROVED` | 待翻译 |
| `options.status.SENT` | 待翻译 |
| `options.status.ACCEPTED` | 待翻译 |
| `options.status.REJECTED` | 待翻译 |
| `options.status.EXPIRED` | 待翻译 |
| `Global.scopeNames.Quote` *(optional later)* | 待翻译 |
| `Global.scopeNamesPlural.Quote` *(optional later)* | 待翻译 |

### 3.2 QuoteItem

| Key | Status |
| --- | --- |
| `fields.name` | 待翻译 |
| `fields.quantity` | 待翻译 |
| `fields.unitPrice` | 待翻译 |
| `fields.amount` | 待翻译 |
| `fields.quote` | 待翻译 |
| `links.quote` | 待翻译 |
| `labels.Create QuoteItem` | 待翻译 |
| `labels.QuoteItems` | 待翻译 |

### 3.3 ProformaInvoice

| Key | Status |
| --- | --- |
| `fields.name` | 待翻译 |
| `fields.piNumber` | 待翻译 |
| `fields.status` | 待翻译 |
| `fields.paymentStatus` | 待翻译 |
| `fields.quote` | 待翻译 |
| `links.quote` | 待翻译 |
| `links.approvals` | 待翻译 |
| `labels.Create ProformaInvoice` | 待翻译 |
| `labels.ProformaInvoices` | 待翻译 |
| `options.status.DRAFT` | 待翻译 |
| `options.status.ISSUED` | 待翻译 |
| `options.status.SENT` | 待翻译 |
| `options.status.VOID` | 待翻译 |
| `options.paymentStatus.UNPAID` | 待翻译 |
| `options.paymentStatus.PARTIAL` | 待翻译 |
| `options.paymentStatus.PAID` | 待翻译 |
| `options.paymentStatus.OVERDUE` | 待翻译 |
| `Global.scopeNames.ProformaInvoice` *(optional later)* | 待翻译 |
| `Global.scopeNamesPlural.ProformaInvoice` *(optional later)* | 待翻译 |

### 3.4 Approval

| Key | Status |
| --- | --- |
| `fields.name` | 待翻译 |
| `fields.status` | 待翻译 |
| `fields.approvalLevel` | 待翻译 |
| `fields.targetType` | 待翻译 |
| `fields.targetId` | 待翻译 |
| `fields.quote` | 待翻译 |
| `fields.proformaInvoice` | 待翻译 |
| `links.quote` | 待翻译 |
| `links.proformaInvoice` | 待翻译 |
| `labels.Create Approval` | 待翻译 |
| `labels.Approvals` | 待翻译 |
| `options.status.PENDING` | 待翻译 |
| `options.status.APPROVED` | 待翻译 |
| `options.status.REJECTED` | 待翻译 |
| `options.targetType.Quote` | 待翻译 |
| `options.targetType.ProformaInvoice` | 待翻译 |
| `Global.scopeNames.Approval` *(optional later)* | 待翻译 |
| `Global.scopeNamesPlural.Approval` *(optional later)* | 待翻译 |

### 3.5 Files that must be created in a future localization pass

```text
.../i18n/en_US/Quote.json
.../i18n/zh_CN/Quote.json
.../i18n/en_US/QuoteItem.json
.../i18n/zh_CN/QuoteItem.json
.../i18n/en_US/ProformaInvoice.json
.../i18n/zh_CN/ProformaInvoice.json
.../i18n/en_US/Approval.json
.../i18n/zh_CN/Approval.json
```

Optional later: extend `Global.json` (both locales) with C16 tab scope names.

## 4. Key parity result

### 4.1 C16

| Check | Result |
| --- | --- |
| en_US ↔ zh_CN file pair for Quote / QuoteItem / ProformaInvoice / Approval | **N/A — both locales missing** |
| Missing keys | all required keys (see §3) |
| Extra keys | none |
| Naming errors in C16 i18n | none (no files to misname) |

### 4.2 Existing peer parity (context only)

Validated all 15 existing locale pairs for JSON parse success (`json_errors = 0`).

Leaf-key parity:

- Exact parity: Lead, Opportunity, EmailEvent, Global, LearningSignal, ProspectPool, ProspectingDashboard, ProspectingSearch, ResearchEvidence, SalesFeedback, SearchJob, SearchStrategy
- Pre-existing zh_CN gaps (tooltips only): DraftApproval (3), ReplyEvent (2), SendExecution (4)

These peer tooltip gaps are **out of C16 scope**; recorded so a future localization pass does not assume perfect historical parity.

## 5. Recommended next step

1. **Do not** invent a new i18n layout. Place files under `Modules/Prospecting/Resources/i18n/{en_US,zh_CN}/` using the `fields` / `links` / `labels` / `options` shape from `DraftApproval` / `EmailEvent`.
2. Author **en_US stubs first** with complete key sets from §3 (option tokens copied verbatim from entityDefs).
3. Then author **zh_CN** with identical keys only — enforce leaf-key parity in CI/tests before merge.
4. Keep `paymentStatus` options separate from PI `status` options in both languages (do not reuse workflow labels for payment states).
5. Keep C16 `Approval` labels distinct from C11 `DraftApproval` (different entity files; do not overload DraftApproval strings).
6. Defer `Global.scopeNames*` until tab UI polish if entity `labels` prove sufficient in EspoCRM.
7. Optionally add a permanent regression test that C16 en_US/zh_CN key sets match once files exist.

## 6. Validation performed

| Check | Result |
| --- | --- |
| Existing i18n JSON parse (`en_US` + `zh_CN`, 30 files) | PASS |
| C16 i18n JSON | N/A (absent) |
| Metadata / ACL / layouts / workflows modified | **No** |
| Translations authored | **No** |

## 7. Commit decision

This change is **report-only**. Per policy:

- i18n content was **not** created or edited (creating translations is a separate authorized pass).
- Report file alone is eligible for commit/push.

## Verdict

**AUDIT COMPLETE — C16 localization not started; missing-key list prepared; no i18n modifications made.**
