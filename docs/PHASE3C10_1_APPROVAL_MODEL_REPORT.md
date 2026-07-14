# Phase3C10.1 — Human Approval Model Report

## Scope

This phase adds a mandatory, human-only approval-state contract after the C09
EmailDraft boundary. It is a local, offline connector model only. It does not
send email, invoke a provider, create a SendRequest, execute a campaign, write
CRM data, create Leads or Opportunities, or use AI for approval.

## Model

`chitu_connector.espocrm_sync.human_approval` defines the immutable
`DraftApproval` record:

| Required field | Model field |
| --- | --- |
| draftId | `draft_id` |
| approvalId | `approval_id` |
| status | `status` |
| reviewerId placeholder | `reviewer_id` (`None` until human decision) |
| createdAt | `created_at` |
| decidedAt | `decided_at` |
| rejectionReason | `rejection_reason` |
| approvalVersion | `approval_version` |

The contract version is `c10.1-human-approval-v1`. One draft identity can have
one approval record. A rejected draft is terminal; a revised draft must have a
new `draft_id` and begins a separate review cycle.

## State transition contract

| From | To | Command |
| --- | --- | --- |
| `DRAFT_READY` | `PENDING_REVIEW` | `submit_for_review` |
| `PENDING_REVIEW` | `APPROVED` | `approve` with named reviewer |
| `PENDING_REVIEW` | `REJECTED` | `reject` with named reviewer and reason |
| `APPROVED` | `READY_TO_SEND` | `mark_ready_to_send` |

All other transitions fail with `ValueError`. `READY_TO_SEND` is only an
approval-contract state: it does not perform or authorize delivery code in
this phase.

## Audit trace

Each creation and accepted transition appends an `ApprovalAuditTrace` containing
`who`, `when`, `decision`, and `approval_version`, together with the draft and
approval identifiers. Approval and rejection require a non-empty human
`reviewer_id`; no method automatically approves a draft.

## Validation

The offline test module `test_phase3c10_1_human_approval_model.py` covers:

- submit for review and pending-review audit trace;
- approval and the explicit transition to `READY_TO_SEND`;
- rejection with reviewer, reason, and audit trace;
- invalid transition rejection;
- duplicate approval attempt rejection;
- blocked resubmission or approval of an already rejected draft.

C10.0, C09, and the repository core regression gate are run as separate
validation commands for this phase.
