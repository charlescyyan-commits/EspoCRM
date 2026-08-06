# Phase3C25 WP2.2 Authorization Charter — Generation and Validation Boundary

| Field | Value |
| --- | --- |
| Document Type | Authorization Charter (governance gate) |
| Work Package | WP2.2 — Generation and Validation Boundary |
| Parent | Phase3C25 WP2 — AI Commercial Brief (`docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md`, RATIFIED) |
| Identity | **WP2.2 — Generation and Validation Boundary** |
| Status | **CURRENT AUTHORITATIVE** (2026-08-06) — replaces the historical WP2.2 application-layer chain |
| Date | 2026-08-06 |
| Supersedes | Historical WP2.2 application-layer records (Authorization Charter / Implementation Plan / Implementation Authorization / Release Record / Freeze Review) — retained as **HISTORICAL / SUPERSEDED** per `docs/PHASE3C25_WP2_AUTHORIZATION_STATE_SYNCHRONIZATION.md` |
| C20 closure | Tag `phase3c20-governance-closure`; C20 Dependency Closure Amendment ratified at `b632f1d` (RATIFIED WITH INFORMATIONAL NOTES) |
| C25 WP2.0 | **SATISFIED — READY FOR CONSUMPTION** (Capability identity + Purpose policy + Boundary evidence) |
| WP2.1B | **FROZEN** — tag `phase3c25-wp2-1b-freeze` → commit `fa3e620` (13-path persistence allowlist; 16/16 tests) |
| Audit storage | ADR-C25-007 **RATIFIED** — audit writer / ledger owned by **WP2.3** (default) |
| Planning Authorization | **YES** — this charter authorizes WP2.2 planning / design review only |
| Implementation Authorization | **NO** — requires a separate WP2.2 Foundation Review, a ratified Implementation Plan, and a new Implementation Authorization |
| Commit / push / tag | **NOT AUTHORIZED** by this charter |

```text
WP2.2 — Generation and Validation Boundary
  human-initiated draft CommercialBrief formation
  proposal artifact + provenance attachment + validation
  consumes the frozen WP2.1B persistence contract (read-only)
  references C20 capability / purpose / boundary evidence (read-only)
  NO provider execution
  NO AI runtime expansion
  NO autonomous or scheduled generation
  NO CRM lifecycle mutation (no Lead / Opportunity creation)
  NO deployment change
```

---

## 1. Purpose and Replacement

This charter is the **current authoritative** authorization record for
Phase3C25 WP2.2 — **Generation and Validation Boundary**. It replaces the
historical WP2.2 application-layer chain (charter / implementation plan /
implementation authorization / release record / freeze review) as the
authoritative WP2.2 scope definition.

The historical WP2.2 chain is **HISTORICAL / SUPERSEDED**: its Authorization
Charter was never approved, its Implementation Plan was never ratified, and
its Implementation Authorization self-recorded status was superseded (its
"commit / push / tag NOT AUTHORIZED" clause was not honored — commit `d6ee017`,
tag `phase3c25-wp2-2-freeze`). See
`docs/PHASE3C25_WP2_AUTHORIZATION_STATE_SYNCHRONIZATION.md` §4–§5.

This charter is the first gate of a **new** WP2.2 authorization chain. It
defines scope and boundaries only. It authorizes **planning and design review**
for WP2.2. Implementation remains **NOT AUTHORIZED** and requires the separate
gates recorded in §10 (Exit Criteria) and §11 (Authorization Boundary).

---

## 2. Scope

WP2.2 covers the **generation and validation boundary** of the
`CommercialBrief` lifecycle: transforming a **human-initiated** generation
request into a validated, provenance-attached **draft** `CommercialBrief`,
persisted under the frozen WP2.1B contract.

### In scope (planning / design boundary under this charter)

- Human-initiated generation request handling (`brief.generate`,
  `brief.regenerate`)
- Draft `CommercialBrief` creation flow (proposal artifact + generation
  metadata + provenance references)
- Provenance attachment — the 9 immutable WP2.1B provenance fields (Charter
  §9.1 + Plan §8.1) and source evidence references
- Validation boundary — mandatory fields, provenance completeness,
  forbidden-field guard, evidence anchoring, minimum evidence (D4)
- Idempotency controls (single-flight + unique index)
- Failure / partial-generation handling (no brief on failure; no partial
  persistence)
- Generation versioning
- Test suites for the above (boundary / authorization / provenance /
  idempotency / ACL / forbidden-surface checks)

### Out of scope (other work packages)

| Area | Owner |
| --- | --- |
| Review lifecycle, accept / dismiss, dispositions | WP2.3 |
| Append-only audit implementation | WP2.3 |
| Presentation / source navigation | WP2.4 |
| Persistence contract, provenance fields, ACL | WP2.1B (FROZEN — consumed read-only) |

---

## 3. Allowed Implementation Surfaces

Candidate surfaces are defined by the ratified Plan §24 / §28.1. **None may be
created or modified for delivery under this charter.** They become available
only under the separate WP2.2 Implementation Authorization (§11).

| Surface | Purpose | Owner |
| --- | --- | --- |
| `Services/CommercialBriefGenerationService.php` (incl. internal idempotency component) | Human-initiated generation → draft brief | WP2.2 |
| `Services/CommercialBriefValidationService.php` | Provenance consistency + supersession validation | WP2.2 |
| `Api/PostBriefGenerate.php` | `brief.generate` endpoint | WP2.2 |
| `Api/PostBriefRegenerate.php` | `brief.regenerate` endpoint | WP2.2 |
| `Resources/routes.json` (modify existing — created once with the complete 3-route table; no other WP modifies) | Route registration | WP2.2 |
| `tests/test_phase3c25_wp2_2_*.py` + `tests/fixtures/**` (proposal stubs only) | Tests | WP2.2 |

Explicitly excluded from the WP2.2 surface (must never be created by WP2.2):
audit entity/writer/guards (WP2.3), review/lifecycle service (WP2.3),
presentation layer (WP2.4), persistence-contract files (WP2.1B frozen),
controllers or clientDefs not listed above, and all C20 runtime files.

If a required path is missing from this list, **stop** and obtain an allowlist
amendment. Do not expand silently.

---

## 4. Forbidden Surfaces

Explicitly forbidden — WP2.2 implementation MUST NOT include:

| Category | Forbidden |
| --- | --- |
| **Provider execution** | Direct OpenAI / DeepSeek / any provider calls; API-key handling; credential management; provider selection; SDK / transport ownership; HTTP outbound |
| **AI runtime expansion** | `CompletionRequest` runtime execution; `ProviderBinding` execution; AIJob executor implementation; worker / queue / scheduler / retry / cancellation / reservation engines |
| **Autonomous generation** | Any unattended, event-driven, or AI self-triggered generation; automatic promotion of a draft to commercial effect |
| **Scheduled generation** | Scheduler / cron / batch / webhook / event-listener triggered generation |
| **CRM lifecycle mutation** | Automatic CRM mutation; OpportunityCandidate lifecycle transition; C22 execution / ActionGate influence; C24 transition via the anchor link |
| **Lead creation** | `Lead` creation / conversion / qualification writes |
| **Opportunity creation** | `Opportunity` creation or pipeline mutation |
| **Deployment changes** | Migrations; `AfterInstall` changes; Railway / deployment files; runtime activation; production use |
| **Outbound** | Email sending; messaging; autonomous outreach |
| **Audit (WP2.3-owned)** | `CommercialBriefAuditEvent`; `CommercialBriefAuditWriter`; append-only audit guard; audit ledger persistence |
| **WP2.1B baseline** | Modification of the frozen persistence contract, entity, provenance fields, ACL, workflow metadata, or i18n at `phase3c25-wp2-1b-freeze` |
| **C20 / C24 / C22 ownership** | `ProviderRoute` creation; C20 capability value addition; `ProviderBinding` decision; credentials / SDK ownership; C22 execution modules; C24 lifecycle transition |
| **Historical WP2.2 artifacts** | Adoption / reliance on commit `d6ee017`, tag `phase3c25-wp2-2-freeze`, `Controllers/CommercialBrief.php`, `clientDefs/CommercialBrief.json`, `CommercialBriefProposalService`, `CommercialBriefReviewService`, historical hooks — retained, not adopted, quarantine pending before runtime use |

---

## 5. C20 / C25 Ownership Boundary

| Owner | Owns | WP2.2 relationship |
| --- | --- | --- |
| **C20** | Capability registry / identity (`COMMERCIAL_BRIEF`); purpose policy (`commercial_brief_generation`); ProviderBinding / provider governance; AIJob / AIRequestLog / PromptTemplate runtime; credentials / SDK / transport | Read-only consumption of identity / purpose / boundary evidence; **references only, never mutation** |
| **C25** | `CommercialBrief` artifact (WP2.1B persistence); generation / validation workflow (WP2.2); review lifecycle (WP2.3); presentation (WP2.4) | WP2.2 owns generation / validation workflow only |
| **C22** | Prospecting / outreach execution; ActionGate; ExecutionLedger | No interaction; no integration |
| **C24** | OpportunityCandidate lifecycle (read-only anchor for the brief) | Read-only reference; no transition through the anchor link |

**No ownership transfer.** WP2.2 must not assume ownership of ProviderBinding,
the capability portfolio, connector dispatch, or C20 invariant activation.
C25 may reference C20 identity/policy/provenance surfaces; it must not
implement provider routing or dispatch.

---

## 6. Generation Boundary

**Human-initiated only.** Generation is triggered exclusively by an explicit
human request. No scheduler, cron, webhook, event listener, batch, or
autonomous loop.

**Draft creation flow:**

```text
Human requester
  → generation request (brief.generate / brief.regenerate)
  → assemble evidence references (WP1 context, requester source ACL)
  → draft proposal artifact (advisory content only)
  → attach provenance (9 immutable fields; source evidence references)
  → validate (mandatory fields, provenance completeness,
             forbidden-field guard, evidence anchoring, minimum evidence D4)
  → persist draft CommercialBrief via the frozen WP2.1B contract
```

Rules:

- Draft content is **advisory proposal only**. Human review authority is a
  separate WP2.3 concern; no automatic promotion from draft to commercial
  effect.
- **No brief on failure.** Persistence is all-or-nothing — no partial,
  placeholder, or incomplete row (Parent Charter §18).
- **Live provider generation is NOT authorized here.** Any future path that
  invokes C20 provider execution requires a separate Runtime Expansion /
  execution authorization **outside WP2.2**. WP2.2 does not inherit provider
  authority from the "generation" label.
- Any governed-async path reuses C20's existing `AIJob` lifecycle through
  C20-owned services, under human initiation (Parent Charter §11). WP2.2 never
  implements an AIJob executor or provider dispatch. The exact dispatch
  boundary is resolved by the WP2.2 Foundation Review / Implementation Plan
  (OQ-G).

---

## 7. Validation Boundary

The validation boundary guards the transition from request to persisted draft:

- **Mandatory fields present** — complete four advisory sections, designations,
  anchor reference.
- **Provenance completeness** — the 9 immutable WP2.1B provenance fields
  present and consistent (Charter §9.1; Plan §8.1).
- **Forbidden-field guard** — no schema-level forbidden field
  (score / priority / ranking / probability / forecast / stage / lifecycle /
  authority fields, etc.).
- **Evidence anchoring** — every claim maps to source references;
  minimum evidence (D4: ≥ 1 governed source artifact, chain complete).
- **Supersession reference validation** — `supersedesBriefId` references
  validate against the frozen supersession model.

Validation is **not** autonomous qualification. It does not accept, dismiss,
or override review — those are human-governed WP2.3 actions. Incomplete or
invalid drafts are rejected **before** persistence; a validation failure is
surfaced to the human requester, never stored as a partial record.

---

## 8. Idempotency Requirements

- **Deterministic idempotency key** (Parent Charter §17.1):

  ```text
  idempotencyKey = H( anchorCandidateId
                      | evidenceSetHash
                      | generationVersion
                      | briefPurpose
                      | requesterId )
  ```

  Whether `requesterId` enters the canonical generation identity is decided by
  the WP2.2 Implementation Plan.
- **Structural dedupe** — single-flight in the generation service + unique
  index (structural, not convention).
- **Retry of the same request** returns the existing draft / generation —
  no duplicate generation, no duplicate row.
- **Changed evidence set** → changed `evidenceSetHash` → a new generation
  (a new revision), not a duplicate.
- **Idempotency dedupe window** (OQ-E) — bounded per brief purpose; resolved
  at the WP2.2 Foundation Review / Implementation Plan.

---

## 9. Audit Relationship with WP2.3

- ADR-C25-007 is **RATIFIED**: the append-only audit store
  (`CommercialBriefAuditEvent` + `CommercialBriefAuditWriter` + append-only
  guard) is owned by **WP2.3** (default).
- `CommercialBriefSaveOption::AUDIT_WRITE_AUTHORIZED` exists as a constant on
  the frozen WP2.1B save-option class. **No audit writer is authorized in
  WP2.2.**
- WP2.2 **must not** create the audit entity, writer, guards, or audit
  storage, and **must not** write audit events.
- WP2.2 design **must be audit-compatible**: generation carries C20
  `AIJob` / `AIRequestLog` provenance references so that WP2.3 can record
  generation governance events once WP2.3 is separately authorized. Human
  review events never create an `AIRequestLog` (Charter §9.2).
- WP2.2 exit requires the audit write path per ADR to be **available** (i.e.,
  WP2.3 authorized) before generation freeze (§10).

---

## 10. Exit Criteria

WP2.2 implementation is eligible to exit only when all of the following hold:

| # | Criterion | Status |
| --- | --- | --- |
| 1 | C20 dependency closure **ratified** (capability identity + purpose policy + boundary evidence) | ✅ `b632f1d` |
| 2 | ADR-C25-007 **ratified** (audit storage decision) | ✅ |
| 3 | WP2.1B **exit / FROZEN** (`phase3c25-wp2-1b-freeze` → `fa3e620`) | ✅ |
| 4 | Audit write path per ADR **available** | ⏳ pending WP2.3 authorization |
| 5 | WP2.2 Foundation Review completed and approved; deferred gates **D4 / OQ-D, OQ-E, OQ-G** dispositioned | ⏳ required |
| 6 | Generation boundary + failure matrix green; **idempotency** (incl. regeneration) verified; **no-partial** proven | ⏳ required |
| 7 | Boundary tests green — no provider invoke / HTTP outbound / worker / queue / scheduler; no CRM mutation; ACL / authorization / provenance-preservation checks green | ⏳ required |
| 8 | Independent C20–C25 boundary verification; invariant compliance checklist signed | ⏳ required |
| 9 | Independent **Verification Review PASS** before freeze | ⏳ required |

WP2.2 does not reach freeze on this charter alone; freeze requires a separate
Verification Review and Freeze Closure.

---

## 11. Authorization Boundary

| Scope | Status |
| --- | --- |
| C20 foundation gate (capability identity + purpose policy + boundary evidence) | **SATISFIED** |
| WP2.1B CommercialBrief persistence | **FROZEN** |
| WP2.2 planning / design review | **AUTHORIZED** (this charter) |
| WP2.2 Implementation | **NOT AUTHORIZED** — requires Foundation Review + ratified Implementation Plan + separate Implementation Authorization |
| WP2.3 audit implementation | **NOT AUTHORIZED** |
| Runtime expansion / provider execution | **NOT AUTHORIZED** |
| Deployment / production | **NOT AUTHORIZED** |

```text
This charter replaces the historical WP2.2 application-layer chain as the
current authoritative WP2.2 record. It authorizes planning and design review
only. Implementation, entity creation, metadata changes, provider execution,
runtime expansion, deployment, and production use remain NOT AUTHORIZED.
```

---

*End of Phase3C25 WP2.2 Authorization Charter — Generation and Validation
Boundary (CURRENT AUTHORITATIVE, 2026-08-06).*
