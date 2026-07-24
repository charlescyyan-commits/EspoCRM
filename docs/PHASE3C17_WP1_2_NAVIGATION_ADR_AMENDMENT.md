# Phase3C17 WP1.2 Navigation ADR Amendment A2

**Status:** Accepted (incorporated into ADR-C17; recorded here for governance traceability)

**Date:** 2026-07-23

**References:**
- `docs/architecture/ADR_C17_NAVIGATION_OPERATIONAL_CENTERS.md` (the amended ADR)
- `docs/PHASE3C17_WP1_NAVIGATION_IA_AUDIT.md` (frozen IA audit)
- `docs/PHASE3C17_WP0_EXIT_RECONCILIATION_ATTESTATION.md` (WP0 exit authorization)

---

## 1. Purpose

This document is the formal record of **Amendment A2** — the WP1.2 architecture review
findings (A–J) applied to
[ADR-C17](architecture/ADR_C17_NAVIGATION_OPERATIONAL_CENTERS.md). It is a governance
companion to the ADR, not a replacement. All A2 decisions are frozen in the ADR; this
file exists to satisfy the WP1.2 documentation gate that `PHASE3C17_WP1_2_NAVIGATION_ADR_AMENDMENT.md`
be present in the repository.

The underlying ADR was:

1. **Authored** as WP1.2 (navigation architecture proposal).
2. **Amended** as WP1.2A (independent architecture review; findings A–J incorporated).
3. **Accepted** for WP1.2–WP1.4 implementation by the authorized C17 implementation task.

## 2. Amendment A-J Summary

The independent WP1.2A architecture review identified findings A through J. Each was
addressed and the resulting text incorporated directly into the ADR. The ADR's
**Amendment record** (`ADR_C17_NAVIGATION_OPERATIONAL_CENTERS.md:13`) confirms:

> WP1.2A review findings A–J remain incorporated.

The specific amendments converged on the following frozen decisions:

| Finding | Topic | Disposition |
|---|---|---|
| A | Entity visibility classification framework | Adopted; six frozen classes (A–F) |
| B | Lead as sole Class E global native tab | Confirmed; no duplication allowed |
| C | Research Center = Lead (not ResearchEvidence) | Adopted; ResearchEvidence is Class D supporting object |
| D | Navigation composition authority | Single writer governance chain established |
| E | Center vs entity ownership boundary | Centers own composition only, not persistence/ACL/lifecycle |
| F | DraftApproval/Outreach terminology | Separated from Approval; distinct Center entry |
| G | Quote Center scope boundary | Quote, Approval, ProformaInvoice each in assigned class |
| H | Prohibited mutation paths | Dashboard read-only; no status writes from navigation |
| I | Migration plan phasing | Six phases; ADR acceptance → implementation → validation |
| J | C16 ADR relationship | Evolve with partial supersession; C16 not deprecated |

## 3. Frozen Entity Visibility Classification

Per the WP1.2A review, the following classification is **frozen** and must not be
reopened without a new ADR amendment:

| Class | Definition | C17 Assignments |
|---|---|---|
| **A** | Primary operational entry — one physical navigation entry | `ProspectingDashboard`, `ProspectingSearch`, `DraftApproval`, `Quote` |
| **B** | Related record panel — no top-level duplicate | `SendExecution`, `ReplyEvent`, `Approval`, `ProformaInvoice` |
| **C** | Detail action — no global navigation entry | (none assigned in C17) |
| **D** | Supporting object — access through owner or Center | `ResearchEvidence`, `EmailEvent`, `SalesFeedback`, `QuoteItem` |
| **E** | Global native module — appears exactly once | `Lead` |
| **F** | Derived/analytics object — dashboard-only | `LearningSignal` |

## 4. Navigation Governance Chain (Frozen)

```text
Accepted ADR-C17
  → canonical declarative desired-state artifact
    (deployment/navigation/phase3c17_navigation.json)
  → one controlled idempotent provisioning materializer
    (deployment/provisioning/phase3c17_provision_operational_centers_navigation.php)
  → runtime config.tabList
  → drift validation (desired-vs-effective comparison; re-materialize to converge)
```

No second `ConfigWriter`/`tabList` writer is permitted. The U04 compatibility wrapper
(`phase3u04_provision_navbar_tab_order.php`) is deprecated and delegates to C17.

## 5. Non-Negotiable Implementation Boundaries

Frozen for all C17 navigation work:

- No new business entities
- No database redesign
- No workflow ownership changes
- No ACL redesign
- No record-security redesign
- No duplicated lifecycle ownership
- No direct UI status mutation
- No independent navigation SPA
- No custom global navigation framework
- No PI redesign
- No removal of required bulk-processing paths
- No hiding of an entity without a verified replacement access path

## 6. Migration Plan (Summary)

| Phase | Scope | Status |
|---|---|---|
| 1 | ADR review, WP1.2A amendments A–J, independent WP0 exit audit | **Complete** — ADR Accepted |
| 2 | Declarative artifact, single materializer, idempotent provisioning | **Complete** — WP1.3–WP1.4 |
| 3 | Metadata and visibility cleanup; classification enforcement | **Complete** — WP1.3 |
| 4 | Operational Center implementation (composition only) | **Complete** — WP1.3–WP1.4 |
| 5 | Post-implementation runtime validation | Deferred to target CRM |
| 6 | C16 ADR annotation (if required by governance) | Deferred |

## 7. Relationship to Amendment A1

[Amendment A1](architecture/ADR_C17_NAVIGATION_OPERATIONAL_CENTERS.md#adr-amendment-a1--wp14-navigation-product-polish-reconciliation)
(WP1.4 Navigation Product Polish Reconciliation) is a governed evolution within the
authority of this ADR. It refined physical ordering, Chinese-first labels, dashboard
consolidation, and release governance without changing the frozen A2 classification
or governance chain. Both amendments are now incorporated; the ADR is **Accepted**.

## 8. Governance Closure

This Amendment A2 file closes the WP1.2 documentation gate. The authoritative record
of all navigation decisions remains the underlying ADR. If a future reader finds a
discrepancy between this file and the ADR, the ADR text is authoritative.

---

*Amendment A2 accepted 2026-07-23; recorded in repository 2026-07-25 for documentation
closure. WP1.2A findings A–J incorporated. No architecture decisions changed.*
