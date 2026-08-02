# Phase3C20 RT-WP0 — Runtime Baseline and Contract Lock

| Field | Value |
| --- | --- |
| Document Type | Runtime baseline report (documentation and repository verification only) |
| Work package | RT-WP0 |
| Status | RT-WP0 EXITED |
| Date | 2026-08-02 |
| Frozen governance baseline | `928aa5f734f8d7f643cdb45a7549fed7ada0c400` |
| Governing charter | `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` (RATIFIED) |
| Production code | NOT MODIFIED / NOT AUTHORIZED |
| RT-WP0 exit | EXITED |

```text
Scope: planning/documentation and live-repository verification only.
No production code. No metadata. No entities. No routes. No Connector changes.
No invariant activation. No C25 WP2.2. No stage/commit/push/tag by this WP alone.
```

## Administrative Ratification Record

Runtime Baseline accepted.

At baseline ratification, RT-WP0 Exit had not yet been claimed.

| Field | Value |
| --- | --- |
| Review | RT-WP0 Independent Baseline Review |
| Verdict | PASS WITH INFORMATIONAL NOTES |
| Date | 2026-08-02 |

| Item | Result |
| --- | --- |
| Runtime Baseline | PASS |
| Repository Lock | PASS |
| Runtime Ownership | PASS |
| Dependency Matrix | PASS |
| C25 Boundary | PASS |
| INV Evidence | PASS |
| Authorization Matrix | PASS |
| BLOCKER | NONE |
| HIGH | NONE |
| MEDIUM | NONE |

## Administrative Exit Record

| Field | Value |
| --- | --- |
| Review | RT-WP0 Exit Review |
| Verdict | PASS WITH INFORMATIONAL NOTES |
| Date | 2026-08-02 |
| RT-WP0 Exit | EXITED |

RT-WP0 exited; RT-WP1 may be separately authorized.

No runtime implementation is authorized.

---

## 1. Purpose and Entry Gate

RT-WP0 locks the live runtime contracts against the ratified Runtime
Implementation Charter so later work packages have exact owners, boundaries,
and a no-change surface for frozen C20 governance.

| Entry condition | Verified |
| --- | --- |
| Phase3C20 Governance FROZEN at `928aa5f` | YES — `HEAD == 928aa5f734f8d7f643cdb45a7549fed7ada0c400` |
| Runtime Implementation Charter RATIFIED | YES — status sync completed 2026-08-02 |
| Separate RT-WP0 authorization (docs/verification) | YES — authorized to produce this baseline only |
| Production code authorized | NO |

---

## 2. Live Contract Lock (verified 2026-08-02)

### 2.1 Completion capability and purpose

| Contract | Live fact | Charter lock |
| --- | --- | --- |
| `CompletionCapability` enum | Exactly four values: `RESEARCH_EVIDENCE`, `QUALIFICATION_INSIGHT`, `DRAFT_ASSISTANCE`, `REPLY_ASSISTANCE` | Four-value portfolio unchanged |
| `COMMERCIAL_BRIEF` | Absent from enum and from connector/crm-extension source | Inactive; not delivered; not implemented |
| Adapter `_SYSTEM_PROMPTS` | Keyed to exactly the same four capabilities | Non-routability gate for any future value |
| `commercial_brief_generation` | No binding registration or source occurrence under connector/crm-extension | Purpose not delivered |
| `Capability` family enum | Exactly `SEARCH`, `ENRICHMENT`, `COMPLETION` | Unchanged |

### 2.2 Capability Registry and taxonomy

| Contract | Live fact |
| --- | --- |
| Registry location | `chitu-connector/.../providers/registry.py` (and related capability modules) |
| Failure taxonomy | `taxonomy.py` — retryable set exactly `{NETWORK, PROVIDER, RATE_LIMIT}` |
| Purpose rejection | Registry fails closed (`PURPOSE_NOT_ALLOWED` / `CAPABILITY_UNAVAILABLE` patterns per WP2 tests) |
| Secret rejection | Secret-bearing resolution inputs rejected |

### 2.3 CRM AIPlatform surface

| Contract | Live fact |
| --- | --- |
| Module layout | `Entities/`, `Hooks/`, `Resources/`, `Services/`, `Binding.php` only |
| Runtime dirs | **Absent:** `Controllers/`, `Api/`, `Actions/`, `Jobs/` |
| Services present | `AIJobService`, `AIRequestLogService`, `PromptTemplateService` + save-option helpers |
| Guards present | `AIJobStatusMutationGuard`, `AIRequestLogAppendOnlyGuard`, `PromptTemplateMutationGuard` |
| `AIJob` cancel-reason fields | **Absent** (`cancelReason` / `cancelReasonCode` not in entityDefs) |
| `AIJob` retry fields | `attemptCount`, `nextRetryAt`, `failureCategory` present; **no** retry executor/classifier |
| Dispatch orchestration | **Absent** — no `AIDispatchService` |
| ProviderBinding CRM entity | **Absent** — no entityDefs/service/guard |
| Completion dispatch executor | **Absent** — no `completion/dispatch.py` |

### 2.4 Connector invocation map (corrected path)

| Layer | Verified path / behavior |
| --- | --- |
| PHP port | `crm-extension/files/custom/Espo/Modules/Prospecting/ProviderBoundary/ConnectorBoundary.php` — `execute(ProviderExecutionRequest): ProviderResultEnvelope` |
| Port ownership note | Port lives under **Prospecting** `ProviderBoundary`, not under `Modules/AIPlatform/` (charter §4.3 narrative path was imprecise; this report locks the live path) |
| Connector runtime | `chitu-connector` implements outbound execution; workers use claim semantics (`acquisition/worker.py`) |
| CRM egress | PHP performs no outbound provider HTTP (C20-INV-03 surface; WP0 boundary guards) |
| Ownership rule (charter) | CRM owns governed dispatch orchestration (future RT-WP3); Connector owns outbound provider dispatch, adapter invocation, transport, provider HTTP |

### 2.5 SendExecution versus AIJob retry

| Runtime | Live ownership | RT-WP lock |
| --- | --- | --- |
| SendExecution retry / idempotency | Connector-side (`espocrm_sync` / claim patterns; `send_idempotency.py` present) | Unchanged; outside RT-WP5 |
| AIJob / Completion retry | Schema fields only; no CRM retry policy service | RT-WP5 scope when separately authorized |

---

## 3. Invariant Evidence Matrix (authoritative registry)

Source: `docs/adr/C20_INVARIANT_REGISTRY.md` at HEAD `928aa5f`.

| Invariant | Registry status | Runtime evidence class | Later owner |
| --- | --- | --- | --- |
| C20-INV-05 | DEFERRED | READY surfaces present (service + guard); activation evidence pending | RT-WP7 |
| C20-INV-06 | DEFERRED | REQUIRES CHANGE — cancel-reason contract missing | RT-WP4 → RT-WP7 |
| C20-INV-07 | DEFERRED | READY surfaces present (append-only guard); activation evidence pending | RT-WP7 |
| C20-INV-08 | DEFERRED | REQUIRES CHANGE — dispatch-to-log producer missing | RT-WP3 → RT-WP7 |
| C20-INV-09 | DEFERRED | READY surfaces present (PromptTemplate immutability); activation evidence pending | RT-WP7 |
| C20-INV-10 | DEFERRED | REQUIRES CHANGE — AIJob retry executor missing | RT-WP5 → RT-WP7 |
| C20-INV-11 | DEFERRED | REQUIRES CHANGE — pre-dispatch reservation missing | RT-WP6 → RT-WP7 |

```text
C20-INV-05 through C20-INV-11 remain DEFERRED.
Invariant activation is NOT AUTHORIZED by RT-WP0.
```

---

## 4. Dependency Graph (locked)

```text
RT-WP0  (this baseline — exit pending independent review)
 ├─ RT-WP1  (capability/purpose — NOT AUTHORIZED)
 └─ RT-WP2  (ProviderBinding surface — NOT AUTHORIZED; Foundation Review first)

RT-WP1 + RT-WP2
        ↓
      RT-WP3  (dispatch orchestration + exactly-once log — NOT AUTHORIZED)

RT-WP3
 ├─ RT-WP4  (cancel-reason — NOT AUTHORIZED)
 ├─ RT-WP5  (AIJob retry — NOT AUTHORIZED)
 └─ RT-WP6  (reservation — NOT AUTHORIZED; Foundation Review first)

RT-WP3 + RT-WP4 + RT-WP5 + RT-WP6
        ↓
      RT-WP7  (invariant activation — NOT AUTHORIZED)
        ↓
      RT-WP8  (runtime freeze — NOT AUTHORIZED)
```

Shared-file primary owners (locked from charter §18.1):

| Shared file | Primary | Secondary |
| --- | --- | --- |
| `Services/AIJobService.php` | RT-WP4 | RT-WP5 (after RT-WP4 freeze) |
| `Resources/metadata/entityDefs/AIJob.json` | RT-WP4 | RT-WP6 (after RT-WP4 freeze; form per RT-WP6 Foundation Review) |
| `Services/AIDispatchService.php` | RT-WP3 | RT-WP6 (after RT-WP3 freeze) |

---

## 5. Transaction Map (locked planning reference)

| Transaction | Owner | Boundary rule |
| --- | --- | --- |
| AIJob create | `AIJobService` | One save with save option; idempotency precheck outside txn |
| AIJob transition | `AIJobService` | `TransactionManager::run`; status + timestamps atomic |
| AIRequestLog create | `AIRequestLogService` | Log write + PromptTemplate mark-referenced in txn |
| Dispatch attempt | CRM orchestrator + connector claim | Reservation first; claim atomic; one log + one transition write-back |
| Retry | CRM retry executor (future) | Eligibility → RUNNING → attempt identity → log |
| Reservation | CRM orchestrator (future) | Created before outbound dispatch; released/completed after outcome |

```text
No CRM transaction may contain an outbound provider call.
```

---

## 6. Exact Candidate Allowlist (locked reference)

Authoritative planned allowlist remains charter §28 / §28.1:

| Metric | Count |
| --- | --- |
| Allowlist rows | 40 |
| Unique path strings (as written) | 37 |
| Unique files if braces expand | 39 |
| Shared coordinated paths | 3 |

RT-WP0 **does not** implement any allowlist row. RT-WP0 adds only this baseline
document (and administrative charter pointers if separately synced).

No-change / forbidden for all runtime WPs unless a new ADR or separately
authorized governance action says otherwise:

* Frozen C20 governance ADRs and WP1–WP3 governance completion package
* Live four-value `CompletionCapability` portfolio (additive change only under RT-WP1 authorization)
* SendExecution retry semantics
* Connector credential custody model
* C20-INV-03 no CRM provider HTTP
* C25 documents and C25 WP2.2 generation path

---

## 7. Runtime Test Harness Inventory

| Item | Verified |
| --- | --- |
| Canonical runner | `pytest.ini` — `testpaths = crm-extension/tests` + `tests`; `pythonpath` includes `chitu-connector` |
| Existing C20 CRM tests | `test_phase3c20_wp0_*`, `wp1_*`, `wp3_*` under `crm-extension/tests/` |
| Existing C20 connector tests | `test_phase3c20_wp2_*` under `chitu-connector/tests/` |
| Planned RT tests (not created) | `test_phase3c20_rt_wp1_*` … `rt_wp6_*` per charter allowlist |

RT-WP0 establishes that the harness exists and is the required home for later
RT contract tests. RT-WP0 does not add new test files.

---

## 8. Reusable Paths and Gaps

### Reusable now

* AIJob / AIRequestLog / PromptTemplate entity + service + guard stack
* CapabilityRegistry + completion adapter four-capability routing gate
* Provider error taxonomy and SendExecution failure classification
* Prospecting `ConnectorBoundary` port shape
* Connector worker claim pattern (pattern reference for RT-WP3/6)

### Missing (runtime incomplete by design)

* CRM ProviderBinding policy surface
* CRM dispatch orchestration + connector completion dispatch executor
* Cancel-reason contract
* AIJob retry policy/executor
* Pre-dispatch idempotency reservation
* AIPlatform Controllers/Api/Jobs surfaces

---

## 9. Frozen Runtime State Affirmations

```text
COMMERCIAL_BRIEF is not active, not delivered, and not implemented.
```

```text
commercial_brief_generation is not delivered.
```

```text
C20-INV-05 through C20-INV-11 remain DEFERRED.
```

```text
C25 WP2.2 remains NO GO.
```

```text
Any runtime code remains NOT AUTHORIZED.
```

```text
RT-WP1 through RT-WP8 remain NOT AUTHORIZED.
```

---

## 10. Informational Notes (non-blocking)

| ID | Note |
| --- | --- |
| N-01 | Charter §4.3 referenced ConnectorBoundary under AIPlatform; live port is under Prospecting. Later WPs must use the live path. |
| N-02 | Remaining Foundation Reviews (RT-WP2, RT-WP6) and AIJob ACL gate remain pre-implementation gates, not RT-WP0 exit blockers. |
| N-03 | This report does not claim RT-WP0 exit. Exit requires independent baseline review PASS. |

---

## 11. Authorization Boundary (RT-WP0)

| Item | Status |
| --- | --- |
| Runtime Charter | RATIFIED |
| RT-WP0 | EXITED |
| RT-WP1 | MAY BE SEPARATELY AUTHORIZED |
| RT-WP2–RT-WP8 | NOT AUTHORIZED |
| Runtime Code | NOT AUTHORIZED |
| C25 WP2.2 | NO GO |

RT-WP0 exited following successful independent exit review.

No runtime implementation is authorized.

---

## 12. Exact Next Task

```text
No RT-WP1 work package is authorized by this status synchronization.
```

RT-WP1 may proceed only after a separate explicit authorization.

---

## 13. References

1. `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md`
2. `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
3. `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md`
4. `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md`
5. `docs/adr/C20_INVARIANT_REGISTRY.md`
6. Live HEAD: `928aa5f734f8d7f643cdb45a7549fed7ada0c400`

---

*RT-WP0 documentation baseline only. No production file was created or modified
outside this report and any administrative charter pointer sync. Runtime
implementation begins only under separate explicit authorization for each later
work package.*
