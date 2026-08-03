# Phase3C20 RT-WP3 Implementation Authorization

| Field | Value |
| --- | --- |
| Document type | RT-WP3 Lite implementation authorization evidence record |
| Date | 2026-08-03 |
| Authorization state | **AUTHORIZED WITH CONDITIONS** |
| Governing baseline | `928aa5f734f8d7f643cdb45a7549fed7ada0c400` |
| RT-WP2 completion | `phase3c20-rt-wp2-implementation-completed` → `b167275757f7a404ff8b4c09f037a63610bce142` |
| Charter tag | `phase3c20-rt-wp3-charter-ratified` → `12ec8a86ce3adc1a04f94b600f5926a301793eb7` |
| Scope class | Dispatch Foundation Lite + Runtime Guards Lite only |
| Implementation | **NOT STARTED** — code begins only after Foundation Review PASS |

```text
This record documents RT-WP3 implementation authorization
(AUTHORIZED WITH CONDITIONS) for Lite / Foundation scope only.
It does not authorize full Runtime Charter §22 exit, connector outbound,
AIRequestLog producer, Jobs/Api worker paths, RT-WP4–RT-WP8, or C25.
```

---

## 1. Purpose

Record the separately issued RT-WP3 implementation authorization and its
conditions so the Foundation Gate can ratify an exact file allowlist and
release Lite implementation.

---

## 2. Verification evidence

| Check | Result |
| --- | --- |
| Local HEAD | `12ec8a86ce3adc1a04f94b600f5926a301793eb7` |
| Charter tag `phase3c20-rt-wp3-charter-ratified` | Present; peels to HEAD |
| RT-WP3 Implementation Charter | RATIFIED |
| Independent Charter Review | PASS WITH INFORMATIONAL NOTES |
| RT-WP3 Implementation Plan | Present; Lite-scoped |
| Independent Plan Review | PASS WITH INFORMATIONAL NOTES |
| RT-WP0 / RT-WP1 | EXITED / EXITED |
| RT-WP2 | COMPLETED + TAGGED |
| C25 WP2.2 | NO GO |

---

## 3. Authorized scope (conditions — allowed)

| # | Allowed surface | Boundary |
| --- | --- | --- |
| 1 | Dispatch request contract | Request identity + purpose/capability/binding/provenance references; no execution |
| 2 | Purpose validation | Registered purpose only; fail-closed; no inference |
| 3 | Capability resolution | Exactly four `CompletionCapability` values |
| 4 | ProviderBinding lookup | Read/consume RT-WP2 policy only |
| 5 | Eligibility validation | Policy classifications only; no job/queue/retry state |
| 6 | Execution boundary assembly | References-only boundary object; stop before invoke |
| 7 | Runtime Guards Lite | Reject invalid capability; `COMMERCIAL_BRIEF`; missing binding; secret-shaped input |

```text
Dispatch Foundation Lite + Runtime Guards Lite only.
```

---

## 4. Conditions — forbidden scope

| # | Forbidden surface | Condition |
| --- | --- | --- |
| 1 | Provider execution | No provider invocation, adapter, transport, or model call |
| 2 | Connector call / HTTP egress | No `ConnectorBoundary.execute`; no CRM provider HTTP |
| 3 | Retry / reservation / queue / worker | No RT-WP5/RT-WP6 surfaces; no `Jobs/AIDispatchWorker` |
| 4 | API outbound execution | No outbound execution Api/routes in Lite |
| 5 | AIRequestLog outbound producer | No INV-08 / §22 exit claim |
| 6 | ProviderBinding mutation | No create/update/delete of ProviderBinding; consume only |
| 7 | Secret custody | No secret resolution, token handling, credential access, provider authentication |
| 8 | Capability portfolio change | No fifth enum; `COMMERCIAL_BRIEF` not a capability |
| 9 | C25 runtime | No CommercialBrief / Opportunity / sales lifecycle authority |
| 10 | Invariant activation | INV-02/03 ACTIVE unchanged; INV-04–13 DEFERRED unchanged |
| 11 | RT-WP4 / RT-WP5 / RT-WP6 / RT-WP8 | Deferred |
| 12 | RT-WP7 full guard/activation system | Deferred; Lite guards only |
| 13 | Commit / push / tag | Separate later authorization only |

---

## 5. Exact file allowlist

Exact allowlist is **ratified by the Foundation Review**, not by this record
alone. This authorization constrains that allowlist to CRM service / DTO /
guards / tests under Lite scope and forbids Connector, `CompletionCapability`,
ProviderBinding mutation, and C25 files.

---

## 6. Gate sequence

1. This authorization record exists.
2. Foundation Review PASS with exact allowlist.
3. Implementation stays inside allowed scope (§3) and outside forbidden (§4).
4. Independent Implementation Review PASS before any exit claim.
5. Commit / push / tag only under separate explicit authorization.

---

## 7. Non-expansion statement

```text
This record does not authorize full RT-WP3 §22 exit.
This record does not authorize RT-WP4–RT-WP8.
This record does not authorize Runtime Code outside the Foundation allowlist.
This record does not authorize invariant activation.
This record does not authorize C25 WP2.2.
This record does not authorize commit, push, or tag.
```

---

## 8. Authorization state

| Item | Status |
| --- | --- |
| RT-WP3 Charter | RATIFIED |
| RT-WP3 Implementation | AUTHORIZED WITH CONDITIONS (Lite) |
| Exact file allowlist | Foundation Review ownership |
| Runtime code | NOT STARTED |
| C25 WP2.2 | NO GO |

*Authorization evidence only. No code, metadata, test, commit, push, or tag.*
