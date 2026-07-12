# Phase 3A-2.3 EspoCRM Extension Skeleton Report

**Date:** 2026-07-11  
**Scope:** local EspoCRM metadata extension only  
**Status:** IMPLEMENTED; API preflight blocked by existing API-user ACL

## Audit Result

`integration/espocrm_sync/real_client.py` requires these runtime metadata items before it allows any sync operation:

- Lead base fields `name`, `website`, `description` plus eight `pe*` fields.
- `ResearchEvidence` and its ten required fields.
- Lead link `researchEvidences`.

No preflight condition, authentication implementation, sync logic, or contract field was changed.

## Extension Files Created

### Module package

- `espocrm_extension/files/custom/Espo/Modules/Prospecting/Entities/ResearchEvidence.php`
- `espocrm_extension/files/custom/Espo/Modules/Prospecting/Controllers/ResearchEvidence.php`

### Runtime-safe Custom overlay

- `espocrm_extension/files/custom/Espo/Custom/Resources/metadata/entityDefs/Lead.json`
- `espocrm_extension/files/custom/Espo/Custom/Resources/metadata/entityDefs/ResearchEvidence.json`
- `espocrm_extension/files/custom/Espo/Custom/Resources/metadata/scopes/ResearchEvidence.json`
- `espocrm_extension/files/custom/Espo/Custom/Resources/metadata/clientDefs/ResearchEvidence.json`
- `espocrm_extension/files/custom/Espo/Custom/Entities/ResearchEvidence.php`
- `espocrm_extension/files/custom/Espo/Custom/Controllers/ResearchEvidence.php`

The Custom overlay uses EspoCRM's supported `custom/Espo/Custom` location. No `application/Espo`, vendor, or core file was changed.

## Entity, Fields, and Relationship

| Item | Result |
|---|---|
| Lead score fields | `peOpportunityScoreV4`, `peConfidence`, `peEvidenceCoverage` are floats; `peScoreTier` is enum; product/qualification/version fields are nullable varchars. |
| ResearchEvidence entity | Registered as a standard EspoCRM entity with minimal `Entity` class and standard `Record` controller; no sync business methods. |
| ResearchEvidence fields | `peEvidenceId`, `peClaim`, `peClaimType`, `peSourceUrl`, `peEvidenceText`, `peConfidence`, `peCapturedAt`, `peSchemaVersion`, `peSnapshotHash`, plus required `name`. |
| Lead relationship | `Lead.researchEvidences` is `hasMany`; `ResearchEvidence.lead` is `belongsTo`. |

## Installation and Metadata Verification

1. Copied the extension metadata into the local Docker volume at `/var/www/html/custom/Espo/`.
2. Ran only the EspoCRM standard command `php command.php rebuild`; no SQL or manual table alteration was used.
3. Verified PHP syntax for all installed `ResearchEvidence` entity/controller shells.
4. Verified generated cache contains `ResearchEvidence`, `Espo\Custom\Entities\ResearchEvidence`, `Espo\Custom\Controllers\ResearchEvidence`, the entity definition, and the Lead relationship.
5. Verified extension package tests: **12/12 PASS**.

## API Preflight Result

| Check | Result |
|---|---|
| `X-Api-Key` authentication as `chitu_ai_connector` | PASS |
| Local target | PASS - `http://localhost:8080` only |
| Runtime metadata cache | PASS - ResearchEvidence is registered |
| `preflight()` through API user | FAIL |
| Failure cause | Existing API-user ACL marks `ResearchEvidence` false, so `GET Metadata` strips entity fields and Lead relationship from the API response. |

The failure is authorization visibility, not missing entity metadata. Updating the API user's role/ACL would modify authentication/authorization configuration and is explicitly outside this task; no bypass was added.

## Data Operation Confirmation

- Lead POST: not called.
- ResearchEvidence POST: not called.
- Relationship POST: not called.
- Lead/Evidence delete: not called.
- Real customer data: untouched.
- Email, SMTP, DeepSeek, Apify, Playwright: not called.

## Minimal Unblock Action

An authorized administrator must grant the existing local API user's role visibility to `ResearchEvidence` (at least read access for preflight; create/edit/delete only when a separately authorized synthetic sync begins). Then rerun `authenticate()` and `preflight()` unchanged.
