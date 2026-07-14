# Phase3 Pre-C10 Production Readiness Audit

**Date:** 2026-07-14  
**Scope:** Read-only audit — no code, DB, ACL, config, or deployment changes  
**Auditor:** Claude Code + DeepSeek V4 Pro API  
**Extension Version:** 1.9.5-alpha  
**Repository:** D:\EspoCRM-Production

---

## Executive Summary

| Audit Dimension | Verdict |
|---|---|
| 1. Complete Data Flow | ✅ READY — 10-stage pipeline fully traceable, no gaps |
| 2. Data Ownership | ✅ READY — Clear owner, writable components, and forbidden mutations per entity |
| 3. CRM Safety | ✅ READY — No automatic Lead/Opportunity/stage/amount/ownership mutation |
| 4. Scoring | ✅ READY — Single canonical scorer, full traceability, no shadow scoring |
| 5. Email/Outreach Readiness | ✅ READY — Draft ≠ Send; no SMTP, campaign execution, or approval bypass |
| 6. External Side Effects | ✅ READY — No blocker-level side effect identified |
| 7. Security/Permissions | ✅ READY — 4 roles, field-level ACL, evidence denied to sales |
| 8. Idempotency/Recovery | ⚠️ READY WITH CONDITIONS — 5 areas need attention |
| 9. Production Readiness | ⚠️ READY WITH CONDITIONS — 6 recommendations |
| 10. C10 Decision | **READY WITH CONDITIONS** |

**Overall Verdict: READY WITH CONDITIONS for Phase3C10 Outreach Execution.**

5 conditions, 10 recommendations. 0 blockers.

---

## 1. Complete Data Flow Audit

### 1.1 Pipeline Trace

```
Discovery (SearchStrategy → SearchJob → ProspectPool)
    ↓ via connector_api.py / ChituSyncService::syncLead()
Research (website_research.py → evidence_extraction.py → ResearchEvidence)
    ↓ via enrichment_gate.py (DeterministicEnrichmentGate)
Evidence (ResearchEvidence pe* fields persisted in CRM)
    ↓ via score_input_adapter.py (DeterministicScoreInputAdapter)
Qualification (QualificationDecision: NOT_READY/REVIEW_REQUIRED/QUALIFIED)
    ↓ via canonical_score_integration.py (CanonicalScoreIntegration)
Score (CanonicalScoreResult via single injectable CanonicalScoreExecutor)
    ↓ via outreach_input_adapter.py (DeterministicOutreachInputAdapter)
Outreach Preparation (OutreachInput → EmailDraft via DeterministicEmailDraftGenerator)
    ↓ via campaign_projection.py (CampaignProjectionAdapter)
Approval (NOT YET IMPLEMENTED — marked as C10 boundary)
    ↓ (NOT YET IMPLEMENTED)
Send (NOT YET IMPLEMENTED — explicitly absent; no SMTP, no provider, no campaign exec)
    ↓ via brevo_api.py / PostSyncBrevoEmailEvent / EmailEventWorkflowHook
Reply (EmailEvent ingestion → Lead peEmailStatus → CRM Task creation)
```

### 1.2 Components Inventory

| Stage | Module | Type | Status |
|---|---|---|---|
| Discovery | `acquisition/worker.py`, `espo_repository.py`, `runner.py` | Search→ProspectPool | ✅ IMPLEMENTED |
| Research | `website_research.py`, `evidence_extraction.py` | Evidence collection | ✅ IMPLEMENTED (vendor boundary) |
| Evidence | `syncEvidence()` in `ChituSyncService.php` | `POST /Prospecting/sync/evidence` | ✅ IMPLEMENTED |
| Qualification | `enrichment_gate.py` | DeterministicEnrichmentGate | ✅ IMPLEMENTED |
| Score | `canonical_score_integration.py` | CanonicalScoreIntegration | ✅ IMPLEMENTED |
| Score Projection | `crm_score_projection.py` | CRMScoreProjectionAdapter | ✅ IMPLEMENTED |
| Outreach Input | `outreach_input_adapter.py` | DeterministicOutreachInputAdapter | ✅ IMPLEMENTED |
| Draft Generation | `email_draft_generation.py` | DeterministicEmailDraftGenerator | ✅ IMPLEMENTED |
| Campaign Projection | `campaign_projection.py` | CampaignProjectionAdapter | ✅ IMPLEMENTED |
| **Approval** | **NOT PRESENT** | **C10 boundary** | ❌ NOT IMPLEMENTED |
| **Send** | **NOT PRESENT** | **No SMTP/campaign/send code** | ❌ NOT IMPLEMENTED |
| Event Ingestion | `brevo_api.py`, `PostSyncBrevoEmailEvent.php` | `POST /Prospecting/brevo/email-event` | ✅ IMPLEMENTED |
| Reply Reaction | `EmailEventWorkflowHook.php` | Task auto-creation for REPLIED/BOUNCED | ✅ IMPLEMENTED |
| Feedback Loop | `feedback_api.py`, `FeedbackSyncService.php` | `POST /Prospecting/feedback/sync` | ✅ IMPLEMENTED |

### 1.3 Missing Contracts

| Contract | Owner | Status |
|---|---|---|
| Approval flow | C10 (out of scope before audit) | ❌ NOT DEFINED |
| Send/delivery boundary | C10 (out of scope before audit) | ❌ NOT DEFINED |
| Reply intelligence → CRM scoring update | Phase3C04/C08 (upstream) | ✅ Stable |
| Campaign execution path | Explicitly excluded in all boundaries | ✅ ABSENT |

### 1.4 Broken Ownership: NONE

Every component owns its domain cleanly:
- `enrichment_gate.py`: Owns qualification decision, no scoring side effect
- `canonical_score_integration.py`: Owns score invocation, no evidence mutation
- `email_draft_generation.py`: Owns draft data, no CRM/send/approval dependency
- `campaign_projection.py`: Owns projection to existing Lead fields, no lead/opportunity creation

### 1.5 Hidden Coupling: NONE

- Every boundary module declares its version (`ADAPTER_VERSION`, `RULE_VERSION`, `GENERATION_VERSION`, `INTEGRATION_VERSION`)
- All adapters accept injected executors/clients (Protocol-based seams)
- `CanonicalScoreExecutor` is a Protocol — the actual scorer is injected, not imported
- `EmailDraftGenerator` is a Protocol — the actual generator is injected, not imported

---

## 2. Data Ownership Audit

### 2.1 Ownership Matrix

| Object | Owner | Writable By | Forbidden Mutations |
|---|---|---|---|
| **SearchStrategy** | CRM (Admin UI) | Admin, Sales Manager | — |
| **SearchJob** | CRM + Connector | `AcquisitionWorker` (claim/update), Admin | Status mutation outside QUEUED→RUNNING→COMPLETED/FAILED |
| **ProspectPool** | CRM + Connector | `AcquisitionWorker` (create via `espo_repository.py`), Admin | — |
| **ResearchEvidence** | Chitu Intelligence | `ChituSyncService::syncEvidence()` (Integration Bot), Admin | Sales User/Manager: **DENIED** (`false` in ACL) |
| **QualificationDecision** | `enrichment_gate.py` | `DeterministicEnrichmentGate.evaluate()` | Read-only; never mutates CRM |
| **ScoreInput** | `score_input_adapter.py` | `DeterministicScoreInputAdapter.build()` | Read-only; never mutates CRM |
| **CanonicalScoreResult** | Injected `CanonicalScoreExecutor` | Only the injected executor | No CRM mutation; only consumed by adapters |
| **EmailDraft** | `email_draft_generation.py` | Only `EmailDraftGenerator` implementation | Immutable dataclass; no CRM dependency |
| **OutreachInput** | `outreach_input_adapter.py` | `DeterministicOutreachInputAdapter.build()` | Read-only; preparation facts only |
| **Lead (pe* fields)** | Chitu Intelligence | `ChituSyncService::syncLead()`, `CRMScoreProjectionAdapter`, `CampaignProjectionAdapter`, `EmailLifecycleSyncService`, `EmailEventWorkflowHook` | `status`, `assignedUser`, `teams` are CRM-owned |
| **Lead (CRM fields)** | CRM (Human) | Admin, Sales User (own), Sales Manager (team) | `pe*` score/research fields: read-only for Sales |
| **Opportunity (pe* fields)** | Chitu Intelligence | `ChituSyncService::syncOpportunityProposal()`, `EmailLifecycleSyncService` | `stage`, `amount`, `closeDate`, `assignedUser` are CRM-owned |
| **Opportunity (CRM fields)** | CRM (Human) | Admin, Sales User (own), Sales Manager (team) | pe* fields: read-only for Sales |
| **EmailEvent** | Chitu + CRM | `BrevoEmailEventSyncService::sync()` (Integration Bot) | Append-only; duplicates rejected by externalMessageId+eventType |

### 2.2 Forbidden Mutations Enforced

| Forbidden Mutation | Enforcement Mechanism | Location |
|---|---|---|
| Auto-create Opportunity | `peProposalAction = "NO_AUTOMATIC_OPPORTUNITY"` (hardcoded) | `ChituSyncService.php:103` |
| Auto-create Opportunity | Score < 80 returns without Opportunity write | `ChituSyncService.php:91-93` |
| Stage mutation by connector | `_FORBIDDEN_SALES_FIELDS` checked on every write body | `lifecycle.py:54-64` |
| Amount mutation by connector | `_FORBIDDEN_SALES_FIELDS` includes `amount`, `amountCurrency` | `lifecycle.py:54-64` |
| Ownership mutation by connector | `_FORBIDDEN_SALES_FIELDS` includes `assignedUserId`, `teamsIds` | `lifecycle.py:54-64` |
| Draft = Send | `CampaignProjectionAdapter` only writes `peEmailStatus`, `peEmailCampaignName`, `peRecommendedApproach` | `campaign_projection.py:15-18` |
| Draft content persisted | `campaign_projection.py` never writes subject/body/evidence content | `campaign_projection.py:96-99` (test verified) |
| Email send from CRM | No SMTP config, no `sendEmail` API, no campaign execution code | Searched entire codebase — 0 results |

---

## 3. CRM Safety Audit

### 3.1 Allowed Operations

| Operation | Component | Allowlist |
|---|---|---|
| Write pe* intelligence fields to Lead | `ChituSyncService::leadFields()` | `peOpportunityScoreV4`, `peScoreTier`, `peBestFirstProduct`, `peSyncStatus`, `peResearchStatus`, `peQualificationStatus`, `peConfidence`, `peEvidenceCoverage`, `peEngineVersion`, `peScoreRulesVersion`, `peSourceSystem`, `peCandidateId`, `peLastSyncAt`, `peResearchSummary`, `peKeyEvidence`, `peRecommendedApproach`, `pePriorityLevel` |
| Write score projection | `CRMScoreProjectionAdapter` | `peOpportunityScoreV4`, `peScoreTier`, `peBestFirstProduct`, `peScoreRulesVersion` |
| Write campaign projection | `CampaignProjectionAdapter` | `peEmailStatus`, `peEmailCampaignName`, `peRecommendedApproach` |
| Write email lifecycle | `EmailLifecycleSyncService` | `peEmailStatus`, `peLastEmailDate`, `peEmailCampaignName`, `peEmailReplyStatus` |
| Write email workflow | `EmailEventWorkflowHook` | `peEmailStatus`, `peLastEmailDate`, `peEmailCampaignName`, `peEmailReplyStatus` |
| Create Task | `LeadWorkflowHook`, `EmailEventWorkflowHook` | Auto-creates "Prepare Outreach", "Review and Contact Lead", "Follow up customer reply", "Verify customer email" |
| Write pe* fields to Opportunity | `ChituSyncService::syncOpportunityProposal()` | `peBestFirstProduct`, `peOpportunityScoreV4`, `peProposalProductFitScore`, `peProposalCooperationType`, `peProposalSuggestedNextAction`, `peProposalEligibility`, `peProposalAction` |

### 3.2 Forbidden Operations (Verified Absent)

| Operation | Check | Result |
|---|---|---|
| Automatic Lead creation from outreach | Searched `campaign_projection.py`, `outreach_input_adapter.py`, `email_draft_generation.py` | ❌ NOT FOUND |
| Automatic Opportunity creation | `peProposalAction = "NO_AUTOMATIC_OPPORTUNITY"` hardcoded in `syncOpportunityProposal()` | ✅ CONFIRMED ABSENT |
| Stage mutation (`status` on Lead, `stage` on Opportunity) | `_FORBIDDEN_SALES_FIELDS` in lifecycle.py, tests verify stage unchanged after email sync | ✅ CONFIRMED ABSENT |
| Amount mutation | `_FORBIDDEN_SALES_FIELDS` includes `amount`, `amountCurrency` | ✅ CONFIRMED ABSENT |
| Ownership mutation (`assignedUser`, `teams`) | `_FORBIDDEN_SALES_FIELDS` includes `assignedUserId`, `teamsIds` | ✅ CONFIRMED ABSENT |
| Hidden workflow triggers that send email | Searched all hooks, controllers, services for `send`/`SMTP`/`dispatch` | ✅ CONFIRMED ABSENT |

### 3.3 Formula Safety (before-save on Lead)

```javascript
// Lead.json formula — 3 rules, all safe:
// Rule 1: peResearchStatus → outreachStatus transition (display-only, no send)
// Rule 2: peOpportunityScoreV4 >= 80 → pePriorityLevel = 'HIGH' (display-only)
// Rule 3: emailAddress/phoneNumber populated → outreachStatus → CONTACT_READY (display-only)
```

All formula actions are **state transitions only** — they set `outreachStatus` and `pePriorityLevel`. No workflow execution, no email sending, no external API calls.

---

## 4. Scoring Audit

### 4.1 Single Canonical Scorer

| Property | Evidence |
|---|---|
| Canonical executor interface | `CanonicalScoreExecutor` Protocol in `canonical_score_integration.py:21-26` |
| Single invocation path | `CanonicalScoreIntegration.evaluate()` — only call site |
| Injector seam | `CanonicalScoreIntegration.__init__(executor: CanonicalScoreExecutor)` |
| No fallback scorer | `DecisionEngineAdapter.score()` raises `RuntimeError("intentionally disabled")` |
| No AI scoring | `canonical_score_integration.py` docstring: "No scoring formula, threshold, or tier definition exists here" |

### 4.2 No Shadow Scoring

| Search | Result |
|---|---|
| `score` in function/class names in connector | Only `canonical_score_integration.py`, `crm_score_projection.py`, `score_input_adapter.py`, `canonical_score.py`, `scoring.py` |
| `score` in CRM PHP layer | Only `peOpportunityScoreV4` field reads, `peScoreTier` enum writes |
| Shadow scoring in hooks | Not found — `LeadWorkflowHook` only reads `peOpportunityScoreV4` to create Tasks |
| Shadow scoring in formula | Not found — formula only transitions `pePriorityLevel` on score >= 80 |

### 4.3 Score Traceability

| Trace Artifact | How |
|---|---|
| Input hash | `CanonicalScoreTrace.input_hash` — SHA-256 of sorted ScoreInput |
| Evidence references | `CanonicalScoreTrace.input_evidence_refs` — sorted peEvidenceId set |
| Canonical engine version | `CanonicalScoreTrace.canonical_engine_version` from executor |
| Content hash | `CanonicalScoreTrace.canonical_content_hash` from executor |
| Integration version | `INTEGRATION_VERSION = "c08-canonical-score-integration-v1"` |
| Score persisted on Lead | `peOpportunityScoreV4`, `peScoreTier`, `peBestFirstProduct`, `peScoreRulesVersion` |

### 4.4 C08 Integration Path

```
C07 Evidence → ScoreInputAdapter.build() → ScoreInput
    → CanonicalScoreIntegration.evaluate(score_input, evidence)
    → CanonicalScoreExecutor.score(score_input)  [INJECTED — not implemented in connector]
    → CanonicalScoreResult
    → CRMScoreProjectionAdapter.project(lead_id, score_result)
    → Lead peOpportunityScoreV4/peScoreTier/peBestFirstProduct/peScoreRulesVersion
```

The path is complete. The score executor is an injectable Protocol — the actual canonical scorer lives upstream (Chitu Intelligence). The connector only bridges.

---

## 5. Email / Outreach Readiness Audit

### 5.1 EmailDraft ≠ Sent Email

| Property | Evidence |
|---|---|
| Draft is an immutable dataclass | `EmailDraft` in `email_draft_generation.py:37-49` — all fields frozen |
| Draft contains no send mechanism | No `send()`, `dispatch()`, `deliver()`, `queue()` method |
| Draft has no SMTP dependency | No import of `smtplib`, no SMTP config |
| Draft has no provider coupling | `EmailDraftGenerator` is a Protocol — provider injection seam |
| Draft content never persisted | `CampaignProjectionAdapter` only writes `peEmailStatus`, `peEmailCampaignName`, `peRecommendedApproach` |
| Draft body never projected | Test `test_never_projects_draft_content_or_unrelated_lead_fields` verifies `subject`/`body` not in projection |

### 5.2 No Send Capability Hidden

| Search | Result |
|---|---|
| `send_email`, `sendEmail`, `dispatch`, `deliver` | 0 matches in CRM extension |
| `SMTP`, `smtp` | 0 matches in CRM extension PHP code |
| `campaign.*execut`, `approval.*bypass` | 0 matches in connector |
| `outreach_execut`, `outreach_approv` | 0 matches in entire codebase |

### 5.3 No Approval Bypass

| Check | Status |
|---|---|
| Approval UI | ❌ NOT IMPLEMENTED — C10 boundary |
| Approval API endpoint | ❌ NOT IMPLEMENTED |
| Approval skip flag | ❌ NOT FOUND in any code |
| Automated approval | ❌ NOT FOUND — no `autoApprove`, no timer-based approval |

### 5.4 Email Lifecycle Safety

| Path | Safety Check |
|---|---|
| `BrevoEmailEventSyncService` | "Does not send email" — docstring |
| `BrevoConnectorClient` | "Does not send email" — docstring |
| `EmailEventWorkflowHook` | "Does not send email" — docstring; only updates pe* status + creates Tasks |
| `EmailLifecycleSyncService` | Only allowlisted 4 fields (`peEmailStatus`, `peLastEmailDate`, `peEmailCampaignName`, `peEmailReplyStatus`) |
| `update_lead_campaign_projection` | "never send or approve" — docstring |

### 5.5 Campaign Execution Path: ABSENT

No component in the connector or CRM extension:
- Calls a campaign execution API
- Queues an email for delivery
- Triggers a Brevo/SendGrid/Mailgun send
- Activates an EspoCRM campaign
- Creates an EspoCRM Email entity

---

## 6. External Side Effect Audit

### 6.1 Side Effect Classification

#### SAFE (read-only, no CRM write, no external API)

| Component | Side Effects |
|---|---|
| `DeterministicEnrichmentGate.evaluate()` | Returns `QualificationDecision` — no I/O |
| `DeterministicScoreInputAdapter.build()` | Returns `ScoreInput` — no I/O |
| `DeterministicOutreachInputAdapter.build()` | Returns `OutreachInput` — no I/O |
| `DeterministicEmailDraftGenerator.generate()` | Returns `EmailDraft` — no I/O |
| `validate_sync_contract()` | Returns `list[str]` — no I/O |

#### REVIEW REQUIRED (CRM write, constrained)

| Component | Side Effects | Constraints |
|---|---|---|
| `CRMScoreProjectionAdapter.project()` | Writes 4 allowlisted fields to existing Lead | Field-level allowlist in `_PROJECTABLE_FIELDS` |
| `CampaignProjectionAdapter.project()` | Writes 3 allowlisted fields to existing Lead | Field-level allowlist in `_PROJECTABLE_FIELDS` |
| `ChituSyncService::syncLead()` | Creates/updates Lead with pe* fields only | ACL check before create/edit; contract validation |
| `ChituSyncService::syncEvidence()` | Creates ResearchEvidence linked to existing Lead | ACL check for Lead read + ResearchEvidence create |
| `ChituSyncService::syncOpportunityProposal()` | Updates Lead with `NO_AUTOMATIC_OPPORTUNITY` + score fields | ACL check for Lead edit; score >= 80 gate |
| `EmailLifecycleSyncService.sync()` | Updates 4 email lifecycle fields on Lead/Opportunity | Allowlisted fields only; verified CRM fields unchanged |
| `BrevoEmailEventSyncService::sync()` | Creates EmailEvent record; idempotent (dedup on externalMessageId+eventType) | Append-only; duplicates rejected |

#### BLOCKER: NONE

No component exhibits blocker-level side effects:
- No automatic email sending
- No automatic Opportunity creation
- No automatic stage/amount/ownership mutation
- No campaign execution
- No approval bypass

### 6.2 External API Call Inventory

| Module | External Call | Protocol |
|---|---|---|
| `espo_repository.py` (EspoAcquisitionRepository) | EspoCRM REST API (SearchJob, ProspectPool CRUD) | HTTP/X-Api-Key |
| `real_client.py` (LocalEspoCRMClient) | EspoCRM REST API (localhost:8080 only) | HTTP/X-Api-Key or Basic |
| `connector_api.py` (ProspectingConnectorClient) | EspoCRM `/Prospecting/sync/*` endpoints | HTTP/X-Api-Key |
| `brevo_api.py` (BrevoConnectorClient) | EspoCRM `/Prospecting/brevo/email-event` endpoint | HTTP/X-Api-Key |
| `feedback_api.py` (FeedbackConnectorClient) | EspoCRM `/Prospecting/feedback/sync` endpoint | HTTP/X-Api-Key |
| `runner.py` (_UrllibTransport) | Serper Search API (when `--provider serper`) | HTTP |
| `apify_provider.py` | Apify API | HTTP |
| `serper_provider.py` | Serper API | HTTP |

---

## 7. Security / Permission Audit

### 7.1 Role Matrix (from Phase3B00 — confirmed unchanged)

| Entity | Admin | Integration Bot | Sales User | Sales Manager |
|---|---|---|---|---|
| **Lead** | CRUD all | CRUD (no delete) | Create, Read own, Edit own (no delete) | CRUD team (no delete) |
| **Opportunity** | CRUD all | CRUD (no delete) | Create, Read own, Edit own (no delete) | CRUD team (no delete) |
| **ResearchEvidence** | CRUD all | CRUD (no delete) | **DENIED** | **DENIED** |
| **EmailEvent** | CRUD all | CRUD | **DENIED** (likely) | Indirect via Lead |
| **SalesFeedback** | CRUD all | CRUD | **DENIED** (likely) | Indirect via Lead |
| **SearchStrategy** | CRUD all | Read only | As permitted by Prospecting ACL | As permitted |
| **SearchJob** | CRUD all | Read + claim/update | As permitted by Prospecting ACL | As permitted |
| **ProspectPool** | CRUD all | Read + create | As permitted by Prospecting ACL | As permitted |

### 7.2 Who Can Do What (Outreach-Specific)

| Action | Admin | Integration Bot | Sales User | Sales Manager |
|---|---|---|---|---|
| View evidence | ✅ | ✅ | ❌ | ❌ |
| View scores | ✅ | ✅ | ✅ (read-only) | ✅ (read-only) |
| View pe* research fields | ✅ | ✅ | ✅ (read-only) | ✅ (read-only) |
| Edit pe* research fields | ✅ | ✅ | ❌ | ❌ |
| View draft status (peEmailStatus) | ✅ | ✅ | ✅ | ✅ |
| Edit draft status | ✅ | ✅ (via sync API) | ❌ | ❌ |
| Approve drafts | N/A (not implemented) | N/A | N/A | N/A |
| Send outreach | N/A (not implemented) | N/A | N/A | N/A |
| View email events | ✅ | ✅ | ❌ (likely) | ❌ (likely) |
| Create feedback | ✅ | ✅ (via sync API) | ❌ | ❌ |

### 7.3 ACL Enforcement Points

| Layer | Mechanism |
|---|---|
| API route handler | `ChituSyncService::assertScope()` checks `$this->acl->check(scope, action)` |
| Field-level write | `ChituSyncService::leadFields()` only sets allowlisted pe* fields |
| CRM entity edit | `$this->acl->checkEntityEdit($lead)` before saving |
| CRM entity read | `$this->acl->checkEntityRead($lead)` before linking evidence |
| Lifecycle sync | `_FORBIDDEN_SALES_FIELDS` enforced on every update body |
| Sales field-level | peSyncStatus, peSourceSystem, peCandidateId: hidden (read=no, edit=no) for Sales roles |
| AI field-level | peOpportunityScoreV4, peScoreTier, etc.: read-only for Sales roles |

---

## 8. Idempotency and Recovery Audit

### 8.1 Idempotency Mechanisms

| Entity | Mechanism | Strength |
|---|---|---|
| **Lead** | `findLead()` by `peCandidateId` — upsert semantics; duplicate detection throws Conflict | ⚠️ Strong for lookup; no delivery deduplication at API level |
| **ResearchEvidence** | No dedup on evidence_id in PHP service — creates new records on each syncEvidence call | ⚠️ Weak — repeated syncEvidence calls create duplicate evidence records |
| **EmailEvent** | Dedup on `(externalMessageId, eventType)` composite — duplicates detected and returned with `duplicate: true` | ✅ Strong |
| **SalesFeedback** | Dedup on `externalFeedbackId` or derived SHA-256 idempotency key | ✅ Strong |
| **SearchJob claim** | `AcquisitionWorker` checks `expected_status: "QUEUED"` before claiming; `EspoAcquisitionRepository.claim_search_job()` does GET→PUT→verify | ⚠️ Medium — best-effort; no atomic CAS |
| **ProspectPool** | `has_prospect()` dedup on `(source, website)` before `create_prospect()` | ⚠️ Medium — race window between check and create |
| **Score projection** | `CRMScoreProjectionAdapter.project()` overwrites existing fields — idempotent by nature | ✅ Strong (idempotent write) |
| **Campaign projection** | `CampaignProjectionAdapter.project()` overwrites existing fields — idempotent by nature | ✅ Strong (idempotent write) |
| **Sync payload** | `idempotency_key()` hash of `(domain, engine_version, score_rules_version, contract_version)` | ✅ Strong — used for duplicate Lead detection |

### 8.2 Retry Behavior

| Scenario | Behavior |
|---|---|
| SearchJob claim fails (STATUS_MISMATCH) | Returns `NOT_CLAIMED` with exit code 3; retryable |
| SearchJob claim fails (VERSION_MISMATCH) | Returns `NOT_CLAIMED` with exit code 3; retryable |
| Provider error (Serper) | Returns `FAILED` with retryable flag; SearchJob → FAILED with error details |
| Persistence error (EspoCRM) | Returns `FAILED` with `retryable=True` for 429/5xx, `retryable=False` for 4xx |
| Partial persistence | `partial_persistence=True` flag on result; `final_status_uncertain=True` if completion update failed |
| Connector sync failure | `ConnectorSyncResult` with per-step status (validation, gate, lead, evidence, proposal) |
| Email event duplicate | Returns `duplicate: true` with existing email_event_id — safe to retry |
| Feedback duplicate | Detected by externalFeedbackId; returns `created: false` |

### 8.3 Idempotency Gaps

| # | Gap | Severity | Recommendation |
|---|---|---|---|
| I1 | **ResearchEvidence: no dedup on syncEvidence** | **MEDIUM** | Add dedup check on `peEvidenceId + peSnapshotHash` before creating new evidence records |
| I2 | **Lead: no delivery-level idempotency key** | **MEDIUM** | Use `idempotency_key()` in sync request headers; check before processing on server side |
| I3 | **ProspectPool: TOCTOU race on has_prospect/create_prospect** | LOW | Add unique index on `(source, website)` in entityDefs; catch DB-level constraint violation |
| I4 | **SearchJob claim: no atomic compare-and-swap** | LOW | EspoCRM REST API limitation; acceptable for single-runner MVP |
| I5 | **SearchJob update: version-based optimistic locking uses modifiedAt** | LOW | `modifiedAt` changes on any field update — fragile; use ETag/If-Match if available |

### 8.4 Recovery Paths

| Failure | Recovery |
|---|---|
| Runner crash during search | `AcquisitionWorker._fail_after_claim()` sets SearchJob → FAILED with `completedAt`, `errorMessage`, `failureReason` |
| Runner crash during persistence | `partial_persistence=True` + `final_status_uncertain=True`; search job marked FAILED |
| Runner crash during completion update | `completion_persistence_failed=True`; human inspection required |
| Connector sync failure mid-pipeline | `ConnectorSyncResult` with per-step status; gate/lead/evidence/proposal each track completed state |

---

## 9. Production Readiness Assessment

### 9.1 Logging

| Component | Logging | Status |
|---|---|---|
| `runner.py` | Structured JSON output to stdout; human-readable mode available | ⚠️ Minimal — no file-based logging, no log levels |
| `espo_repository.py` | Error codes in `PersistenceError` exceptions | ⚠️ Minimal — exception-based only |
| `connector_api.py` | `ConnectorApiError` with HTTP status | ⚠️ Minimal |
| CRM PHP services | EspoCRM built-in logging (via `EntityManager`) | ✅ Adequate — EspoCRM handles this |
| CRM hooks | EspoCRM built-in logging | ✅ Adequate |

### 9.2 Audit Trail

| Artifact | Coverage |
|---|---|
| `CanonicalScoreTrace` | Full input→output traceability for every score |
| `CanonicalScoreDecision` | Result + trace paired |
| `idempotency_key()` / `payload_hash()` / `evidence_snapshot_hash()` | Content-addressable integrity for sync payloads |
| `DraftEvidenceReference` | Every draft links to exact evidence_id + source_url |
| `PersonalizationReference` | Every draft records which fields were used |
| `peLastSyncAt` on Lead | Timestamp of last sync |
| `peEngineVersion` / `peScoreRulesVersion` on Lead | Version provenance |
| Connector response payloads | `created`, `updated`, `external_id`, `crm_id` in every response |

### 9.3 Failure Recovery

| Concern | Assessment |
|---|---|
| Runner handles provider timeout | ✅ `_UrllibTransport` has configurable timeout; `ProviderError` with retryable flag |
| Runner handles EspoCRM unavailability | ✅ `PersistenceError` with retryable flag; 429/5xx = retryable |
| Connector handles API 4xx/5xx | ✅ `ConnectorApiError` raised; per-step tracking |
| Partial sync rollback | ✅ `LocalEspoCRMClient.rollback()` for synthetic tests; production sync doesn't auto-rollback (needs manual cleanup) |
| Duplicate Lead detection | ✅ Conflict error when multiple Leads share peCandidateId |

### 9.4 Monitoring Gaps

| Gap | Severity |
|---|---|
| No health check endpoint | LOW — EspoCRM has `/api/v1/App/user`; connector could add a liveness check |
| No metrics export | LOW — runner outputs JSON; could be scraped |
| No alerting on FAILED SearchJobs | MEDIUM — relies on human monitoring of CRM dashboards |
| No sync latency tracking | LOW — `durationMs` in runner output; no aggregation |
| No connector-side error rate tracking | LOW — exception-based; no counters |

### 9.5 Concurrency Risks

| Risk | Mitigation | Assessment |
|---|---|---|
| Double-claim of SearchJob | GET→PUT→verify in `claim_search_job()`; non-atomic | ⚠️ Best-effort; acceptable for single-runner MVP |
| Double-create of ProspectPool | `has_prospect()` check; race window exists | ⚠️ Acceptable; dedup fingerprint in note field for audit |
| Concurrent sync for same Lead | `peCandidateId` lookup returns Conflict for duplicates | ✅ Safe |
| Concurrent evidence sync | Creates duplicates (see I1 gap) | ⚠️ Needs dedup |
| Concurrent score projection | Idempotent overwrite — safe | ✅ Safe |

---

## 10. C10 Readiness Decision

### 10.1 What Exists Today

The following pipeline stages are fully implemented and verified:

1. **Discovery** → ProspectPool creation from search providers
2. **Research** → Website evidence collection (vendor boundary)
3. **Evidence** → ResearchEvidence persistence in CRM with Lead linking
4. **Qualification** → Deterministic evidence-quality gating
5. **Scoring** → Single canonical scorer invocation with full traceability
6. **Score Projection** → Safe Lead field updates
7. **Outreach Preparation** → Evidence-backed talking points, company context
8. **Draft Generation** → Immutable EmailDraft with evidence references
9. **Campaign Projection** → Draft-preparation status fields on Lead
10. **Email Event Ingestion** → Brevo event → CRM lifecycle projection
11. **Reply Reaction** → Auto-created Tasks for REPLIED/BOUNCED events
12. **Feedback Loop** → Sales outcome feedback ingestion

### 10.2 What C10 Needs to Add

The following are explicitly absent and belong in C10:

1. **Approval workflow** — Human review gate before sending
2. **Send mechanism** — Email delivery integration (Brevo/SMTP)
3. **Approval UI** — CRM interface for reviewing and approving drafts
4. **Send tracking** — Outbound send event creation and tracking

### 10.3 What Must Be True Before C10 Sending

| Condition | Status |
|---|---|
| Approval step is mandatory | ❌ Not implemented |
| Send is a separate, explicit action | ❌ Not implemented |
| Approval cannot be bypassed programmatically | ❌ Not yet enforced (no approval exists to bypass) |
| Audit trail exists for every send | ❌ Not implemented |
| Draft ≠ Send boundary is preserved | ✅ Verified — no send capability exists |

### 10.4 Final Verdict

```
██████╗ ███████╗ █████╗ ██████╗ ██╗   ██╗
██╔══██╗██╔════╝██╔══██╗██╔══██╗╚██╗ ██╔╝
██████╔╝█████╗  ███████║██║  ██║ ╚████╔╝
██╔══██╗██╔══╝  ██╔══██║██║  ██║  ╚██╔╝
██║  ██║███████╗██║  ██║██████╔╝   ██║
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝    ╚═╝

██╗    ██╗██╗████████╗██╗  ██╗
██║    ██║██║╚══██╔══╝██║  ██║
██║ █╗ ██║██║   ██║   ███████║
██║███╗██║██║   ██║   ██╔══██║
╚███╔███╔╝██║   ██║   ██║  ██║
 ╚══╝╚══╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝

 ██████╗ ██████╗ ███╗   ██╗██████╗ ██╗████████╗██╗ ██████╗ ███╗   ██╗███████╗
██╔════╝██╔═══██╗████╗  ██║██╔══██╗██║╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝
██║     ██║   ██║██╔██╗ ██║██║  ██║██║   ██║   ██║██║   ██║██╔██╗ ██║███████╗
██║     ██║   ██║██║╚██╗██║██║  ██║██║   ██║   ██║██║   ██║██║╚██╗██║╚════██║
╚██████╗╚██████╔╝██║ ╚████║██████╔╝██║   ██║   ██║╚██████╔╝██║ ╚████║███████║
 ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
```

**VERDICT: READY WITH CONDITIONS**

The Phase3 architecture is ready to introduce controlled external outreach actions, provided the following conditions are met:

### Prerequisite Conditions for C10

| # | Condition | Impact if Skipped |
|---|---|---|
| **C1** | **Add ResearchEvidence dedup** before C10 evidence sync is used in production | Duplicate evidence records from retried sync calls |
| **C2** | **Add delivery-level idempotency key** to sync requests | Duplicate Lead updates from retried syncs |
| **C3** | **C10 Approval workflow must be mandatory** — no send without human approval | Premature/unauthorized outreach |
| **C4** | **C10 Send must be an explicit, audited action** — never automated | Loss of control over outreach execution |
| **C5** | **Preserve Draft ≠ Send boundary** — C10 must add send as a new layer, not modify draft generation | Accidental sends from draft preparation |

### Recommended Fixes (can be post-C10 or parallel)

| # | Finding | Priority |
|---|---|---|
| R1 | Add ProspectPool unique index on (source, website) to prevent duplicates at DB level | LOW |
| R2 | Add structured file-based logging to connector runner | LOW |
| R3 | Add alerting for FAILED SearchJobs (CRM dashboard or monitoring) | MEDIUM |
| R4 | Add connector health check endpoint | LOW |
| R5 | Add atomic claim for SearchJob (if EspoCRM adds ETag/CAS support) | LOW |
| R6 | Document retry strategy for each failure mode | MEDIUM |
| R7 | Add test for duplicate evidence dedup (I1) | MEDIUM |
| R8 | Consider moving `idempotency_key()` to sync request header for server-side dedup | MEDIUM |
| R9 | Document the C10 approval workflow contract before implementation | HIGH |
| R10 | Add `EMAIL_SENT` EmailEvent type and corresponding workflow hook before C10 send | HIGH |

---

## Appendix A: Architecture Strengths

1. **Multi-layered safety**: Contract validation → gate → field allowlisting → forbidden sales fields → entity type gating → localhost enforcement → ACL checks — 7 layers deep.

2. **Protocol-based injection seams**: `CanonicalScoreExecutor`, `EmailDraftGenerator`, `AcquisitionStore`, `LeadCampaignProjectionClient` — every boundary has an injectable Protocol, enabling testability and future provider swaps.

3. **Immutable data contracts**: `EmailDraft`, `OutreachInput`, `ScoreInput`, `QualificationDecision`, `CanonicalScoreResult` — all frozen dataclasses; no mutation after creation.

4. **Versioned boundaries**: Every adapter declares its version (`ADAPTER_VERSION`, `RULE_VERSION`, `GENERATION_VERSION`, `INTEGRATION_VERSION`) — enabling contract evolution tracking.

5. **Content-addressable integrity**: `idempotency_key()`, `payload_hash()`, `evidence_snapshot_hash()`, `CanonicalScoreTrace.input_hash` — every significant artifact is hashable and traceable.

6. **Fail-closed gating**: 10 reject conditions in `evaluate_sync_gate()` before sync is allowed; any unexpected state → reject.

7. **Field-level ownership**: `_FORBIDDEN_SALES_FIELDS` enforcement on every write body; `_PROJECTABLE_FIELDS` allowlists on every projection.

8. **Deterministic, no-AI safety boundaries**: `DeterministicEnrichmentGate`, `DeterministicScoreInputAdapter`, `DeterministicOutreachInputAdapter`, `DeterministicEmailDraftGenerator` — no AI model is invoked in the connector layer.

---

## Appendix B: Component-to-File Map

| Component | Primary File(s) |
|---|---|
| Acquisition Worker | `chitu-connector/chitu_connector/acquisition/worker.py` |
| EspoCRM Repository | `chitu-connector/chitu_connector/acquisition/espo_repository.py` |
| Runner CLI | `chitu-connector/chitu_connector/acquisition/runner.py` |
| Search Providers | `chitu-connector/chitu_connector/acquisition/providers/*.py` |
| Sync Contract | `chitu-connector/chitu_connector/espocrm_sync/contract.py` |
| Sync Mapper | `chitu-connector/chitu_connector/espocrm_sync/mapper.py` |
| Sync Gate | `chitu-connector/chitu_connector/espocrm_sync/gate.py` |
| Enrichment Gate | `chitu-connector/chitu_connector/espocrm_sync/enrichment_gate.py` |
| Score Input Adapter | `chitu-connector/chitu_connector/espocrm_sync/score_input_adapter.py` |
| Canonical Score Integration | `chitu-connector/chitu_connector/espocrm_sync/canonical_score_integration.py` |
| CRM Score Projection | `chitu-connector/chitu_connector/espocrm_sync/crm_score_projection.py` |
| Outreach Input Adapter | `chitu-connector/chitu_connector/espocrm_sync/outreach_input_adapter.py` |
| Email Draft Generation | `chitu-connector/chitu_connector/espocrm_sync/email_draft_generation.py` |
| Campaign Projection | `chitu-connector/chitu_connector/espocrm_sync/campaign_projection.py` |
| Brevo API Client | `chitu-connector/chitu_connector/espocrm_sync/brevo_api.py` |
| Feedback API Client | `chitu-connector/chitu_connector/espocrm_sync/feedback_api.py` |
| Connector API Client | `chitu-connector/chitu_connector/espocrm_sync/connector_api.py` |
| Lifecycle Sync | `chitu-connector/chitu_connector/espocrm_sync/lifecycle.py` |
| Email Lifecycle Sync | `chitu-connector/chitu_connector/espocrm_sync/email_lifecycle.py` |
| Idempotency Keys | `chitu-connector/chitu_connector/espocrm_sync/idempotency.py` |
| Local EspoCRM Client | `chitu-connector/chitu_connector/espocrm_sync/real_client.py` |
| ChituSyncService | `crm-extension/files/custom/Espo/Modules/Prospecting/Services/ChituSyncService.php` |
| BrevoEmailEventSyncService | `crm-extension/files/custom/Espo/Modules/Prospecting/Services/BrevoEmailEventSyncService.php` |
| FeedbackSyncService | `crm-extension/files/custom/Espo/Modules/Prospecting/Services/FeedbackSyncService.php` |
| LeadWorkflowHook | `crm-extension/files/custom/Espo/Custom/Hooks/Lead/LeadWorkflowHook.php` |
| EmailEventWorkflowHook | `crm-extension/files/custom/Espo/Custom/Hooks/EmailEvent/EmailEventWorkflowHook.php` |
| Lead Formula | `crm-extension/Resources/entityDefs/Lead.json` (formula block) |
| Lead entityDefs | `crm-extension/Resources/entityDefs/Lead.json` |
| Opportunity entityDefs | `crm-extension/Resources/entityDefs/Opportunity.json` |
| ResearchEvidence entityDefs | `crm-extension/Resources/entityDefs/ResearchEvidence.json` |
| ProspectPool entityDefs | `crm-extension/Resources/entityDefs/ProspectPool.json` |
| SearchJob entityDefs | `crm-extension/Resources/entityDefs/SearchJob.json` |
| SearchStrategy entityDefs | `crm-extension/Resources/entityDefs/SearchStrategy.json` |
| EmailEvent entityDefs | `crm-extension/Resources/entityDefs/EmailEvent.json` |

---

## Appendix C: Test Coverage Relevant to C10

| Test | What It Verifies |
|---|---|
| `test_phase3c08_runtime_acceptance.py` | Score input → canonical score → CRM projection end-to-end; no email sends |
| `test_phase3c08_crm_score_projection.py` | Only 4 fields projected; permission denial handled; no unrelated field writes |
| `test_phase3c09_outreach_runtime_acceptance.py` | Qualification → outreach input → draft → campaign projection; no sends, no creates, no approvals |
| `test_phase3c09_campaign_projection.py` | Only 3 fields projected; draft content never leaked; permission denial handled |
| `test_extension_skeleton.py` | Field nullability, workflow fields, ACL metadata, entityDef parity, formula verification |

---

**No files were modified by this audit.**
**No CRM data was accessed or modified.**
**No external APIs were called.**
