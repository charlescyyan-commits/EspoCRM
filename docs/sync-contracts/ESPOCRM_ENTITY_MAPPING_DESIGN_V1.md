# EspoCRM Entity Mapping Design V1

## Mapping Summary

| Engine concept | EspoCRM target | Sync action | Rationale |
|---|---|---|---|
| eligible prospect | Lead | create or controlled update | A prospect remains unconfirmed until human CRM review |
| verified commercial customer | Account | human-only creation/conversion | Not every discovered or outreach-ready prospect is an Account |
| qualified sales pursuit | Opportunity | human-only creation | An Opportunity represents a sales chance, not a search result |
| evidence item | custom `ResearchEvidence` | create or controlled update | Preserves traceable, queryable support without overloading Lead fields |
| raw research and scoring process | Engine only | never synchronized | Too large, sensitive, or non-sales-operational |

## Lead Mapping

The future extension creates a Lead only after the synchronization gate passes. It searches by `peCanonicalDomain` before creating a record. The Engine may update only fields in the **Engine-owned import** group; it must not overwrite CRM ownership, human decisions, or commercial activity.

| CRM field | Contract path | Required | Nullable | Ownership | Notes |
|---|---|---:|---:|---|---|
| `name` | `company.name` | Yes | No | Engine at import | Display company name; future extension maps to the selected Espo Lead display/name convention. |
| `website` | `company.website` | Yes | No | Engine at import | HTTPS URL, normalized from researched site. |
| `country` | `company.country_code` | No | Yes | Engine at import | Only direct evidence-backed country; target/search country is not substituted. |
| `leadSource` | `source.channel` | Yes | No | Engine at import | Controlled enum such as `WEB_SEARCH` or `CONTROLLED_MANUAL_INPUT`. |
| `peCandidateId` | `identity.candidate_id` | Yes | No | Engine immutable | Engine candidate trace key. |
| `peCanonicalDomain` | `identity.canonical_domain` | Yes | No | Engine immutable | Lowercase canonical logical identity; unique import key. |
| `peQualificationStatus` | `qualification.status` | Yes | No | Engine snapshot | Must be `OUTREACH_READY` for import. |
| `peResearchStatus` | `research.status` | Yes | No | Engine snapshot | `COMPLETE` is required by the gate. |
| `peCustomerType` | `qualification.customer_type` | No | Yes | Engine snapshot | Business identity, not a CRM lifecycle status. |
| `peOpportunityScoreV4` | `score.value` | Yes | No | Engine snapshot | Normalized V4 score, 0-100. |
| `peScoreTier` | `score.score_tier` | Yes | No | Engine snapshot | `A`, `B`, or `C` only for import. |
| `peConfidence` | `score.aggregate_confidence` | Yes | No | Engine snapshot | Decimal 0-1. |
| `peEvidenceCoverage` | `score.evidence_coverage` | Yes | No | Engine snapshot | Decimal 0-1. |
| `peBestFirstProduct` | `recommendation.best_first_product` | No | Yes | Engine snapshot | Recommendation, not a quoted product or deal item. |
| `peCrossSellPath` | `recommendation.cross_sell_path` | No | Yes | Engine snapshot | Compact ordered string list; no raw reasoning. |
| `peEngineVersion` | `provenance.engine_version` | Yes | No | Engine immutable | Engine release identifier. |
| `peScoreRulesVersion` | `score.rules_version` | Yes | No | Engine immutable | Must identify V4. |
| `peEvidenceSchemaVersion` | `provenance.evidence_schema_version` | Yes | No | Engine immutable | Evidence item interpretation version. |
| `peRegistryVersion` | `provenance.official_brand_registry_version` | No | Yes | Engine immutable | Brand-filter registry used in decision. |
| `peEvidenceSnapshotHash` | `provenance.evidence_snapshot_hash` | Yes | No | Engine immutable | Hash for the exact imported evidence snapshot. |
| `peSyncStatus` | `sync.status` | Yes | No | Extension-owned | `PENDING`, `SYNCED`, `REJECTED`, or `CONFLICT`; never used as sales status. |
| `peSyncedAt` | `sync.synced_at` | No | Yes | Extension-owned | Receiver timestamp, not Engine research time. |

### Lead Fields That Must Never Be Imported

- raw HTML, page captures, crawler logs, request/response headers, cookies, technical debug data, secrets, or provider payloads;
- raw search result payloads, raw score decision objects, detailed score component calculations, or full scoring prompts;
- CRM owner, team, status, follow-up dates, calls, meetings, email activities, conversion decision, or sales-stage data; and
- inferred company country without direct evidence.

## Account Mapping and Transition Proposal

The future extension must **not** create Accounts automatically. A Lead becomes Account-eligible only after a CRM user confirms that the company is a real customer/prospect relationship worth managing as an account. The Engine may provide a `account_transition_proposal` with `eligible: true` only as non-binding context.

| Proposed Account field | Source | Required at human conversion | Notes |
|---|---|---:|---|
| `name` | `company.name` | Yes | Human may correct CRM display name. |
| `website` | `company.website` | Yes | Revalidated by CRM user if needed. |
| `billingAddressCountry` | `company.country_code` | No | Leave null when country is not direct-evidence supported. |
| `peCanonicalDomain` | `identity.canonical_domain` | Yes | Retained as duplicate guard and provenance link. |
| `peEngineSnapshotHash` | `provenance.evidence_snapshot_hash` | Yes | Records the intelligence snapshot that prompted review. |

The proposed transition cannot update an existing Account, merge Accounts, choose an owner, or create customer/contact records. Those remain explicit CRM-user decisions.

## Opportunity Mapping and Proposal

The future extension must **not** create an Opportunity automatically. `OUTREACH_READY` means research and qualification are sufficient for controlled outreach, not that a sales opportunity exists.

An Opportunity may be created only by a CRM user after Lead review or Account conversion and confirmation of a concrete sales pursuit. The user chooses the amount, close date, owner, and stage. The import may provide these non-binding defaults:

| Proposed Opportunity field | Source | Default behavior |
|---|---|---|
| `name` | `company.name` + `recommendation.best_first_product` | Human must confirm/edit before creation. |
| `product_interest` | `recommendation.best_first_product` | Nullable; product recommendation only. |
| `estimated_fit` | `score.score_tier`, `score.value`, `score.evidence_coverage` | Read-only advisory summary, not revenue prediction. |
| `priority` | `score.score_tier` | Suggested only; human confirms. |
| `sales_stage` | none | No Engine default beyond `Prospecting`; CRM user owns final value. |

## Evidence Mapping - Recommended Custom Entity

**Recommendation: Option B, custom `ResearchEvidence` entity.** EspoCRM Notes are rejected because they do not provide controlled schema, evidence-item deduplication, versioned provenance, or a clean Lead relationship.

Each imported `ResearchEvidence` record belongs to one Lead and may be linked to a later Account without changing its immutable source snapshot.

| `ResearchEvidence` field | Contract path | Required | Nullable | Notes |
|---|---|---:|---:|---|
| `name` | generated from `claim` | Yes | No | Short sales-readable label. |
| `peEvidenceId` | `evidence[].evidence_id` | Yes | No | Unique within evidence schema/version. |
| `peClaim` | `evidence[].claim` | Yes | No | Compact asserted fact. |
| `peSourceUrl` | `evidence[].source_url` | Yes | No | Public source URL. |
| `peEvidenceText` | `evidence[].evidence_text` | Yes | No | Bounded excerpt, maximum 1,000 characters. |
| `peConfidence` | `evidence[].confidence` | Yes | No | Decimal 0-1. |
| `peCapturedAt` | `evidence[].captured_at` | Yes | No | Original capture time. |
| `peClaimType` | `evidence[].claim_type` | Yes | No | Controlled claim type. |
| `peSchemaVersion` | `evidence[].schema_version` | Yes | No | Evidence schema version. |
| `peSnapshotHash` | `provenance.evidence_snapshot_hash` | Yes | No | Links item to import snapshot. |
| `leadId` | receiving Lead | Yes | No | Required parent relationship. |

## Engine-Only Data

The following remains exclusively in the Engine: discovery queries, ICP configuration, raw sources, raw payloads, raw HTML, page traversal history, technical diagnostics, full evidence corpus, scoring component calculations, intermediate classifications, state-transition audit history, retry policy, registry internals, and all provider-specific data.
