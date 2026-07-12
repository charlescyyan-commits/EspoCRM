# Phase 3A-2.4 Final Report — Synthetic Sync Rollback Complete

**Date:** 2026-07-11  
**Scope:** Final rollback verification after Lead `delete=all` grant  
**New Lead created this run:** NO  
**Extension / auth logic / ACL modified by agent:** NO  
**Non-synthetic data touched:** NO

## Final Checklist

```text
CREATE   PASS
VERIFY   PASS
ROLLBACK PASS
```

## 1. Runtime Environment

| Item | Value |
|---|---|
| CWD | `D:\Chitu-intelligence` |
| Target | `http://localhost:8080` |
| Client | Existing `LocalEspoCRMClient` |
| API user | `chitu_ai_connector` |
| `ESPOCRM_TEST_ENV` | `true` |
| API key | present (not printed) |

## 2. Authentication — PASS

| Step | Result |
|---|---|
| `authenticate()` | PASS |
| `GET /api/v1/App/user` | PASS |

### ACL at final run

| Scope | create | read | edit | delete |
|---|---|---|---|---|
| Lead | yes | all | all | **all** |
| ResearchEvidence | yes | all | all | **all** |

## 3. CREATE — PASS

Prior synthetic create (not re-created in this run):

| Record | Id |
|---|---|
| Lead | `6a518bfc1927182bb` |
| Name | `Synthetic 3D Dealer Test GmbH` |
| Marker | `[CHITU_SYNTHETIC_TEST]` |
| ResearchEvidence | `6a518bfc2e154ca1f` (already deleted in earlier rollback attempt; confirmed still 404) |

## 4. VERIFY — PASS

Pre-final-rollback confirmation of remaining synthetic Lead:

| Check | Result |
|---|---|
| Synthetic Lead found by marker | PASS |
| Name matches constant | PASS |
| Marker in description | PASS |

Earlier Phase 3A-2.4 verify of score/evidence/relationship fields also PASS (see prior run evidence before first evidence DELETE).

## 5. ROLLBACK — PASS

### Pre-state

- Synthetic Lead `6a518bfc1927182bb` still present (blocked previously by Lead delete ACL).
- Linked ResearchEvidence list empty (evidence already removed when ResearchEvidence delete was granted).

### Action

Called existing `rollback(lead_id, evidence_ids=())`:

1. No remaining evidence ids to delete (already gone).  
2. `DELETE /api/v1/Lead/6a518bfc1927182bb` → success.

### Post-state verification

| Check | Result |
|---|---|
| `find_synthetic_lead()` | `null` |
| `GET Lead/6a518bfc1927182bb` | **HTTP 404** |
| `GET ResearchEvidence/6a518bfc2e154ca1f` | **HTTP 404** |
| Name+marker leftovers | none |
| Relationship residue | none |

Environment clean: **YES**

## 6. Failure History (resolved)

| Attempt | Result | Cause |
|---|---|---|
| Earlier rollback | FAIL | ResearchEvidence delete worked; Lead DELETE **HTTP 403** because `Lead.delete=no` |
| This run | PASS | After `Lead.delete=all`, Lead DELETE succeeded; both entities GET 404 |

## 7. Safety Confirmation

- No new synthetic Lead created  
- No Extension changes  
- No auth-code changes  
- No ACL edits by this agent  
- Only synthetic marker Lead targeted  
- Non-synthetic CRM records untouched  

## 8. Phase 3A-2.4 Conclusion

Synthetic localhost sync path is complete for the required gates:

1. Prior CREATE of synthetic Lead + ResearchEvidence  
2. VERIFY of fields / relationship  
3. ROLLBACK with full cleanup (Lead + Evidence gone, no residue)

Phase 3A-2.4 synthetic rollback verification: **COMPLETE / PASS**
