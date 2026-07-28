# Phase3C20 WP1.3.3 — Runtime Verification Closure

## 1. Status

**Status:** PASS WITH BLOCKER
**Phase:** Phase3C20 WP1.3.3
**Type:** Verification closure — documentation only

This document records the runtime verification pass for WP1.3.3. It records
observed behaviour, gate findings, and the intentional decision that
ProviderCredential remains metadata-only. No code, configuration, test,
artifact, or metadata change accompanies this closure.

## 2. Baseline

- **Branch:** `master`
- **Baseline commit:** `87f636a` — *phase3c20-wp1.3.2: add ProviderCredential layout
  and i18n surface*
- **Commit chain:**
  - `6c97c94` phase3c20-wp1.3.1: add AI Platform credentials administration surface
  - `1692eb4` phase3c20-wp1.2.4: verify ProviderCredential security gate
  - `8406741` phase3c20-wp1.2.3: enforce ProviderCredential custody contract
  - `3f126aa` phase3c20-wp1.2.2: add ProviderCredential ACL metadata boundary

## 3. Verification Scope

The WP1.3.3 runtime verification pass examined:

- ProviderCredential ACL boundary enforcement at runtime
- `credentialReference` write-only field behaviour
- Frontend direct-route access patterns
- Administration surface availability and routing
- i18n label surface completeness

The pass was a **runtime-behaviour verification**, not a code-review or
static-analysis pass. Every finding reflects observed system behaviour at
baseline `87f636a`.

## 4. Passed Runtime Checks

The following checks passed at runtime:

| # | Check | Result |
|---|-------|--------|
| 1 | Administration → AI Platform menu entry renders | PASS |
| 2 | ProviderCredential list view loads without error | PASS |
| 3 | ProviderCredential detail view renders field layout | PASS |
| 4 | ACL metadata boundary denies unauthorised read access | PASS |
| 5 | ACL metadata boundary denies unauthorised write access | PASS |
| 6 | i18n labels resolve for all visible UI surfaces | PASS |
| 7 | `credentialReference` field is not returned in read payloads | PASS |
| 8 | `credentialReference` write is accepted via API | PASS |
| 9 | Layout definitions load from metadata without error | PASS |
| 10 | No JavaScript console errors on administration surfaces | PASS |

## 5. ACL Findings

The ProviderCredential ACL boundary, defined in WP1.2.2 and enforced in WP1.2.3,
was verified at runtime:

- **Read gate:** Non-admin users receive an access-denied response when
  requesting ProviderCredential records. The gate is enforced at the ACL layer,
  not delegated to controller-level guards.
- **Write gate:** Non-admin users receive an access-denied response when
  attempting create, update, or delete operations on ProviderCredential records.
- **Scope enforcement:** The ACL boundary is applied uniformly across list, view,
  edit, and delete operations.

No ACL bypass was observed.

## 6. credentialReference Write-Only Behaviour

The `credentialReference` field follows the custody contract established in the
WP1.0 Skeleton Charter:

- **Read (GET):** `credentialReference` is excluded from API responses. The field
  is not present in list or detail payloads.
- **Write (POST/PUT):** `credentialReference` is accepted. The value is persisted
  but never surfaced in read responses.
- **Listing:** No record in the list view exposes `credentialReference` content.

This behaviour is intentional and matches the reference-only custody model: the
system stores a credential reference for administrative tracking but does not
expose it through any read path.

## 7. Frontend Direct Route Limitation

A direct browser navigation to a ProviderCredential frontend route (e.g.,
`#Admin/aiproPlatformProviderCredential`) without first loading the
administration panel does **not** render the credential management interface.

This is a **known and intentional limitation**:

- The administration panel loads its sub-routes through a parent controller that
  initialises the AIPlatform module context.
- A direct route hit bypasses that initialisation, so the sub-route router does
  not resolve the target view.
- This is consistent with how other administration sub-panels behave in EspoCRM.

**Decision:** Direct UI route is intentionally unsupported. The supported entry
point is **Administration → AI Platform → Credentials**.

## 8. Decision Record

**ProviderCredential remains metadata-only.**

ProviderCredential is a reference-only administrative custody surface. It stores
externally held credential references with no runtime provider execution, no
secret material, no background jobs, and no integration ports.

The following are explicitly **out of scope** for WP1:

- A credential create/edit form in the administration UI
- A credential activation/deactivation lifecycle
- A credential rotation workflow
- Provider credential validation against an external API
- Health-check or connectivity probes using stored credential references

## 9. Final Status

**PASS WITH BLOCKER**

| Criterion | Verdict |
|-----------|---------|
| ACL boundary enforcement | PASS |
| credentialReference write-only contract | PASS |
| Layout and i18n surface | PASS |
| Frontend direct route | PASS (intentionally unsupported) |
| Controlled admin custody UI | **BLOCKER** (requires separate approved WP) |

The **single blocker** is the absence of a controlled administration UI for
credential custody. The metadata surface, ACL gates, and i18n labels are all in
place and verified — but there is no create/edit form for an administrator to
manage ProviderCredential records through the UI.

This blocker is **accepted and deferred**: it requires a separate approved work
package with its own scope, design, and security review. WP1 intentionally
stopped at the metadata and ACL boundary; a custody UI was never part of WP1
scope.

## 10. Future Work

`Controlled admin custody UI` requires a separate approved WP. That WP must
address at minimum:

- A create/edit form in **Administration → AI Platform → Credentials**
- Field-level validation for `providerKey`, `environment`, and `displayName`
- `credentialReference` write-only entry with no read-back exposure
- `fingerprint` generation on credential write
- `lastFour` externally-supplied-only constraint enforcement
- `rotationDueAt` / `lastRotatedAt` date pickers
- ACL-gated access consistent with the existing metadata boundary
- Audit-log entries for credential create, update, and delete operations

Until that WP is approved and executed, ProviderCredential records must be
managed through the API or direct database operations by an authorised
administrator.
