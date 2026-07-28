# Phase3C20 Charter — AI Platform Governance and Orchestration Foundation

**Status:** Active

**Date:** 2026-07-28

**Baseline:** `phase3c19-freeze` @ `4a7a111`, release line `1.9.12-alpha`

**Governing ADR:** `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` (Proposed, marker
`adr-c20-aiplatform-v1`)

**Invariant registry:** `docs/adr/C20_INVARIANT_REGISTRY.md`

**Constraints of record:** `AGENTS.md` / `CLAUDE.md`, `docs/architecture/BOUNDARIES.md`

---

## 1. Mission

Establish an AI Platform **governance and orchestration** layer inside EspoCRM.

C20 does **not** create an AI engine, a scoring engine, or an autonomous agent. Ownership
follows ADR-C20 §2 D2:

| Concern | Owner |
| --- | --- |
| `canonical_score`, ICP matching, qualification logic and verdicts, research logic, intelligence generation | **Chitu** |
| Workflow, permissions, orchestration, persistence, audit, operator control | **EspoCRM** |
| Provider routing, credential references, `AIJob` orchestration, `AIRequestLog`, `PromptTemplate` versioning, governance | **AIPlatform module** |
| All outbound provider I/O | **`chitu_connector` (sole egress)** |

---

## 2. Audit Findings That Motivate C20

| # | Finding | Response |
| --- | --- | --- |
| F1 | No credential custody in CRM — provider keys exist only in connector environment, with no admin surface, rotation, or access audit | WP1 |
| F2 | AI invocations leave no CRM-visible trace; failures are invisible to operators | WP3 |
| F3 | Token and currency spend is unattributable to a prospect, user, or capability | WP3 |
| F4 | Prompt changes make historical output unexplainable | WP3 |
| F5 | Provider choice is code, not configuration | WP2 |
| F6 | No health signal on which to base fallback routing | WP1 |
| F7 | `BridgeErrorClass` lacked `RATE_LIMIT` parity with `SendExecution.failureCategory` and the connector provider contract, causing hard ingress rejection of rate-limited results | **WP0.4 — closed** |
| F8 | No canonical test invocation; suite red across two freezes | **WP0.1 — closed** |

---

## 3. Governance Baseline (WP0 deliverables — this package)

| Sub-WP | Deliverable | State |
| --- | --- | --- |
| WP0.1 | Test foundation — `pytest.ini` (canonical invocation), stale C14 assertion repair | Complete |
| WP0.2 | `docs/adr/C20_INVARIANT_REGISTRY.md` — machine-checkable index of all 22 ADR §8 invariants, with meta-tests | Complete |
| WP0.3 | Boundary guards — `test_phase3c20_wp0_boundary_guards.py` | Complete |
| WP0.4 | `BridgeErrorClass` parity — `RATE_LIMIT` alignment plus `QUOTA` and `CONTENT_FILTER` | Complete |
| WP0.5 | Registry alignment — `C20-INV-03` and `C20-INV-18` reclassified `DEFERRED → ACTIVE` | This package |
| WP0.6 | This charter and the ADR WP0 execution record | This package |

**Outstanding WP0 items** are listed in §8.

---

## 4. Work Package Map

| WP | Objective | Key exclusions |
| --- | --- | --- |
| **WP0** | Governance hardening before any AIPlatform code | No AIPlatform runtime, no provider calls, no `AIQualificationInsight` entity |
| **WP1** | `Modules/AIPlatform` skeleton; `ProviderCredential` custody; Administration → AI Platform surface | No provider invocation; no completion adapter |
| **WP2** | Capability ports; `EnrichmentProvider` adapter; recorded-fixture tests | **Gated on ADR §11.1 human ratification** |
| **WP3** | `AIJob`, `AIRequestLog`, `PromptTemplate`, `AIQualificationInsight`; guards, cost accounting, health checks | No autonomous triggering |
| **WP4** | Test-infrastructure completion; `BUILD_INFO` provenance stamp | — |
| **WP5** | Vertical slice — operator-triggered AI-assisted research on one `ProspectPool` record, writing `ResearchEvidence` | No email path, no scoring |

Successor phases: **C21** AI Prospecting Automation (human approval mandatory);
**C22** Autonomous Outreach Agent + production freeze.

---

## 5. Exit Gates

### WP0 exit gate

1. Canonical invocation (`pytest -q`) green across `crm-extension/tests` and `tests`.
2. Registry complete: 22 rows, declared counts equal actual row tallies, every `ACTIVE`
   row references an existing test file.
3. No `DEFERRED` invariant has undisclosed full enforcement.
4. Every WP0 change to a Prospecting surface is recorded in §7 with a stated rationale.
5. Release-line integrity: `build_release_package.py --check` green, sidecar matches,
   ZIP payload byte-identical to `crm-extension/files/`, and **no version string maps to
   more than one artifact**.
6. Charter and ADR accurately describe what WP0 executed.

### Per-WP exit gates (WP1–WP5)

Each WP exits when its owning ADR §8 invariants are `ACTIVE` in the registry with real
contract tests, the canonical suite is green, and the charter decision log records any
change to a frozen surface.

### Standing gates

`build_release_package.py --check` · `tests/regression/test_phase3s01_release_integrity.py`
· extension skeleton inventory · navigation contract tests · UI Runtime Artifact Parity
Gate for any admin UI.

---

## 6. Boundaries (carried from C17/C18/C19, still frozen)

C20 must **NOT**:

- Modify Chitu scoring logic, AI research logic, or the email-generation engine
  (`AGENTS.md`)
- Open outbound provider connections from PHP — the connector is sole egress (ADR §2 D3)
- Compute a score, or create any second scoring or qualification authority
- Modify C19-frozen lifecycle **services, guards, or action keys** (ADR §10)
- Modify navigation desired-state or the materializer
- Ship any email-sending path
- Import real customer data

---

## 7. Frozen Surface Decision — WP0.4 Error Taxonomy Expansion

### 7.1 Decision

**WP0.4 modified three Prospecting files and the connector failure taxonomy. This charter
records that decision, its rationale, and its bounds.**

| Surface | Change | Classification |
| --- | --- | --- |
| `Services/BridgeErrorClass.php` | Added `RATE_LIMIT`, `QUOTA`, `CONTENT_FILTER` constants; extended `values()`; added `isAutoRetryEligible()` | Value object |
| `Services/SendExecutionBridgeAdapterService.php` | Three added translation-map entries | Ingress adapter |
| `Services/SendExecutionResultAdapterService.php` | Three added translation-map entries | Ingress adapter |
| `Resources/metadata/entityDefs/SendExecution.json` | `failureCategory` enum widened with `QUOTA`, `CONTENT_FILTER` | Persistence enum |
| `Resources/i18n/{en_US,zh_CN}/SendExecution.json` | Labels for the two new categories | Presentation |
| `chitu_connector/espocrm_sync/failure_classification.py` | Added `QUOTA`, `CONTENT_FILTER` | Classification enum |
| `chitu_connector/espocrm_sync/send_execution_bridge.py` | Widened `BridgeErrorClass`; added `is_auto_retry_eligible()` | Transport / taxonomy |

### 7.2 Why this is not a lifecycle-ownership change

ADR §10 excludes *"Any change to the C19-frozen lifecycle **services, guards, or action
keys**."* WP0.4 touched none of the three. Verified against commit `962a7ae`:

| C19-frozen lifecycle surface | Changes in WP0 |
| --- | --- |
| `Services/SendExecutionTransitionService.php` — the transition owner | **0** |
| `Hooks/SendExecution/SendExecutionStatusMutationGuard.php` — the persistence guard | **0** |
| `Resources/metadata/app/prospectingWorkflow.json` — action keys | **0** |

The changed files occupy a different layer:

- **`BridgeErrorClass` is a value object**, not a service. A `final class` of constants
  plus `values()` and a pure predicate. It owns no state, performs no persistence, and
  participates in no transition.
- **The two adapters are ingress translators.** Both changes are additional entries in a
  `errorClass → failureCategory` constant map. No control flow, no branch, no
  persistence call was added or altered.
- **The `entityDefs` change widens an accepted-value set.** No field was added, removed,
  renamed, or retyped; no existing value's behaviour changed; no transition matrix,
  status field, or ACL rule was touched.

**Additive taxonomy expansion is orthogonal to lifecycle ownership.** The lifecycle
answers *may this record move from state A to state B, and who may authorize it.* The
taxonomy answers *how do we classify the failure that already occurred.* WP0.4 changed
only the second. Every status write on `SendExecution` still passes through
`SendExecutionTransitionService` under `SendExecutionStatusMutationGuard`, authorized by
the unchanged action keys — exactly as at `phase3c19-freeze`.

### 7.3 Retry ownership is unchanged

`BridgeErrorClass::isAutoRetryEligible()` and the connector's `is_auto_retry_eligible()`
are **classification predicates only**. Neither schedules, counts, nor triggers a retry.
Enforced by contract test: the PHP helper must not reference
`SendExecutionTransitionService` and must not introduce `nextRetryAt`.

Retry scheduling remains connector-side, where `RATE_LIMIT` already sat in the retryable
bucket alongside `NETWORK`. Eligible: `NETWORK`, `PROVIDER`, `RATE_LIMIT`. Not eligible:
`AUTH`, `VALIDATION`, `UNKNOWN`, `QUOTA`, `CONTENT_FILTER` — consistent with ADR §4.3.

### 7.4 Why the change was necessary

Before WP0.4, a connector result carrying `errorClass = 'RATE_LIMIT'` — a value the
connector could produce and `SendExecution.failureCategory` could store — was **rejected
at the CRM boundary** by `SendExecutionBridgeResult` and again by
`SendExecutionResultAdapterService::failureCategory()`. The `SendExecution` received no
terminal result and remained in its prior state, invisible to the `c18FailedSend` queue.
This was a live taxonomy break, not a cosmetic gap.

### 7.5 Bounds of this decision

This decision authorizes **additive value-object and enum widening only**. It does not
authorize changes to transition services, mutation guards, action keys, transition
matrices, ACL, or any narrowing of an accepted-value set. Narrowing would be a breaking
change and requires a separate ADR.

### 7.6 Observable consequence

Rate-limit, quota, and content-filter failures that were previously rejected now persist
as `FAILED` with the corresponding `failureCategory`. Operators will see failures that
were previously invisible, and `c18FailedSend` counts will rise. This is previously-hidden
failure becoming visible, not a regression — and it must be stated in the release notes
for the line that ships it.

---

## 8. Outstanding WP0 Items

| # | Item | Blocking? |
| --- | --- | --- |
| O1 | **Release line: `1.9.12-alpha` currently maps to two artifacts** — `E11715D2…` at `phase3c19-freeze`, `1F981503…` at `962a7ae`. WP0.4 changed shipped payload without a version bump. Requires `1.9.13-alpha`. | **Yes** |
| O2 | `BOUNDARIES.md` §2/§3 stale — DeepSeek runtime described as out of scope; Apify listed "Not Implemented" though `providers/apify_provider.py` exists | No |
| O3 | `C20-INV-10` partially enforced by `test_retry_classification_preservation` but credited at zero; registry has no `PARTIAL` status | No |
| O4 | `C20-INV-17` guard fails **by design** when WP3 creates `AIQualificationInsight` — must be replaced with real INV-17 enforcement, never weakened | No |
| O5 | `C20-INV-18` guard hardcodes four transition owners; scope must widen as services are added | No |
| O6 | C19 debt: charter WP1.5 row; Intelligence Center Research Workbench retro-charter | No |
| O7 | `v1.9.12-alpha` tag never applied at `4a7a111` | No |
| O8 | ADR §11.1 ratification — gates WP2 only | No (blocks WP2) |

---

## 9. Decision Log

| Date | Decision | Reference |
| --- | --- | --- |
| 2026-07-28 | Phase3C20 chartered; WP0 governance-first sequencing adopted | §3, §4 |
| 2026-07-28 | **WP0.4 error taxonomy expansion is additive and does not constitute a C19-frozen lifecycle change** under ADR §10. Transition service, mutation guard, and action keys verified unchanged at `962a7ae`. | §7 |
| 2026-07-28 | Retry ownership remains connector-side; CRM helpers are classification predicates only, contract-enforced | §7.3 |
| 2026-07-28 | `C20-INV-03` and `C20-INV-18` reclassified `DEFERRED → ACTIVE`; both were already enforced by WP0.3 guards. Counts 7/15 → 9/13. | WP0.5 |
| 2026-07-28 | `C20-INV-17` remains `DEFERRED` — its only coverage is an entity-absence scope guard, not invariant enforcement | §8 O4 |
| 2026-07-28 | Version bump to `1.9.13-alpha` required before WP0 exit; deferred to a separate commit | §8 O1 |
| 2026-07-28 | `Modules/Automation` not created in C20 | ADR §2 D1 |

---

*WP0.5/WP0.6 package: documentation and test-count governance only. No runtime PHP,
metadata, connector, navigation, or artifact changes are made by this charter.*
