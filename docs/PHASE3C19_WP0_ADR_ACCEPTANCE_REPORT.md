# Phase3C19 WP0 — ADR Acceptance Report

**Status:** WP0 closed
**Date:** 2026-07-26
**Baseline:** `9bbd44a` (`phase3c18: open 1.9.11-alpha release line with WP2 reconciliation`) / `phase3c18-freeze`
**Mode:** DOCUMENTATION ONLY — no PHP, metadata, or test changes
**Commit message:** `phase3c19: add WP0 charter and ADR governance baseline`

---

## 1. WP0 Scope

Complete C19 WP0 governance closure: charter the phase, accept the two governing
ADRs, reconcile the architecture documents, and commit **documentation only**.

Explicitly not done in WP0: PHP changes, metadata changes, test changes, feature
implementation, release artifact rebuilds, tag mutation.

---

## 2. Accepted Decisions

| # | Decision | Document | Marker |
| --- | --- | --- | --- |
| D1 | Phase3C19 chartered: Command Center evolves from monitoring dashboard to daily sales action center; WP0–WP3 map frozen | `docs/PHASE3C19_CHARTER.md` | — |
| D2 | **ADR-C19 Accepted.** `replyStatus` = immutable provider fact (ingress-owned); `triageStatus` = work lifecycle (`ReplyTriageService`-owned); `PostSyncReplyEvent` ingress contract; `c19OpenReplies` queue contract | `docs/adr/ADR-C19_REPLY_EVENT_LIFECYCLE.md` | **`adr-c19-replyevent-v1`** |
| D3 | **ADR-C18 amendment A6 Accepted.** Retry/Cancel reuse existing transitions; **no RecoveryService**; sentAt remediation owned by transition service; additive cancel audit fields (`cancelledAt`/`cancelledBy`/`cancelReason`); **Ignore = CANCELLED + cancelReason** | `docs/adr/ADR-C18-A6_SEND_RECOVERY_ACTION_BOUNDARY.md` | **`adr-c18-sendexecution-v2`** |
| D4 | Earlier draft's Ignore-as-marker model (`ignoredAt`/`ignoredBy`/`ignoreReason`, reversible Unignore) **rejected**; `docs/PHASE3C19_SEND_RECOVERY_ARCHITECTURE.md` reconciled to A6 | this report; ADR-C18-A6 §4 | — |
| D5 | Failed Send admission to the Command Center approved in principle (WP3); C18 WP2.2 test-contract amendment recorded as a WP3 prerequisite with decision-log entry | `docs/PHASE3C19_COMMAND_CENTER_DESIGN.md` §5.1 | — |
| D6 | 待回复 semantic gap resolved by ADR-C19 (event-level triage); the audit's Lead `peAwaitingReply` fallback is **not** needed | `docs/PHASE3C19_COMMAND_CENTER_DESIGN.md` §2.4, §3 | — |

---

## 3. Marker Stack After WP0

| Marker | Phase | Scope | Test assertion |
| --- | --- | --- | --- |
| `adr-c18-sendexecution-v1` | C18 | A1–A5 lifecycle invariants | Existing C18 suites — unchanged |
| `adr-c18-sendexecution-v2` | C19 (A6) | Recovery entry-point boundary, sentAt remediation, cancel audit fields, Ignore semantics | C19-WP2 recovery suite (to be built) |
| `adr-c19-replyevent-v1` | C19 | ReplyEvent provider-fact / triage split, ingress, `c19OpenReplies` | C19-WP1 reply suite (to be built) |

---

## 4. Files Added / Changed in WP0 (documentation only)

| File | State | Content |
| --- | --- | --- |
| `docs/PHASE3C19_CHARTER.md` | Added | Phase charter, audit findings F1–F5, WP map, boundaries, marker stack |
| `docs/adr/ADR-C19_REPLY_EVENT_LIFECYCLE.md` | Added | Reply lifecycle ADR (D2) |
| `docs/adr/ADR-C18-A6_SEND_RECOVERY_ACTION_BOUNDARY.md` | Added | Send recovery amendment A6 (D3) |
| `docs/PHASE3C19_REPLY_CENTER_ARCHITECTURE.md` | Added | Reply Center architecture implementing ADR-C19 |
| `docs/PHASE3C19_SEND_RECOVERY_ARCHITECTURE.md` | Added (reconciled from untracked audit draft) | Send recovery architecture implementing ADR-C18-A6; as-built inventory preserved; recovery model replaced per D4 |
| `docs/PHASE3C19_COMMAND_CENTER_DESIGN.md` | Added | Command Center audit + WP3 queue-evolution design, reconciled to WP0 decisions |
| `docs/PHASE3C19_WP0_ADR_ACCEPTANCE_REPORT.md` | Added | This report |

---

## 5. Verification (docs-only gate)

Executed against the working tree at WP0 close:

| Check | Result |
| --- | --- |
| `git status --short` — WP0 changes limited to `docs/` | ✅ (7 files above; all under `docs/`) |
| No `*.php` in WP0 change set | ✅ |
| No `crm-extension/**` metadata in WP0 change set | ✅ |
| No `crm-extension/tests/**` in WP0 change set | ✅ |
| Governance markers present in ADRs | ✅ `adr-c19-replyevent-v1`, `adr-c18-sendexecution-v2` |
| Baseline unchanged | ✅ HEAD `9bbd44a` at WP0 start; no tag mutation |

Pre-existing working-tree items **excluded** from the WP0 commit (not WP0 scope,
left untouched for their owning work streams):

- `M crm-extension/files/client/custom/res/templates/dashlets/prospecting-summary.tpl` (line-ending-only drift)
- `?? EspoCRM/` (audit workspace directory)

---

## 6. Implementation Gates Opened by WP0

| WP | Gate source | Summary |
| --- | --- | --- |
| C19-WP1 (Reply Center) | ADR-C19 §8 | `triageStatus` + guard + `ReplyTriageService` + `PostSyncReplyEvent` + `c19OpenReplies` + authorization bindings; marker `adr-c19-replyevent-v1` in policy/tests |
| C19-WP2 (Send Recovery) | ADR-C18-A6 §8 | Quote-pattern entry point; cancel audit fields; sentAt remediation; Ignore=Cancel UI; marker `adr-c18-sendexecution-v2` in policy/tests |
| C19-WP3 (Command Center) | `PHASE3C19_COMMAND_CENTER_DESIGN.md` §5 | C18 test-contract amendment; provisioner `c19` ids; 5 new queue bindings; re-titles; composition contracts |

---

## 7. Decision Log

| Date | Decision |
| --- | --- |
| 2026-07-26 | WP0 scope frozen: documentation only on baseline `9bbd44a` |
| 2026-07-26 | ADR-C19 Accepted (`adr-c19-replyevent-v1`) |
| 2026-07-26 | ADR-C18-A6 Accepted (`adr-c18-sendexecution-v2`); Ignore-as-marker draft rejected |
| 2026-07-26 | Docs-only verification passed; WP0 closed; WP1–WP3 authorized |
