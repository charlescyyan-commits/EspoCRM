# Phase3C23 Charter Amendment V1

## Document Header

| Field | Value |
| --- | --- |
| **Document Type** | Charter Amendment — Charter Modification Preparation Artifact |
| **Subject** | Phase3C23 — AI Prospecting Optimization & Learning Governance |
| **Status** | READY FOR CHARTER MODIFICATION |
| **Date** | 2026-07-30 |
| **Owner** | Phase3C23 Governance |
| **Baseline** | `phase3c22-final-freeze` |
| **Charter Under Amendment** | `docs/PHASE3C23_CHARTER.md` (v1.0-draft, 911 lines) |
| **Governing Charter Review** | `docs/audit/PHASE3C23_CHARTER_REVIEW.md` — APPROVED WITH CONDITIONS |
| **Condition Resolution** | All six conditions (C1–C6) resolved in this amendment |
| **This Document Is** | Charter Modification Preparation Artifact |
| **This Document Is NOT** | Final Charter; Implementation specification; Ratification |

---

## 1. Review Condition Mapping

| Condition | Severity | Title | Resolution | New Invariant |
| --- | --- | --- | --- | --- |
| C1 | BLOCKING | C21/C23 Intelligence Separation Boundary | Define hard ownership separation; OptimizationInsight ≠ AIQualificationInsight | C23-INV-SEP-004 |
| C2 | BLOCKING | Aggregate Evidence Boundary | OptimizationInsight evidenceReference limited to aggregate-level sources only; forbid per-prospect references | C23-INV-PROV-003 |
| C3 | BLOCKING | ActionGate Isolation | C23 output must not become ActionGate decision input; structural prohibition on surfacing C23 data at the gate | C23-INV-SEP-005 |
| C4 | REQUIRED | Metric Sample Governance | Stratify sample size thresholds: n ≥ 5 descriptive, n ≥ 30 comparative; mandatory confidence intervals below threshold | C23-INV-MET-004 |
| C5 | REQUIRED | Naming Correction | Rename `CANDIDATE_QUALITY_SCORE` → `CANDIDATE_OUTCOME_QUALITY` | None (terminology change) |
| C6 | REQUIRED | Data Freshness Governance | Add sourcePeriod, freshness indicator; staleness flagging requirement | C23-INV-PROV-004 |

---

## 2. C1 Resolution — Intelligence Separation Boundary

### 2.1 Problem

The Charter Review identified that the distinction between C21 `AIQualificationInsight` (per-prospect qualification intelligence) and C23 `OptimizationInsight` (aggregate operational strategy recommendation) was described in prose but lacked a dedicated invariant. Without one, OptimizationInsight could evolve to include per-prospect qualification recommendations, functionally becoming a parallel qualification authority.

### 2.2 Hard Ownership Separation

The following hard boundary is established between C21 and C23 intelligence:

```text
┌─────────────────────────────────────────────────────────────────┐
│ C21 — Intelligence Governance (FROZEN)                          │
│                                                                 │
│  AIQualificationInsight                                         │
│    ├── Per-prospect qualification intelligence                  │
│    ├── Research interpretation                                  │
│    ├── Intelligence confidence (AI certainty about a prospect)   │
│    ├── Answers: "Is THIS prospect a good fit?"                  │
│    └── Immutable; advisory only; no execution authority         │
│                                                                 │
│  ─── HARD BOUNDARY: C23 must not create per-prospect ───────   │
│       qualification intelligence or ranking authority           │
│                                                                 │
│ C23 — Optimization & Learning (THIS AMENDMENT)                  │
│                                                                 │
│  OptimizationInsight                                            │
│    ├── Aggregate operational strategy recommendations           │
│    ├── Performance improvement learning                         │
│    ├── Statistical confidence (confidence in the recommendation)│
│    ├── Answers: "Which STRATEGIES work better across cohorts?"  │
│    └── Immutable; advisory only; human-reviewed status          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Decision

**C21 owns per-prospect qualification intelligence. C23 owns aggregate operational optimization learning. The two layers serve fundamentally different purposes at different levels of abstraction and must not overlap.**

| Dimension | C21 (Intelligence) | C23 (Optimization) |
| --- | --- | --- |
| **Granularity** | Per-prospect (individual ProspectPool) | Aggregate (cohorts, segments, time windows) |
| **Question** | "Is this specific prospect qualified?" | "Which strategies work better across many prospects?" |
| **Confidence meaning** | AI certainty about prospect fit | Statistical confidence in the recommendation |
| **Output** | Qualification recommendation | Strategy/process recommendation |
| **Consumer** | Human operator evaluating a prospect | Human operator reviewing strategy |
| **Authority** | Advisory only (C21-INV-03) | Advisory only (C23-INV-ADV-001) |

### 2.4 Forbidden Overlap

OptimizationInsight MUST NOT represent:

| Forbidden | Rationale | Owned By |
| --- | --- | --- |
| **Prospect qualification** | "This prospect is a good fit" is C21 territory | C21 AIQualificationInsight |
| **Ranking authority** | "Prospect A > Prospect B" implies scoring authority | Chitu / C21 |
| **Intelligence interpretation** | "This research evidence means the prospect is qualified" is C21 territory | C21 ResearchEvidence |
| **Individual prospect recommendation** | "Send outreach to this specific prospect" is C22 execution territory | C22 ActionGate |
| **Per-prospect confidence** | Confidence about an individual prospect's fit is C21 territory | C21 AIQualificationInsight |

### 2.5 New Invariant

| Field | Value |
| --- | --- |
| **ID** | C23-INV-SEP-004 |
| **Statement** | `OptimizationInsight` provides aggregate operational strategy recommendations. It MUST NOT represent per-prospect qualification intelligence, ranking authority, intelligence interpretation, or individual prospect recommendations. `OptimizationInsight` is structurally distinct from `AIQualificationInsight` in granularity, purpose, confidence meaning, and consumer. |
| **Category** | C21/C22 Separation |
| **Enforcement** | Entity design (no per-prospect FK fields) + contract test (verify no OptimizationInsight references ProspectCandidate or ProspectPool entityTypes) |
| **Owning ADR** | ADR-C23-001 |
| **Status** | DOCUMENTATION_ONLY |
| **Activation Trigger** | `OptimizationInsight` entity creation + C23 Charter ratification |

---

## 3. C2 Resolution — Aggregate Evidence Boundary

### 3.1 Problem

The Charter Review identified that `OptimizationInsight.evidenceReference` accepts any entityType/entityId, which could include individual ProspectCandidate or ProspectPool records. If OptimizationInsight accumulates per-prospect evidence references, it could functionally become a shadow per-prospect intelligence store — violating the C21/C23 intelligence separation boundary.

### 3.2 Decision

**OptimizationInsight.evidenceReference MUST reference only aggregate operational evidence sources. Per-prospect entity references are structurally forbidden.**

### 3.3 Allowed Evidence References

| Allowed Source | EntityType | Rationale |
| --- | --- | --- |
| Aggregated PerformanceMetric records | `PerformanceMetric` | Pre-computed aggregate metrics |
| ProspectRun batch outcomes | `ProspectRun` | Run-level execution container (aggregate by design) |
| ExecutionLedger aggregate views | `ExecutionLedger` | Time-windowed, grouped execution data |
| Period-based analysis snapshots | `PerformanceMetric` | Point-in-time aggregate measurements |
| C21 intelligence aggregates | `IntelligenceAggregate` | Pre-aggregated intelligence views |
| C20 provider performance data | `AIJob`, `AIRequestLog` | Provider-level aggregates |

### 3.4 Forbidden Evidence References

| Forbidden Source | EntityType | Rationale |
| --- | --- | --- |
| Individual prospect candidate | `ProspectCandidate` | Per-prospect — C22 execution identity |
| Individual research pool entry | `ProspectPool` | Per-prospect — C21 intelligence identity |
| Individual CRM business identity | `Lead` | Per-entity — CRM Core identity |
| Individual CRM account | `Account` | Per-entity — CRM Core identity |
| Individual CRM opportunity | `Opportunity` | Per-entity — CRM Core lifecycle |
| Individual research evidence | `ResearchEvidence` | Per-prospect — C21 intelligence evidence |
| Individual qualification insight | `AIQualificationInsight` | Per-prospect — C21 qualification |

### 3.5 Structural Enforcement

The `evidenceReference` field definition is amended to include a structural constraint:

```text
evidenceReference: JSON Array of {entityType, entityId, field, relationship}
  ALLOWED entityTypes: PerformanceMetric, ProspectRun, ExecutionLedger,
                       IntelligenceAggregate, AIJob, AIRequestLog
  FORBIDDEN entityTypes: ProspectCandidate, ProspectPool, Lead, Account,
                         Opportunity, ResearchEvidence, AIQualificationInsight
```

### 3.6 New Invariant

| Field | Value |
| --- | --- |
| **ID** | C23-INV-PROV-003 |
| **Statement** | `OptimizationInsight.evidenceReference` MUST reference only aggregate operational evidence sources. References to individual prospect identities (`ProspectCandidate`, `ProspectPool`), CRM identities (`Lead`, `Account`, `Opportunity`), or per-prospect intelligence records (`ResearchEvidence`, `AIQualificationInsight`) are forbidden. |
| **Category** | Data Provenance |
| **Enforcement** | Entity design (enum constraint on evidenceReference.entityType) + contract test (verify no forbidden entityTypes in any OptimizationInsight record) |
| **Owning ADR** | ADR-C23-001 |
| **Status** | DOCUMENTATION_ONLY |
| **Activation Trigger** | `OptimizationInsight` entity creation |

---

## 4. C3 Resolution — ActionGate Isolation

### 4.1 Problem

The Charter Review identified that while the Charter prevents C23 from bypassing ActionGate, it does not prevent C23 data from being surfaced to operators at the ActionGate, where it could influence approval decisions. A structural prohibition is needed: C23 analytics data must not appear in the ActionGate review interface or be used as evidence in approval/denial decisions.

### 4.2 Risk Scenario

```text
FORBIDDEN PATH (C3 blocks this):

  C23 PerformanceMetric: "ICP segment A has 90% positive reply rate"
          ↓
  Displayed at ActionGate during prospect review
          ↓
  Operator: "Segment A has great metrics, I'll approve without reading"
          ↓
  ActionGate approval decision influenced by C23 data
          ↓
  C23 analytics functionally become ActionGate evidence

CORRECT PATH:

  C23 OptimizationInsight: "ICP segment A shows strong performance"
          ↓
  Human strategy review (separate from ActionGate)
          ↓
  Human decides: "Let's continue targeting segment A"
          ↓
  Human configures ProspectRun targeting (through C22 config, not C23)
          ↓
  Each individual action still goes through ActionGate on its own merits
```

### 4.3 Decision

**C23 output (PerformanceMetric values, OptimizationInsight recommendations) MUST NOT be presented at C22 ActionGate or used as evidence in ActionGate approval/denial decisions. C23 data is for strategic review, not operational gating.**

### 4.4 Boundary Diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│ C23 DOMAIN (Strategic Review)                                    │
│                                                                 │
│  OptimizationInsight ──→ Human Strategy Review                   │
│  PerformanceMetric  ──→ Performance Dashboard                    │
│                                                                 │
│  ─── HARD BOUNDARY: C23 data does not cross into ────────────   │
│       ActionGate operational interface                           │
│                                                                 │
│ C22 DOMAIN (Operational Gating)                                  │
│                                                                 │
│  ActionGate ←── HUMAN APPROVAL (on individual action merits)     │
│  ActionGate inputs:                                              │
│    ✓ ProspectCandidate identity                                  │
│    ✓ C21 intelligence context (AIQualificationInsight,           │
│      ResearchEvidence)                                           │
│    ✓ Proposed action details                                     │
│    ✓ Predicted cost                                              │
│    ✗ C23 PerformanceMetric values                                │
│    ✗ C23 OptimizationInsight recommendations                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.5 Scope of Prohibition

The prohibition covers:

| Path | Forbidden? | Rationale |
| --- | --- | --- |
| C23 metrics displayed in ActionGate UI | **YES** | Would influence approval decisions |
| C23 insights cited as approval rationale | **YES** | "This segment performs well" is not an approval reason |
| C23 data in human strategy review | **NO** | Strategy review is the intended C23 consumer |
| C23 data in performance dashboards | **NO** | Dashboards are informational, not operational gates |
| Operator manually referencing C23 data | **Cannot prevent** | Operator knowledge cannot be structurally blocked; the structural prohibition removes C23 data from the gate interface |

### 4.6 New Invariant

| Field | Value |
| --- | --- |
| **ID** | C23-INV-SEP-005 |
| **Statement** | C23 analytics data (`PerformanceMetric` values, `OptimizationInsight` recommendations, and any derived C23 output) MUST NOT be presented in the C22 ActionGate review interface or used as evidence in ActionGate approval/denial decisions. C23 data is for strategic review, not operational gating. |
| **Category** | C21/C22 Separation |
| **Enforcement** | Service boundary (C23 services have no write access to ActionGate presentation layer) + contract test (verify ActionGate UI data sources exclude C23 entities) |
| **Owning ADR** | ADR-C23-001 |
| **Status** | DOCUMENTATION_ONLY |
| **Activation Trigger** | `ActionGate` UI implementation + C23 analytics service implementation |

---

## 5. C4 Resolution — Metric Sample Governance

### 5.1 Problem

The Charter Review identified that C23-INV-MET-001's minimum sample size of 5 data points is statistically insufficient for comparative metrics. With n=5 per group, only massive effect sizes (>1.8 standard deviations) are detectable. Presenting comparisons based on such small samples as meaningful insights produces misleadingly confident recommendations.

### 5.2 Decision

**Sample size thresholds are stratified by metric type. Descriptive metrics require n ≥ 5. Comparative optimization metrics require n ≥ 30 per group. Metrics below their threshold must carry mandatory confidence intervals and explicit LOW_CONFIDENCE flagging.**

### 5.3 Stratified Thresholds

| Metric Category | Metric Types | Minimum Sample Size | Below Threshold |
| --- | --- | --- | --- |
| **Descriptive** | `SUCCESS_RATE`, `REPLY_RATE`, `AVERAGE_LATENCY`, `ACTIONGATE_DENIAL_RATE`, `COST_PER_ACTION` | n ≥ 5 | Flag `LOW_CONFIDENCE`; require confidence interval |
| **Comparative** | `TEMPLATE_PERFORMANCE`, `PROVIDER_PERFORMANCE`, `ICP_PERFORMANCE`, `POSITIVE_REPLY_RATE`, `COST_PER_POSITIVE_REPLY`, `RESEARCH_DEPTH_CORRELATION`, `CANDIDATE_OUTCOME_QUALITY` | n ≥ 30 per group | Flag `LOW_CONFIDENCE`; require confidence interval; display explicit "insufficient data for reliable comparison" warning |
| **Trend** | Any metric computed over time periods | n ≥ 3 time periods, each with n ≥ 10 | Flag `LOW_CONFIDENCE`; display "emerging trend — more data needed" |

### 5.4 Confidence Interval Requirements

All PerformanceMetric records must include a `confidenceInterval` when:
1. The metric is comparative AND n < 100 per group
2. The metric is below its category threshold
3. The metric is used as the basis for an OptimizationInsight

Confidence intervals use 95% confidence level by default. Methodology must be documented in ADR-C23-005.

### 5.5 New Invariant

| Field | Value |
| --- | --- |
| **ID** | C23-INV-MET-004 |
| **Statement** | `PerformanceMetric` sample size thresholds are stratified by metric category: descriptive metrics require n ≥ 5; comparative optimization metrics require n ≥ 30 per group; trend metrics require n ≥ 3 time periods each with n ≥ 10. Metrics below their category threshold MUST be flagged `LOW_CONFIDENCE` and include a mandatory confidence interval. Comparative metrics below threshold MUST additionally display "insufficient data for reliable comparison." |
| **Category** | Metric Integrity |
| **Enforcement** | Service guard (`PerformanceMetric` creation validates sampleSize against metricType category threshold) + contract test |
| **Owning ADR** | ADR-C23-005 |
| **Status** | DOCUMENTATION_ONLY |
| **Activation Trigger** | `PerformanceMetric` entity creation + metric computation service implementation |

### 5.6 Amendment to C23-INV-MET-001

The original C23-INV-MET-001 is **superseded** by C23-INV-MET-004 and re-scoped:

| Field | Value |
| --- | --- |
| **ID** | C23-INV-MET-001 (REVISED) |
| **Statement** | Every `PerformanceMetric` must declare its `sampleSize`. Metrics with sampleSize below the category-specific threshold defined in C23-INV-MET-004 must be flagged `LOW_CONFIDENCE`. Metrics with no declared sampleSize are invalid. |
| **Status** | DOCUMENTATION_ONLY |
| **Supersedes** | Original C23-INV-MET-001 (flat n ≥ 5 threshold) |

---

## 6. C5 Resolution — Naming Correction

### 6.1 Problem

The Charter Review identified that the `metricType` enum value `CANDIDATE_QUALITY_SCORE` implies C23 is computing candidate quality scores — a violation of the Chitu/C21 scoring authority boundary. The metric actually measures execution outcome quality (reply rates, conversion rates correlated with candidate segments), not candidate scores.

### 6.2 Decision

**Rename `CANDIDATE_QUALITY_SCORE` to `CANDIDATE_OUTCOME_QUALITY` throughout the Charter and all derived artifacts.**

### 6.3 Semantic Clarification

| Term | Meaning | NOT |
| --- | --- | --- |
| `CANDIDATE_OUTCOME_QUALITY` | Measures the quality of execution outcomes associated with candidate cohorts — reply rates, positive reply rates, conversion rates. A performance measurement of what happened, not a judgment of candidate fitness. | NOT a qualification score. NOT a ranking score. NOT AI authority over prospect quality. |

### 6.4 Affected Charter Sections

| Charter Section | Change |
| --- | --- |
| §6.1.2 PerformanceMetric.metricType enum | `CANDIDATE_QUALITY_SCORE` → `CANDIDATE_OUTCOME_QUALITY` |
| §11.3 Category 6: Metric Integrity | No invariant ID change; terminology update in descriptions |
| All references | Global find-replace |

---

## 7. C6 Resolution — Data Freshness Governance

### 7.1 Problem

The Charter Review identified that OptimizationInsight records lack any temporal validity mechanism. Insights based on old execution data may mislead operators — a strategy that worked 6 months ago may no longer be effective. An invariant requiring insights to declare their data recency and be flagged when stale is needed.

### 7.2 Decision

**Every OptimizationInsight must declare its source data period and generation timestamp. Insights based on data older than a defined freshness threshold must be flagged STALE. Stale insights must not be presented as current recommendations without explicit staleness warning.**

### 7.3 New Entity Fields

The following fields are added to `OptimizationInsight`:

| Field | Type | Description |
| --- | --- | --- |
| `sourcePeriodStart` | DateTime | Start of the source data period this insight is based on |
| `sourcePeriodEnd` | DateTime | End of the source data period this insight is based on |
| `generatedAt` | DateTime | When this insight was generated (may differ from createdAt for batch-generated insights) |
| `freshnessStatus` | Enum | `CURRENT` (data within freshness window), `AGING` (approaching staleness threshold), `STALE` (data exceeds freshness threshold), `ARCHIVAL` (retained for historical reference only) |

### 7.4 Freshness Thresholds

| Freshness Status | Condition | Display Requirement |
| --- | --- | --- |
| `CURRENT` | `generatedAt` ≤ 30 days ago AND `sourcePeriodEnd` ≤ 90 days ago | Normal display |
| `AGING` | `generatedAt` 31–60 days ago OR `sourcePeriodEnd` 91–180 days ago | Display with "Based on data from [period] — recency: aging" |
| `STALE` | `generatedAt` > 60 days ago OR `sourcePeriodEnd` > 180 days ago | Display with prominent "⚠ STALE — based on data from [period]. Conditions may have changed." |
| `ARCHIVAL` | Explicitly marked for archival | Display with "Historical record — not a current recommendation" |

### 7.5 Staleness and Supersession

When a new OptimizationInsight is generated for the same strategic domain (same insightType + suggestedScope) with fresher data:
1. The new insight is created with `freshnessStatus = CURRENT`
2. The prior insight's `freshnessStatus` transitions to `STALE` or `ARCHIVAL`
3. The new insight's `supersedes` field references the prior insight
4. Human operators see only CURRENT and AGING insights by default; STALE and ARCHIVAL are filtered

### 7.6 New Invariant

| Field | Value |
| --- | --- |
| **ID** | C23-INV-PROV-004 |
| **Statement** | Every `OptimizationInsight` must declare its `sourcePeriodStart`, `sourcePeriodEnd`, and `generatedAt`. Insights where `sourcePeriodEnd` exceeds 180 days or `generatedAt` exceeds 60 days MUST be flagged `STALE`. Stale insights MUST NOT be presented as current recommendations without an explicit staleness warning. |
| **Category** | Data Provenance |
| **Enforcement** | Service guard (OptimizationInsight creation validates required temporal fields) + contract test (verify stale insights carry correct freshnessStatus) |
| **Owning ADR** | ADR-C23-005 |
| **Status** | DOCUMENTATION_ONLY |
| **Activation Trigger** | `OptimizationInsight` entity creation |

---

## 8. Updated Invariant Registry Plan

### 8.1 New Invariant Summary

This amendment introduces 6 new invariants and revises 1 existing invariant:

| ID | Category | Statement (Abbreviated) | Condition |
| --- | --- | --- | --- |
| C23-INV-SEP-004 | C21/C22 Separation | OptimizationInsight provides aggregate strategy recommendations; must not represent per-prospect qualification, ranking, or intelligence interpretation | C1 |
| C23-INV-PROV-003 | Data Provenance | OptimizationInsight evidenceReference limited to aggregate sources; per-prospect entityTypes forbidden | C2 |
| C23-INV-SEP-005 | C21/C22 Separation | C23 data must not be presented at ActionGate or used as ActionGate evidence | C3 |
| C23-INV-MET-004 | Metric Integrity | Stratified sample size thresholds: n≥5 descriptive, n≥30 comparative, n≥3×10 trend; mandatory LOW_CONFIDENCE + confidence intervals below threshold | C4 |
| C23-INV-MET-001 (REVISED) | Metric Integrity | PerformanceMetric must declare sampleSize; below-threshold metrics flagged LOW_CONFIDENCE per C23-INV-MET-004 | C4 |
| C23-INV-PROV-004 | Data Provenance | OptimizationInsight must declare sourcePeriod + generatedAt; stale insights flagged and warned | C6 |

### 8.2 Full Updated Registry (23 invariants)

| # | ID | Category | Statement (Abbreviated) | Status |
| --- | --- | --- | --- | --- |
| 1 | C23-INV-OWN-001 | Ownership Boundary | C23 owns OptimizationInsight and PerformanceMetric exclusively | DOCUMENTATION_ONLY |
| 2 | C23-INV-OWN-002 | Ownership Boundary | C23 does not own any C20/C21/C22/CRM entity | DOCUMENTATION_ONLY |
| 3 | C23-INV-OWN-003 | Ownership Boundary | OptimizationInsight immutable after creation; status via supersession | DOCUMENTATION_ONLY |
| 4 | C23-INV-OWN-004 | Ownership Boundary | PerformanceMetric immutable after creation; point-in-time measurements | DOCUMENTATION_ONLY |
| 5 | C23-INV-PROV-001 | Data Provenance | OptimizationInsight must reference specific source evidence | DOCUMENTATION_ONLY |
| 6 | C23-INV-PROV-002 | Data Provenance | PerformanceMetric must declare scope, period, sampleSize, source references | DOCUMENTATION_ONLY |
| 7 | **C23-INV-PROV-003** | **Data Provenance** | **OptimizationInsight evidenceReference limited to aggregate sources only** | **DOCUMENTATION_ONLY** |
| 8 | **C23-INV-PROV-004** | **Data Provenance** | **OptimizationInsight must declare sourcePeriod + generatedAt; stale insights flagged** | **DOCUMENTATION_ONLY** |
| 9 | C23-INV-ADV-001 | Advisory-Only AI | No C23 AI output may be interpreted as execution directive | DOCUMENTATION_ONLY |
| 10 | C23-INV-ADV-002 | Advisory-Only AI | C23 AI invocations route through C20 capability interfaces | DOCUMENTATION_ONLY |
| 11 | C23-INV-ADV-003 | Advisory-Only AI | C23 must not generate directive output (approve, send, execute, etc.) | DOCUMENTATION_ONLY |
| 12 | C23-INV-HG-001 | Human Governance | Every OptimizationInsight requires human review before any strategy/execution change | DOCUMENTATION_ONLY |
| 13 | C23-INV-HG-002 | Human Governance | Future automation requires dedicated Charter Amendment | DOCUMENTATION_ONLY |
| 14 | C23-INV-SEP-001 | C21/C22 Separation | C23 reads C21 records as read-only analytical input | DOCUMENTATION_ONLY |
| 15 | C23-INV-SEP-002 | C21/C22 Separation | C23 reads C22 records as read-only analytical input | DOCUMENTATION_ONLY |
| 16 | C23-INV-SEP-003 | C21/C22 Separation | No parallel intelligence store, execution ledger, or qualification authority | DOCUMENTATION_ONLY |
| 17 | **C23-INV-SEP-004** | **C21/C22 Separation** | **OptimizationInsight is aggregate strategy; NOT per-prospect qualification** | **DOCUMENTATION_ONLY** |
| 18 | **C23-INV-SEP-005** | **C21/C22 Separation** | **C23 data must not be presented at ActionGate** | **DOCUMENTATION_ONLY** |
| 19 | C23-INV-MET-001 (REVISED) | Metric Integrity | PerformanceMetric must declare sampleSize; below-threshold → LOW_CONFIDENCE | DOCUMENTATION_ONLY |
| 20 | C23-INV-MET-002 | Metric Integrity | PerformanceMetric values not used as automated triggers | DOCUMENTATION_ONLY |
| 21 | C23-INV-MET-003 | Metric Integrity | Metric computation methodology documented and reproducible | DOCUMENTATION_ONLY |
| 22 | **C23-INV-MET-004** | **Metric Integrity** | **Stratified sample size thresholds: n≥5 descriptive, n≥30 comparative, n≥3×10 trend** | **DOCUMENTATION_ONLY** |

### 8.3 Updated Category Counts

| Category | Original Count | New Count | Change |
| --- | --- | --- | --- |
| Ownership Boundary (OWN) | 4 | 4 | — |
| Data Provenance (PROV) | 2 | 4 | +2 (PROV-003, PROV-004) |
| Advisory-Only AI (ADV) | 3 | 3 | — |
| Human Governance (HG) | 2 | 2 | — |
| C21/C22 Separation (SEP) | 3 | 5 | +2 (SEP-004, SEP-005) |
| Metric Integrity (MET) | 3 | 4 | +1 (MET-004); MET-001 revised |
| **Total** | **17** | **22** | **+5 new, 1 revised** |

Note: C5 (naming correction) produces no new invariant. The net increase is 5 invariants + 1 revision = 22 total.

---

## 9. ADR Impact

### 9.1 Updated ADR Ownership

| ADR | New Invariants Owned | Change |
| --- | --- | --- |
| ADR-C23-001 (Optimization Ownership Boundary) | +C23-INV-SEP-004, +C23-INV-PROV-003, +C23-INV-SEP-005 | Now owns 3 additional invariants covering C21/C23 separation, aggregate evidence, and ActionGate isolation |
| ADR-C23-005 (Metric Governance) | +C23-INV-MET-004, +C23-INV-PROV-004, revised C23-INV-MET-001 | Now owns 2 additional invariants + 1 revision covering sample governance and data freshness |

### 9.2 ADR Scope Expansion

| ADR | Original Scope | Expanded Scope |
| --- | --- | --- |
| ADR-C23-001 | Ownership boundary, advisory-only principle, enforcement mechanisms | + C21/C23 intelligence separation boundary, aggregate evidence constraints, ActionGate isolation |
| ADR-C23-005 | Metric computation methodology, scope, confidence, misuse prevention | + Stratified sample size governance, data freshness/staleness requirements |

### 9.3 No New ADRs Required

The 6 conditions are resolved within the existing 5-ADR framework. ADR-C23-001 and ADR-C23-005 absorb the additional scope. No new ADRs are required.

---

## 10. Charter Modification Instructions

### 10.1 Required Charter Changes

The following sections of `docs/PHASE3C23_CHARTER.md` must be modified:

| Charter Section | Change | Condition |
| --- | --- | --- |
| §3.3 (C21 Dependency) | Add hard C21/C23 intelligence separation paragraph with per-prospect vs aggregate distinction table | C1 |
| §3.4 (C22 Dependency) | Add ActionGate isolation clause: "C23 data must not be presented at ActionGate or used as ActionGate evidence" | C3 |
| §6.1.1 (OptimizationInsight) | Add 4 new fields: `sourcePeriodStart`, `sourcePeriodEnd`, `generatedAt`, `freshnessStatus`. Add constraint on `evidenceReference` entityTypes. | C2, C6 |
| §6.1.2 (PerformanceMetric) | Rename `CANDIDATE_QUALITY_SCORE` → `CANDIDATE_OUTCOME_QUALITY` in metricType enum | C5 |
| §7.2 (Allowed vs Forbidden) | Add row for "Qualification" category reinforcing C21/C23 separation | C1 |
| §11.3 (Invariant Candidates) | Add 6 new invariants (SEP-004, PROV-003, SEP-005, MET-004, PROV-004); revise MET-001 | C1–C6 |
| §11.2 (Invariant Categories) | Update counts: PROV 2→4, SEP 3→5, MET 3→4; total 17→22 | C1–C6 |
| Appendix B (Decision Boundary Examples) | Add 3 forbidden operations: per-prospect OptimizationInsight, ActionGate display of C23 data, stale insight presentation | C1, C3, C6 |

### 10.2 Charter Changes Explicitly NOT Required

- No new WP definitions (WPs unchanged)
- No new ADRs (existing 5-ADR framework absorbs scope)
- No entity removals
- No Charter Governance section changes (amendment process unchanged)
- No Risk Register changes (risks already identified; conditions add mitigations)

### 10.3 Post-Modification Status

After Charter modification:
- Charter version: v1.1-draft (condition resolution applied)
- Invariant count: 22 (17 original + 5 new; 1 revised)
- All 6 conditions resolved
- Charter ready for ratification review

---

## 11. Validation Checklist

| Check | Criterion | Status |
| --- | --- | --- |
| V1 | C1 resolved: Hard C21/C23 intelligence separation defined with invariant C23-INV-SEP-004 | ✓ |
| V2 | C2 resolved: Aggregate evidence boundary defined with invariant C23-INV-PROV-003 | ✓ |
| V3 | C3 resolved: ActionGate isolation defined with invariant C23-INV-SEP-005 | ✓ |
| V4 | C4 resolved: Stratified sample size thresholds with invariant C23-INV-MET-004; MET-001 revised | ✓ |
| V5 | C5 resolved: CANDIDATE_QUALITY_SCORE → CANDIDATE_OUTCOME_QUALITY | ✓ |
| V6 | C6 resolved: Data freshness governance with invariant C23-INV-PROV-004; 4 new fields on OptimizationInsight | ✓ |
| V7 | No new ADRs required (existing framework absorbs scope) | ✓ |
| V8 | No WP changes required | ✓ |
| V9 | All invariants DOCUMENTATION_ONLY | ✓ |
| V10 | Charter modification instructions specified | ✓ |
| V11 | Invariant count: 22 (consistent) | ✓ |

---

## 12. References

| Reference | Path |
| --- | --- |
| C23 Charter (under amendment) | `docs/PHASE3C23_CHARTER.md` |
| C23 Charter Review | `docs/audit/PHASE3C23_CHARTER_REVIEW.md` |
| C22 Charter Amendment V1 (precedent) | `docs/audit/PHASE3C22_CHARTER_AMENDMENT_V1.md` |
| C21 ADR (Accepted) | `docs/adr/ADR-C21_AI_SALES_INTELLIGENCE_ARCHITECTURE.md` |
| C21 Invariant Registry | `docs/adr/C21_INVARIANT_REGISTRY.md` |
| C22 Invariant Registry (Draft) | `docs/audit/C22_INVARIANT_REGISTRY_DRAFT.md` |

---

*Charter Amendment V1 — Charter Modification Preparation Artifact only. This document resolves review conditions. It authorizes Charter modification, not implementation. No entity creation, metadata modification, code changes, commits, pushes, or tags are authorized by this document.*
