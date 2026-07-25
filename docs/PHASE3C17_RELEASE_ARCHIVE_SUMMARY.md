# Phase3C17 Release Archive Summary

**Role:** Historical release archive (documentation only)  
**Date:** 2026-07-25  
**Branch:** `master`  
**Final verdict:** **PASS — Frozen**

---

## 1. Executive Summary

Phase3C17 closed the operational Command Center and navigation governance work for the Chitu Prospecting Integration extension: Quote lifecycle completion gates, shared workflow authorization, server-side Command Center queues, operational-center navigation IA, record-controller packaging for center scopes, and post-install metadata materialization so fresh installs expose controllers and routes without a manual rebuild step.

**Final verdict: PASS — Frozen.**

Frozen state:

| Item | Value |
| --- | --- |
| Release branch | `master` |
| Final HEAD | `2a20c545d0bff480712161cca208e955ec74c3cf` |
| Release tag | `v1.9.10-alpha` (preserved; not retagged) |
| Freeze tag | `phase3c17-freeze` (`837cc43a3927bf4fe46cad7c222cb9e18e006916`) |
| Artifact | `deployment/prospecting-extension-1.9.10-alpha.zip` |
| Artifact SHA-256 | `DB9189EEEEA78370D1CFDEDBBE1AE5CC888C974220EE5E3CB0FDC705A51D845D` |

---

## 2. Release Identity

| Field | Value |
| --- | --- |
| Version | `1.9.10-alpha` |
| HEAD SHA | `2a20c545d0bff480712161cca208e955ec74c3cf` |
| Release tag | `v1.9.10-alpha` → `2a20c54` (annotated object `bca7175…`; message preserved as-is) |
| Freeze tag | `phase3c17-freeze` → tag object `837cc43a3927bf4fe46cad7c222cb9e18e006916` → commit `2a20c54` |
| Artifact | `deployment/prospecting-extension-1.9.10-alpha.zip` |
| Artifact SHA-256 | `DB9189EEEEA78370D1CFDEDBBE1AE5CC888C974220EE5E3CB0FDC705A51D845D` |
| Integrity | `python crm-extension/scripts/build_release_package.py --check` **PASS** at freeze |

---

## 3. Timeline of Major Milestones

Verified milestones only (commit messages / phase reports already in-repo):

| Milestone | What it delivered | Representative evidence |
| --- | --- | --- |
| **WP0.2** | Quote `SENT → ACCEPTED` lifecycle completion (`markAccepted`) | `cb2cfa5`; `docs/PHASE3C17_WP0_2_ACCEPTED_IMPLEMENTATION.md` |
| **WP0.3** | Quote Record controller for REST create/list/view | `f87fb01`; `docs/PHASE3C17_WP0_3_QUOTE_CONTROLLER_IMPLEMENTATION.md` |
| **WP0.4 / WP0.4b** | Shared Workflow Authorizer + externalized role bindings | `3f051fd`, `0cf57d7`; WP0.4 / WP0.4b reports |
| **WP0.5 / WP0 exit** | Metadata source convergence guard; WP0 exit attestation | `6920719`, `827c396`; exit attestation |
| **WP1** | Operational Centers navigation IA, ADR acceptance, materializer, product polish, runtime defect closure | `6fd69f6` … `3725230`; WP1 reports + ADR amendment A2 (`94af890`) |
| **CC-0A** | Server-side center queue filters | `ffc05d7` |
| **CC-0B** | Command Center dashboard provisioning hardening | `8883e1c` |
| **CC-1** | Center composition + queue runtime integrity (controllers / filters) | `3837ef6`, `5ff7cc3`, `3bff2e2` |
| **R1** | Fresh-install / queue API runtime verification on disposable Docker | Queue smoke evidence; finalization / rebuild reports |
| **R1.1** | Runtime route materialization investigation (stale metadata after install) | `8273a43`; `docs/PHASE3C17_R1_1_RUNTIME_ROUTE_MATERIALIZATION_AUDIT.md` |
| **Final** | Install lifecycle rebuild hook restored; artifact reconciled; freeze tags | `2a20c54`; reconciliation report; tags `v1.9.10-alpha` + `phase3c17-freeze` |

---

## 4. Frozen Architecture Decisions

### Lifecycle ownership

Mutation ownership remains service-bound (not dashboards, not navigation, not AfterInstall):

| Concern | Owner |
| --- | --- |
| `Quote.status` | `QuoteTransitionService` |
| `Approval.status` | `ApprovalService` |
| Workflow orchestration | `ApprovalDecisionService` |
| Authorization boundary | Shared workflow authorizer (+ externalized bindings) |

Dashboards and Command Center queues do **not** write status fields.

### Queue architecture

Command Center queues are frozen as:

- **read-only** operational surfaces
- **ACL-filtered** through EspoCRM record ACL
- **server-side filtered** (primary filters / selectDefs)
- **navigation / composition entry points only**

No lifecycle decisions occur inside dashboard or dashlet code.

### Navigation governance

- ADR-C17 accepted; WP1.2 Amendment A2 recorded for governance traceability
- `tabList` / composition authority follows the materializer chain (single-writer governance)
- No unauthorized top-level navigation expansion beyond the frozen Class A–F entity visibility model
- Centers own composition only — not persistence, ACL design, or lifecycle mutation

### Installation lifecycle hardening

`AfterInstall.php` calling `DataManager::rebuild()` is part of the **final released** `1.9.10-alpha` contract (`2a20c54`).

Purpose: after extension install, regenerate metadata / route map / entity registry / controller discovery so web requests find newly packaged controllers without a separate manual rebuild step.

This is release hardening, not an experimental local patch.

---

## 5. Validation Evidence

Recorded at freeze (representative gates from phase reports and release tags):

| Gate | Result |
| --- | --- |
| Extension offline suite | **267** tests PASS (recorded on `v1.9.10-alpha` tag message and CC-1 / reconciliation evidence) |
| Release integrity (S01 / consumers) | PASS during packaging and reconciliation cycles |
| Artifact `--check` | PASS — source ↔ ZIP ↔ sidecar parity at SHA `DB9189EE…` |
| Runtime smoke | Command Center / queue composition smoke; center routes exercised on disposable Docker |
| API route verification | `DraftApproval`, `Approval`, `ReplyEvent`, `SendExecution` (and related Quote) list routes verified after materialization |

**Fresh-install finding (R1 / R1.1):** installing controllers alone was insufficient when metadata cache was not rebuilt — APIs returned controller-missing **404** / missing-filter **400** despite files on disk.

**Final resolution:** post-install `DataManager::rebuild()` lifecycle hardening in `AfterInstall`, packaged into the frozen `1.9.10-alpha` artifact.

---

## 6. Deferred Items / Next Phase Boundary

Explicitly **out of Phase3C17 / frozen `1.9.10-alpha`**:

| Deferred | Boundary |
| --- | --- |
| **CC-2** | SendExecution operational workflow / send-queue expansion |
| Analytics | Future dashboard / read-only expansion beyond Command Center composition |
| Additional business centers | New top-level centers or Class A entries |
| New lifecycle mutation | Any new status write paths or ownership changes |
| ACL redesign | Role/ACL model changes beyond packaging existing scopes |

Future work must open a **new phase and/or version**; it must not mutate tagged `v1.9.10-alpha` or `phase3c17-freeze` history.

---

## 7. Release Governance Notes

- Tagged versions are **immutable**. Do not force-move `v1.9.10-alpha`.
- `v1.9.10-alpha` was **preserved** as the release identity tag (message retained as authored).
- `phase3c17-freeze` marks the **frozen architecture state** at the same commit (`2a20c54`).
- Artifact identity for this freeze is SHA-256 `DB9189EEEEA78370D1CFDEDBBE1AE5CC888C974220EE5E3CB0FDC705A51D845D`.
- Any subsequent product, packaging, navigation, ACL, or lifecycle change requires a new phase/version trail — not edits under these freeze tags.

---

**Archive status:** Phase3C17 historically closed at `2a20c54` / `1.9.10-alpha` / `phase3c17-freeze`.
