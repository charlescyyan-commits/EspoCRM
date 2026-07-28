# Phase3C20 WP0 Freeze Readiness Report

**Status:** Audit record — advisory

**Audit date:** 2026-07-28

**Audit baseline:** `962a7ae` — *phase3c20: complete WP0 AI platform governance foundation*

**Mode:** Read-only. No files were modified, no commits created, and no artifact rebuilt
during the audit itself.

**Scope:** Phase3C20 WP0 (WP0.1 Test Foundation, WP0.2 Invariant Registry,
WP0.3 Boundary Guards, WP0.4 BridgeError Parity).

---

## 0. Provenance and Standing of This Record

This report preserves audit findings that previously existed only in review
correspondence. It is recorded here so the reasoning survives independently of any
external transcript.

**Attribution, stated plainly:** the audit was produced with AI assistance (Claude), and
the same assistant authored the predecessor draft of `ADR-C20_AI_PLATFORM_ARCHITECTURE.md`.
Review of the ADR's provider, credential, and `AIJob` sections is therefore **self-review,
not independent assurance**, and should carry correspondingly less weight. The registry,
guard, artifact-provenance, and frozen-surface findings below concern artifacts the
assistant did not author and are more detached.

This record does not confer approval. WP0 exit is governed by
`docs/PHASE3C20_CHARTER.md` §5.

---

## 1. Test Evidence

Canonical invocation, established by `pytest.ini` in WP0.1:

```
$ pytest -q
571 passed, 1317 subtests passed
```

| Partition | Result |
| --- | --- |
| **Canonical total** (`crm-extension/tests` + `tests`) | **571 passed, 1317 subtests** |

*An earlier audit draft cited `570 passed, 1 skipped, 1002 subtests` from a different
collection snapshot. The figures above are the live canonical result at evidence
persistence (baseline `962a7ae` + this governance package).*

**Significance.** This is the first fully green suite since before `phase3c18-freeze`.
Two assertions in `tests/test_phase3c14_3_1d_failure_projection_hardening.py` had been
failing across two freezes, inherited from C18 commit `5a9287f`. WP0.1 repaired both by
**replacement rather than deletion**:

| Stale assertion | Replacement | Effect |
| --- | --- | --- |
| `assertIn("saveEntity($execution)")` — pinned a pre-C18 implementation detail | `assertIn("SendExecutionTransitionService")`, `assertIn("transitionService->transition")`, `assertNotIn("->saveEntity(")` | **Stronger.** Now asserts the adapter does not persist directly, which is the actual C18 boundary rule. |
| `"authorization"` in the forbidden-marker list — substring false positive on `skipAuthorization` | Four credential-header forms: `'authorization'`, `"authorization"`, `authorization:`, `authorization ` | Preserves secret-leak detection; no longer trips on the workflow option key. |

Prior to WP0.1 there was no `pytest.ini`, `conftest.py`, or `tests/__init__.py`. The
suite only collected with `PYTHONPATH` set and a non-default import mode. **This was the
root cause of the C19 freeze checklist recording "Full tests PASS (384 tests)" for a run
that structurally excluded 22 root test files** — 384 is exactly the
`crm-extension/tests` partition. Establishing a canonical invocation closes that class of
defect.

---

## 2. Registry Findings — C20-INV-03 and C20-INV-18

### 2.1 Finding

Two invariants were marked `DEFERRED` with `test_file = -` while already enforced by
active WP0.3 guards. The registry understated actual coverage.

| Invariant | As-audited | Enforcing test | Corrected |
| --- | --- | --- | --- |
| **C20-INV-03** — no outbound HTTP from PHP to provider domains | `DEFERRED` / WP1 / `-` | `test_php_runtime_has_no_direct_provider_egress` | `ACTIVE` / WP0 / `test_phase3c20_wp0_boundary_guards.py` |
| **C20-INV-18** — no transition service may read `AIQualificationInsight` | `DEFERRED` / WP3 / `-` | `test_prospecting_transition_owners_do_not_read_ai_qualification_insight` | `ACTIVE` / WP0 / `test_phase3c20_wp0_boundary_guards.py` |

Counts corrected: **ACTIVE 7 → 9, DEFERRED 15 → 13.**

The meta-test `test_active_and_deferred_total_validation` hardcodes both counts, so
`crm-extension/tests/test_phase3c20_wp0_invariant_registry.py` required a matching update.
Editing the registry alone turns the suite red.

### 2.2 Enforcement verified, not assumed

Both guards were demonstrated to fire against deliberately planted violations, then the
probes removed and green restored:

| Guard | Planted violation | Observed |
| --- | --- | --- |
| INV-03 | `curl_init("https://api.openai.com/v1/chat")` in a scratch service file | `FAILED … provider host marker 'api.openai.com'` |
| INV-18 | `AIQualificationInsight` reference appended to `ReplyTriageService.php` | `SUBFAILED(service='ReplyTriageService.php')` |

A negative assertion never observed failing is indistinguishable from a typo that matches
nothing. Both are real.

**INV-03 scope:** scans `crm-extension/files` in full — 7 word-boundary regexes
(`curl_init`, `curl_exec`, `file_get_contents('http…`, `fsockopen`, `stream_socket_client`,
`GuzzleHttp\`, `new \GuzzleHttp\Client`) plus a 9-entry provider host denylist.

**INV-18 scope:** the four Prospecting transition owners —
`SendExecutionTransitionService`, `ReplyTriageService`, `QuoteTransitionService`,
`ApprovalService`.

### 2.3 ADR §8 conformance

All 22 registry rows correspond 1:1 to ADR §8 numbered invariants. No missing rows, no
extras, no misnumbering. Declared counts equal actual row tallies.

### 2.4 Correctly deferred — two distinctions worth preserving

**C20-INV-17** (`AIQualificationInsight` has no lifecycle ownership) is covered only by
`test_no_ai_qualification_insight_lifecycle_writer`, which asserts the entity **must not
exist**. That is a WP0 scope guard, not invariant enforcement. `DEFERRED` is correct.

> **WP3 migration note.** This guard will fail **by design** the moment WP3 creates
> `AIQualificationInsight`. It must be *replaced* with real INV-17 enforcement — no status
> field, no transition matrix, no owning transition service — and must **not** be weakened
> or deleted to restore green.

**C20-INV-10** (retry eligibility solely by the §4.3 taxonomy) is **partially enforced**
by `test_retry_classification_preservation`, which locks the classification table in both
Python and PHP. The behavioural half — "zero retry attempts" — cannot be tested until an
`AIJob` retry engine exists. The registry has no `PARTIAL` status, so real coverage is
credited at zero. This is a registry *schema* limitation. Non-blocking; tracked as charter
§8 O3.

---

## 3. Artifact Provenance Issue — `1.9.12-alpha` SHA Mismatch

### 3.1 Finding

**Version `1.9.12-alpha` maps to two distinct artifacts.**

| Commit | Version | Artifact SHA-256 |
| --- | --- | --- |
| `4a7a111` (`phase3c19-freeze`) | 1.9.12-alpha | `E11715D2771ABE82F393B4BD86124329223CDAA2FE37A6EC0CF7FC5B0D3C1218` |
| `c9926cd` | 1.9.12-alpha | `E11715D2771ABE82F393B4BD86124329223CDAA2FE37A6EC0CF7FC5B0D3C1218` |
| **`962a7ae`** | **1.9.12-alpha** | **`1F98150306E9C45CFFC6596CBBA816BDCBD7D5F49986D96FAF3535ADCECE49B4`** |

WP0.4 changed shipped payload — PHP, metadata, and i18n, all inside
`crm-extension/files/` — and rebuilt the artifact **without a version bump**.

At the audit baseline, **6 documents cited `E11715D2` and 0 cited `1F981503`**, including
the C19 freeze checklist, runtime gate summary, and release notes. Installing
"1.9.12-alpha" therefore yields different bytes depending on which commit it is built
from, and the frozen C19 release record silently no longer matches `master`.

### 3.2 Internal integrity is intact

The current artifact is self-consistent — this is a versioning defect, not corruption:

| Check | Result |
| --- | --- |
| `build_release_package.py --check` | PASS |
| Sidecar `.sha256` vs computed | Match |
| ZIP payload vs `crm-extension/files/` | Byte-identical |
| `manifest.json` version vs ZIP manifest | Match |

### 3.3 Relationship to the parity-gate ADR

This is the exact failure described in the UI Runtime Artifact Parity Gate ADR
(**drafted but not yet committed to this repository** — see §8) at §1.2: *"the ZIP carries no provenance… Two ZIPs with the same filename and the same
version can have different contents, and nothing in the artifact reveals which one is
installed."* The `BUILD_INFO` provenance stamp proposed in that ADR §6.3 would have made
this detectable at install time. Tracked for WP4.

### 3.4 Required remedy

Bump to `1.9.13-alpha`: update `manifest.json`, rename artifact and sidecar, perform one
rebuild, and add release notes describing the payload change and its observable
consequence (§4.4). Separately, backfill the `v1.9.12-alpha` tag at `4a7a111` so the C19
freeze artifact remains uniquely addressable — the absence of that tag is what allowed the
collision to pass unnoticed.

---

## 4. Frozen Surface Decision — WP0.4 BridgeError Parity

Full rationale and bounds: `docs/PHASE3C20_CHARTER.md` §7. Summarised here for audit
completeness.

### 4.1 The defect WP0.4 closed

`BridgeErrorClass` lacked `RATE_LIMIT`, while the connector provider contract could
produce it and `SendExecution.failureCategory` could store it. The result was **hard
ingress rejection**, not graceful degradation: `SendExecutionBridgeResult` threw
`BridgeRejectionException('Unknown error class: RATE_LIMIT')` at construction, and
`SendExecutionResultAdapterService::failureCategory()` threw again. The `SendExecution`
received no terminal result, remained in its prior state, and never appeared in the
`c18FailedSend` queue. A live taxonomy break, not a cosmetic gap.

### 4.2 Changes made

`BridgeErrorClass.php` gained `RATE_LIMIT`, `QUOTA`, `CONTENT_FILTER` plus
`isAutoRetryEligible()`; both bridge adapters gained three translation-map entries each;
`entityDefs/SendExecution.json` widened `failureCategory`; i18n gained two labels; the
connector failure taxonomy gained the matching classes.

### 4.3 Why this is not a lifecycle change

ADR §10 excludes changes to *"C19-frozen lifecycle **services, guards, or action keys**."*
Verified at `962a7ae`:

| Surface | Changes |
| --- | --- |
| `Services/SendExecutionTransitionService.php` — transition owner | **0** |
| `Hooks/SendExecution/SendExecutionStatusMutationGuard.php` — persistence guard | **0** |
| `Resources/metadata/app/prospectingWorkflow.json` — action keys | **0** |

`BridgeErrorClass` is a value object — a `final class` of constants with `values()` and a
pure predicate; it owns no state, performs no persistence, and participates in no
transition. Both adapter changes are additional entries in a constant
`errorClass → failureCategory` map with no control flow altered. The `entityDefs` change
widens an accepted-value set without adding, removing, renaming, or retyping a field.

**The lifecycle answers whether a record may move from state A to state B and who may
authorize it. The taxonomy answers how an already-occurred failure is classified. WP0.4
changed only the second.** Every `SendExecution` status write still passes through
`SendExecutionTransitionService` under `SendExecutionStatusMutationGuard`, authorized by
unchanged action keys.

### 4.4 Retry ownership and observable consequence

Both `isAutoRetryEligible()` helpers classify only. Contract-enforced: the PHP helper must
reference no `SendExecutionTransitionService` and introduce no `nextRetryAt`. Retry
scheduling remains connector-side. Eligible: `NETWORK`, `PROVIDER`, `RATE_LIMIT`. Not
eligible: `AUTH`, `VALIDATION`, `UNKNOWN`, `QUOTA`, `CONTENT_FILTER`.

**Consequence to state in release notes:** failures previously rejected at the bridge now
persist as `FAILED` with the corresponding category. Operators will see failures that were
previously invisible, and `c18FailedSend` counts will rise. This is hidden failure becoming
visible, not a regression.

### 4.5 Bounds

This decision authorizes **additive value-object and enum widening only**. It does not
authorize changes to transition services, mutation guards, action keys, transition
matrices, ACL, or any *narrowing* of an accepted-value set. Narrowing is breaking and
requires a separate ADR.

---

## 5. Blockers

Status as at the audit baseline `962a7ae`, with current disposition.

| ID | Blocker | Severity | Disposition |
| --- | --- | --- | --- |
| **B1** | **`1.9.12-alpha` maps to two artifacts.** Payload changed without a version bump; 6 documents cite the superseded hash, 0 cited the current one. | **HIGH** | **OPEN.** Requires the `1.9.13-alpha` bump (§3.4). |
| **B2** | **Frozen-surface change had no paper trail.** WP0.4 modified `entityDefs/SendExecution.json`, `BridgeErrorClass`, and two adapters with no charter, no ADR decision-log entry, and no resolution of the §10 exclusion ambiguity. | MEDIUM | **Resolved** by `docs/PHASE3C20_CHARTER.md` §7 and ADR §14. |
| **B3** | **No C20 charter existed.** Every prior phase had one. WP0 had no artifact defining scope, exit gates, or decisions. | MEDIUM | **Resolved** by `docs/PHASE3C20_CHARTER.md`. |
| **B4** | **Registry alignment uncommitted.** `master` still reported INV-03 and INV-18 as `DEFERRED`. | MECHANICAL | **Resolved** when the C1 alignment lands. |

**Additional finding:** the ADR's closing statement read *"WP0 documentation only — no
runtime, code, metadata, test, or artifact changes"* while the WP0 commit made all five.
Corrected; execution recorded in ADR §14.

### Non-blocking, tracked in charter §8

O2 `BOUNDARIES.md` §2/§3 stale · O3 INV-10 partial-coverage credit · O4 INV-17 WP3
migration note · O5 INV-18 hardcoded guard scope · O6 C19 debt (charter WP1.5 row,
Workbench retro-charter) · O7 `v1.9.12-alpha` tag never applied · O8 ADR §11.1
ratification (gates WP2 only).

---

## 6. Recommended Commit Order

| # | Commit | Content | Closes |
| --- | --- | --- | --- |
| **C1** | `phase3c20: persist WP0 governance evidence (registry alignment + charter + ADR §14)` | Registry INV-03/18 ACTIVE 9/13; charter; freeze readiness report; ADR §14 | B2, B3, B4 |
| **C3** | `phase3c20: bump release line to 1.9.13-alpha` | `manifest.json`; rename artifact + sidecar; **one** rebuild; `RELEASE_NOTES_1.9.13-alpha.md` including the §4.4 visibility change | **B1** |
| **C4** | `phase3c20: record WP0 deferral and coverage notes` | INV-17 WP3 migration note; INV-18 dynamic-coverage requirement; INV-10 partial-coverage credit | O3, O4, O5 |
| **C5** | `phase3c20: refresh BOUNDARIES and close C19 documentation debt` | `BOUNDARIES.md` §2/§3; charter WP1.5 row; Workbench retro-charter | O2, O6 |
| **C6** | `phase3c20: tag WP0 exit` | Tag `v1.9.13-alpha` + `phase3c20-wp0-exit` on one commit per convention; backfill `v1.9.12-alpha` at `4a7a111` | O7 |

**Critical path: C1 (this package) → C3.** C4 and C5 may run in parallel; C6 last.

**WP1 should not begin before C3.** C1, C4, and C5 do not gate implementation, but
starting WP1 while one version string maps to two artifacts means the first WP1 build
inherits an ambiguous baseline — which is precisely what WP0 existed to prevent.

After C3, re-verify: `build_release_package.py --check`, sidecar match, source↔ZIP byte
parity, and `pytest -q`. That is the WP0 exit gate per charter §5.

---

## 7. Verdict as at `962a7ae`

**BLOCKED** — on B1 (artifact provenance / version bump still pending).

B2, B3, and B4 are addressed by the governance-evidence package that lands this report,
the charter, ADR §14, and registry alignment (ACTIVE 9 / DEFERRED 13).

The engineering was sound: **571 passing tests** with zero failures, an internally
consistent artifact, a structurally correct 22-row registry, and two guards demonstrably
firing. Remaining blocker B1 is release hygiene, not defective code.

---

## 8. Related

- `docs/PHASE3C20_CHARTER.md`
- `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` (§8 invariants, §14 execution record)
- `docs/adr/C20_INVARIANT_REGISTRY.md`
- UI Runtime Artifact Parity Gate ADR — **drafted, not committed.** Intended path
  `docs/architecture/ADR_UI_RUNTIME_ARTIFACT_PARITY_GATE.md`. Its §6.3 `BUILD_INFO`
  provenance stamp would have made the §3 collision detectable at install time.
  Committing it is an open action.
- `docs/PHASE3C19_FREEZE_CHECKLIST.md` (cites the superseded `E11715D2` artifact)
- `AGENTS.md` / `CLAUDE.md`, `docs/architecture/BOUNDARIES.md`

---

*Audit record. Documentation only — no runtime, PHP, metadata, connector, or artifact
changes are made by this document.*
