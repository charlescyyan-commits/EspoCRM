# EspoCRM Sync Adapter Implementation Report V1

## Modules Created

| Module | Responsibility |
|---|---|
| `models.py` | Typed source, result, gate, mock, and audit models. |
| `contract.py` | V1 payload model and offline structural validation. |
| `mapper.py` | Engine-to-contract and contract-to-Lead-field mapping. |
| `gate.py` | Ordered, fail-closed import eligibility checks. |
| `idempotency.py` | Domain identity, delivery idempotency, evidence snapshot, and payload hashes. |
| `client.py` | Memory-only mock target plus adapter orchestration. |
| `audit.py` | In-memory audit log. |

## Mapping Rules

- Company name, normalized website, and direct-evidence country map from `Candidate` and `WebsiteResearchResult`.
- Candidate source is normalized to one of the unchanged contract's allowed source channels.
- V4 maps `opportunity_score`, tier, confidence, coverage, score-rule version, result hash, recommendation, and reason codes without recomputation.
- Country is null unless the research result has direct country evidence and is not inference-based.
- Lead fields follow `ESPOCRM_ENTITY_MAPPING_DESIGN_V1.md`; no CRM-owned field is emitted.
- Compact evidence follows V1 exactly; `evidence_references()` returns only ID and claim type for lightweight CRM-facing handling.

## Gate Rules

The adapter allows only `OUTREACH_READY` sources that have Canonical Scoring V4, tier A/B/C, score, coverage at least 0.50, confidence at least 0.60, compact evidence, an accessible non-failed research result, and no official-brand or business exclusion. It rejects before mock client invocation otherwise.

## Idempotency Design

- Logical record identity: SHA-256 of `espocrm-lead-v1|canonical_domain`.
- Delivery key: SHA-256 of `espocrm-sync-v1|canonical_domain|engine_version|score_rules_version|contract_version`, matching the existing V1 sync-rules requirement.
- Payload hash: canonical JSON excluding volatile `requested_at` and the hash field itself.
- Evidence snapshot hash: preserved from research output when available; otherwise deterministically derived from compact evidence items.

## Mock and Audit Behavior

`MockEspoCRMClient` keeps only process-memory history. It returns `SUCCESS`, `DUPLICATE`, or `VALIDATION_ERROR` and makes no HTTP request. The adapter converts those outcomes to audit states `SYNCED`, `DUPLICATE`, or `REJECTED`; the preliminary `READY` state is always recorded.

## Contract Compatibility Note

The task's abbreviated evidence-reference example is implemented as a lightweight helper, while the primary payload retains the compact evidence fields mandated by `ESPOCRM_SYNC_CONTRACT_V1.json`. No contract change was made.
