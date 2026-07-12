# EspoCRM Sync Contract Boundary V1

**Phase:** 3A-1 - design only  
**Status:** approved design artifact; no CRM integration is implemented by this document.

## Purpose

This boundary defines a one-way, evidence-backed contract from Prospecting Engine to EspoCRM. It does not authorize an EspoCRM extension, CRM configuration, database write, API request, customer synchronization, email, or background job.

## Current Engine Capability

The Engine can produce a normalized candidate, business-qualification result, Website Research result, Canonical Scoring V4 result, and evidence references. Its current relevant controls are:

- official-brand, platform, and duplicate filtering before scoring;
- explicit technical failure versus business exclusion separation;
- evidence-item identifiers, source URLs, capture timestamps, confidence, and schema versions;
- V4 output with `opportunity_score`, `score_tier`, `evidence_coverage`, `aggregate_confidence`, `best_first_product`, rule version, and result hash;
- business routing and CRM visibility that are distinct from scoring; and
- a state model that includes `OUTREACH_READY`, `APPROVED_FOR_CRM`, and `SYNCED_TO_ESPO` but does not itself authorize a CRM write.

## Target Responsibility

| System | Owns | Does not own |
|---|---|---|
| Prospecting Engine | discovery, research, qualification, V4 scoring, evidence collection, product recommendation, eligibility decision | CRM records, sales ownership, outreach execution, account conversion, opportunity lifecycle |
| EspoCRM | Lead review, salesperson ownership, sales actions, account lifecycle, opportunity lifecycle, customer activity history | crawling, discovery, scoring calculation, evidence generation, score-rule changes, email strategy |
| Human CRM user | approval/rejection, Lead-to-Account conversion, Opportunity creation, sales stage changes, edits to commercial outcomes | rewriting Engine evidence or score history |

The Engine remains the source of truth for intelligence. EspoCRM is the execution and human-review layer.

## Allowed Phase 3A-1 Work

- Define versioned JSON payloads, mappings, validation, deduplication, and extension architecture.
- Define fields intended for a future Lead, Account, Opportunity, and `ResearchEvidence` entity.
- Design offline contract tests and rollback behavior.

## Prohibited Work

- EspoCRM PHP, metadata, extension, field, API, or UI implementation.
- Any EspoCRM, production database, queue, or external API modification or call.
- Automatic synchronization, historical migration, email creation/sending, SMTP, Apify, DeepSeek, or Playwright execution.
- Changes to Prospecting Engine rules, V3 scoring, V4 scoring, evidence fixtures, or business data.

## Field Design Principles

1. **Reference evidence; do not copy raw research.** CRM receives compact, sales-readable evidence records and stable references, never raw HTML, crawler logs, cookies, headers, debug payloads, or credentials.
2. **Do not turn uncertainty into fact.** A candidate target country is not a CRM company country unless direct country evidence supports it. Nullable fields remain null rather than receiving defaults.
3. **Preserve provenance.** Every score-related value carries Engine, score-rule, evidence-schema, and registry versions plus an immutable evidence snapshot hash.
4. **Separate recommendation from commitment.** `best_first_product`, fit, and score are decision support, not an Opportunity or sales commitment.
5. **Use stable identity.** The normalized `canonical_domain` is the logical prospect identity. It is not a raw URL and must be used for duplicate prevention.

## One-Way Synchronization Principle

The only planned data direction is:

```text
Prospecting Engine -> validated contract -> future EspoCRM extension -> Lead + ResearchEvidence
```

EspoCRM must not call back to alter Engine scores, qualification, evidence, rules, or versions. CRM-only fields such as owner, call outcome, lifecycle status, conversion decision, and Opportunity stage remain in CRM and are not written back.

## Synchronization Gate

A future extension may accept a payload only when every condition holds:

1. `qualification.status == "OUTREACH_READY"`.
2. `score.rules_version == "canonical-scoring-v4.0"`.
3. `score.score_tier` is `A`, `B`, or `C`; it is not `D` or `INSUFFICIENT_EVIDENCE`.
4. `score.evidence_coverage >= 0.50` and `score.aggregate_confidence >= 0.60`.
5. Evidence references are present and resolve to at least one valid compact evidence record.
6. `provenance.official_brand_excluded == false` and no exclusion reason is present.
7. Research has no technical failure and the website is accessible.
8. Contract, evidence, and score versions are recognized by the receiving extension.
9. The logical identity and idempotency key pass duplicate checks.

All other states, including `DISCOVERED`, `RESEARCH_QUEUED`, `RESEARCHING`, `FAILED_TECHNICAL`, `REJECTED_BUSINESS`, and `EXCLUDED`, are denied. `OUTREACH_READY` is necessary but never sufficient by itself.

## Rollback and Fail-Closed Behavior

- A receiver that cannot validate a payload rejects it without creating or updating CRM records.
- A version mismatch, missing required evidence, stale V3 score, official-brand flag, or duplicate conflict is a visible rejection with a reason code, not a silent fallback.
- A future extension must create immutable import/audit records before any mutable Lead update.
- Disabling the extension or revoking its credential stops future imports; it does not delete CRM-owned records or alter Engine history.
- Reprocessing an accepted payload uses the same idempotency key and must return the existing result without duplication.

## Authorization Boundary

This document completes the contract-design prerequisite only. Phase 3A-2 requires separate explicit authorization before any extension code or real integration is created.
