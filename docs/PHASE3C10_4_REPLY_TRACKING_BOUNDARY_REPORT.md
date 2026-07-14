# Phase3C10.4 — Reply Tracking Boundary Report

## Scope

This phase creates a reply-event model and tracking contract after a completed
C10.3 controlled send execution. It records event metadata and preserves the
original C10.3 send audit trace. It does not generate replies, call AI,
classify sentiment, modify score, create an Opportunity, send follow-up, or
execute any workflow.

## Reply event model

`ReplyEvent` contains the required fields:

| Required field | Model field |
| --- | --- |
| replyEventId | `reply_event_id` |
| leadId | `lead_id` |
| draftId | `draft_id` |
| sendAttemptId | `send_attempt_id` |
| threadId | `thread_id` |
| receivedAt | `received_at` |
| senderReference | `sender_reference` |
| replyStatus | `reply_status` |
| eventVersion | `event_version` |

The supported states are `SENT`, `REPLIED`, `BOUNCED`, and `UNSUBSCRIBED`.

## Deterministic identity and preserved trace

`generate_reply_event_id` hashes the event version, lead, draft, send attempt,
thread, UTC receipt timestamp, sender reference, and reply status. The
`InMemoryReplyEventRegistry` stores each resulting identity once; a repeat
returns `DUPLICATE` with the original immutable event.

`ReplyTrackingService` resolves `send_attempt_id` through the C10.3 execution
registry and accepts an event only when the matched execution is `SENT`. It
also requires the supplied lead and draft to match that execution. Each stored
event contains the exact original `SendExecutionAuditTrace` tuple.

## Validation

`test_phase3c10_4_reply_tracking_boundary.py` covers:

- reply-event creation and original-send-trace preservation;
- duplicate-event ignore behavior;
- bounced event recording;
- unsubscribed event recording;
- malformed event rejection before registry write.

All tests use local in-memory registries and a fake C10.2 provider only.
