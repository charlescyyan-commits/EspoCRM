# EspoCRM Extension Architecture Plan V1

## Scope

This is a future implementation layout only. No directories, PHP files, EspoCRM metadata, routes, services, fields, or API endpoints are created in Phase 3A-1.

```text
espocrm_extension/
  custom/
    Espo/
      Custom/
        Resources/
          metadata/
          i18n/
          layouts/
        Entities/
          ResearchEvidence.php
        Controllers/
          ProspectingSync.php
        Services/
          ProspectingSyncService.php
          ProspectingContractValidator.php
          ProspectingIdempotencyService.php
          ResearchEvidenceImportService.php
```

## Future Components

| Component | Responsibility | Must not do |
|---|---|---|
| metadata | Define the planned Lead import fields and `ResearchEvidence` entity/relationship | Modify existing CRM data during installation without migration approval |
| `ProspectingSync` controller | Receive an authenticated, versioned payload | Expose a generic CRM write endpoint or accept unvalidated fields |
| contract validator | Validate JSON schema, semantic gates, version support, and nullable handling | Calculate score or infer missing data |
| idempotency service | Enforce record identity, delivery idempotency, and protected-field conflict detection | Merge unrelated CRM records automatically |
| sync service | Create/update Engine-owned Lead fields and linked evidence in one controlled transaction | Set CRM owner, sales activity, Account, Opportunity, or lifecycle outcome |
| evidence import service | Create/reconcile compact immutable `ResearchEvidence` snapshot records | Store raw HTML, logs, cookies, or technical payloads |

## Future Endpoint Contract

The only planned endpoint is a narrow import endpoint, conceptually:

```text
POST /api/v1/prospecting-engine/import
Content-Type: application/json
Idempotency-Key: <same value as payload.sync.idempotency_key>
```

It accepts exactly `ESPOCRM_SYNC_CONTRACT_V1.json`, authenticates a dedicated service principal, returns one receiver result from `ESPOCRM_SYNC_RULES_V1.md`, and writes an audit record. There is no general-purpose Lead, Account, Opportunity, or Engine-update API.

## Transaction and Error Policy

1. Authenticate the service principal and enforce least privilege.
2. Validate schema and semantic gate before opening a record mutation transaction.
3. Lookup by `record_identity_key`; resolve delivery idempotency.
4. Create/update the Lead's Engine-owned fields and import `ResearchEvidence` snapshot records atomically.
5. Store a receiver audit result with payload hash and timestamps.
6. On any failure, roll back the transaction and return a visible reject/conflict result.

The future receiver must not make external network calls, run research, calculate scores, create emails, or enqueue outreach jobs.

## Security Boundary

- Use a dedicated integration credential scoped to the single import endpoint and import entities.
- Verify payload size, content type, contract major version, and idempotency key before processing.
- Redact source excerpts in receiver errors and logs; never log credentials, cookies, raw HTML, or raw provider payloads.
- Treat `ResearchEvidence` text as untrusted data when rendered in CRM UI.
- Keep Engine-to-CRM transport one-way. CRM event hooks must not write into the Engine.

## Phase 3A-2 Entry Checklist

- Explicit authorization to implement the extension.
- Confirmed EspoCRM version and supported extension conventions.
- Approved exact custom-field naming and Lead status behavior.
- Dedicated integration credential and least-privilege role design.
- Approved migration/install strategy and a disposable test CRM.
- Contract test fixtures accepted, including compatibility and rollback cases.
