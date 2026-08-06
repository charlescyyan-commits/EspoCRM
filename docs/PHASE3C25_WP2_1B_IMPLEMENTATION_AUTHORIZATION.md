# Phase3C25 WP2.1B Implementation Authorization

| Field | Value |
| --- | --- |
| Document Type | **Governance Authorization Record** (Implementation Authorization Issuance) |
| Work Package | WP2.1B — CommercialBrief persistence layer |
| Status | **AUTHORIZED WITH CONDITIONS** |
| Date | 2026-08-06 |
| Parent | Phase3C25 WP2 — AI Commercial Brief |
| Governing charter | `docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md` (RATIFIED) |
| Governing plan | `docs/PHASE3C25_WP2_IMPLEMENTATION_PLAN.md` (RATIFIED — implementation-planning reference only) |
| Review basis | `PHASE3C25 WP2.1B Implementation Authorization Review` (2026-08-06) — **PASS WITH CONDITIONS** |
| Implementation Authorization | **YES** — limited to the allowed implementation scope in §4, subject to the conditions in §3 |
| Prohibitions honored | This record creates governance documents only: **no code, no PHP, no Runtime, no Railway, no database, no deployment, no feature, and no governance-boundary change** |

```text
WP2.1B implementation — AUTHORIZED WITH CONDITIONS (2026-08-06)

The authorization is derived from the completed WP2.1B Implementation
Authorization Review (Verdict: PASS WITH CONDITIONS). No review finding was
BLOCKER or HIGH. Conditions C1–C4 are binding and must be satisfied before
and during WP2.1B implementation.
```

---

## 1. Authorization Status

**WP2.1B Implementation: AUTHORIZED WITH CONDITIONS.**

This record formally issues the WP2.1B implementation authorization that the
ratified Plan reserved for a separate, scoped authorization (Plan §23.2;
WP2.1A decision §3 "WP2.1B (separately authorized)"; ADR-C25-007 §13
"WP2.1B — `CommercialBrief` entity/persistence (separately authorized)").
It authorizes the **CommercialBrief persistence layer only** — entity
contract, metadata, ACL, provenance schema, guards, save option, and static
contract tests — as specified in §4. Everything outside §4 remains **NOT
AUTHORIZED**.

The authorization does **not** reopen, re-authorize, or reverse the
historical WP2.2 chain (see §6).

---

## 2. Review Reference

| Item | Value |
| --- | --- |
| Review | PHASE3C25 WP2.1B Implementation Authorization Review |
| Date | 2026-08-06 |
| Verdict | **PASS WITH CONDITIONS** |
| BLOCKER findings | None |
| HIGH findings | None |
| MEDIUM findings | M1 (historical WP2.2 code overlap → C1); M2 (state-record sync at issuance → C4) |
| LOW findings | L1 (Plan §8.1 `capability`/`purpose` ratification → C2); L2 (naming deviation → C1); L3 (test location) |
| INFORMATIONAL findings | I1 (WP2.2 tag/code disposition is a separate action); I2 (audit writer default = WP2.3) |

The review confirmed the WP2.1B authorization boundary: foundation gate
satisfied (**Capability identity `COMMERCIAL_BRIEF` + Purpose policy
`commercial_brief_generation` + Boundary evidence**, established by the C20
Dependency Closure Addendum 2026-08-03 and ratified at `b632f1d`
2026-08-06); WP2.1A ADR (ADR-C25-007) **RATIFIED** 2026-08-02;
C20-INV-05…11 remain **DEFERRED** (owning WP3) with no runtime maturity
dependency introduced by WP2.1B; and no leakage of provider execution,
autonomous execution, deployment, runtime activation, or credential
authority.

---

## 3. Conditions (Binding)

### C1 — Historical WP2.2 code is not the WP2.1B baseline

The historical WP2.2 implementation commit `d6ee017` must **not** be treated
as the WP2.1B implementation baseline. Specifically:

- Files at paths that coincide with the WP2.1B allowlist (§4) —
  `Entities/CommercialBrief.php`, `Services/CommercialBriefSaveOption.php`,
  `Resources/metadata/entityDefs/CommercialBrief.json`,
  `Resources/metadata/scopes/CommercialBrief.json`,
  `Resources/metadata/aclDefs/CommercialBrief.json` — are **unowned
  artifacts**. WP2.1B must re-deliver or verify each against the ratified
  contract (Plan §8 field model, §23.2 scope, §28.1 allowlist) before or as
  part of implementation, or obtain an explicit allowlist/disposition
  amendment first.
- Historical files **outside** the WP2.1B allowlist —
  `Controllers/CommercialBrief.php`,
  `Resources/metadata/clientDefs/CommercialBrief.json`,
  `Services/CommercialBriefProposalService.php`,
  `Services/CommercialBriefReviewService.php`,
  `Services/BriefProvenanceValidator.php`,
  `Hooks/CommercialBrief/CommercialBriefImmutabilityGuard.php`,
  `Hooks/CommercialBrief/CommercialBriefReviewStatusGuard.php` — must **not**
  be modified, adopted, or relied upon by WP2.1B. Their disposition is a
  separate governance action (review INFORMATIONAL I1).
- WP2.1B guards/services are created under the Plan §28.1 names:
  `CommercialBriefImmutableGuard`, `CommercialBriefStateGuard`,
  `CommercialBriefAuthorizationService` — not the historical names
  (review LOW L2).

### C2 — WP2.1B provenance contract = Charter §9.1 + Plan §8.1 additions

The WP2.1B provenance contract is explicitly ratified as: Charter §9.1
mandatory provenance fields (**7**: `sourceAIJobId`, `sourceAIRequestLogId`,
`provider`, `model`, `generationVersion`, `promptTemplateId`,
`promptTemplateVersion`) **plus** Plan §8.1 plan-level additions
(`capability`, `purpose`), for a total of **9** provenance fields, all
immutable. The Plan §8.1 additions (marked "Plan-level additions (marked;
not in charter §9.1)") are hereby ratified by this authorization.

### C3 — Only the Plan §28.1 WP2.1B allowlist may be delivered

WP2.1B may create or modify **only** the Plan §28.1 WP2.1B allowlist rows
(13 files, see §4). The following are **forbidden** for WP2.1B:

- Controller (`Controllers/CommercialBrief.php` and any per-action API class);
- `clientDefs` (incl. `clientDefs/CommercialBrief.json`);
- migrations / SQL / `AfterInstall` raw DDL (schema via Espo metadata rebuild only);
- runtime activation / runtime tests / runtime verification;
- provider call / generation / AIJob invocation;
- audit writer (audit implementation defaults to **WP2.3** per ADR-C25-007).

### C4 — Authorization-state synchronization completed

The authorization-state records that previously asserted "WP2.1B **NOT
AUTHORIZED**" are administratively updated to reflect
**WP2.1B = AUTHORIZED WITH CONDITIONS (2026-08-06)**. See §8 for the
synchronization record. The WP2.2 / WP2.3 / Any Code "NOT AUTHORIZED" states
are unchanged.

---

## 4. Scope — Allowed Implementation Scope

**CommercialBrief persistence layer.** Allowed deliverables:

| # | Deliverable | Allowlist rows (Plan §28.1) | Notes |
| --- | --- | --- | --- |
| 1 | Entity contract | `Entities/CommercialBrief.php` | CommercialBrief entity contract per Plan §8 |
| 2 | Metadata | `Resources/metadata/entityDefs/CommercialBrief.json`, `scopes/CommercialBrief.json`, `aclDefs/CommercialBrief.json`, `app/acl.json` (append), `app/aclPortal.json` (append), `app/commercialBriefWorkflow.json` | entityDefs/scopes/ACL/portal/workflow; schema via Espo metadata rebuild — **no migration files** |
| 3 | i18n | `Resources/i18n/en_US/CommercialBrief.json`, `Resources/i18n/zh_CN/CommercialBrief.json` | key parity en_US / zh_CN |
| 4 | Provenance schema | embedded in entity contract | Charter §9.1 (7 fields) + Plan §8.1 (`capability`, `purpose`) = **9 immutable provenance fields** (condition C2) |
| 5 | Guards | `Hooks/CommercialBrief/CommercialBriefImmutableGuard.php`, `Hooks/CommercialBrief/CommercialBriefStateGuard.php` | immutability guard + state guard under Plan §28.1 names (condition C1) |
| 6 | Save option | `Services/CommercialBriefSaveOption.php` | includes the `AUDIT_WRITE_AUTHORIZED` constant (ADR-C25-007 §3); **no audit writer** |
| 7 | Authorization service | `Services/CommercialBriefAuthorizationService.php` | per Plan §28.1 |
| 8 | Anchor link | embedded in entity contract | read-only `OpportunityCandidate` anchor reference (C24-INV-SEP-002, LIFE-001) |
| 9 | Static contract tests | `tests/test_phase3c25_wp2_1b_*.py` (repo root) | static contract tests only; **no runtime tests** |

Data ownership: C25 owns `CommercialBrief`; entity budget = **1** business
artifact (`CommercialBrief`); the audit ledger (`CommercialBriefAuditEvent`)
is **not** part of WP2.1B. No CRM Core FK and no write path to CRM Core
(ADR-C25-005 §3.6). §8.2 forbidden-fields denylist applies: no score/rank
authority, no forecast, no lifecycle authority, no execution authority, no
autonomous decision, no CRM Core FK, no credentials, no provider internals,
no legal-hold field. Human review boundary is preserved: review transitions
are **WP2.3**; WP2.1B has no transitions and no autonomous path.

---

## 5. Exclusions — Excluded Scope

**No** (remains **NOT AUTHORIZED** for WP2.1B):

- **AI generation** — generation logic, generation workflow, AIJob
  invocation, generation runtime;
- **Provider execution** — provider calls, ProviderRoute/ProviderBinding
  interaction, model execution;
- **Autonomous action** — review transitions, accept/dismiss/invalidate/
  archive, autonomous decisions;
- **Runtime activation** — runtime tests, runtime verification, invariant
  activation (C20-INV-05…11 remain DEFERRED, owning WP3);
- **Deployment** — Railway / deployment / production activation;
- **Audit writer** — `CommercialBriefAuditWriter`,
  `CommercialBriefAuditEvent` entity, append-only guard, audit tests
  (default **WP2.3** per ADR-C25-007 §3, §13);
- **Controller / clientDefs / layouts / routes** — incl.
  `Controllers/CommercialBrief.php`,
  `clientDefs/CommercialBrief.json`, layouts, dedicated routes;
- **migrations / SQL / AfterInstall DDL**;
- **B5/search metadata**, **merged service wrappers**, **per-action
  save-option classes**;
- **Historical WP2.2 non-allowlist files** (see C1).

The exclusions in this section are unchanged from the ratified Plan (§23.2
out-of-scope, §28.1 exclusions) and the WP2.1B Implementation Authorization
Review.

---

## 6. Current Authorization State

| Scope | Status (after this authorization) |
| --- | --- |
| WP2 foundation gate (Capability identity + Purpose policy + Boundary evidence) | **SATISFIED** |
| WP2.1A audit-storage decision (ADR-C25-007) | **RATIFIED** (documentation only) |
| **WP2.1B implementation** | **AUTHORIZED WITH CONDITIONS** (2026-08-06) |
| WP2.2 generation | **NOT AUTHORIZED** (historical chain retained as HISTORICAL / SUPERSEDED) |
| WP2.3 audit implementation | **NOT AUTHORIZED** (separately authorized after ADR ratified) |
| Any code | **NOT AUTHORIZED** outside the WP2.1B §4 scope |
| C20-INV-05…11 | **DEFERRED** (owning WP3; not activated) |
| Runtime expansion / deployment / Railway | **NOT AUTHORIZED** |
| Historical WP2.2 chain (charter / plan / authorization / release / freeze) | **HISTORICAL — SUPERSEDED** |
| WP2.2 code `d6ee017` + tag `phase3c25-wp2-2-freeze` | Present in tree; **NOT AUTHORIZED**; disposition pending a separate governance action |

---

## 7. Next Authorized Action

1. **WP2.1B implementation** under Plan §23.2 scope and §28.1 allowlist,
   honoring conditions C1–C3. Allowed deliverables are the 13 WP2.1B
   allowlist rows listed in §4.
2. **Static contract tests only** — `tests/test_phase3c25_wp2_1b_*.py` at
   repo root. No runtime verification in WP2.1B.
3. **Schema via Espo metadata rebuild** — no migration files.
4. After WP2.1B implementation, a **WP2.1B verification / implementation
   verification review** precedes any further work package authorization.
5. **WP2.3 audit implementation** and **WP2.2 generation** remain **NOT
   AUTHORIZED** and require their own separate authorizations when their
   predecessor gates are satisfied.

No WP2.1B action in §7 authorizes any generation, provider execution,
autonomous action, runtime activation, or deployment.

---

## 8. Administrative State Synchronization Record (C4)

The following state records are administratively updated (additive
amendment notes) to reflect **WP2.1B = AUTHORIZED WITH CONDITIONS
(2026-08-06)**; no history is rewritten and no other authorization state
changes:

| # | File | Amendment |
| --- | --- | --- |
| 1 | `docs/PHASE3C25_WP2_1B_IMPLEMENTATION_AUTHORIZATION.md` (this record) | Created — WP2.1B **AUTHORIZED WITH CONDITIONS** |
| 2 | `docs/PHASE3C25_WP2_AUTHORIZATION_STATE_SYNCHRONIZATION.md` | Amendment added; §9 final-state table updated to WP2.1B **AUTHORIZED WITH CONDITIONS** |
| 3 | `docs/audit/PHASE3C25_STATE_RECONCILIATION.md` | Amendment added; §4 authorization boundary updated to WP2.1B **AUTHORIZED WITH CONDITIONS** |
| 4 | `docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md` | Amendment note added after the 2026-08-06 synchronization note |
| 5 | `docs/PHASE3C25_WP2_IMPLEMENTATION_PLAN.md` | Amendment note added after the 2026-08-06 synchronization note |
| 6 | `docs/PHASE3C25_WP2_1A_AUDIT_STORAGE_DECISION.md` | Amendment note added after the 2026-08-06 synchronization note |
| 7 | `docs/PHASE3C25_WP2_0_C20_DEPENDENCY_RESOLUTION.md` | Amendment note added after the 2026-08-06 amendment record |
| 8 | `docs/adr/ADR-C25-007_COMMERCIAL_BRIEF_AUDIT_STORAGE.md` | Amendment note added (§1 and §19) |

The WP2.2 / WP2.3 / Any Code "NOT AUTHORIZED" states and the historical
WP2.2 classification are **unchanged** by this record.

```text
Governance administration only. No code, PHP, runtime, Railway, database,
feature, or governance-boundary change was made by this record or its
accompanying amendments.
```

---

*End of Phase3C25 WP2.1B Implementation Authorization.*
