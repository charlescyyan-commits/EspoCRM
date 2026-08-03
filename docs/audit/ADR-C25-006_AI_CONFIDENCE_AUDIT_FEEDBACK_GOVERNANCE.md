# ADR-C25-006: AI Confidence, Audit and Feedback Governance

| Field | Value |
| --- | --- |
| Status | DOCUMENTATION_ONLY — Draft Governance Foundation (Hardening v2); feedback remains non-truth / non-training |
| Date | 2026-07-31 |
| Baseline | `phase3c25-charter-ratified` (`6e2dcf8`); WP2.2/WP3 freezes |
| Depends On | `docs/PHASE3C25_CHARTER_DRAFT.md` (v2.1-draft) §5–§7, §10; `docs/audit/PHASE3C25_IMPLEMENTATION_RISK_REVIEW.md`; ADR-C25-001; ADR-C25-005 — governance extension ADR |
| Related Invariants | `C25-INV-INT-006` (new), `C25-INV-ADV-001`, `C25-INV-PROV-001`, `C25-INV-HG-001` |
| Implementation Authorization | None (invariants not activated) |
| Freeze references | No autonomous learning / model-training loop authorized |

## 1. Context

ADR-C25-001 through ADR-C25-005 define the workspace read model, brief
governance, assistant governance, the human decision surface, and cross-layer
read-only contracts. Three governance areas remain unclosed:

- **A. AI Confidence Boundary** — how C25 AI output communicates confidence
  without claiming certainty (Risk Review §7: advisory labels alone do not
  govern behavior);
- **B. C25 Audit Trail** — what audit events C25 governance requires across
  workspace, brief, assistant, and decision domains;
- **C. Human Feedback Governance** — how feedback on C25 AI output is
  separated from C21 HumanFeedback and prevented from driving automation.

This ADR closes all three areas as governance specification only.

## 2. Decision

1. Every C25 AI output carries a structural confidence boundary (§3).
2. C25 audit trail requirements are defined as governance only — no
   implementation entities are created or authorized (§4).
3. Human feedback on C25 output is C25-scoped, separated from C21
   HumanFeedback, and can never drive automation or truth changes (§5).
4. One new invariant is registered: C25-INV-INT-006, Evidence
   Interpretation Boundary (§6). No further invariants are added (§7).

## 3. AI Confidence Boundary

### 3.1 Mandatory Confidence Elements

Every C25 AI output — AI Commercial Brief, AI Assistant analytical response,
or any future C25 AI-generated output — MUST communicate:

| Element | Requirement |
| --- | --- |
| Evidence basis | The governed source artifacts the output is built on, with entity type and ID references (ADR-C25-005 §4) |
| Confidence indication | A qualitative, evidence-anchored indication (evidence volume, completeness, consistency across sources) — never a numeric probability of a commercial outcome |
| Freshness consideration | The freshness state of the underlying evidence where material to the conclusion (ADR-C25-005 §5) |
| Limitation statement | What the output cannot conclude — a first-class section of the output, not a footnote |

### 3.2 Forbidden Confidence Claims

No C25 AI output may claim:

- a guaranteed outcome;
- commercial certainty;
- probability of winning; or
- revenue prediction.

Forbidden examples:

```text
"Customer will buy."
"Opportunity value is 95%."
"Revenue will increase 30%."
```

### 3.3 Rationale

Advisory designation labels alone do not govern behavior (Risk Review §7).
Confidence must be a structural property of the output: the reader must see
what the AI based its statement on, how much evidence exists, how fresh that
evidence is, and what the AI cannot conclude. Probability-of-winning and
revenue prediction are not interpretive functions — they are score and
forecast functions owned by Chitu/CRM Core and human operators, and are
forbidden outright.

## 4. C25 Audit Trail (Governance Only)

### 4.1 Scope Rule

This section defines audit **requirements** only. It does NOT create, and
must not be read as authorizing, any implementation entity, table, metadata,
or storage design. Audit storage design belongs to the future C25
implementation work package.

### 4.2 Required Audit Events

| Domain | Events | Required Content |
| --- | --- | --- |
| Workspace | context assembled; user access; timestamp | source artifact set and assembly version; actor and access timestamp |
| Brief | generation; review; acceptance/dismissal; feedback | generation: C20 AIJob/AIRequestLog linkage (C25-INV-PROV-001); review and acceptance/dismissal: actor, timestamp, and `acceptanceScope` (ADR-C25-002 §7); feedback: actor, timestamp, feedback reference |
| Assistant | question asked; response generated; evidence referenced | question text and domain classification; response linkage including C20 provenance; source record IDs referenced by the response |
| Decision | human decision event | the human decision collected by the workspace (e.g., intent to transition); enactment is audited by the owning layer (C24 immutable transition record / CRM Core) and is never duplicated by C25 |

### 4.3 Audit Rules

- **Append-only** — audit events are recorded once and never updated;
  corrections are new events.
- **Not business facts** — audit records are governance metadata; they
  create no commercial truth (C25-INV-INT-006).
- **Not lifecycle records** — C25 audit never substitutes for or parallels
  C24's immutable transition records (ADR-C25-004 §7).
- **Provenance continuity** — brief acceptance audit links the human
  acceptance event to the brief's C20 provenance chain (the AIJob that
  produced the brief), so "AI generated → human accepted" is traceable end
  to end (Risk Review R3d/B4). The acceptance itself is a human governance
  event, not a provider invocation.
- **Independence** — deleting C25 audit records must not affect any
  C20–C24 or CRM Core artifact.

## 5. Human Feedback Governance

### 5.1 Feedback Separation

| Aspect | C21 HumanFeedback | C25 Feedback |
| --- | --- | --- |
| Subject | Evidence quality; intelligence interpretation | AI explanation quality; brief usefulness; assistant response quality |
| Governs | C21 intelligence artifacts (ResearchEvidence, AIQualificationInsight) | C25 AI outputs (briefs, assistant responses, workspace presentations) |
| Truth effect | Governed by C21 | None — C25 feedback never changes C21/C24 truth |

### 5.2 Feedback Rules

- C25 feedback is advisory input for human governance review of C25 output
  quality.
- Feedback MUST NOT automatically regenerate AI output — any regeneration
  is a new human-initiated generation (charter §8) producing a new
  superseding artifact.
- Feedback MUST NOT modify source artifacts (C20–C24, CRM Core).
- Feedback MUST NOT change C21/C24 truth — it evaluates C25's explanation
  of the evidence, never the evidence itself.
- Feedback events are audit events (§4.2).

## 6. New Invariant: C25-INV-INT-006 — Evidence Interpretation Boundary

| Field | Definition |
| --- | --- |
| ID | `C25-INV-INT-006` |
| Name | Evidence Interpretation Boundary |
| Category | Interpretation / Truth Boundary |
| Purpose | Ensure C25's interpretation of governed evidence never becomes the canonical source of commercial truth. |
| Rule | C25 may interpret governed evidence — assembling, explaining, summarizing, and presenting AI-assisted commercial understanding — but MUST NOT become the canonical source of commercial truth. All commercial truth remains in CRM Core and the C20–C24 owning layers. C25 interpretations are advisory projections: they carry evidence basis, confidence indication, freshness consideration, and limitation statement; they never assert outcome certainty; and deleting them loses no business fact. |
| Enforcement expectation | Contract tests verify: C25 output schemas exclude truth-asserting fields (priority, score, probability, revenue impact, commercial ranking); every AI output carries the four confidence elements (§3.1); deleting all C25 artifacts changes zero fields on any C20–C24 or CRM Core entity. |
| Relation to previous invariants | Extends C25-INV-OWN-001 (ownership boundary), C25-INV-ADV-001 (advisory non-authority), and C24-INV-REV-003 (analytics cannot mutate CRM lifecycle). Sixth C25 invariant; supersedes none. Numbering note: charter v1.0 IDs INT-001–INT-005 were renumbered in v2.0 to category prefixes (OWN-001, ADV-001, HG-001, SEC-001, PROV-001); INT-006 continues the sequence for the interpretation category. |
| Status | PROPOSED (DOCUMENTATION_ONLY upon package ratification; ACTIVE upon implementation) |

## 7. Invariant Evaluation — No Additional Invariants

| Candidate Invariant | Needed? | Rationale |
| --- | --- | --- |
| Confidence boundary | No — covered by C25-INV-INT-006 + C25-INV-ADV-001 | Confidence declaration is an output-content rule (§3) enforced by response-structure validation, not a separate invariant |
| Audit boundary | No — covered by C25-INV-PROV-001 + C25-INV-INT-006 | Audit requirements are governance definitions (§4); provenance integrity is already governed by PROV-001 and C20 ADR C8; audit records create no business facts under INT-006 |
| Feedback boundary | No — covered by C25-INV-OWN-001 + C25-INV-HG-001 | Feedback separation is an ownership rule (C21 vs. C25 scope); the no-automation rule is already HG-001 plus charter §8 |

Conclusion: one new invariant (C25-INV-INT-006) is necessary and sufficient.
No separate confidence, audit, or feedback invariants are created.

## 8. Explicit Prohibitions

- No AI output without evidence basis, confidence indication, freshness
  consideration, and limitation statement.
- No guaranteed outcome, commercial certainty, probability-of-winning, or
  revenue-prediction claims.
- No audit implementation entities authorized by this ADR — audit
  requirements only.
- No C25 audit record that duplicates or replaces C24 lifecycle audit.
- No feedback-driven automatic regeneration, source modification, or truth
  change.
- No C25 feedback stored as, or merged into, C21 HumanFeedback.

## 9. Consequences

ADR-C25-002 (brief), ADR-C25-003 (assistant), and ADR-C25-004 (workspace)
consume this ADR's confidence, audit, and feedback contracts. Validators
must reject AI outputs missing the §3.1 elements; the §4.2 audit events
become acceptance criteria for the future C25 implementation work package.
C25-INV-INT-006 enters formal registration with the C25 Invariant Registry.
This ADR authorizes no entity, schema, service, API, UI, ACL, or integration
implementation.
