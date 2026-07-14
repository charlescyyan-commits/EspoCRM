# Executive Summary

**Verdict: C11 CONDITIONAL GO.**

C10.6 closed the Evidence production path: `ResearchEvidence` identity, deduplication, and persistence remain frozen. C09/C10 already define draft preparation, human approval, controlled execution, provider adaptation, idempotency, and reply tracking.

The three-layer boundary remains correct:

| Layer | Owns | Does not own |
|---|---|---|
| Chitu Intelligence Engine | Research, enrichment, qualification, scoring, evidence generation | CRM records, sales operation, approval, sending |
| Connector domain | Contract validation, lifecycle semantics, transition guards, deterministic identity, provider-neutral orchestration | AI reasoning, scoring decisions, CRM sales ownership |
| EspoCRM | Sales records, human-visible workflow, approvals, operational records, native ACL/UI/audit | AI reasoning, enrichment, scoring, external intelligence generation |

C11 must persist and project existing C10 concepts. It must not replace the C10 state machine or become an outreach engine. Source review confirms that C10 Protocol seams exist while CRM has no `DraftApproval`, `SendExecution`, or `ReplyEvent` entity. C10.6 Evidence persistence and Connector Contract V1 are outside C11.

# Recommended C11 Scope

## Ownership and projection boundary

| Concept | CRM ownership | Connector ownership | Projection rule |
|---|---|---|---|
| `DraftApproval` | Durable human-visible record: reviewer, decision, audit, Lead relationship | C10.1 transition validation through the unchanged `HumanApprovalRegistry` | Project the accepted lifecycle state to `Lead.peEmailStatus`; never infer approval from Lead fields. |
| `SendExecution` | Durable operational record: request, approval/Lead references, state, result, provider trace, audit trace | C10.3 semantics through the unchanged `SendExecutionRegistry` | Connector writes through the registry; CRM is the durable operational read model. CRM workflow must not advance execution state independently. |
| `ReplyEvent` | Durable immutable event: reply identity, trace references, reply status, original send trace | C10.4 validation and identity through the unchanged `ReplyEventRegistry` | Connector accepts only traceable sent executions; CRM displays the accepted event and its derived Lead status. |
| `DraftStore` | No C11 CRM entity and no full draft-body storage | New connector Protocol, content hash, deterministic retrieval/re-generation | Persist only an approved hash/reference if needed for audit; CRM is not the email-content authority. |
| `SendRequest`, `SendAttempt`, provider cache | No C11 CRM entity | Connector-internal idempotency and transient mechanics | Only accepted `SendExecution` outcome is human-visible. |
| `Lead.peEmail*` | CRM-visible sales/operations summary | Connector is the transition-driven writer | Derived projection only; never canonical C10 state or a reverse command channel. |

The intended model is therefore: CRM holds durable human-visible records; connector owns state-machine semantics and transition execution; Lead `peEmail*` fields are derived projections.

## Recommended sequence

1. **C11.1 — schema and visibility:** native `DraftApproval`, `SendExecution`, and `ReplyEvent` entities; relationships, native layouts/labels/ACLs, normal lookup indexes, and `PENDING_REVIEW`, `READY_TO_SEND`, `SEND_FAILED` on `peEmailStatus`.
2. **C11.2 — registry substitution:** REST-backed implementations of the three existing Protocols. Retain in-memory registries for offline contract tests.
3. **C11.3 — one-way status projection:** one post-transition adapter writes only established `peEmail*` projection fields. It must not create another lifecycle state machine.
4. **C11.4 — DraftStore:** connector-side Protocol and deterministic reference implementation, with approval-content hash verification.
5. **C11.5 — verification:** registry parity, unique-conflict, projection, and trace-continuity tests; then run the complete freeze gate from the candidate commit.

For new entity identity, use one unique key per canonical C10 identity: `DraftApproval.draftId`, `SendExecution.sendRequestId`, and `ReplyEvent.replyEventId`. Use ordinary indexes for Lead and send-attempt lookup.

`peEmailReplyStatus` must remain a varchar in the first schema step. Its existing values need a read-only inventory and approved mapping before any enum migration. The new `ReplyEvent.replyStatus` may use the C10.4 enum independently.

# Out of Scope

C11 must not:

- reimplement C10 approval, send execution, idempotency, reply tracking, or frozen state transitions;
- add SMTP, a provider SDK, credentials, webhooks, delivery reconciliation, campaign execution, retries, queues, or a send worker;
- alter C10.6 Evidence identity, deduplication, persistence, or its active unique index;
- alter Connector Contract V1 or create a new Chitu-to-Espo sync surface;
- move AI reasoning, enrichment, research, scoring, or external intelligence generation into EspoCRM;
- persist full email content in CRM or create a parallel EmailDraft authority;
- use Lead, Opportunity, or EmailEvent fields as a reverse control channel into C10;
- change CRM sales ownership, native sales lifecycle, or create Opportunities automatically.

# Architecture Risks

| Risk | Impact | Required guardrail |
|---|---|---|
| Approval-content drift | Re-generating a draft from current facts can produce content different from the immutable C10.1-approved draft. | Persist/compute approved content hash. A mismatch must reject delivery or require a new `draft_id` and approval. Do not enable delivery in C11. |
| Duplicate lifecycle writers | Existing `EmailLifecycleSyncService` writes `peEmailStatus` and `peEmailReplyStatus`; a C11 bridge could race or overwrite it. | Define one transition-to-projection mapping and one integration credential. No workflow or legacy service may independently advance C11 entity state. |
| Idempotency ambiguity | C11 design documents both database uniqueness and deferred in-memory `SendIdempotencyRegistry`. | Declare C11 single-process and provider-free while it remains in-memory. Do not claim durable at-most-once send behavior. |
| Redundant approval uniqueness | `UNIQUE(draftId)` makes `UNIQUE(leadId, draftId)` redundant. | Keep one unique `draftId` plus a non-unique Lead index unless a separately versioned contract scopes IDs by Lead. |
| Reply-status migration | Existing CRM values are unconstrained and differ from C10.4 reply statuses. | Inventory values, approve a mapping and rollback plan, then migrate separately. |
| Human/connector authority collision | Free CRM editing of state fields could bypass connector transition guards. | Human decisions use approved transition actions; connector validates and records transitions. Execution/reply records are integration-writable and sales-read-only. |
| Trace discontinuity | Persistence can drop approval, request, attempt, or original send-trace identifiers. | Make the entire C10 trace chain mandatory in entities and registry/parity tests. |

# Preconditions

1. **Clean baseline evidence:** C03–C10.6 and release commits now exist, but the current worktree still has an unstaged extension test and untracked gate/test/documentation files. Resolve those before C11.1.
2. **Clean-commit gate:** T07 records 7/7 and 382/382 passing, but the harness and assertion-alignment files remain untracked/unstaged. Re-run and record the same gate from the intended clean C11 base commit.
3. **Reply-value preflight:** inventory existing `peEmailReplyStatus` values and approve a mapping before any varchar-to-enum migration.
4. **Frozen-contract compatibility:** prove that CRM-backed registries preserve every C10 Protocol signature, duplicate/error behavior, immutable trace, and C09 draft identity. In-memory C10 tests remain mandatory.
5. **Authority design:** document reviewer transition action, Integration Bot write authority, projection-field writer, and audit/retention policy before creating entities.
6. **No-side-effect admission:** C11 remains provider-free, worker-free, credential-free, and free of real customer data/outreach.

Once these conditions are met, C11 may proceed as a narrow persistence-and-projection phase. Any real provider, delivery, or multi-worker send path requires separate architecture approval and a new C10 contract version.
