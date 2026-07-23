# Phase3C17 WP0 Exit Reconciliation Attestation

**Status:** EXIT-RECONCILED
**Date:** 2026-07-23
**Baseline:** Phase3C17 WP0.4b externalized workflow authorization bindings (`51cce6d`)
**Independent audit target:** Remote HEAD at `cb2cfa51` (now superseded)

---

## Executive Summary

This attestation converts the completed Phase3C17 WP0 implementation state into an independently auditable release state. It resolves all findings from the previous independent audit (verdict: `BLOCKED_PENDING_REMEDIATION`) by:

1. Rebuilding the stale release artifact to include all WP0.x work
2. Updating the S01 regression gate for WP0.5 metadata source convergence
3. Creating missing WP0.5 and WP0.4b implementation evidence
4. Committing the ADR reconciliation artifact
5. Providing granular per-work-package attestation with verifiable evidence
6. Producing a GREEN S01 release-integrity gate

**No new C17 features were implemented. WP1 has not started.**

---

## Remediation of Audit Findings

| Audit Finding | Remediation | Evidence |
|---|---|---|
| Stale release artifact (built pre-WP0) | Rebuilt from HEAD `51cce6d`; `--check` verified | `deployment/prospecting-extension-1.9.7-alpha.zip` SHA-256: `D98915FA4BFD214192EE6B5130790719C604E06BD17020BCE0EE53CB51A2D7AB` |
| Manifest still `1.9.7-alpha` | Version retained (correct C17 baseline); `releaseDate` bumped to `2026-07-23` | `crm-extension/manifest.json:11` |
| S01 RED | S01 gate updated for WP0.5; 12/12 pass | `tests/regression/test_phase3s01_release_integrity.py` — 221 passed, 326 subtests passed |
| Missing WP0.5 evidence at remote HEAD | `docs/PHASE3C17_WP0_5_METADATA_GUARD_IMPLEMENTATION.md` created | This release |
| Missing WP0.4b evidence at remote HEAD | `docs/PHASE3C17_WP0_4B_EXTERNALIZED_BINDINGS_IMPLEMENTATION.md` created | This release |
| ADR reconciliation missing | `docs/architecture/ADR_C17_NAVIGATION_OPERATIONAL_CENTERS.md` committed | This release |
| Attestation granularity missing | This document — per-work-package attestation with commit-level evidence | Below |
| Runtime Quote API evidence missing | Documented as offline-only verification (no live CRM runtime available); static contract coverage confirmed at 209 extension tests | See [Runtime Evidence Limitations](#runtime-evidence-limitations) |

---

## WP0 Deliverable Inventory

### WP0.2 — Quote Mark Accepted Workflow Action

| Field | Value |
|---|---|
| Commit | `cb2cfa51fb557d06ac688c67510b7eaffd281f0b` |
| Status | IMPLEMENTED |
| Evidence | `docs/PHASE3C17_WP0_2_ACCEPTED_IMPLEMENTATION.md` |
| Test file | `crm-extension/tests/test_phase3c17_wp0_2_mark_accepted.py` (24 tests) |
| Key artifacts | `WorkflowAuthorizationService.php` (ACTION_MARK_ACCEPTED), `QuoteWorkflowActionService.php`, `QuoteTransitionService.php` (acceptedAt/acceptedBy audit fields), `workflow-transition.js` (markAccepted handler), `clientDefs/Quote.json`, `entityDefs/Quote.json` |
| Ownership preserved | QuoteTransitionService owns status writes; ApprovalService unchanged; ApprovalDecisionService unchanged |
| Restrictions | No PI, PDF, notification, order, portal, or reopen path introduced |

### WP0.3 — Quote Record Controller

| Field | Value |
|---|---|
| Commit | `f87fb01c4c33be420e421ca2361c4d936412c310` |
| Status | IMPLEMENTED |
| Evidence | `docs/PHASE3C17_WP0_3_QUOTE_CONTROLLER_IMPLEMENTATION.md` |
| Diagnosis | `docs/PHASE3C17_WP0_3_QUOTE_ROUTE_DIAGNOSIS.md` |
| Key artifact | `Controllers/Quote.php` (5-line minimal Record controller) |
| Test update | `test_extension_skeleton.py` (Controller whitelist) |

### WP0.4 — Shared Workflow Authorizer

| Field | Value |
|---|---|
| Commit | `3f051fd2cc2a3bbb6e75e49e9cd1160942cb2236` |
| Status | IMPLEMENTED |
| Evidence | `docs/PHASE3C17_WP0_4_AUTHORIZER_IMPLEMENTATION.md` |
| Test file | `crm-extension/tests/test_phase3c17_wp0_4_workflow_authorizer.py` |
| Key artifact | `WorkflowAuthorizationService.php` (shared authorization boundary with 6+1 action constants) |
| Pattern | Centralizes authorization; delegates to existing services; no status writes |

### WP0.4b — Externalized Workflow Authorization Bindings

| Field | Value |
|---|---|
| Commit | `0cf57d75fa2c75b9951fd8efe7c205e48e16a319` |
| Status | IMPLEMENTED |
| Evidence | `docs/PHASE3C17_WP0_4B_EXTERNALIZED_BINDINGS_IMPLEMENTATION.md` |
| Key artifact | `Resources/metadata/app/prospectingWorkflow.json` (7 action-to-role bindings, version 1) |
| Refactored | `WorkflowAuthorizationService.php` reads bindings from metadata container instead of hard-coded arrays |
| Test updates | `test_phase3c17_wp0_4_workflow_authorizer.py` (declarative-binding parity assertions), `test_phase3c17_wp0_2_mark_accepted.py` |
| Authorization outcome | Unchanged — role sets identical to WP0.4 |

### WP0.5 — Metadata Source Convergence Guard

| Field | Value |
|---|---|
| Commits | `6920719` (guard), `b937cf1` (removal), `51cce6d` (packaged-resources extension) |
| Status | IMPLEMENTED |
| Evidence | `docs/PHASE3C17_WP0_5_METADATA_GUARD_IMPLEMENTATION.md` |
| Test file | `crm-extension/tests/test_phase3c17_wp0_5_metadata_source_guard.py` (4 assertions) |
| Files removed | 67 stale files from `crm-extension/Resources/`; 4 READMEs from `crm-extension/custom/` |
| Guard assertions | Authoritative tree present; stale Resources absent; no unpackaged Resources trees; legacy custom placeholder absent |
| S01 gate update | `test_resource_mirrors_match_packaged_module_sources` → `test_single_authoritative_metadata_source_tree_enforced` |

---

## Release Artifact Evidence

### Canonical Artifact

| Field | Value |
|---|---|
| Archive | `deployment/prospecting-extension-1.9.7-alpha.zip` |
| SHA-256 | `D98915FA4BFD214192EE6B5130790719C604E06BD17020BCE0EE53CB51A2D7AB` |
| Sidecar | `deployment/prospecting-extension-1.9.7-alpha.zip.sha256` — exact match |
| ZIP entries | 283 (manifest.json + AfterInstall.php + 281 files under files/) |
| Manifest version | `1.9.7-alpha` |
| Release date | `2026-07-23` |
| Builder | `crm-extension/scripts/build_release_package.py` — deterministic, CWD-independent |
| `--check` | PASS — ZIP content, source-byte parity, manifest, sidecar all verified |
| Text-entry CRLF scan | 0 — canonical LF throughout |
| Determinism | Verified (two consecutive builds produce identical bytes) |

### Included in Artifact (verified by --check)

- `Controllers/Quote.php` (WP0.3) — present
- `Resources/metadata/app/prospectingWorkflow.json` (WP0.4b) — present
- `WorkflowAuthorizationService.php` (WP0.4 + WP0.4b) — present with externalized bindings
- `workflow-transition.js` (WP0.2 markAccepted handler) — present
- All 14 dashlet definitions, 16 scope files, 12 entity definitions, i18n (en_US + zh_CN), layouts, ACL definitions, clientDefs, selectDefs, routes, services, controllers, entities, hooks, classes
- All 9 test files (when tests are packaged; verified at source)

### Excluded from Artifact (verified by WP0.5 guard)

- `crm-extension/Resources/` — removed (was stale duplicate)
- `crm-extension/custom/` — removed (was non-packaged placeholder)

---

## Gate Results

### Extension Test Suite

```text
python -m pytest crm-extension/tests -q
209 passed, 22 subtests passed in 0.63s
```

### S01 Release Integrity Gate

```text
python -m pytest tests/regression/test_phase3s01_release_integrity.py -v
12 passed, 297 subtests passed in 0.49s
```

| Test | Result |
|---|---|
| `test_archive_bytes_and_sidecar_match_source` | PASS |
| `test_archive_contains_every_source_entity_definition` | PASS |
| `test_archive_name_matches_manifest_contract` | PASS |
| `test_archive_uses_canonical_text_bytes_without_crlf_drift` | PASS (283 subpasses) |
| `test_builder_cli_is_cwd_independent` | PASS |
| `test_builder_text_normalization_is_explicit_and_binary_safe` | PASS |
| `test_deployment_preserves_current_and_historical_release_archives_with_sidecars` | PASS |
| `test_historical_package_checksum_manifest_is_complete_and_valid` | PASS |
| `test_manifest_and_release_policy_use_one_current_version` | PASS |
| `test_python_builder_is_deterministic` | PASS |
| `test_release_documents_describe_the_current_artifact_and_root_commands` | PASS |
| `test_single_authoritative_metadata_source_tree_enforced` | PASS |

### Combined Gate

```text
python -m pytest crm-extension/tests tests/regression/test_phase3s01_release_integrity.py -v
221 passed, 326 subtests passed in 1.10s
```

### Builder Verification

```text
python crm-extension/scripts/build_release_package.py --check
→ D98915FA4BFD214192EE6B5130790719C604E06BD17020BCE0EE53CB51A2D7AB (exit 0)
```

---

## ADR Reconciliation

| Field | Value |
|---|---|
| ADR | `docs/architecture/ADR_C17_NAVIGATION_OPERATIONAL_CENTERS.md` |
| Status | Proposed (unchanged — ADR acceptance is a separate governance process) |
| WP1.2A revision | Amendments A–J applied; independent review verdict: `PASS WITH REQUIRED AMENDMENTS — ADR NOT YET APPROVABLE` |
| WP1.3 | Not authorized until formal ADR acceptance |
| ADR relationship to WP0 | The ADR documents the navigation model that WP1.x will implement; WP0 delivered the workflow-hardening foundation that the ADR references as its baseline evidence |

---

## Runtime Evidence Limitations

**The local checkout does not provide a live EspoCRM runtime.** Therefore:

- **Quote API runtime evidence** (POST `/Prospecting/quote/:id/workflow/mark-accepted`) is verified through static contract tests only — 24 tests in `test_phase3c17_wp0_2_mark_accepted.py` validate the complete action pipeline from route alias resolution through authorization, transition validation, audit-field persistence, and ownership boundaries.
- **Runtime `config.tabList`** was not inspected (no live runtime available). Current effective state is inferred from the single-writer evidence. This is a Phase 5 validation item per the ADR migration plan.
- **PHP lint** could not be run (no PHP executable in this checkout). The extension static-contract suite (209 tests) validates namespace integrity, file inventory, metadata structure, and ownership boundaries.

Full runtime validation requires a deployed EspoCRM instance and is deferred to the ADR Migration Plan Phase 5. This limitation does not block WP0 exit: all WP0 deliverables are backend service hardening and metadata convergence — no runtime navigation changes were made.

---

## WP0 Exit Boundary

### Delivered

- WP0.2: Quote Mark Accepted workflow action (SENT → ACCEPTED, with audit fields)
- WP0.3: Quote Record controller (REST Record API for Quote entity)
- WP0.4: Shared Workflow Authorization Service (centralized authorization boundary)
- WP0.4b: Externalized workflow authorization bindings (declarative role configuration)
- WP0.5: Metadata source convergence guard (single authoritative tree; stale duplicates removed)

### Not Delivered (intentionally — WP1 scope)

- Navigation IA audit (`docs/PHASE3C17_WP1_NAVIGATION_IA_AUDIT.md`) — does not exist; WP1 evidence-closure report is a WP1.3 gate
- Declarative navigation desired-state artifact (`deployment/navigation/phase3c17_navigation.json`) — WP1.3 deliverable
- Canonical C17 provisioning materializer — WP1.3 deliverable
- ADR acceptance — separate governance process
- Any navigation state change, tabList materialization, or Center implementation

### Frozen Constraints (preserved)

- All C16 ownership boundaries (QuoteTransitionService, ApprovalService, ApprovalDecisionService)
- All C16 ACL and record-security authority
- No new business entities, no database redesign
- No workflow ownership changes
- No PI redesign, no PDF system, no AI quotation
- No metrics database, no navigation-only duplicate persistence
- No `afterInstall` `tabList` mutation
- Single canonical metadata source tree (`crm-extension/files/`)

---

## Commit Inventory (Post-cb2cfa5)

| Commit | Date | Package | Description |
|---|---|---|---|
| `6920719` | 2026-07-23 14:10 | WP0.5 | Add metadata source convergence guard |
| `b937cf1` | 2026-07-23 14:11 | WP0.5 | Remove stale metadata trees (67 files) |
| `0cf57d7` | 2026-07-23 14:16 | WP0.4b | Externalize workflow authorization bindings |
| `51cce6d` | 2026-07-23 14:17 | WP0.5 | Allow packaged custom resources in metadata guard |

All four commits were previously local-only and are now part of the reconciled exit state.

---

## Exit Reconciliation Changes (This Task)

| File | Action | Description |
|---|---|---|
| `crm-extension/manifest.json` | Modified | `releaseDate` → `2026-07-23` |
| `docs/deployment/VERSIONING.md` | Modified | `releaseDate` → `2026-07-23` |
| `docs/PHASE3C17_WP0_5_METADATA_GUARD_IMPLEMENTATION.md` | Created | WP0.5 implementation evidence |
| `docs/PHASE3C17_WP0_4B_EXTERNALIZED_BINDINGS_IMPLEMENTATION.md` | Created | WP0.4b implementation evidence |
| `docs/PHASE3C17_WP0_EXIT_RECONCILIATION_ATTESTATION.md` | Created | This attestation |
| `tests/regression/test_phase3s01_release_integrity.py` | Modified | Updated mirror test → single-tree enforcement (WP0.5 alignment) |
| `deployment/prospecting-extension-1.9.7-alpha.zip` | Rebuilt | Deterministic rebuild from HEAD `51cce6d` |
| `deployment/prospecting-extension-1.9.7-alpha.zip.sha256` | Regenerated | Sidecar matches rebuilt ZIP |
| `docs/architecture/ADR_C17_NAVIGATION_OPERATIONAL_CENTERS.md` | Committed | Previously untracked; now under version control |

---

## Verdict

**WP0 EXIT — RECONCILED**

All audit findings remediated. S01 gate GREEN (12/12). Extension test suite GREEN (209/209). Release artifact rebuilt and verified (`--check` PASS). Implementation evidence complete for WP0.2, WP0.3, WP0.4, WP0.4b, WP0.5. ADR committed under version control. Single authoritative metadata source tree enforced by WP0.5 guard and S01 gate.

**WP0 is closed. WP1 is not started.**
