# ADR-C25-003: Revenue Analyst Assistant Governance

| Field | Value |
| --- | --- |
| Status | DOCUMENTATION_ONLY — Draft Governance Foundation (Hardening v2); WP3 Commercial Intelligence Support FROZEN |
| Date | 2026-07-31 |
| Baseline | `phase3c25-charter-ratified` (`6e2dcf8`); WP3 freeze `phase3c25-wp3-freeze` |
| Depends On | `docs/PHASE3C25_CHARTER_DRAFT.md` (v2.1-draft) §5.3, §6; `docs/audit/PHASE3C25_IMPLEMENTATION_RISK_REVIEW.md`; ADR-C25-001; ADR-C25-005; ADR-C25-006 |
| Related Invariants | `C25-INV-SEC-001`, `C25-INV-PROV-001`, `C25-INV-ADV-001`, `C25-INV-INT-006` |
| Implementation Authorization | None for invariant activation; WP3 application delivery separately FROZEN |
| Freeze references | `phase3c25-wp3-freeze` — assistant remains advisory interface; no AI runtime |

## 1. Context

The C25 AI Assistant (WP3) provides AI-assisted analytical Q&A over governed
revenue evidence. Without an explicit governance decision, an assistant
interface could acquire write-capable tools, reach outside the commercial
analytics domain, invoke providers directly, or produce commercial
conclusions that a reader cannot trace to source evidence.

This ADR defines the assistant's operation boundary, structural enforcement
architecture, and output provenance requirements. It resolves charter open
question Q2 (structured Q&A vs. free-form natural language).

## 2. Decision

The Revenue Analyst Assistant is a **read-only analytical interface** to
governed commercial evidence. Its authority is structurally bounded — not
prompt-bounded. Phase 1 uses **structured Q&A with enumerated question
domains** as the safe default. Free-form natural-language Q&A is a governed
future extension requiring independent ADR ratification and boundary refusal
tests before activation.

The assistant answers questions inside the C24 commercial analytics domain,
such as:

- "Why did conversion decline in Q2?"
- "What changed in pipeline quality between periods?"
- "What commercial patterns exist across ICP segments?"
- "How does velocity compare to prior periods?"
- "What does the win/loss pattern suggest?"

## 3. Operation Boundary

### 3.1 Permitted Operations

| Operation | Description |
| --- | --- |
| Query | Read governed evidence by defined query patterns |
| Read | Access C20–C24 and CRM Core entities as read-only |
| Aggregate | Compute summaries over read evidence |
| Compare | Compare evidence across periods, segments, patterns |
| Explain | Explain patterns, trends, and relationships in evidence |
| Summarize | Generate human-readable summaries of evidence |

### 3.2 Forbidden Operations

| Operation | Enforcement |
| --- | --- |
| Create | No entity creation path; enforced at service layer |
| Update | No entity mutation path; enforced at service layer |
| Delete | No entity deletion path; enforced at service layer |
| Send email | No email dispatch capability; enforced at tool capability level |
| Trigger outreach | No outreach execution path; enforced at tool capability level |
| Change lifecycle | No lifecycle mutation path; enforced at service layer |
| Access credentials | No credential read capability; enforced at service layer |
| Direct provider calls | No provider SDK, HTTP, or transport ownership |

## 4. Enforcement Architecture

The security boundary MUST be enforced by:

1. **Tool capability** — the assistant's available tools are a structural
   allow-list. Forbidden operations have no corresponding tool. Tool
   capability must be auditable at the code level, not only observable at
   runtime.
2. **Service layer** — C25 assistant services have zero write paths to
   C20/C21/C22/C23/C24/CRM Core entities. This is enforced by contract
   tests, not by convention.
3. **Not by prompt** — the boundary is not enforced by system prompts,
   refusal rules, or language constraints. Those are defense-in-depth only;
   the structural absence of forbidden capabilities is the primary
   enforcement.

Any AI model invocation for analytical responses routes through C20
capability interfaces (ADR-C20 D3); the assistant holds no credentials and
selects no model (ADR-C25-005).

## 5. Domain Boundary Refusal

If the assistant receives a request outside the C24 commercial analytics
domain, or a request for a forbidden operation, it MUST decline and explain
the boundary. This refusal is a **functional requirement, not a prompt
suggestion** — the service layer must recognize out-of-domain requests and
refuse them before processing. A request requiring CRM mutation ("What
Opportunity should I close?") is declined with the boundary explanation.

## 6. Response Governance

Every analytical response MUST:

- carry the explicit advisory designation, verbatim: "AI-generated
  analytical response — for human review only. Not a forecast, commitment,
  or decision.";
- reference source evidence with provenance (§7);
- declare analytical limitations — what the response cannot conclude;
- use governed evidence only and declare methodology for analysis; and
- phrase recommendations as observations, not directives.

Every analytical response MUST NOT:

- create, modify, or recommend CRM lifecycle actions;
- generate forecasts, commit revenue, or authorize commercial action;
- create forecast or pipeline commitments or revenue recognition entries;
- modify CRM Opportunities, trigger execution or workflow; or
- replace human analytical judgment.

### 6.1 AI Confidence Boundary

Every analytical response MUST communicate (ADR-C25-006 §3):

- **Evidence basis** — the governed source artifacts the response is built
  on, with references (§7);
- **Confidence declaration** — a qualitative, evidence-anchored confidence
  indication (evidence volume, completeness, consistency) — never a
  numeric probability of a commercial outcome;
- **Freshness consideration** — the freshness state of the underlying
  evidence where material to the answer; and
- **Limitation statement** — what the response cannot conclude.

A response MUST NOT claim a guaranteed outcome, commercial certainty,
probability of winning, or revenue prediction. Forbidden: "Customer will
buy." "Opportunity value is 95%." "Revenue will increase 30%."

### 6.2 Prohibited Response Patterns

The Assistant MUST NOT produce (Risk Review R5):

| Prohibited Pattern | Example (FORBIDDEN) |
| --- | --- |
| Ordinal ranking | "first," "second," "top 3 candidates" |
| Opportunity ranking | "Customer X has highest value" |
| Forecast prediction | "Deal Y will close," "is expected to convert" |
| Unsupported comparison | "Company A is better than Company B" |

A comparison is permitted only when grounded in explicitly governed,
non-authoritative data, with the metric name, sample size, period, and
provenance in the same sentence as the comparison (A5): "In 2026-Q2,
Segment A candidates (n=45) showed a REVIEW_PENDING→ACCEPTED conversion
rate of 0.42, compared to Segment B candidates (n=38) at 0.34, based on
PipelineMetric records P1–P10."

The Assistant MUST NOT aggregate multiple signals into a single holistic
judgment ("overall commercial readiness," "composite signal strength"),
and MUST refuse "which entity" questions ("Which candidates should I
review?") at the service layer, before AI model processing (R5c/A6).

## 7. Output Provenance Requirements

Every assistant analytical response that presents findings, explanations, or
conclusions MUST support source traceability. Ungrounded commercial
conclusions are forbidden.

### 7.1 Provenance Chain per Response

| Provenance Element | Description | Example |
| --- | --- | --- |
| Source record IDs | Entity type and ID for every source artifact the analysis is based on | `ReplySignal:abc123, RevenueInsight:def456` |
| Source artifact IDs | Specific C20–C24 artifact references | `CampaignOutcome:campaign-aus-2026Q2` |
| Reporting period | The time window the analysis covers | `2026-Q2 (2026-04-01 to 2026-06-30)` |
| Generation timestamp | When the response was generated | `2026-07-30T14:30:00Z` |
| AIJob ID | The C20 AIJob that produced this analytical response | `C20 AIJob:job-xyz789` |
| AIRequestLog references | The C20 AIRequestLog records for provider invocations | `AIRequestLog:log-001, log-002` |

### 7.2 Traceability Requirement

A human reviewer must be able to trace any analytical claim back to its
source evidence:

```text
Assistant response: "Australia distributor segment shows higher response efficiency"

Must be traceable to:
  -> Campaign Outcome records (CRM Core)
  -> ReplySignal records (C24 WP1)
  -> RevenueInsight records (C24 WP3)
  -> PipelineMetric records (C24 WP3)
```

### 7.3 Forbidden: Ungrounded Conclusions

| Forbidden | Permitted |
| --- | --- |
| "This deal will close." (no source, predictive claim) | "Based on ReplySignal confidence and engagement velocity in records X, Y, Z, this candidate shows stronger-than-average commercial engagement." |
| "Segment A is better than Segment B." (no period, no source) | "In 2026-Q2, Segment A candidates (n=45) showed 23% higher REPLY_SIGNAL conversion than Segment B candidates (n=38), based on RevenueInsight records R1, R2 and PipelineMetric records P1–P10." |

### 7.4 Provenance Survival

The provenance chain MUST survive deletion of the assistant response.
Provenance records in C20 AIJob/AIRequestLog and source artifacts in
C20–C24/CRM Core are independent of C25 assistant response lifecycle
(C25-INV-PROV-001).

## 8. Explicit Prohibitions

- No write-capable, send, trigger, lifecycle, credential, or provider tools.
- No prompt-only enforcement of the read-only boundary.
- No answers outside the C24 commercial analytics domain.
- No ungrounded commercial conclusions without the §7 provenance chain.
- No responses without advisory designation and limitation declaration.
- No ordinal ranking, opportunity ranking, forecast prediction, or
  unsupported comparison language (§6.2).
- No confidence claims without evidence basis, freshness consideration,
  and limitation declaration (§6.1).
- No "which entity" answers; refusal at the service layer (§6.2).
- No free-form NL Q&A in Phase 1 without independent ADR ratification and
  boundary refusal tests.

## 9. Consequences

Future assistant tool definitions must implement the structural allow-list;
service-layer contract tests must verify zero write, send, trigger,
lifecycle-mutation, credential-access, or direct-provider paths. Response
validators must reject analytical responses missing provenance elements,
advisory designation, or limitation declarations. The assistant composes
into the Human Decision Workspace (ADR-C25-004) as a read-only analytical
surface. This ADR authorizes no entity, schema, service, API, UI, ACL, or
integration implementation.
