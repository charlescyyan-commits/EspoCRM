# Phase3C20 RT-WP2 Implementation Authorization

| Field | Value |
| --- | --- |
| Document type | RT-WP2 implementation authorization evidence record |
| Date | 2026-08-03 |
| Authorization state | **AUTHORIZED WITH CONDITIONS** (recorded, not re-granted) |
| Recorded by | RT-WP2 Implementation Foundation Review |
| Governing baseline | `928aa5f734f8d7f643cdb45a7549fed7ada0c400`; RT-WP0 exit `7846f6f5c3d33ecfe161cbe2099521ab00bac365`; RT-WP1 exit `8f11ee4578d4626fa3ae950c9645b4cbcfc6befd` |
| Charter tag | `phase3c20-rt-wp2-charter-ratified` → `16a30af4dd872094d23c6ac147bcec0b22a6380a` |
| Implementation | **NOT STARTED** — this record authorizes nothing beyond the stated policy scope |

```text
This record documents the already-existing RT-WP2 implementation authorization
(AUTHORIZED WITH CONDITIONS). It does not re-grant, expand, or interpret that
authorization beyond the boundaries stated in the ratified RT-WP2 Charter and
the Implementation Plan.
```

## 1. Purpose

This document is the authorization evidence required by the RT-WP2
Implementation Foundation Review, gate R1 (Runtime Charter §21). It records
that RT-WP2 implementation is separately authorized with conditions, and it
records those conditions. It follows the RT-WP1 precedent of recording an
implementation authorization as a dedicated audit document
(`docs/audit/PHASE3C20_RT_WP1_IMPLEMENTATION_AUTHORIZATION.md`).

## 2. Verification evidence

| Check | Result |
| --- | --- |
| Local HEAD | `16a30af4dd872094d23c6ac147bcec0b22a6380a` |
| Charter tag `phase3c20-rt-wp2-charter-ratified` | Present; peels to `16a30af4dd872094d23c6ac147bcec0b22a6380a` (HEAD) |
| RT-WP2 Implementation Charter | RATIFIED (`docs/PHASE3C20_RT_WP2_IMPLEMENTATION_CHARTER.md`) |
| RT-WP2 Implementation Plan | PASS WITH INFORMATIONAL NOTES (`docs/PHASE3C20_RT_WP2_IMPLEMENTATION_PLAN.md`, `docs/audit/PHASE3C20_RT_WP2_IMPLEMENTATION_PLAN_REVIEW.md`) |
| RT-WP2 Foundation Review | READY FOR IMPLEMENTATION (`docs/audit/PHASE3C20_RT_WP2_IMPLEMENTATION_FOUNDATION_REVIEW.md`) |
| RT-WP0 / RT-WP1 | EXITED / EXITED |
| C25 WP2.2 | NO GO |

## 3. Authorized scope (conditions — allowed)

Implementation is authorized strictly for the following policy surfaces, and
nothing else:

| # | Allowed surface | Boundary |
| --- | --- | --- |
| 1 | **ProviderBinding policy entity** | CRM policy representation of one authorized provider candidate; determines eligibility only |
| 2 | **Purpose registration contract** | Governed, namespaced registration and validation of business/use-case identifiers |
| 3 | **Capability mapping** | Every registered purpose maps to exactly one of the four existing `CompletionCapability` values |
| 4 | **Eligibility classification** | Deterministic, non-secret classification of a supplied candidate (`BOUND`, `UNBOUND`, `DISABLED`, `PURPOSE_NOT_REGISTERED`, `CAPABILITY_MISMATCH`, `CREDENTIAL_REFERENCE_MISSING`, `NOT_AUTHORIZED`) |
| 5 | **Credential reference provenance** | Reference-only custody plus configuration-change provenance; never a secret or an execution ledger |

```text
ProviderBinding is policy, not execution.
Purpose is explicit registration, not capability.
Capability is the four-value fixed portfolio.
Credential is reference only.
```

## 4. Conditions — forbidden scope

Implementation must not contain or assume any of the following:

| # | Forbidden surface | Condition |
| --- | --- | --- |
| 1 | Provider execution | No provider invocation, adapter construction, transport construction, or model call |
| 2 | Dispatch | No dispatch orchestration; no `allowed_provider_bindings` runtime hand-off to a caller |
| 3 | Retry | No retry classification, scheduling, backoff, or executor |
| 4 | Reservation | No idempotency reservation, lease, attempt claim, or concurrency control |
| 5 | Secret custody | No secret resolution, decryption, plaintext, header, session, or secret export; `credentialReference` only |
| 6 | C25 runtime | No `CommercialBrief` creation, mutation, consumption, registration, or provider binding |
| 7 | Adapter / connector change | No change to any `chitu_connector` source or adapter |
| 8 | Queue / worker / job | No `Jobs/`, `Api/`, `Controllers/`, scheduler, or background work |
| 9 | Execution lifecycle | No `AIJob`, `AIRequestLog`, `PromptTemplate`, `ProviderCredential` mutation; binding `DRAFT/ACTIVE/DISABLED/REVOKED` is configuration state only |
| 10 | Invariant activation | No `C20_INVARIANT_REGISTRY.md` status change; INV-02/03 ACTIVE unchanged; INV-04–13 DEFERRED unchanged |
| 11 | Capability portfolio | No fifth enum member; `COMMERCIAL_BRIEF` not a capability; `commercial_brief_generation` not registered |
| 12 | Parallel authorization | No authorization outside verified EspoCRM ACL, WorkflowAuthorization, or a verified system-configuration boundary |
| 13 | C25 workspace | No C25 workspace, UI, route, or provider ownership |

## 5. Implementation file allowlist

Implementation is limited to the exact 15-row allowlist ratified by the
Foundation Review (decision #16) and recorded in the Implementation Plan §11.
The allowlist derives from Runtime Charter §28 RT-WP2 rows; one row
(`Services/ProviderBindingMutationSaveOption.php`) is ratified at the
Foundation Review as a coordinated part of the save-option/guard mechanism for
the authorized policy surface (Runtime Charter §21.1 decisions #13 and #16).
This is an allowlist ratification within the already-authorized policy scope;
it is not a new authorization.

## 6. Conditions sequence and gates

Implementation begins only after all of the following hold:

1. This authorization record exists (satisfied).
2. RT-WP2 Foundation Review verdict is READY FOR IMPLEMENTATION (satisfied).
3. The 15-row implementation allowlist is ratified (satisfied at Foundation Review).
4. Each implementation step stays within the allowed scope of §3 and outside every forbidden surface of §4.
5. Independent implementation review PASS is obtained before any exit claim.
6. Commit/push/tag occur only under a separate, explicit authorization.

## 7. Non-expansion statement

```text
This record does not authorize RT-WP3–RT-WP8.
This record does not authorize runtime code outside the RT-WP2 allowlist.
This record does not authorize invariant activation.
This record does not authorize C25 WP2.2.
This record does not authorize commit, push, or tag.
```

## 8. Authorization state log

| Field | Value |
| --- | --- |
| Date | 2026-08-03 |
| Event | RT-WP2 implementation authorization recorded at the Foundation Gate |
| State | RT-WP2 Implementation: AUTHORIZED WITH CONDITIONS |
| Implementation | NOT STARTED → READY TO START (after Foundation Review PASS) |
| Effect | Authorization evidence now exists; conditions recorded |
| Non-effect | No new scope, no expanded allowlist beyond §5, no runtime code, no C25 release |

## 9. References

1. `docs/PHASE3C20_RT_WP2_IMPLEMENTATION_CHARTER.md`
2. `docs/PHASE3C20_RT_WP2_IMPLEMENTATION_PLAN.md`
3. `docs/audit/PHASE3C20_RT_WP2_IMPLEMENTATION_PLAN_REVIEW.md`
4. `docs/audit/PHASE3C20_RT_WP2_IMPLEMENTATION_FOUNDATION_REVIEW.md`
5. `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md`
6. `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
7. `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md`
8. `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md`
9. `docs/adr/C20_INVARIANT_REGISTRY.md`
10. `docs/audit/PHASE3C20_RT_WP1_IMPLEMENTATION_AUTHORIZATION.md` (precedent)

*This record creates no code, modifies no metadata, creates no entity, modifies
no test, and performs no commit, push, or tag.*
