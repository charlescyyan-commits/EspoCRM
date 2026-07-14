# Phase3C10.6.1 — ResearchEvidence Unique Index Activation Report

## Status

**PASS** — the existing C10.6 ResearchEvidence identity metadata and PHP writer
were deployed to the running local EspoCRM overlay, then activated with the
standard EspoCRM rebuild and cache-clear operations.

## Backup

Backup completed before deployment and rebuild:

`D:\EspoCRM-Production\temp\backups\phase3c10_6_1-20260714-151113`

It contains a consistent MariaDB logical dump plus copies of the active
EspoCRM `custom` and `data` directories.

## Deployed existing C10.6 files

Only the already-completed workspace files below were copied into the running
`/var/www/html/custom` overlay:

- `Espo/Modules/Prospecting/Resources/metadata/entityDefs/ResearchEvidence.json`
- `Espo/Modules/Prospecting/Services/ChituSyncService.php`

No source design, fields, schema definitions, or business data were changed in
this activation phase.

## Activation

Commands completed successfully inside the `espocrm` container:

```text
php command.php rebuild
php command.php clear-cache
```

The deployed PHP service also passed `php -l` before activation.

## Verification

### Runtime metadata

The active ResearchEvidence metadata overlay contains
`c10EvidenceIdentity` and the identity fields:

- `peCanonicalUrl`
- `peEvidenceTypeNormalized`
- `peClaimHash`

The successful rebuild created the matching database key, which confirms that
EspoCRM loaded the deployed metadata.

### PHP mapping

The deployed production writer contains:

```php
'peEvidenceType' => $this->evidenceType($item)
```

`evidenceType` receives `evidence_type` when supplied and never maps
`claim_type` into `peEvidenceType`.

### Database unique index

Post-rebuild schema inspection of `research_evidence` returned:

```text
UNIQUE KEY UNIQ_C10_EVIDENCE_IDENTITY
(lead_id, pe_canonical_url, pe_evidence_type_normalized, pe_claim_hash, delete_id)
```

`delete_id` is the existing EspoCRM soft-delete-safe component of the unique
key; active records are protected by the C10.6 business identity columns.

### Historical duplicate precheck

The read-only duplicate precheck was rerun after rebuild:

```text
status: READY_FOR_REBUILD
duplicateGroups: []
skippedRecordIds: []
```

No record was modified or deleted by the check.

### Regression Gate

Complete Regression Gate: **PASS, 7/7 required suites**.

| Suite | Result |
| --- | --- |
| Extension | 57/57 PASS |
| Connector | 270/270 PASS |
| Worker | 31/31 PASS |
| Static | 2/2 PASS |
| Runtime | 11/11 PASS |
| Baseline | 3/3 PASS |

Gate result artifact:

`D:\EspoCRM-Production\temp\test-results\regression-gate-20260714-151601-457.json`

## Boundary confirmation

This phase only deployed existing C10.6 ResearchEvidence metadata and PHP
writer changes. It did not modify Outreach Lifecycle contracts, Provider,
Worker, CRM Opportunity workflow, or CRM business records. No git commit was
created.
