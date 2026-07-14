# Phase3C10.6 — Evidence Production Alignment Report

## Status

**PASS WITH RISKS** — the production PHP write path now has deterministic
identity lookup and a schema-level active-row uniqueness definition. The
database preflight completed without duplicate groups, while the metadata
rebuild has intentionally not been run against the shared CRM database.

## Changed files

- `crm-extension/files/custom/Espo/Modules/Prospecting/Services/ChituSyncService.php`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/ResearchEvidence.json`
- `crm-extension/Resources/entityDefs/ResearchEvidence.json`
- `deployment/provisioning/phase3c10_6_check_research_evidence_duplicates.php`
- `chitu-connector/chitu_connector/espocrm_sync/research_evidence_persistence.py`
- `chitu-connector/chitu_connector/espocrm_sync/mapper.py`
- `chitu-connector/chitu_connector/espocrm_sync/contract.py`
- `docs/sync-contracts/ESPOCRM_SYNC_CONTRACT_V1.json`
- `crm-extension/tests/test_extension_skeleton.py`
- `chitu-connector/tests/test_phase3c10_6_evidence_production_alignment.py`

## Production path: before and after

Before C10.6 the automated production path was:

`ProspectingConnectorClient.sync_evidence → POST /Prospecting/sync/evidence → PostSyncEvidence → ChituSyncService::syncEvidence → unconditional INSERT`

Every call created a new `ResearchEvidence` row. The PHP writer assigned
`peEvidenceType` from `claim_type`; the Python
`ResearchEvidencePersistenceAdapter` was not part of this runtime path.

After C10.6 the same endpoint remains the production writer and keeps the
existing request/response shape. For every evidence item it now:

1. Normalizes source URL, evidence format type, and claim text.
2. Computes C10.6 identity columns.
3. Looks up an existing active `ResearchEvidence` row by those columns.
4. Updates snapshot metadata and evidence payload fields when found, or creates
   one row when absent.
5. Relies on the database unique index as the final concurrent-insert guard.

`peEvidenceType` receives `payload.evidence_type`; it never receives
`claim_type`. The V1 pass-through is optional and backward compatible: required
V1 fields and `contract_version: "1.0"` are unchanged. A legacy producer that
omits the optional value is stored as `LEGACY_UNKNOWN`, rather than incorrectly
reusing `claim_type`.

## Identity definition

The active-row business identity is:

`leadId + canonicalUrl + normalizedEvidenceType + claimSha256`

- `canonicalUrl`: HTTP(S) scheme/host normalization, default-port removal,
  slash normalization, fragment removal, and sorted canonical query pairs.
- `normalizedEvidenceType`: collapsed whitespace and lower case.
- `claimSha256`: SHA-256 of the whitespace-normalized claim text.

The metadata index includes EspoCRM `deleteId` in addition to the four identity
columns. This is EspoCRM's soft-delete-safe implementation of uniqueness: only
active rows share the business identity, while a deleted row does not prevent a
future active record from being created.

## Migration status

EspoCRM entity metadata now declares `c10EvidenceIdentity` as a unique index
on `leadId`, `peCanonicalUrl`, `peEvidenceTypeNormalized`, `peClaimHash`, and
`deleteId`, with `deleteId: true`. EspoCRM creates metadata-defined indexes on
a database rebuild.

The read-only preflight script
`deployment/provisioning/phase3c10_6_check_research_evidence_duplicates.php`
must run before that rebuild. It reports duplicate active identity groups and
returns exit code `2` when manual remediation is required; it never updates or
deletes records. The local container preflight completed with
`READY_FOR_REBUILD`, zero duplicate groups, and zero skipped records. No
backfill, rebuild, or DDL execution was run, so shared-database migration
status is **PRECHECK PASS / DDL PENDING**.

## Python adapter positioning

`ResearchEvidencePersistenceAdapter` remains in place, but its module and
class documentation now explicitly identify it as a reference implementation
and contract-test utility. Production evidence writes remain PHP
`ChituSyncService::syncEvidence`; no runtime dependency on the Python adapter
was introduced.

## Tests and checks

- `test_phase3c10_6_evidence_production_alignment.py`: **6/6 PASS**
  - same payload twice creates one record;
  - same URL with a different claim hash creates two records;
  - `claim_type=PRODUCT`, `evidence_type=CUSTOMER_CASE` maps to
    `peEvidenceType=CUSTOMER_CASE`;
  - duplicate sync updates snapshot metadata without creation;
  - idempotent retry preserves one identity;
  - PHP handler, contract pass-through, and unique-index metadata are checked.
- C10.0–C10.6 related tests: **43/43 PASS**.
- C07 evidence tests: **21/21 PASS**.
- PHP lint: `ChituSyncService.php` and the duplicate-check script **PASS** in
  the local EspoCRM container.
- Complete Regression Gate: **7/7 required suites PASS** — Extension 57,
  Connector 270, Worker 31, Static 2, Runtime 11, and Baseline 3.

## Risks

- The unique index is not live until EspoCRM metadata is rebuilt. The preflight
  found no duplicate groups, but this patch intentionally does not execute DDL
  or alter historic data.
- Historic rows written before C10.6 can contain `claim_type` in
  `peEvidenceType`; the preflight flags its legacy-evaluation limitation so
  those rows receive manual review before any backfill or remediation.
- The optional `evidence_type` V1 pass-through is non-breaking, but external
  producers that have not yet upgraded will retain the explicit
  `LEGACY_UNKNOWN` classification instead of a source-format classification.
- Database-level conflict handling is intentionally left to the unique index;
  callers will receive the platform's constraint failure for a true concurrent
  insert race rather than silently creating a duplicate.

## Boundary confirmation

**No Outreach Lifecycle contract changed.** C09 draft generation, C10
approval/send/reply behavior, Provider code, Worker code, and CRM Opportunity
workflow logic were not modified.
