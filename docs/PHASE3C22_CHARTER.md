# Phase3C22 Charter

## Status

**RATIFIED — Autonomous Prospecting Execution Governance.**

This Charter implements the accepted governance boundaries defined by the Charter
Amendment V1 (`docs/audit/PHASE3C22_CHARTER_AMENDMENT_V1.md`) and the accepted
C22 Architecture Decision Records. It authorizes bounded governance design and
separately approved work packages; it does not authorize provider execution,
autonomous action without human approval, CRM lifecycle automation, or C21
intelligence mutation.

## Baseline

- C21: **FROZEN** — AI Intelligence Governance (`docs/PHASE3C21_CHARTER.md`).
- C20: **ACTIVE** — AI Capability Governance (`docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md`).
- Charter Amendment V1: **APPROVED** — Preparation Artifact (`docs/audit/PHASE3C22_CHARTER_AMENDMENT_V1.md`).
- Charter Review: **APPROVED WITH CONDITIONS** — All five conditions (C1–C5) resolved (`docs/audit/PHASE3C22_CHARTER_REVIEW.md`).
- C22 Invariant Registry: **DOCUMENTATION_ONLY** — 29 invariants across 6 categories (`docs/adr/C22_INVARIANT_REGISTRY.md`).

---

## 1. C22 Definition

```text
C22 = Autonomous Prospecting Execution Governance Layer
```

C22 governs the execution of prospecting actions — external candidate discovery,
enrichment, AI-powered research, approval-gated outreach, and reply detection.
C22 is the governance layer that sits between C21 intelligence (advisory) and
CRM Core (business lifecycle), governing the execution pipeline that transforms
external discovery targets into execution outcomes.

### 1.1 What C22 Is

C22 governs:

- External candidate discovery and identity management (pre-CRM)
- Execution batch orchestration (`ProspectRun` as execution container)
- Approval boundary enforcement (`ActionGate`)
- Append-only execution record-keeping (`ExecutionLedger`)
- Outreach execution through provider abstraction (`OutreachExecution`)
- Automation rule definition and governance (`AutomationRule`)
- Action audit trail (`ActionLedger`)
- Reply signal monitoring (`ReplyDetection`)

### 1.2 What C22 Is NOT

| Not C22 | Owner |
| --- | --- |
| **C21 intelligence extension** | C21 owns ResearchEvidence, AIQualificationInsight, HumanFeedback, IntelligenceAggregate. C22 consumes C21 intelligence context as read-only input; it does not extend, modify, or reinterpret C21 records |
| **CRM workflow replacement** | CRM Core owns Lead, Account, Opportunity lifecycle. C22 executes prospecting actions up to the CRM boundary; it does not replace or automate CRM workflows |
| **CRM lifecycle owner** | CRM Core owns business lifecycle (sales stage, pipeline phase, revenue association). C22 terminates at ReplyDetection and does not cross into CRM lifecycle without human operator decision |
| **Provider runtime** | C20 owns ProviderBinding, Capability Registry, AIJob, AIRequestLog. C22 requests capability invocation through C20 interfaces; it does not own provider resolution, credential custody, or AI execution evidence |
| **Scoring or qualification authority** | Chitu owns `canonical_score` and qualification decisions. C22 may route based on Chitu outputs; it does not compute scores or qualification verdicts |

### 1.3 C22 Position in the Layer Stack

```text
┌──────────────────────────────────────────────────────────────┐
│ CRM Core                                                     │
│   Lead · Account · Opportunity · Lifecycle · Revenue         │
│   ← Human or authorized workflow decision only               │
├──────────────────────────────────────────────────────────────┤
│ C22 — Autonomous Prospecting Execution Governance            │
│   ProspectCandidate · ProspectRun · ActionGate               │
│   ExecutionLedger · OutreachExecution                        │
│   AutomationRule · ActionLedger                              │
│   ← Reads C21 intelligence; requests C20 capability           │
├──────────────────────────────────────────────────────────────┤
│ C21 — AI Intelligence Governance          ← FROZEN           │
│   ResearchEvidence · AIQualificationInsight                  │
│   HumanFeedback · IntelligenceAggregate                      │
│   ← Advisory intelligence; no execution authority            │
├──────────────────────────────────────────────────────────────┤
│ C20 — AI Capability Governance            ← ACTIVE           │
│   AIJob · AIRequestLog · PromptTemplate                      │
│   ProviderCredential · ProviderRoute · ProviderHealth        │
│   ← Execution governance; provider abstraction; credential    │
│     custody; cost accounting                                 │
├──────────────────────────────────────────────────────────────┤
│ Chitu — External Intelligence Authority  ← UNMODIFIABLE      │
│   canonical_score · qualification · research · scoring       │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Execution Architecture

### 2.1 The Execution Chain

```text
┌─────────────────────────────────────────────────────────────────┐
│ C22 EXECUTION CHAIN                                             │
│                                                                 │
│  External Discovery                                             │
│    Provider: Apify / Serper / SearchProvider                    │
│    Egress: C20 Connector                                        │
│    ↓                                                            │
│  ProspectCandidate (created/updated)                            │
│    Execution identity; not CRM identity (ADR-C22-001)           │
│    ↓                                                            │
│  Enrichment                                                     │
│    Provider: Apollo / Hunter / EnrichmentProvider               │
│    Egress: C20 Connector                                        │
│    ↓                                                            │
│  AI Research Context                                            │
│    Provider: DeepSeek / CompletionProvider                      │
│    Egress: C20 Connector                                        │
│    C21 intelligence: read-only context (ResearchEvidence,       │
│      AIQualificationInsight, IntelligenceAggregate)             │
│    ↓                                                            │
│  ActionGate ←── HUMAN APPROVAL REQUIRED (ADR-C22-002)           │
│    Evidence: ProspectCandidate + C21 context + predicted cost   │
│    Decision: APPROVED / DENIED / DEFERRED                       │
│    ↓ (if APPROVED)                                              │
│  OutreachExecution                                              │
│    Provider: Instantly / Brevo / SMTP / EmailDeliveryProvider   │
│    Egress: C20 Connector                                        │
│    Idempotency: Key persisted before dispatch                   │
│    ↓                                                            │
│  ExecutionLedger                                                │
│    Append-only execution record                                 │
│    ↓                                                            │
│  ReplyDetection ←── C22 TERMINAL BOUNDARY (ADR-C22-006)        │
│    Read-only monitoring of provider reply signals               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ─── C22 / CRM BOUNDARY — HUMAN DECISION REQUIRED ───           │
│                                                                 │
│  Human CRM process (outside C22 scope):                         │
│    · Promote to ProspectPool (intelligence accumulation)        │
│    · Promote to Lead (CRM acceptance)                           │
│    · Archive / ignore                                           │
│    · Schedule follow-up (new ProspectRun)                       │
│                                                                 │
│  ─── CRM CORE (outside C22 scope) ───                           │
│                                                                 │
│  Lead → Opportunity → Account → Revenue lifecycle               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Terminal Boundary

**The C22 execution chain terminates at `ReplyDetection`.**

- `ReplyDetection` is the last step where C22 has execution authority
- After `ReplyDetection`, the next action is a **business decision**, not an execution action
- All transitions from C22 execution outcomes to CRM business actions are **human-gated** and occur outside C22 scope

### 2.3 Forbidden CRM Crossings

C22 must not:

| Action | Owner | Boundary |
| --- | --- | --- |
| Auto-create Lead | CRM Core | Hard — human only |
| Auto-convert Lead | CRM Core | Hard — CRM workflow only |
| Auto-create Opportunity | CRM Core | Hard — CRM workflow only |
| Auto-create Account | CRM Core | Hard — CRM workflow only |
| Modify sales stage | CRM Core | Hard — CRM workflow only |
| Write to `canonical_score` | Chitu | Hard — AGENTS.md prohibition |
| Auto-create ProspectPool | C21 | Hard — C22 does not own Prospecting identity |
| Modify C21 intelligence records | C21 | Hard — C22 reads only |

---

## 3. Entity Ownership Boundary

### 3.1 Three-Layer Identity Model

| Layer | Entity | Owner | Purpose |
| --- | --- | --- | --- |
| 1 | **ProspectPool** | C21 Intelligence | Research collection grouping; persistent intelligence accumulation. C21 attaches ResearchEvidence, AIQualificationInsight, HumanFeedback. C22 may reference as read-only intelligence context. |
| 2 | **ProspectCandidate** | C22 Execution | Execution candidate identity; transient execution scope. Created by C22 search/discovery. Tracked through the execution chain. May link to ProspectPool for intelligence context. NOT a CRM identity. |
| 3 | **Lead** | CRM Core | Business relationship identity; CRM lifecycle (sales stage, pipeline, revenue). Created by human operator or authorized CRM workflow. NEVER auto-created by C22. |

### 3.2 Hard Distinctions

```text
ProspectCandidate ≠ Lead
```
- `ProspectCandidate` is an execution identity, not a CRM business identity
- `ProspectCandidate` has no CRM lifecycle, no sales stage, no revenue association
- Conversion to `Lead` requires explicit human approval through an authorized CRM workflow
- C22 must not auto-create, auto-convert, or auto-promote `ProspectCandidate` to `Lead`

```text
ProspectCandidate ≠ ProspectPool
```
- `ProspectPool` is a research/collection grouping — C21 attaches intelligence records to it
- `ProspectCandidate` is an execution identity — C22 tracks it through the execution chain
- A `ProspectCandidate` may link to a `ProspectPool` for intelligence context, but they are distinct identities
- `ProspectCandidate` is transient (execution lifecycle); `ProspectPool` is persistent (intelligence accumulation)
- `ProspectCandidate` does not replace, duplicate, or override `ProspectPool`

### 3.3 C22 Entity Ownership Matrix

| Entity | Owner | Creates | Modifies | Deletes |
| --- | --- | --- | --- | --- |
| `ProspectCandidate` | C22 | Search/Discovery actions | Enrichment/Research actions | Never (archive only) |
| `ProspectRun` | C22 | Operator or scheduled trigger | Execution state transitions | Never (terminal states only) |
| `ActionGate` | C22 | Per-action gate creation | Human approval/denial | Never (append-only record) |
| `ExecutionLedger` | C22 | Every execution action | Never — immutable after write | Never — guard-enforced |
| `OutreachExecution` | C22 | After ActionGate approval | Provider result recording | Never (append-only) |
| `AutomationRule` | C22 | Admin configuration | Admin reconfiguration | Admin only (with audit) |
| `ActionLedger` | C22 | Every C22 action | Never — immutable after write | Never — guard-enforced |

### 3.4 Entities C22 Does NOT Own

| Entity | Owner | C22 Relationship |
| --- | --- | --- |
| `ProspectPool` | C21 / Prospecting | Read-only intelligence context reference |
| `ResearchEvidence` | C21 | Read-only consumption |
| `AIQualificationInsight` | C21 | Read-only consumption |
| `HumanFeedback` | C21 | Must NOT touch |
| `IntelligenceAggregate` | C21 | Read-only consumption |
| `Lead` | CRM Core | May reference after human promotion; must NOT auto-create |
| `Opportunity` | CRM Core | Must NOT create or modify |
| `Account` | CRM Core | Must NOT create or modify |
| `AIJob` | C20 | Request via C20 interfaces; must NOT create directly |
| `AIRequestLog` | C20 | Reference only; must NOT create directly |

---

## 4. Human Approval Rule

### 4.1 The Rule

**Human approval is the default, permanent execution gate for all C22 execution actions.**

The word "initially" is struck from all C22 governance documents. Human approval
is not a temporary phase, a transitional convenience, or a placeholder for
future autonomy. It is the permanent default.

### 4.2 Gate Rules

- Every execution action that crosses the C22 execution boundary must pass through `ActionGate` with a human approval decision
- No action proceeds without gate resolution: the gate must return APPROVED, DENIED, or DEFERRED
- There is no default-approve path, no silent-approve path, and no timeout-approve path
- AI cannot self-approve — no automated process may issue an approval decision
- `AutomationRule` cannot bypass `ActionGate` — rules may propose actions, but they may not approve them
- After execution failure: ActionGate re-entry required (ADR-C22-007)
- After gate denial: no retry without new gate

### 4.3 Future Automation Guard

Any future change to the human-approval-default model requires **all** of:

1. A dedicated C22 Charter Amendment
2. A dedicated ADR defining:
   - Which action types may be rule-approved (and which remain human-only forever)
   - What evidence is required for rule evaluation
   - The maximum scope and budget of rule-approved actions
   - The audit trail requirements
   - The escalation path for rule-denied actions
3. A rule cannot approve an action that has no prior human-approved precedent under equivalent circumstances
4. Independent review and acceptance of the Charter Amendment

### 4.4 What Can Never Be Automated

| Action | Reason |
| --- | --- |
| Lead creation from ProspectCandidate | CRM Core boundary; business identity creation |
| Opportunity creation | CRM Core boundary; revenue lifecycle |
| Account creation | CRM Core boundary; business identity creation |
| ProspectPool creation from ProspectCandidate | C21 boundary; intelligence identity creation |
| Modifying C21 intelligence records | C21 freeze; intelligence governance |
| Writing to canonical_score | Chitu authority (AGENTS.md prohibition) |

---

## 5. ActionGate

### 5.1 What ActionGate Owns

| Owned By ActionGate | Description |
| --- | --- |
| **Approval decision** | APPROVED / DENIED / DEFERRED with operator identity and timestamp |
| **Authorization boundary** | Role-gated approval permissions; not all operators may approve all action types |
| **Execution permission** | The affirmative grant to proceed with a specific execution action |
| **Decision evidence** | What was presented, what was decided, by whom, when |
| **Gate audit trail** | Every gate decision recorded in `ExecutionLedger` |
| **Re-entry governance** | Every execution failure returns to ActionGate before retry |

### 5.2 What ActionGate Does NOT Own

| Not Owned By ActionGate | Owner |
| --- | --- |
| **Provider runtime** | C20 Connector (transport, retry, credential custody) |
| **CRM lifecycle** | CRM Core (Lead, Opportunity, Account management) |
| **Intelligence interpretation** | C21 (ResearchEvidence, AIQualificationInsight) |
| **Action proposal generation** | C22 execution logic (what to do, not whether to do it) |
| **Reply detection execution** | C22 ReplyDetection (read-only monitoring) |
| **Failure classification** | ADR-C22-005 (C22 classification service, informed by C20 error taxonomy) |

### 5.3 Gate Decisions

| Decision | Meaning |
| --- | --- |
| **APPROVED** | Proceed to execution; record approval in ExecutionLedger with operator ID, timestamp, scope |
| **DENIED** | Terminal for this action; record denial in ExecutionLedger with operator ID, timestamp, reason; no retry without new ActionGate entry |
| **DEFERRED** | Action paused; operator sets deadline; ActionGate required on resume |

### 5.4 Gate Evidence

At the gate, the human operator is presented with:

- **Identity:** ProspectCandidate record, linked ProspectPool (if any), external provider IDs
- **Proposed action:** Action type (enrich, research, send), target (provider, channel, recipient), content, predicted cost, predicted scope
- **Intelligence context (read-only from C21):** ResearchEvidence, AIQualificationInsight, IntelligenceAggregate, HumanFeedback history
- **Execution history:** ExecutionLedger entries for this ProspectCandidate, prior gate decisions, prior execution results, retry count and budget remaining

---

## 6. ExecutionLedger

### 6.1 Definition

`ExecutionLedger` is the **append-only execution history** for all C22 actions.
No update or delete path exists for any role. Every execution action creates an
ExecutionLedger record. Every ActionGate decision is recorded. Immutability is
enforced at the database level.

### 6.2 Records

ExecutionLedger records:

- **Action request** — what was proposed, by which rule or operator, with what parameters
- **Approval result** — ActionGate decision (APPROVED/DENIED/DEFERRED), operator identity, timestamp, evidence snapshot
- **Execution result** — provider outcome, success/failure, provider correlation ID
- **Provider outcome** — response code, error classification, timing
- **Failure classification** — TRANSIENT / PERMANENT / GOVERNANCE with rationale
- **Retry context** — attempt number, budget consumed, backoff applied

### 6.3 Immutability

Following the C19 `SendExecution` and C20 `AIRequestLog` patterns:

- Database-level enforcement: `REVOKE UPDATE, DELETE ON execution_ledger FROM crm_user`
- ACL denial for all roles
- Correction-by-supersession (a new record supersedes, never overwrites)

---

## 7. Provider Boundary

### 7.1 C20 D3 Reaffirmation

C22 inherits and reaffirms C20 D3 (ADR-C20 §2, D3):

> **All outbound provider I/O goes through the connector.** No PHP code in either module opens an HTTP connection to any provider endpoint.

### 7.2 Provider Ownership Split

```text
┌──────────────────────────────────────────────────────────────┐
│ CRM (EspoCRM)                                                │
│                                                              │
│  Owns:                                                       │
│    · Policy (what, when, who, budget)                        │
│    · Authorization (ActionGate)                              │
│    · Audit (ExecutionLedger, ActionLedger)                   │
│    · Provider metadata (ProviderCredential reference)        │
│                                                              │
│  Does NOT own:                                               │
│    · API execution                                           │
│    · Runtime state                                           │
│    · Secret storage                                          │
│    · HTTP transport                                          │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Connector (chitu_connector)                                  │
│                                                              │
│  Owns:                                                       │
│    · API execution (HTTP transport, retry, timeout)          │
│    · Runtime state (provider health, rate limit tracking)    │
│    · Secret storage (environment variables, never in DB)     │
│    · Provider adapters                                       │
│                                                              │
│  Does NOT own:                                               │
│    · Policy decisions                                        │
│    · Authorization decisions                                 │
│    · Audit trail ownership                                   │
│    · PHP metadata or SQL                                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 7.3 Forbidden Provider Patterns

```text
FORBIDDEN — CRM direct provider egress:

  C22 PHP → curl_exec("https://api.apify.com/...")
  C22 PHP → file_get_contents("https://api.apollo.io/...")
  C22 PHP → new GuzzleHttp\Client()->post("https://api.instantly.ai/...")
  C22 PHP → $mailer->send($smtpConfig)

REQUIRED:

  C22 PHP → C20 AIJobService / CapabilityService
    → Connector (sole egress) → Provider adapter
```

---

## 8. Retry and Loop Governance

### 8.1 Failure Classification (ADR-C22-005)

Every C22 execution failure is classified into exactly one of three categories:

| Category | Definition | Retry Allowed | Examples |
| --- | --- | --- | --- |
| **TRANSIENT** | Temporary condition; may resolve with time | Yes, with budget + ActionGate | Network timeout, HTTP 503, rate limit (429) |
| **PERMANENT** | Non-recoverable; retry won't change outcome | **No — terminal** | Invalid credential (401), hard bounce, validation error (422), quota exhausted |
| **GOVERNANCE** | Policy/authorization decision | **No — terminal** | ActionGate denied, budget ceiling breached, chain depth exceeded |

Unclassified failures default to PERMANENT (do not retry what you don't understand).

### 8.2 Retry Decision Model

```text
Failure → CLASSIFY →
  TRANSIENT + budget available → ActionGate re-entry → APPROVED → Retry
  TRANSIENT + budget exhausted → TERMINAL (operator intervention)
  PERMANENT → TERMINAL (operator must correct root cause; new action, not retry)
  GOVERNANCE → TERMINAL (operator must address governance concern)

FORBIDDEN: Failure → AUTO RETRY → Execute
```

### 8.3 Retry Budget

| Parameter | Default | Scope |
| --- | --- | --- |
| `maxRetriesPerAction` | 3 | Per individual action |
| `maxRetriesPerRun` | 10 | Total across all actions in a run |
| `retryBackoffBaseMs` | 1000 | Exponential backoff base |
| `retryBackoffMaxMs` | 60000 | Maximum backoff ceiling |
| `retryJitter` | Yes | Random jitter |
| `rateLimitRetryBudgetConsumption` | 0 | Rate-limit retries do not consume attempt count |

Budget exhaustion → terminal `FAILED` → operator intervention required.

### 8.4 ActionGate Re-Entry (ADR-C22-007)

After any execution failure, the path back to execution **must** go through `ActionGate`:

```text
CORRECT:
  Execution → Failure → Classification → ExecutionLedger → ActionGate → APPROVED → Retry

FORBIDDEN:
  Failure → AUTO RETRY → Execute
  Failure → AutomationRule bypass → Execute
  Failure → Provider direct replay → Send
  Failure → New ProspectRun auto-create
  Failure → Silent retry with same params
```

Re-entry is mandatory for ALL failure categories. Even TRANSIENT failures require ActionGate re-entry. Classification determines retry eligibility; the gate determines retry authorization.

### 8.5 Rate-Limit Retry Governance (ADR-C22-005 Addendum)

Rate-limit responses (HTTP 429 with `Retry-After`) are classified as TRANSIENT and do not consume the attempt-count retry budget. However, three additional constraints govern rate-limit handling:

| Rule | Requirement |
| --- | --- |
| **Backoff is mandatory** | Immediate retry after RATE_LIMIT is forbidden; controlled backoff required |
| **Wait window is bounded** | Infinite waiting on continuous 429 is forbidden; `maxRateLimitWaitMs` (default: 300000) caps total wait |
| **Execution timeout is binding** | Rate-limit wait cannot extend execution beyond `ProspectRun`/Action timeout |

Window exceeded → stop → human review. Rate-limit exemption from attempt-count budget is not a license for unbounded wall-clock execution.

### 8.6 Forbidden Autonomous Cycles

| Cycle | Description | Prevention |
| --- | --- | --- |
| **A: Send-Retry Loop** | Send → Fail → Retry → Send → Fail → ... | Retry budget + ActionGate re-entry |
| **B: Search-Research-Send Infinite** | Search → Research → Send → Reply → Research → Send → ... | Chain depth (max 7) + ProspectRun scope |
| **C: Failure-Search Regeneration** | Send → Fail → Search (new) → Enrich → Research → Send → Fail → ... | ProspectRun scope boundary; new search requires new ProspectRun |
| **D: AutomationRule Bypass** | DENIED → Rule adjusts params → Execute bypassing gate | Gate cannot be bypassed by rule |
| **E: Provider Direct Replay** | Failure → C20 retry without C22 awareness → duplicate call | C20/C22 retry layer separation + idempotency |
| **F: Auto-Promotion Loop** | Reply → Positive → Auto-Lead → Auto-Opportunity | CRM boundary invariants |

### 8.7 Chain Depth Limit

```text
MAX_CHAIN_DEPTH = 7

Search              (depth 1)
  → Enrichment       (depth 2)
    → AI Research      (depth 3)
      → ActionGate      (depth 4)
        → Outreach       (depth 5)
          → Ledger       (depth 6)
            → Reply       (depth 7)  ← TERMINAL
```

No automated step beyond depth 7. A new `ProspectRun` can be created by a human operator, but the chain does not self-extend.

---

## 9. Invariant Reference

C22 execution invariants are maintained in:

**`docs/adr/C22_INVARIANT_REGISTRY.md`**

The registry defines **29 invariants** across 6 categories:

| Category | Prefix | Count | Key Concerns |
| --- | --- | --- | --- |
| **Identity** | C22-INV-ID | 3 | ProspectCandidate ≠ Lead; ProspectCandidate ≠ ProspectPool; no CRM identity mutation |
| **Execution** | C22-INV-EX | 6 | ActionGate mandatory; human approval default; ExecutionLedger append-only; chain terminates at ReplyDetection; no C19-frozen mutation; ProspectRun is execution container |
| **Provider** | C22-INV-PR | 4 | No HTTP from PHP; C20 credential custody; C22 does not own C20 records; EmailDeliveryProvider port |
| **Retry / Loop Prevention** | C22-INV-RETRY | 9 | Finite retry budget; chain depth bounded; ActionGate re-entry; 6 forbidden cycles; failure classification; idempotency key; rate-limit backoff/window/timeout |
| **C21 Boundary** | C22-INV-C21 | 3 | C21 records read-only; no C21 modification; no parallel intelligence store |
| **CRM Boundary** | C22-INV-CRM | 4 | No auto-Lead; no auto-Opportunity; no sales stage mutation; no canonical_score writes |
| **Total** | | **29** | |

All invariants are currently **DOCUMENTATION_ONLY**. Activation requires C22 Charter ratification, designated owning ADR acceptance, defined activation triggers, and specified contract test paths. The invariant lifecycle follows C20/C21 precedent:

```text
DOCUMENTATION_ONLY → PROPOSED → ACTIVE → (never deleted, superseded only)
```

---

## 10. ADR Reference

### 10.1 C22 Governance ADRs

The following ADRs define the C22 governance architecture and are incorporated by reference into this Charter:

| # | ADR ID | Title | Status |
| --- | --- | --- | --- |
| 1 | **ADR-C22-001** | ProspectCandidate Identity Boundary | Draft Complete |
| 2 | **ADR-C22-002** | Human Approval Gate | Draft Complete |
| 3 | **ADR-C22-005** | Retry Failure Classification | Draft Complete |
| 4 | **ADR-C22-006** | CRM Lifecycle Boundary | Draft Complete |
| 5 | **ADR-C22-007** | ActionGate Re-Entry Rules | Draft Complete |

Supporting addendum:

- **ADR-C22-005 Addendum** — Rate-Limit Retry Governance (C22-INV-RETRY-007/008/009)

### 10.2 Implementation ADRs (Pending)

The following ADRs are prerequisites for C22 implementation work packages and remain pending:

| # | ADR ID | Title | Prerequisite For |
| --- | --- | --- | --- |
| 6 | ADR-C22-003 | ExecutionLedger Immutability | WP1 — ExecutionLedger entity |
| 7 | ADR-C22-004 | Provider Egress Boundary | WP1 — Provider egress |
| 8 | ADR-C22-008 | ProspectRun Scope Isolation | WP2 — ProspectRun |
| 9 | ADR-C22-009 | Duplicate Prevention / Idempotency | WP2 — Idempotency |

### 10.3 Related Governance Artifacts

| Artifact | Path | Status |
| --- | --- | --- |
| C22 Charter Amendment V1 | `docs/audit/PHASE3C22_CHARTER_AMENDMENT_V1.md` | APPROVED |
| C22 Charter Review | `docs/audit/PHASE3C22_CHARTER_REVIEW.md` | APPROVED WITH CONDITIONS |
| C22 Invariant Registry | `docs/adr/C22_INVARIANT_REGISTRY.md` | DOCUMENTATION_ONLY |
| C21 Charter (FROZEN) | `docs/PHASE3C21_CHARTER.md` | FROZEN |
| C21 ADR (Accepted) | `docs/adr/ADR-C21_AI_SALES_INTELLIGENCE_ARCHITECTURE.md` | Accepted |
| C20 ADR (Accepted) | `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` | Accepted |
| C20 Invariant Registry | `docs/adr/C20_INVARIANT_REGISTRY.md` | Active |
| C21 Invariant Registry | `docs/adr/C21_INVARIANT_REGISTRY.md` | Active |

---

## 11. Condition Resolution Summary

All five conditions from the Charter Review (`docs/audit/PHASE3C22_CHARTER_REVIEW.md`) are resolved:

| # | Condition | Severity | Resolved By |
| --- | --- | --- | --- |
| **C1** | ProspectCandidate Identity Boundary | BLOCKING | ADR-C22-001 |
| **C2** | Human Approval Default | BLOCKING | ADR-C22-002 |
| **C3** | CRM Lifecycle Boundary | BLOCKING | ADR-C22-006 |
| **C4** | C22 Invariant Registry | REQUIRED | C22_INVARIANT_REGISTRY_DRAFT.md (29 invariants) |
| **C5** | Autonomous Loop Prevention | REQUIRED | ADR-C22-005 + ADR-C22-007 + Rate-Limit Addendum |

---

## 12. Charter Modification Authorization

This Charter authorizes **governance design and bounded work package planning only**. It does not authorize:

- Entity creation
- Metadata modification
- Service implementation
- Hook/guard implementation
- Test authoring
- Connector modification
- Release artifact changes
- PHP changes
- Commit, push, or tag (without explicit approval)

Implementation authorization requires independently approved work package plans that reference this Charter and the required ADRs.

---

*Charter ratification document. Incorporates Charter Amendment V1, accepted ADRs (C22-001, C22-002, C22-005, C22-006, C22-007), Invariant Registry Draft, and Rate-Limit Retry Governance Addendum. References C20 D3, C21 freeze, and CRM Core boundaries.*
