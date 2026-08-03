# Phase3C20 RT-WP5 Implementation Authorization

| Field | Value |
| --- | --- |
| Document type | RT-WP5 Lite implementation authorization + Foundation allowlist record |
| Date | 2026-08-03 |
| Authorization state | **AUTHORIZED WITH CONDITIONS** + Foundation **READY FOR IMPLEMENTATION** |
| Charter commit | `a2e47aa7deed6d4f4b1762cde4f07d18445256e7` |
| Charter path | `docs/PHASE3C20_RT_WP5_IMPLEMENTATION_CHARTER.md` |
| Independent charter review | `docs/audit/PHASE3C20_RT_WP5_IMPLEMENTATION_CHARTER_REVIEW.md` (PASS / RATIFIED) |
| Plan review | PASS WITH INFORMATIONAL NOTES |
| Foundation review | `docs/audit/PHASE3C20_RT_WP5_IMPLEMENTATION_FOUNDATION_REVIEW.md` (**READY FOR IMPLEMENTATION**) |
| Scope class | Failure Metadata Foundation Lite only |

```text
This record documents RT-WP5 Lite implementation authorization
(AUTHORIZED WITH CONDITIONS) and the Foundation-ratified exact file allowlist.
It does not authorize full Runtime Charter §24 retry classification/executor,
RT-WP6–RT-WP8, connector outbound, Jobs/queue, retry/recovery, or C25.
```

---

## 1. Authorized scope (conditions — allowed)

| # | Allowed surface |
| --- | --- |
| 1 | Failure vocabulary (five foundation codes) |
| 2 | Failure classification (metadata-only, fail-closed) |
| 3 | Failure metadata contract (logical non-secret fields) |
| 4 | Audit representation (non-secret, reviewable) |
| 5 | Correlation with RT-WP4 Lite terminal states (`FAILED` / `BLOCKED`) |

```text
Failure Metadata Foundation Lite only.
Not a failure execution system.
Not a retry engine.
```

---

## 2. Forbidden scope (conditions — not authorized)

Retry, recovery, retry count/policy/schedule, queue, worker, scheduler,
reservation, provider error execution, connector changes, HTTP outbound,
AIJob lifecycle mutation, C25 / Opportunity / sales authority, secret
handling, credential resolution, INV-10 activation, full §24 executor.

---

## 3. Exact file allowlist (Foundation ratified)

Base prefix: `crm-extension/files/custom/Espo/Modules/AIPlatform/`

| # | Path | Purpose |
| --- | --- | --- |
| 1 | `Services/AIFailureMetadata.php` | Five-code vocabulary |
| 2 | `Services/AIFailureMetadataService.php` | Record / classify / correlate / audit representation |
| 3 | `Services/AIFailureMetadataGuard.php` | Fail-closed validation |
| 4 | `crm-extension/tests/test_phase3c20_rt_wp5_failure_metadata.py` | Contract + isolation + regression |

**Allowlist count:** exactly **4** rows.

Persistence: **service-owned in-memory / returned record contract** only.
No entityDefs / AIJob field attachment in this allowlist.

Secondary eight-value C20 taxonomy annotation: **excluded** from this Lite
allowlist.

---

## 4. Security rules

| Rule | Required |
| --- | --- |
| No secrets in metadata / logs / fixtures | Yes |
| No credential resolution | Yes |
| No provider authentication | Yes |
| No CRM provider HTTP (C20-INV-03) | Yes |
| No Connector / adapter invoke | Yes |
| No retry / recovery side effects | Yes |

---

## 5. Invariant status

```text
C20-INV-02 ACTIVE
C20-INV-03 ACTIVE
C20-INV-04–13 DEFERRED
```

---

## 6. Authorization state

| Item | Status |
| --- | --- |
| RT-WP5 Lite Charter | RATIFIED |
| RT-WP5 Lite Implementation Authorization | AUTHORIZED WITH CONDITIONS |
| Exact file allowlist | **FOUNDATION RATIFIED (4 rows)** |
| Foundation Review | READY FOR IMPLEMENTATION |
| Runtime code | Authorized to implement **within allowlist only** after this gate |
| Full §24 Retry Executor | NOT AUTHORIZED |
| RT-WP6–RT-WP8 | NOT AUTHORIZED |
| C25 WP2.2 | NO GO |

*Authorization + Foundation allowlist evidence. Implementation must stay inside §3.*
