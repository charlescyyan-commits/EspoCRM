# Phase3A28 Opportunity Workflow Report

**Date:** 2026-07-11  
**Scope:** Native EspoCRM Opportunity workflow extension and local validation  
**Verdict:** API and runtime PASS; browser workflow verification BLOCKED by missing local UI credentials

## Architecture and Scope

EspoCRM remains the CRM sales-operation system. Chitu Intelligence remains responsible for discovery, research, scoring, product recommendation, and email generation.

This phase adds only EspoCRM metadata overlays for the native `Opportunity` entity. It does not add a custom frontend, React page, pipeline engine, score computation, email generation, or automated Opportunity creation.

`Phase3A24` integration code and its Lead sync contract were not modified.

## Native Opportunity Audit

EspoCRM 10.0.1 provides the native `Opportunity` entity, detail layout, ACL scope, sales activities, and conversion workflow.

| Requirement | Native EspoCRM evidence | Result |
|---|---|---:|
| Opportunity availability | `Crm` module `Opportunity` entity and native UI scope | PASS |
| Lead conversion targets | `Lead.convertEntityList = [Account, Contact, Opportunity]` | PASS |
| Lead to Account | `Lead.createdAccount` / `Account.originalLead` | PASS |
| Lead to Contact | `Lead.createdContact` / `Contact.originalLead` | PASS |
| Lead to Opportunity | `Lead.createdOpportunity` / `Opportunity.originalLead` | PASS |
| Opportunity to Account | Native `Opportunity.account` relationship | PASS |
| Opportunity to Contact | Native primary `contact` and multiple `contacts` relationships | PASS |
| Sales activities | Native `Task`, `Call`, `Meeting`, and `Email` child relationships | PASS |

Native conversion is invoked through `POST Lead/action/convert`. It is human-triggered in the EspoCRM UI and creates only the selected Account, Contact, and Opportunity records.

## Opportunity Stages

No custom pipeline engine or stage field was created. EspoCRM's native `Opportunity.stage` is preserved:

| MVP meaning | Native stage |
|---|---|
| Prospecting | `Prospecting` |
| Qualification | `Qualification` |
| Proposal | `Proposal` |
| Negotiation | `Negotiation` |
| Won | `Closed Won` |
| Lost | `Closed Lost` |

`Closed Won` and `Closed Lost` are retained instead of renaming them to `Won` and `Lost`, preserving EspoCRM's built-in closed-stage behavior and reporting semantics.

## Fields Added

All fields are nullable and CRM-owned. They are not populated by the Chitu sync path.

| Field | Type | Purpose |
|---|---|---|
| `peOpportunitySource` | `varchar(100)` | Opportunity source context |
| `peProductInterest` | `varchar(255)` | Product interest context |
| `peEstimatedValue` | `currency` | Optional estimated-value context |
| `peExpectedCloseDate` | `date` | Optional expected-close context |

Native Opportunity fields remain authoritative for commercial record data:

- `stage` for sales stage
- `amount` for CRM sales amount
- `closeDate` for CRM close date
- `account`, `contact`, `contacts`, and `originalLead` for relationships

The new `peEstimatedValue` and `peExpectedCloseDate` fields provide optional Customer Intelligence context; they do not overwrite native `amount` or `closeDate`.

## Metadata and Layout Changes

The native Opportunity detail layout keeps its existing Overview fields and adds one native panel:

| Section | Fields |
|---|---|
| Customer Intelligence | Product Interest, Opportunity Source, Estimated Value, Expected Close Date |

No Opportunity links, native stages, scope definitions, controllers, services, or core EspoCRM files were overridden.

## Validation Results

### Runtime and Extension

| Check | Result |
|---|---:|
| `espocrm` container health | PASS |
| Metadata/layout/translation files deployed | PASS |
| `php command.php clear-cache` | PASS |
| `php command.php rebuild` | PASS |
| Runtime metadata exposes four required Opportunity fields | PASS |

### API, Conversion, and Relationships

Synthetic marker: `[CHITU_PHASE3A28_TEST]`.

| Check | Result |
|---|---:|
| Create synthetic qualified Lead | PASS |
| Native Lead conversion to Account + Contact + Opportunity | PASS |
| Converted Lead status | PASS: `Converted` |
| Opportunity creation | PASS |
| Stage persistence | PASS: `Prospecting` |
| Native amount and close-date persistence | PASS: `50000`, `2026-09-30` |
| `peProductInterest` persistence | PASS: `Resin Tank` |
| `peOpportunitySource` persistence | PASS: `Qualified Lead Conversion` |
| `peEstimatedValue` persistence | PASS: `50000` |
| `peExpectedCloseDate` persistence | PASS: `2026-09-30` |
| Opportunity `accountId` relationship | PASS |
| Opportunity primary `contactId` relationship | PASS |
| Opportunity `contactsIds` relationship | PASS |
| Opportunity `originalLeadId` relationship | PASS |
| Synthetic residue after cleanup | PASS: no active Lead, Account, Contact, or Opportunity records |

### ACL Verification

The local `chitu_ai_connector` API user has the following effective permissions:

| Entity | Create | Read | Edit | Delete |
|---|---:|---:|---:|---:|
| Lead | yes | all | all | all |
| Account | yes | all | all | no |
| Contact | yes | all | all | no |
| Opportunity | yes | all | all | no |

Conversion and read/edit verification passed under these native ACLs. The expected API delete denials for Account, Contact, and Opportunity were enforced; only marker-guarded synthetic residue was removed through the local system cleanup path.

### Existing Lead Workflow Regression

| Check | Result |
|---|---:|
| `run_local_synthetic_sync()` create/read/link/rollback | PASS |
| `espocrm_extension.tests.test_extension_skeleton` | PASS: 16 tests |
| `tests.test_espocrm_sync_adapter` | PASS: 20 tests |
| `tests.test_espocrm_real_client` | PASS: 9 tests |
| Total automated tests | PASS: 45 tests |

### Browser Verification

| Check | Result |
|---|---:|
| Browser reaches native EspoCRM login screen | PASS |
| Lead conversion UI | BLOCKED |
| Opportunity visibility UI | BLOCKED |
| Customer Intelligence layout rendering UI | BLOCKED |

The local test environment contains an API key only. It has no configured UI-capable `ESPOCRM_TEST_USERNAME`/`ESPOCRM_TEST_PASSWORD` or admin username/password. No account configuration was changed solely to bypass this authentication boundary. Therefore the browser could confirm the healthy native login page, but could not complete authenticated UI checks.

## Files Changed

- `espocrm_extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/Opportunity.json`
- `espocrm_extension/Resources/entityDefs/Opportunity.json`
- `espocrm_extension/files/custom/Espo/Modules/Prospecting/Resources/layouts/Opportunity/detail.json`
- `espocrm_extension/Resources/layouts/Opportunity/detail.json`
- `espocrm_extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/Opportunity.json`
- `espocrm_extension/tests/test_extension_skeleton.py`
- `docs/espocrm-extension/PHASE3A28_OPPORTUNITY_WORKFLOW_REPORT.md`

## Explicit Non-Changes

- No EspoCRM core files were modified.
- No custom frontend, React page, or EspoCRM UI replacement was created.
- No custom pipeline engine was created.
- No Chitu scoring or email-generation logic moved into EspoCRM.
- No automatic Lead, Account, Contact, or Opportunity creation was added to the Chitu sync path.
- No Phase3A24 foundation code, contract, or Lead-sync behavior was modified.

## Completion Status

The native Opportunity workflow is implemented and passes runtime, metadata, API CRUD, field-persistence, relationship, ACL, synthetic-conversion, cleanup, and Lead-sync regression verification.

To close the final browser verification gate, provide a disposable local EspoCRM UI session or credentials for the existing local test environment. No architecture redesign or core modification is required.
