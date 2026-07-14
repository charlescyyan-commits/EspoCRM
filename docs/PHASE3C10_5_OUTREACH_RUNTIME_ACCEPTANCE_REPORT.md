# Phase3C10.5 — Outreach Lifecycle Runtime Acceptance Report

## Scope

This phase adds synthetic acceptance coverage only. It does not alter C07, C08,
C09, or C10.0–C10.4 runtime code, and it does not add a real delivery,
provider, CRM, workflow, or persistence integration.

## Acceptance Fixture

`test_phase3c10_5_outreach_lifecycle_runtime_acceptance.py` composes the
existing frozen boundaries in memory:

1. Two synthetic `ResearchEvidence` records enter C07 qualification.
2. A frozen canonical-score executor is invoked through the C08 adapter and
   integration trace.
3. C09 creates an evidence-backed deterministic email draft.
4. C10.1 records a human review transition through `READY_TO_SEND`.
5. C10.3 creates the C10.0-B request and invokes a C10.2 in-memory fake
   provider.
6. C10.4 records a traceable synthetic reply event.

The fixture does not persist evidence, draft, score, approval, execution, or
reply records outside in-memory registries. `DRAFT_ID` is a synthetic opaque
identifier associated with the generated C09 draft for contract tracing only.

## Acceptance Coverage

- Approval enforcement: a `DRAFT_READY` draft cannot execute; C10.3 returns
  `APPROVAL_NOT_READY` without invoking the provider.
- Successful lifecycle: a human-reviewed `READY_TO_SEND` draft reaches `SENT`
  after the fake provider returns `ACCEPTED`, then accepts a `REPLIED` event.
- Idempotency: replaying the same C10.0-B request, C10.3 execution request,
  or C10.4 reply identity returns the existing result/event and performs no
  second fake-provider call.
- Trace preservation: assertions retain evidence identifiers and C08 score
  trace, draft ID, approval ID, send request ID, send attempt ID, and reply
  event ID through the complete synthetic path.
- Failure containment: rejected approvals cannot execute; a fake provider
  `FAILED` result reaches C10.3 `FAILED`; replies for non-sent or malformed
  traces are rejected.

## Side-Effect Boundary

Every acceptance scenario uses a `SideEffectLedger` and asserts zero entries
for real email sends, SMTP calls, external-provider calls, CRM writes, Lead
creation, Opportunity creation, and workflow execution. The provider is a
test-local in-memory double; its recorded calls are not external-provider
calls.

## Validation

Run from `D:\EspoCRM-Production\chitu-connector`:

```powershell
& <python> -m unittest tests.test_phase3c10_5_outreach_lifecycle_runtime_acceptance -v
& <python> -m unittest discover -s tests -p 'test_phase3c10*.py' -v
& <python> -m unittest discover -s tests -p 'test_phase3c09*.py' -v
```

Then run the repository Regression Gate with the C10.5 test and this report as
changed paths. Results are recorded after execution in the delivery summary.

## Explicit Non-Goals

- No actual email sending, SMTP, or provider SDK/API call.
- No CRM write, Lead/Opportunity creation, campaign, or workflow execution.
- No approval automation or AI decision.
- No scoring, research, or draft-generation implementation change.
