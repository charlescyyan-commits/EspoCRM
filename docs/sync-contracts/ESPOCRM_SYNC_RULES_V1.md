# EspoCRM Sync Rules V1

## Eligibility Rules

The receiving extension validates the JSON schema and then applies this ordered, fail-closed decision sequence:

1. Reject unknown major `contract_version`.
2. Reject a non-canonical or missing `canonical_domain`.
3. Reject any status other than `OUTREACH_READY`.
4. Reject non-V4 scores, null score fields, `D`, or `INSUFFICIENT_EVIDENCE` tiers.
5. Reject coverage below `0.50`, confidence below `0.60`, or no compact evidence item.
6. Reject technical research failure or unavailable website.
7. Reject official-brand exclusions and any conflicting exclusion indicator.
8. Reject evidence or provenance versions the extension cannot interpret.
9. Resolve idempotency and domain conflicts before any CRM record mutation.
10. Create/update the Lead and `ResearchEvidence` records only after all prior rules pass.

## Status and Authority Rules

| Rule | Required behavior |
|---|---|
| Engine authority | May set imported intelligence fields only. It cannot set CRM owner, team, sales status, activity, account, opportunity, or conversion fields. |
| CRM authority | May manage sales execution and human review. It cannot write data back into the Engine or overwrite Engine provenance fields. |
| Imported Lead status | A future extension may use a distinct `Imported - Review Required` Lead status, but human workflow configuration is Phase 3A-2 work. |
| Account creation | Human CRM action only after Lead review. No bulk or automatic conversion. |
| Opportunity creation | Human CRM action only after confirmed commercial pursuit. No opportunity is created from score, tier, or `OUTREACH_READY` alone. |
| Evidence mutation | Evidence snapshots are immutable. A new Engine snapshot is represented as a new import revision, not rewritten history. |

## Idempotency and Duplicate Strategy

Two different keys prevent two different failure modes:

| Key | Calculation | Purpose |
|---|---|---|
| `record_identity_key` | `sha256("espocrm-lead-v1|" + canonical_domain)` | One logical Lead per canonical domain. Used for CRM lookup and duplicate prevention. |
| `idempotency_key` | `sha256("espocrm-sync-v1|" + canonical_domain + "|" + engine_version + "|" + score.rules_version)` | Same Engine/score-version delivery cannot create a second import. |
| `payload_hash` | SHA-256 of canonical serialized payload excluding receiver-generated fields | Detects a changed evidence snapshot or controlled update. |

Receiver behavior:

- Same `idempotency_key` and same `payload_hash`: return prior result; do not create or update another Lead.
- Same `record_identity_key`, new `payload_hash`, compatible version: update only Engine-owned snapshot fields and append/reconcile evidence by `peEvidenceId + peSnapshotHash`.
- Same domain but incompatible company identity or incompatible major version: return `CONFLICT`; require human review.
- Existing CRM Lead has manual edits: never overwrite CRM-owned fields. A future extension logs a field-level conflict if an Engine-owned field was manually changed.

## Official Brand and Technical Failure Protection

- Any official-brand root, regional, store, subdomain, redirect, or confirmed entity identity is denied before CRM import.
- A brand keyword alone is not exclusion evidence; resellers and multi-brand dealers remain eligible when the upstream qualification permits them.
- Marketplace, directory, platform, and media exclusions are denied as business-ineligible records.
- `FAILED_TECHNICAL`, timeout, CAPTCHA, or unavailable websites are denied without treating them as low-quality businesses.

## Version Strategy

| Version | Policy |
|---|---|
| `contract_version` | Semantic version. V1 receiver accepts `1.x` additive changes only; unknown major versions reject. |
| `engine_version` | Stored on every import; it identifies the producing Engine release and does not determine CRM sales behavior. |
| `score.rules_version` | V4 is mandatory for V1 import. V3 is explicitly rejected and remains historical Engine-only data. |
| `evidence_schema_version` | Must be supported by the receiver before evidence records are created. |
| brand registry version | Stored for decision provenance; registry changes are not retroactively applied to historic imports. |

Backward-compatible changes may add optional properties and optional evidence claim types. Removing, renaming, changing a required field's meaning, or lowering gate semantics requires a new major contract and explicit approval.

## Receiver Results

| Result | Meaning |
|---|---|
| `SYNCED` | One Lead and its evidence snapshot were created/updated under idempotent rules. |
| `ALREADY_SYNCED` | The same delivery was previously accepted. |
| `REJECTED_VALIDATION` | Schema or required field validation failed. |
| `REJECTED_GATE` | Qualification, evidence, score, brand, or technical gate failed. |
| `REJECTED_VERSION` | Contract, score, or evidence version is unsupported. |
| `CONFLICT` | Domain identity or protected CRM-field conflict requires human review. |

All results are audit records. None trigger email, enrichment, Lead conversion, Account creation, or Opportunity creation.
