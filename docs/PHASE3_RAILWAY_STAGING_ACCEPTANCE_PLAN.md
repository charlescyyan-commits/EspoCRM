# Phase3 Railway Staging Acceptance Plan

| Field | Value |
| --- | --- |
| Document Type | Staging acceptance criteria (documentation only) |
| Environment | Railway **staging** only |
| Production promotion | **Not authorized** |
| Scope | Frozen C1–C25 baseline acceptance |
| WP4 Freeze Tag | `phase3c25-wp4-freeze` → `9ad1ff5889abae15551df245d6e97f182445f367` |
| Repository baseline | `origin/master` at freeze-evidence tip (`c8a7b36` — WP4 freeze evidence reconciliation) and descendants only after separate authorization |
| Related operational plan | `docs/deployment/RAILWAY_C25_STAGING_PLAN.md` (how to deploy) |
| This document | **What must pass** before commercial validation |
| Status | **DRAFT — acceptance criteria defined; Railway Staging NOT STARTED** |

```text
This document defines Railway staging acceptance criteria for the frozen
C1–C25 baseline.

It is NOT a production deployment guide.
It does NOT authorize Runtime Expansion, invariant activation,
ownership transfer, or unrestricted AI runtime.

No implementation changes are authorized by this document.
```

---

## 1. Executive Summary

Railway staging is intended for:

- Frozen architecture validation
- Application runtime validation
- Metadata validation
- AI integration validation under **controlled** conditions

It is **NOT**:

- a production release
- an autonomous sales system
- unrestricted AI runtime
- authorization to mutate CRM / C22 / C24 ownership boundaries

Acceptance here proves that the frozen extension overlay and governance
boundaries behave correctly in a disposable Railway environment, with
optional controlled AI/provider and enrichment integrations for
validation only.

---

## 2. Deployment Scope

### 2.1 Application

| Component | Included |
| --- | --- |
| EspoCRM core | Yes |
| `crm-extension` overlay | Yes |

### 2.2 Included modules (frozen baseline)

| Layer | Included surface | Constraint |
| --- | --- | --- |
| **C20** | Capability / purpose references (Package A identity consume) | No Runtime Expansion; Runtime Lite remains CLOSED |
| **C21** | ResearchEvidence, QualificationInsight, human feedback | FROZEN governance; advisory / human-gated |
| **C22** | Existing Prospect Execution Foundation | FROZEN; **no autonomous activation** |
| **C24** | Commercial intelligence (RevenueInsight, PipelineMetric, OpportunityCandidate) | FROZEN; C25 consumes **read-only** |
| **C25 WP2.2** | CommercialBrief | FROZEN |
| **C25 WP3** | CommercialInsight, BusinessReviewContext | FROZEN |
| **C25 WP4** | DecisionSupportContext, HumanReviewDecisionRecord, PresentationFeedback | FROZEN (`phase3c25-wp4-freeze`) |

### 2.3 Explicitly out of scope for this acceptance cycle

- Production credentials / production database
- Unrestricted provider keys without staging guards
- Autonomous agent loops
- Scheduler / worker / queue / AIJob runtime expansion
- Outbound automation (email send / Instantly / CRM lifecycle advancement)

---

## 3. Infrastructure Acceptance

### 3.1 Railway

Verify:

| Check | Criterion |
| --- | --- |
| Service deployment | Service reaches healthy / reachable state |
| Environment variables | Staging-only vars present; production secrets absent |
| Database connection | App connects to staging MySQL/MariaDB |
| Persistent volume | `/var/www/html/data` (or documented volume) persists across restart |
| Restart behavior | Service recovers without data loss of volume contents |
| Health checks | Public health endpoint succeeds (e.g. `/`) |

### 3.2 Docker

Verify:

| Check | Criterion |
| --- | --- |
| Image build | Dockerfile build succeeds from repo root |
| Extension overlay | `crm-extension/files` overlay present at runtime |
| Entrypoint behavior | Staging guards refuse production / forbidden prod providers as designed |
| Permission handling | Web/data permissions allow EspoCRM to run |

**Infrastructure acceptance result:** PASS / FAIL _(record after execution)_

---

## 4. Database Acceptance

Verify:

- MySQL connectivity
- migration / install process
- metadata rebuild
- cache rebuild
- restart persistence

**Required evidence:**

| Evidence | Required |
| --- | --- |
| Installation success | Yes |
| Login success | Yes |
| Restart test (volume retained) | Yes |

**Database acceptance result:** PASS / FAIL _(record after execution)_

---

## 5. Application Acceptance

### 5.1 Authentication

- Admin login succeeds on staging

### 5.2 Metadata — entities load

Confirm EspoCRM loads scopes / entityDefs for:

| Entity | Layer |
| --- | --- |
| CommercialBrief | C25 WP2.2 |
| CommercialInsight | C25 WP3 |
| BusinessReviewContext | C25 WP3 |
| DecisionSupportContext | C25 WP4 |
| HumanReviewDecisionRecord | C25 WP4 |
| PresentationFeedback | C25 WP4 |

Also confirm C21 / C24 entities required by the E2E scenario remain listable where authorized (ResearchEvidence, QualificationInsight, and C24 read surfaces as applicable).

### 5.3 ACL

Verify:

- Human reviewer permissions allow review / accept / dismiss where designed
- API / system actors **cannot** perform unauthorized approval actions
- No bypass of human authority gates

### 5.4 Controllers / UI

Verify where permitted by ACL:

- list view
- detail view
- create / update only through authorized services / actions

**Application acceptance result:** PASS / FAIL _(record after execution)_

---

## 6. AI Provider Integration Acceptance

### 6.1 Clarification

External AI providers are **allowed for controlled validation** in Railway staging.

**Allowed providers / adapters (examples):**

- DeepSeek
- OpenAI
- Other CompletionProvider adapters under C20 identity/policy consumption

**Allowed purposes:**

- summarization
- analysis
- classification
- proposal generation

**Forbidden:**

- AI autonomous decision
- AI approval
- AI execution
- CRM lifecycle mutation
- accept / dismiss of HumanReviewDecisionRecord by AI/system
- Runtime Expansion beyond closed Runtime Lite / unauthorized AIJob paths

### 6.2 Acceptance checks

| Check | Pass criterion |
| --- | --- |
| Controlled completion call | Returns advisory content under staging credentials |
| Provenance | Outputs retain / link sourceEvidenceReference lineage where applicable |
| Authority | Human must still accept / dismiss / close; AI cannot |
| No lifecycle side effects | No Lead / Opportunity / ProspectRun mutation from provider call |

**AI provider acceptance result:** PASS / FAIL / PASS WITH NOTES _(record after execution)_

---

## 7. External Data Source Acceptance

**Allowed (controlled staging):**

- Apify
- Search providers
- Enrichment providers

**Purpose:** provide **test data** only:

- company research
- commercial evidence
- qualification input

**Forbidden automatic effects:**

- Lead creation
- Opportunity creation
- Outbound execution

**External data acceptance result:** PASS / FAIL / N/A _(record after execution)_

---

## 8. C20 Provider Boundary Validation

| Provider DOES | Provider DOES NOT |
| --- | --- |
| Provide completion capability under controlled staging use | Own business decisions |
| Consume capability / purpose identity by reference | Mutate CRM lifecycle |
| Remain subject to C20 Package A / Runtime Lite closure | Trigger C22 execution / outbound |

**C20 boundary result:** PASS / FAIL _(record after execution)_

---

## 9. C25 End-to-End Validation Scenario

### 9.1 Test flow

```text
External company data
        ↓
ResearchEvidence
        ↓
QualificationInsight
        ↓
CommercialBrief
        ↓
CommercialInsight
        ↓
DecisionSupportContext
        ↓
HumanReviewDecisionRecord
        ↓
Human action (accept / dismiss / annotate)
```

### 9.2 Required verifications

| Check | Pass criterion |
| --- | --- |
| Provenance preserved | sourceEvidenceReference / capabilityReference / purposeReference retained across artifacts |
| Human authority preserved | Only human completes accept / dismiss / close |
| No automatic lifecycle changes | No CRM Lead/Opportunity or C22/C24 ownership mutation |
| Decision support role | DecisionSupportContext remains advisory workspace; no DecisionIntentRecord / intent engine |

**C25 E2E result:** PASS / FAIL _(record after execution)_

---

## 10. C22 Boundary Validation

Verify C25 (and staging AI/data integrations) **cannot**:

| Forbidden action | Expected |
| --- | --- |
| Create ProspectRun | Blocked / absent |
| Execute outreach | Blocked / absent |
| Modify Action Ledger / ExecutionLedger | Blocked / absent |
| Send emails | Blocked / absent |
| Advance Lead lifecycle | Blocked / absent |

**C22 boundary result:** PASS / FAIL _(record after execution)_

---

## 11. Acceptance Evidence

### 11.1 Screenshots (minimum)

| Evidence | Required |
| --- | --- |
| Login | Yes |
| Entity list (C25 surfaces) | Yes |
| Entity detail | Yes |
| AI output (if provider exercised) | Yes |
| Provenance fields visible | Yes |
| Review workflow (human accept/dismiss or equivalent) | Yes |

### 11.2 Logs

| Evidence | Required |
| --- | --- |
| Deployment success | Yes |
| Database success | Yes |

### 11.3 Tests

Run existing pytest suites relevant to frozen baseline, at minimum:

```text
python -m pytest crm-extension/tests/test_phase3c25_wp4_decision_support.py -q
```

Also run prior frozen WP suites as available (WP2.2 / WP3 / related C21–C24 contract tests) and record results.

**Evidence package location (suggested):** `docs/audit/` or staging evidence folder named at execution time — **not created by this plan**.

---

## 12. Known Limitations

**Not included** in this Railway staging acceptance cycle:

- autonomous agent
- scheduler
- worker
- queue
- AIJob runtime (Runtime Expansion)
- outbound automation
- production credentials
- production database
- CRM ownership transfer
- C24 transition invocation from C25
- DecisionIntentRecord / persisted decision-intent store

---

## 13. Acceptance Decision

Possible outcomes after evidence collection:

| Decision | Meaning |
| --- | --- |
| **PASS** | Staging stable; frozen C25 capabilities usable; AI provider validation works under control; boundaries preserved |
| **PASS WITH NOTES** | Usable with documented non-blocking gaps |
| **BLOCKED** | Infrastructure, metadata, authority, or boundary failure; commercial validation must not proceed |

**PASS criteria (all required):**

- Railway staging stable
- C25 frozen capabilities usable
- AI provider validation works (if exercised) without authority breach
- C20 / C22 / C24 / CRM boundaries preserved

**Acceptance decision:** _NOT STARTED_ — record PASS / PASS WITH NOTES / BLOCKED only after execution.

---

## 14. Final Authorization State

| Scope | Status |
| --- | --- |
| C20 Runtime Lite | **CLOSED** |
| C20 Package A | **RELEASED** |
| C21 | **FROZEN** |
| C22 | **FROZEN** |
| C24 | **FROZEN** |
| C25 WP2.2 | **FROZEN** |
| C25 WP3 | **FROZEN** |
| C25 WP4 | **FROZEN** |
| WP4 Freeze Tag | `phase3c25-wp4-freeze` (verified) |
| Railway Staging | **NOT STARTED** |
| Runtime Expansion | **NOT AUTHORIZED** |
| Invariant Activation | **NOT DONE** |

```text
Documentation only.
Defines Railway staging acceptance criteria.
No implementation authorization.
No Runtime Expansion.
No invariant activation.
No ownership changes.
```
