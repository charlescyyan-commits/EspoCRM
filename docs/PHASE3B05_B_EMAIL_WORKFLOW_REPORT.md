# Phase3B05-B — CRM Email Workflow Report

**Date:** 2026-07-12  
**Workspace:** `D:\EspoCRM-Production`  
**Extension:** Chitu Prospecting Integration `1.5.1-alpha`  
**Runtime:** local EspoCRM-Test Docker stack  
**Status:** **PASS**  
**Depends on:** Phase3B05-A `EmailEvent` + Brevo ingest API  
**Boundary:** EspoCRM owns CRM lifecycle/tasks; Brevo owns send/events; Chitu owns research/email generation. Brevo connector package and EmailEvent contract unchanged. LearningSignal untouched.

---

## 1. Lifecycle Design

Conceptual outreach lifecycle (CRM interpretation):

```text
DRAFT_READY → APPROVED → SENT → DELIVERED → OPENED → CLICKED → REPLIED → FOLLOW_UP
                                                              ↘ BOUNCED
```

| State | Meaning in CRM |
|---|---|
| `DRAFT_READY` | Chitu draft ready (existing `peEmailStatus`; not produced by Brevo events) |
| `APPROVED` | Ready for send (Chitu/lifecycle sync; not Brevo) |
| `SENT` | Brevo accepted/sent execution recorded |
| `DELIVERED` | Provider delivery confirmed; stored on `EmailEvent`; Lead coarse enum stays `SENT` |
| `OPENED` | Engagement open; recorded on `EmailEvent` only — **no sales-status change** |
| `CLICKED` | Engagement click; recorded only — **no sales-status change** |
| `REPLIED` | Customer reply; Lead `peEmailStatus/peEmailReplyStatus=REPLIED` + follow-up Task |
| `FOLLOW_UP` | Represented by native Task `Follow up customer reply` (not a new `peEmailStatus` option) |
| `BOUNCED` | Hard/soft bounce; Lead `peEmailStatus=BOUNCED` + verify-email Task |

**Compatibility:** Lead fields `peEmailStatus`, `peLastEmailDate`, `peEmailReplyStatus` remain the Phase3A27 enum/types. No EmailEvent field/API contract changes. DELIVERED/OPENED/CLICKED stay on `EmailEvent.eventType`.

---

## 2. Workflow Rules

Implemented in `Espo\Custom\Hooks\EmailEvent\EmailEventWorkflowHook` (after-save, new EmailEvent only).

Ingest path: Brevo connector → `POST /Prospecting/brevo/email-event` → create `EmailEvent` → hook runs CRM rules.

`BrevoEmailEventSyncService` now **only** appends EmailEvent (idempotent). Lead projection moved to the hook so manual/API creates share one workflow owner.

| Rule | Trigger | Lead actions | Task |
|---|---|---|---|
| 1 | `EmailEvent.eventType=SENT` | `peEmailStatus=SENT` (unless already REPLIED/BOUNCED), update `peLastEmailDate` / campaign | — |
| 2 | `REPLIED` | `peEmailStatus=REPLIED`, `peEmailReplyStatus=REPLIED`, timestamps | **Follow up customer reply** |
| 3 | `BOUNCED` | `peEmailStatus=BOUNCED`, `peEmailReplyStatus=BOUNCED`, timestamps | **Verify customer email** |
| 4 | `OPENED` (and `CLICKED`) | Record event; refresh timestamps/campaign only; **do not** change `peEmailStatus` | — |

`DELIVERED` keeps coarse Lead status at `SENT` (enum has no DELIVERED) while appending the EmailEvent row.

---

## 3. Task Automation

Uses native EspoCRM **Task** only (no custom task entity).

| Event | Task name | Parent | Notes |
|---|---|---|---|
| REPLIED | `Follow up customer reply` | Lead | Priority High; status Not Started; deduped if open task with same name exists |
| BOUNCED | `Verify customer email` | Lead | Priority High; status Not Started; same dedupe |

OPENED creates **zero** tasks (validated).

Lead UI: `clientDefs.Lead.relationshipPanels.tasks` + existing `emailEvents` panel.

---

## 4. ACL

Provisioning: `deployment/provisioning/phase3b05b_provision_email_workflow_roles.php`

| Role | EmailEvent | Task |
|---|---|---|
| Admin | full | full |
| Sales User | read own | create/read/edit/delete own |
| Research User | read all | read own only |
| Integration Bot | create/read/edit (no delete) — sync only | no Task access |

Disposable API user for validation: `phase3b05b_workflow_test` (removed after tests).

---

## 5. Validation

| Check | Result | Evidence |
|---|---|---|
| Extension build | PASS | `prospecting-extension-1.5.1-alpha.zip`; SHA-256 `8AC6EE0DE4F9E3205EFEEE40BEE29511BC18AA95FCC85634A42757B34BFD69D0` |
| Install / rebuild / cache clear | PASS | Installed `1.5.1-alpha`; rebuild; clear-cache; hook present |
| Extension regression | PASS | `31` tests OK |
| Connector regression | PASS | `45` tests OK — **Brevo connector package unmodified** |
| SENT → Lead SENT | PASS | API create SENT; workflow sets status |
| OPENED → no sales-status change | PASS | After SENT+OPENED, `peEmailStatus=SENT`, tasks=0 |
| REPLIED → Task | PASS | Task `Follow up customer reply` created |
| BOUNCED → status + Task | PASS | Final `peEmailStatus=BOUNCED`; Task `Verify customer email` |
| Lead EmailEvent / Task panels metadata | PASS | `PANEL_emailEvents=yes`, `PANEL_tasks=yes` |
| Browser click-through | DEFERRED | Localhost browser policy; ORM + panels verified |
| Cleanup | PASS | Test leads/events/tasks/user removed |

---

## 6. Limitations

1. EspoCRM does not send mail; workflow reacts to EmailEvent only.
2. `FOLLOW_UP` is a Task, not a new `peEmailStatus` enum value (keeps Phase3A27/Chitu lifecycle sync compatible).
3. `DELIVERED`/`OPENED`/`CLICKED` history is on EmailEvent; Lead summary enum remains coarse.
4. Local Docker validation only; browser panel visual confirmation optional.
5. LearningSignal / Phase3B04 feedback contract unchanged.

---

## 7. Files

- `files/custom/Espo/Custom/Hooks/EmailEvent/EmailEventWorkflowHook.php` (new)
- `Services/BrevoEmailEventSyncService.php` (projection removed; hook owns CRM updates)
- `metadata/clientDefs/Lead.json` (tasks panel)
- `manifest.json` → `1.5.1-alpha`
- `deployment/prospecting-extension-1.5.1-alpha.zip`
- `deployment/provisioning/phase3b05b_*.php`
- Extension tests updated; connector sources untouched

---

**Phase3B05-B complete. Status: PASS.**

Do **not** enter Phase3B05-C without explicit authorization.
