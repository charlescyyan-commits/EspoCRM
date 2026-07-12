# Lead Sync Mapping Audit

**Date:** 2026-07-11  
**Scope:** Read-only audit of `integration/espocrm_sync/` Lead mapping  
**Code / data / field changes:** NONE

## Summary

| Question | Short answer |
|---|---|
| Which Lead fields can sync today? | Mapper defines **20** Lead-oriented fields; live POST path currently writes a **subset of 10** (+ synthetic `description`) |
| Apify → Lead fields? | **Indirect only** (discovery candidate identity/source); no Apify-specific Lead columns |
| Website Research → Lead? | Website URL, country (gated), research status, customer type fallback, evidence entity (not Lead blob) |
| Scoring Engine → Lead? | Score, tier, confidence, coverage, best_first_product, rules version |
| Email Engine → Lead? | **None** — not wired into sync adapter |
| opportunity_score / tier / evidence / best_first_product / outreach status | See §4 |

---

## 1. Lead Fields Currently Supported

### 1A. Mapper output — `EspoCRMSyncMapper.lead_fields()`

These are the Lead-oriented fields the Engine-side adapter **knows how to map** from Sync Contract V1:

| EspoCRM field | Contract path |
|---|---|
| `name` | `company.name` |
| `website` | `company.website` |
| `country` | `company.country_code` |
| `leadSource` | `source.channel` |
| `peCandidateId` | `identity.candidate_id` |
| `peCanonicalDomain` | `identity.canonical_domain` |
| `peQualificationStatus` | `qualification.status` |
| `peResearchStatus` | `research.status` |
| `peCustomerType` | `qualification.customer_type` |
| `peOpportunityScoreV4` | `score.value` |
| `peScoreTier` | `score.score_tier` |
| `peConfidence` | `score.aggregate_confidence` |
| `peEvidenceCoverage` | `score.evidence_coverage` |
| `peBestFirstProduct` | `recommendation.best_first_product` |
| `peCrossSellPath` | `recommendation.cross_sell_path` |
| `peEngineVersion` | `provenance.engine_version` |
| `peScoreRulesVersion` | `score.rules_version` |
| `peEvidenceSchemaVersion` | `provenance.evidence_schema_version` |
| `peRegistryVersion` | `provenance.official_brand_registry_version` |
| `peEvidenceSnapshotHash` | `provenance.evidence_snapshot_hash` |

### 1B. Live EspoCRM POST subset — `LocalEspoCRMClient._lead_body()`

Real localhost write path **filters** mapper output to:

| Posted Lead field | Notes |
|---|---|
| `name` | YES |
| `website` | YES |
| `peOpportunityScoreV4` | YES |
| `peScoreTier` | YES |
| `peConfidence` | YES |
| `peEvidenceCoverage` | YES |
| `peBestFirstProduct` | YES |
| `peQualificationStatus` | YES |
| `peEngineVersion` | YES |
| `peScoreRulesVersion` | YES |
| `description` | Synthetic marker block only (`[CHITU_SYNTHETIC_TEST]`, etc.) |

**Not posted by real client today** (even though mapper can produce them):  
`country`, `leadSource`, `peCandidateId`, `peCanonicalDomain`, `peResearchStatus`, `peCustomerType`, `peCrossSellPath`, `peEvidenceSchemaVersion`, `peRegistryVersion`, `peEvidenceSnapshotHash`.

### 1C. Extension Lead metadata currently installed

Skeleton Lead overlay defines the eight `pe*` score/qualification fields + `researchEvidences` link. It does **not** yet declare the fuller design set (`peCanonicalDomain`, `peSyncStatus`, etc.) in the installed entityDefs subset used for Phase 3A-2.1.

Evidence is **not** a Lead field dump: compact items sync to entity `ResearchEvidence` and link via `Lead.researchEvidences`.

---

## 2. Field Provenance by Upstream System

### Apify (search / discovery)

| Contribution | Becomes Lead field? | How |
|---|---|---|
| Discovery hit → `Candidate` (name, raw URL, canonical domain, source, source_url) | Partially | `name` from `candidate.company_name`; domain/source feed contract identity/source; website may fall back to `candidate.raw_url` if research final URL missing |
| Raw Apify payload / SERP HTML | **No** | Explicitly excluded from sync |
| Apify-specific CRM columns | **No** | None defined |

Apify is an upstream **candidate feeder**, not a direct Lead field owner.

### Website Research

| Contribution | Lead / related target |
|---|---|
| `final_url` / accessibility | `website`; gate uses `website_accessible` |
| Direct country evidence | `country` ← `company_country_code` only when non-inferred + evidence ids present |
| Customer type candidates | `peCustomerType` fallback |
| Research completion / failure | `peResearchStatus` / gate (`FAILED_TECHNICAL`) |
| `evidence_items` | **ResearchEvidence** records (not Lead text fields) |
| Brands/products/emails/phones found on site | **Not mapped to Lead columns** in current adapter |

### Scoring Engine (Canonical V4 / score dict)

| Contribution | Lead field |
|---|---|
| `opportunity_score` / `normalized_score` | `peOpportunityScoreV4` |
| `score_tier` | `peScoreTier` |
| `aggregate_confidence` | `peConfidence` |
| `evidence_coverage` | `peEvidenceCoverage` |
| `best_first_product` | `peBestFirstProduct` |
| `score_reasons` | Contract `recommendation.reason_codes` only — **not** a Lead field today |
| `rules_version` | `peScoreRulesVersion` |
| `result_hash` | Contract only — not Lead field |
| `customer_type` (if present on score) | May feed `peCustomerType` |

### Email Engine

| Contribution | Lead field |
|---|---|
| Drafts / sequences / SMTP / reply tracking | **None** |
| Contact emails discovered during research | Collected in Website Research model (`public_emails`) but **not synced** to Lead or Contact by this adapter |

Email Engine is **out of scope** for `integration/espocrm_sync/` today.

### Other Engine layers (for completeness)

| Layer | Lead impact |
|---|---|
| Business qualification / state machine | `peQualificationStatus` (`OUTREACH_READY` gate); rejection blocks sync |
| Official brand filter | Gate / provenance (`official_brand_excluded`); registry version → `peRegistryVersion` (mapper only) |
| ICP / enrichment gate | Not mapped as Lead fields |

---

## 3. Missing Fields (gaps)

### vs Phase 3A-1 Entity Mapping Design (Lead table)

Designed but **not in live POST subset** and/or **not in skeleton Lead entityDefs**:

| Designed CRM field | Mapper? | Live POST? | Skeleton entityDefs? |
|---|---|---|---|
| `country` | YES | NO | NO (uses core Lead country if present) |
| `leadSource` | YES | NO | core field |
| `peCandidateId` | YES | NO | NO |
| `peCanonicalDomain` | YES | NO | NO |
| `peResearchStatus` | YES | NO | NO |
| `peCustomerType` | YES | NO | NO |
| `peCrossSellPath` | YES | NO | NO |
| `peEvidenceSchemaVersion` | YES | NO | NO |
| `peRegistryVersion` | YES | NO | NO |
| `peEvidenceSnapshotHash` | YES | NO | NO |
| `peSyncStatus` | NO (extension-owned) | NO | NO |
| `peSyncedAt` | NO (extension-owned) | NO | NO |

### Engine data that exists but is intentionally / currently not on Lead

| Data | Status |
|---|---|
| Full evidence corpus | Separate `ResearchEvidence` entity (correct) |
| Score component traces / raw decision | Engine-only (by design) |
| Public emails / phones / contact URLs | Not synced |
| Detected brands / products lists | Not synced as Lead multi-fields |
| Outreach email drafts / send status | Not synced |
| CRM owner / sales status / activities | Must never be Engine-imported (by design) |
| Human_Priority / Final_Priority | Human-only; not in sync adapter |

---

## 4. Capability Checklist (requested)

| Capability | Supported? | How |
|---|---|---|
| **opportunity_score** | **YES** | `score.opportunity_score` → `peOpportunityScoreV4` (mapper + live POST) |
| **tier** | **YES** | `score.score_tier` → `peScoreTier` |
| **evidence** | **YES (entity), not Lead blob** | Compact items → `ResearchEvidence` + `Lead.researchEvidences`; Lead also gets `peEvidenceCoverage` / snapshot hash (hash mapper-only today) |
| **best_first_product** | **YES** | `recommendation.best_first_product` ← score → `peBestFirstProduct` |
| **outreach status** | **PARTIAL** | Engine qualification/outreach readiness → `peQualificationStatus` (must be `OUTREACH_READY` to sync). This is **not** CRM outreach/email send status, sequence state, or reply tracking |

Clarifications:

- “Outreach status” in Engine terms ≈ `qualification.status` / prospect state (`OUTREACH_READY`).  
- “Outreach status” in Email Engine / sales-execution terms (sent, replied, bounced) is **not** supported by this sync path.

---

## 5. Architecture Notes (read-only)

```text
Apify / search
    → Candidate
Website Research
    → WebsiteResearchResult (+ EvidenceItem[])
Scoring V4
    → score dict
        ↓
SyncSource → EspoCRMSyncMapper → SyncContractPayload
        ↓
lead_fields() ──────────────► (full mapped Lead dict)
        ↓ filter (_LEAD_FIELDS)
LocalEspoCRMClient POST Lead  ► (subset)
        +
POST ResearchEvidence + link
```

Email Engine does not appear in this pipeline.

---

## 6. Conclusions

1. **Lead sync mapping is score- and qualification-centric**, with company identity from candidate/research.  
2. **Evidence is first-class via `ResearchEvidence`**, not flattened into Lead.  
3. **Mapper is ahead of live POST + skeleton fields** — several design fields are mapped in Python but not yet written or declared on Espo Lead.  
4. **No Email Engine Lead sync** exists in `integration/espocrm_sync/`.  
5. Requested business signals: score, tier, best_first_product, evidence (entity), and Engine outreach-ready status are covered; email outreach lifecycle is not.

No code or CRM data was modified by this audit.
