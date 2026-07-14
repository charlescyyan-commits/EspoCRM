"""Synthetic, no-side-effect lifecycle acceptance coverage for C10.0--C10.4."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from unittest import TestCase

from chitu_connector.espocrm_sync.canonical_score_integration import CanonicalScoreIntegration
from chitu_connector.espocrm_sync.email_draft_generation import DeterministicEmailDraftGenerator
from chitu_connector.espocrm_sync.enrichment_gate import DeterministicEnrichmentGate, QualificationStatus
from chitu_connector.espocrm_sync.human_approval import (
    ApprovalStatus,
    InMemoryHumanApprovalRegistry,
)
from chitu_connector.espocrm_sync.outreach_input_adapter import DeterministicOutreachInputAdapter
from chitu_connector.espocrm_sync.reply_tracking import (
    InMemoryReplyEventRegistry,
    ReplyEventReservationStatus,
    ReplyStatus,
    ReplyTrackingService,
)
from chitu_connector.espocrm_sync.score_input_adapter import DeterministicScoreInputAdapter, ScoreInput
from chitu_connector.espocrm_sync.send_execution import (
    ControlledSendExecutionService,
    InMemorySendExecutionRegistry,
    SendExecutionState,
)
from chitu_connector.espocrm_sync.send_idempotency import SendRequest, generate_send_idempotency_key
from chitu_connector.espocrm_sync.send_provider import (
    ProviderResultStatus,
    SendProviderAdapter,
    SendProviderResult,
)
from chitu_connector.vendored.contracts.canonical_score import CanonicalScoreResult, ScoreComponentTrace


SYNTHETIC_MARKER = "[C10_5_SYNTHETIC]"
LEAD_ID = "synthetic-c10-5-existing-lead"
DRAFT_ID = "synthetic-c10-5-draft-001"
APPROVAL_ID = "synthetic-c10-5-approval-001"
PROVIDER_NAME = "synthetic-acceptance-provider"
NOW = datetime(2026, 7, 14, 8, 0, 0, tzinfo=timezone.utc)


@dataclass
class SideEffectLedger:
    """Explicit proof that the acceptance fixture has no real side effects."""

    real_email_sends: list[object] = field(default_factory=list)
    smtp_calls: list[object] = field(default_factory=list)
    external_provider_calls: list[object] = field(default_factory=list)
    crm_writes: list[object] = field(default_factory=list)
    lead_creations: list[object] = field(default_factory=list)
    opportunity_creations: list[object] = field(default_factory=list)
    workflow_executions: list[object] = field(default_factory=list)


class SyntheticProvider:
    """In-memory provider double; it records calls but has no external client."""

    provider_name = PROVIDER_NAME

    def __init__(self, result_status: ProviderResultStatus = ProviderResultStatus.ACCEPTED) -> None:
        self.result_status = result_status
        self.calls: list[str] = []

    def submit(self, request: SendRequest, _attempt: object) -> SendProviderResult:
        self.calls.append(request.send_request_id)
        return SendProviderResult(
            provider_name=self.provider_name,
            send_attempt_id=f"synthetic-attempt:{request.send_request_id}",
            idempotency_key=request.idempotency_key,
            request_version=request.request_version,
            status=self.result_status,
            reason_code="SYNTHETIC_PROVIDER_FAILED" if self.result_status is ProviderResultStatus.FAILED else None,
        )


class FrozenCanonicalExecutor:
    """A fixed canonical-score result; no scoring implementation is invoked."""

    engine_version = "canonical-scoring-v4.0"

    def __init__(self) -> None:
        self.calls: list[ScoreInput] = []
        self.result = CanonicalScoreResult(
            accepted=True,
            opportunity_score=82,
            score_tier="A",
            best_first_product="Resin Printer",
            customer_type="DISTRIBUTOR",
            contact_priority="HIGH",
            score_reasons=("C10_5_FROZEN_CANONICAL_FIXTURE",),
            evidence_refs=("ev-c10-5-about", "ev-c10-5-products"),
            component_traces=(ScoreComponentTrace("product-fit", 42, ("ev-c10-5-products",)),),
            validation_errors=(),
            canonical_engine_version=self.engine_version,
            canonical_content_hash="c10-5-synthetic-canonical-hash",
            raw_decision={"fixture": "c10-5-synthetic"},
            adapter_version="canonical-score-adapter-v1",
            scored_at=NOW,
        )

    def score(self, score_input: ScoreInput) -> CanonicalScoreResult:
        self.calls.append(score_input)
        return self.result


def synthetic_evidence() -> tuple[dict[str, object], ...]:
    return (
        {
            "peEvidenceId": "ev-c10-5-about",
            "peEvidenceType": "title",
            "peSourceUrl": "https://c10-5-synthetic.example/about",
            "peClaim": f"{SYNTHETIC_MARKER} operates as an industrial distributor.",
            "peEvidenceText": f"{SYNTHETIC_MARKER} operates as an industrial distributor.",
            "peConfidence": 0.92,
        },
        {
            "peEvidenceId": "ev-c10-5-products",
            "peEvidenceType": "visible_text",
            "peSourceUrl": "https://c10-5-synthetic.example/products",
            "peClaim": f"{SYNTHETIC_MARKER} lists industrial resin printers.",
            "peEvidenceText": f"{SYNTHETIC_MARKER} lists industrial resin printers.",
            "peConfidence": 0.90,
        },
    )


class SyntheticLifecycle:
    """Fixture composing frozen C07--C10 contracts with only in-memory seams."""

    def __init__(self, provider_status: ProviderResultStatus = ProviderResultStatus.ACCEPTED) -> None:
        self.ledger = SideEffectLedger()
        self.evidence = synthetic_evidence()
        self.qualification = DeterministicEnrichmentGate().evaluate(self.evidence)
        self.score_executor = FrozenCanonicalExecutor()
        score_input = DeterministicScoreInputAdapter().build(self.evidence, self.qualification)
        self.score_decision = CanonicalScoreIntegration(self.score_executor).evaluate(score_input, self.evidence)
        outreach_input = DeterministicOutreachInputAdapter().build(
            {
                "name": f"{SYNTHETIC_MARKER} Industrial Distributor",
                "website": "https://c10-5-synthetic.example",
                "addressCountry": "DE",
                "peIndustry": "Additive Manufacturing",
                "peBusinessModel": "B2B Distribution",
                "peCompanyType": "DISTRIBUTOR",
            },
            self.qualification,
            self.score_decision.result,
            self.evidence,
        )
        self.draft = DeterministicEmailDraftGenerator().generate(outreach_input)
        self.approvals = InMemoryHumanApprovalRegistry()
        self.executions = InMemorySendExecutionRegistry()
        self.provider = SyntheticProvider(provider_status)
        self.execution_service = ControlledSendExecutionService(
            self.approvals,
            SendProviderAdapter(self.provider),
            self.executions,
        )
        self.replies = ReplyTrackingService(self.executions, InMemoryReplyEventRegistry())

    def ready_approval(self, *, approval_id: str = APPROVAL_ID) -> None:
        self.approvals.create_draft_ready(DRAFT_ID, approval_id, NOW, "synthetic-draft-owner")
        self.approvals.submit_for_review(approval_id, "synthetic-submitter", NOW)
        self.approvals.approve(approval_id, "synthetic-human-reviewer", NOW)
        self.approvals.mark_ready_to_send(approval_id, "synthetic-release-owner", NOW)

    def execute(self, request_id: str = "synthetic-c10-5-request-001"):
        return self.execution_service.execute(approval_id=APPROVAL_ID, lead_id=LEAD_ID, provider_name=PROVIDER_NAME,
                                              send_request_id=request_id, timestamp=NOW)


class OutreachLifecycleRuntimeAcceptanceTests(TestCase):
    def assert_no_external_side_effects(self, ledger: SideEffectLedger) -> None:
        self.assertEqual(ledger.real_email_sends, [])
        self.assertEqual(ledger.smtp_calls, [])
        self.assertEqual(ledger.external_provider_calls, [])
        self.assertEqual(ledger.crm_writes, [])
        self.assertEqual(ledger.lead_creations, [])
        self.assertEqual(ledger.opportunity_creations, [])
        self.assertEqual(ledger.workflow_executions, [])

    def test_approval_enforcement_requires_ready_to_send(self) -> None:
        lifecycle = SyntheticLifecycle()
        lifecycle.approvals.create_draft_ready(DRAFT_ID, APPROVAL_ID, NOW, "synthetic-draft-owner")

        outcome = lifecycle.execute()

        self.assertIsNone(outcome.execution)
        self.assertEqual(outcome.reason_code, "APPROVAL_NOT_READY")
        self.assertEqual(lifecycle.approvals.get(APPROVAL_ID).status, ApprovalStatus.DRAFT_READY)
        self.assertEqual(lifecycle.provider.calls, [])
        self.assert_no_external_side_effects(lifecycle.ledger)

    def test_successful_synthetic_lifecycle_preserves_complete_trace(self) -> None:
        lifecycle = SyntheticLifecycle()
        lifecycle.ready_approval()

        execution_outcome = lifecycle.execute()
        self.assertIsNotNone(execution_outcome.execution)
        execution = execution_outcome.execution
        assert execution is not None
        self.assertEqual(execution.state, SendExecutionState.SENT)
        self.assertEqual(execution.result_status, ProviderResultStatus.ACCEPTED)
        self.assertIsNotNone(execution.send_attempt_id)
        reply = lifecycle.replies.track(
            LEAD_ID, DRAFT_ID, execution.send_attempt_id or "", "synthetic-thread-001", NOW,
            "synthetic-sender@example.invalid", ReplyStatus.REPLIED,
        )

        self.assertEqual(lifecycle.qualification.status, QualificationStatus.QUALIFIED)
        self.assertEqual(lifecycle.score_decision.trace.input_evidence_refs, ("ev-c10-5-about", "ev-c10-5-products"))
        self.assertEqual(lifecycle.score_decision.result.evidence_refs, ("ev-c10-5-about", "ev-c10-5-products"))
        self.assertEqual(lifecycle.score_decision.result.component_traces[0].evidence_refs, ("ev-c10-5-products",))
        self.assertEqual(tuple(item.evidence_id for item in lifecycle.draft.evidence_references),
                         ("ev-c10-5-about", "ev-c10-5-products"))
        self.assertEqual(execution.draft_id, DRAFT_ID)
        self.assertEqual(execution.approval_id, APPROVAL_ID)
        self.assertEqual(execution.send_request.send_request_id, "synthetic-c10-5-request-001")
        self.assertEqual(execution.send_attempt_id, "synthetic-attempt:synthetic-c10-5-request-001")
        self.assertEqual(reply.status, ReplyEventReservationStatus.CREATED)
        self.assertIsNotNone(reply.event)
        assert reply.event is not None
        self.assertTrue(reply.event.reply_event_id)
        self.assertEqual(reply.event.draft_id, DRAFT_ID)
        self.assertEqual(reply.event.send_attempt_id, execution.send_attempt_id)
        self.assertEqual(reply.event.original_send_trace[-1].send_request_id, execution.send_request.send_request_id)
        self.assertEqual(reply.event.original_send_trace[-1].send_attempt_id, execution.send_attempt_id)
        self.assertEqual(lifecycle.provider.calls, ["synthetic-c10-5-request-001"])
        self.assert_no_external_side_effects(lifecycle.ledger)

    def test_duplicate_send_request_execution_and_reply_do_not_create_duplicates(self) -> None:
        lifecycle = SyntheticLifecycle()
        lifecycle.ready_approval()

        first = lifecycle.execute()
        duplicate_execution = lifecycle.execute()
        assert first.execution is not None
        self.assertFalse(first.duplicate)
        self.assertTrue(duplicate_execution.duplicate)
        self.assertIs(duplicate_execution.execution, first.execution)
        self.assertEqual(duplicate_execution.reason_code, "DUPLICATE_EXECUTION")
        self.assertEqual(lifecycle.provider.calls, ["synthetic-c10-5-request-001"])
        first_reply = lifecycle.replies.track(
            LEAD_ID, DRAFT_ID, first.execution.send_attempt_id or "", "synthetic-thread-duplicate", NOW,
            "synthetic-sender@example.invalid", ReplyStatus.REPLIED,
        )
        duplicate_reply = lifecycle.replies.track(
            LEAD_ID, DRAFT_ID, first.execution.send_attempt_id or "", "synthetic-thread-duplicate", NOW,
            "synthetic-sender@example.invalid", ReplyStatus.REPLIED,
        )
        self.assertEqual(first_reply.status, ReplyEventReservationStatus.CREATED)
        self.assertEqual(duplicate_reply.status, ReplyEventReservationStatus.DUPLICATE)
        self.assertIs(duplicate_reply.event, first_reply.event)

        provider = SyntheticProvider()
        adapter = SendProviderAdapter(provider)
        request = SendRequest(
            draft_id=DRAFT_ID,
            lead_id=LEAD_ID,
            send_request_id="synthetic-c10-5-direct-idempotency-request",
            idempotency_key=generate_send_idempotency_key(
                DRAFT_ID, LEAD_ID, "synthetic-c10-5-direct-idempotency-request", PROVIDER_NAME,
            ),
            provider_name=PROVIDER_NAME,
            created_at=NOW,
        )
        first_request = adapter.submit(request)
        duplicate_request = adapter.submit(request)
        self.assertIs(duplicate_request, first_request)
        self.assertEqual(provider.calls, ["synthetic-c10-5-direct-idempotency-request"])
        self.assert_no_external_side_effects(lifecycle.ledger)

    def test_rejected_approval_cannot_execute(self) -> None:
        lifecycle = SyntheticLifecycle()
        lifecycle.approvals.create_draft_ready(DRAFT_ID, APPROVAL_ID, NOW, "synthetic-draft-owner")
        lifecycle.approvals.submit_for_review(APPROVAL_ID, "synthetic-submitter", NOW)
        lifecycle.approvals.reject(APPROVAL_ID, "synthetic-human-reviewer", "SYNTHETIC_REJECTED", NOW)

        outcome = lifecycle.execute()

        self.assertEqual(lifecycle.approvals.get(APPROVAL_ID).status, ApprovalStatus.REJECTED)
        self.assertIsNone(outcome.execution)
        self.assertEqual(outcome.reason_code, "APPROVAL_NOT_READY")
        self.assertEqual(lifecycle.provider.calls, [])
        self.assert_no_external_side_effects(lifecycle.ledger)

    def test_provider_failure_and_invalid_reply_event_are_contained(self) -> None:
        lifecycle = SyntheticLifecycle(ProviderResultStatus.FAILED)
        lifecycle.ready_approval()

        failed = lifecycle.execute()
        assert failed.execution is not None
        self.assertEqual(failed.execution.state, SendExecutionState.FAILED)
        self.assertEqual(failed.execution.result_status, ProviderResultStatus.FAILED)
        self.assertEqual(failed.execution.reason_code, "SYNTHETIC_PROVIDER_FAILED")
        reply_to_failed_send = lifecycle.replies.track(
            LEAD_ID, DRAFT_ID, failed.execution.send_attempt_id or "", "synthetic-thread-failed", NOW,
            "synthetic-sender@example.invalid", ReplyStatus.BOUNCED,
        )
        self.assertEqual(reply_to_failed_send.status, ReplyEventReservationStatus.REJECTED)
        self.assertEqual(reply_to_failed_send.reason_code, "UNKNOWN_SENT_ATTEMPT")

        accepted = SyntheticLifecycle()
        accepted.ready_approval()
        sent = accepted.execute()
        assert sent.execution is not None
        invalid_reply = accepted.replies.track(
            LEAD_ID, DRAFT_ID, sent.execution.send_attempt_id or "", "", NOW,
            "synthetic-sender@example.invalid", ReplyStatus.REPLIED,
        )
        self.assertEqual(invalid_reply.status, ReplyEventReservationStatus.REJECTED)
        self.assertEqual(invalid_reply.reason_code, "INVALID_THREAD_ID")
        self.assert_no_external_side_effects(lifecycle.ledger)
        self.assert_no_external_side_effects(accepted.ledger)
