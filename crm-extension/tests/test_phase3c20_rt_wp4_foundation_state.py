"""Phase3C20 RT-WP4 Lite Execution State Foundation contracts."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_PLATFORM = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "AIPlatform"
SERVICES = AI_PLATFORM / "Services"

STATE = SERVICES / "AIFoundationState.php"
SERVICE = SERVICES / "AIFoundationStateService.php"
GUARD = SERVICES / "AIFoundationStateTransitionGuard.php"

DISPATCH_SERVICE = SERVICES / "AIDispatchService.php"
PROVIDER_BINDING_SERVICE = SERVICES / "ProviderBindingService.php"

INVARIANT_REGISTRY = ROOT / "docs" / "adr" / "C20_INVARIANT_REGISTRY.md"
COMPLETION_BASE = (
    ROOT
    / "chitu-connector"
    / "chitu_connector"
    / "acquisition"
    / "providers"
    / "completion"
    / "base.py"
)

LITE_STATES = {
    "REQUESTED",
    "VALIDATING",
    "READY",
    "BLOCKED",
    "COMPLETED",
    "FAILED",
}

FORBIDDEN_ENGINE_STATES = {
    "QUEUED",
    "RUNNING",
    "RETRY_PENDING",
    "RESERVATION_CONFLICT",
    "CANCELLED",
    "DISPATCHED",
    "PROVIDER_TIMEOUT",
    "EXECUTION_COMPLETED",
}

COMPLETION_PORTFOLIO = {
    "RESEARCH_EVIDENCE",
    "QUALIFICATION_INSIGHT",
    "DRAFT_ASSISTANCE",
    "REPLY_ASSISTANCE",
}

FORBIDDEN_RUNTIME_MARKERS = (
    "curl_init",
    "curl_exec",
    "GuzzleHttp",
    "file_get_contents",
    "fsockopen",
    "stream_socket_client",
    "ConnectorBoundary",
    "chitu_connector",
    "subprocess",
    "CommercialBrief",
    "Opportunity",
    "AIRetryPolicy",
    "IdempotencyReservation",
    "AIDispatchWorker",
    "CancelReason",
    "->saveEntity(",
    "registerPurpose(",
    "->create(",
    "->approve(",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C20RTWP4FoundationStateTests(unittest.TestCase):
    def test_allowlist_files_exist(self) -> None:
        for path in (STATE, SERVICE, GUARD):
            self.assertTrue(path.is_file(), msg=str(path))

    def test_six_state_vocabulary(self) -> None:
        text = read(STATE)
        for state in LITE_STATES:
            self.assertIn(f"const {state}", text)
            self.assertIn(f"'{state}'", text)
        self.assertIn("function assertValid(", text)
        self.assertIn("function isTerminal(", text)
        for state in FORBIDDEN_ENGINE_STATES:
            self.assertIn(f"'{state}'", text)

    def test_transition_matrix_allow_and_reject(self) -> None:
        text = read(GUARD)
        self.assertIn("REQUESTED", text)
        self.assertIn("VALIDATING", text)
        self.assertIn("READY", text)
        self.assertIn("BLOCKED", text)
        self.assertIn("COMPLETED", text)
        self.assertIn("FAILED", text)
        self.assertIn("function assertTransition(", text)
        self.assertIn("illegal transition", text)
        self.assertIn("assertSafeMutationPayload", text)
        self.assertIn("secret-shaped mutation", text)
        # Terminal states have empty allow lists.
        self.assertIn("AIFoundationState::BLOCKED => []", text)
        self.assertIn("AIFoundationState::COMPLETED => []", text)
        self.assertIn("AIFoundationState::FAILED => []", text)

    def test_service_consumes_rt_wp3_outcomes_only(self) -> None:
        text = read(SERVICE)
        self.assertIn("function begin(", text)
        self.assertIn("function transition(", text)
        self.assertIn("function applyDispatchOutcome(", text)
        self.assertIn("function complete(", text)
        self.assertIn("AIDispatchService::CLASS_BOUND", text)
        self.assertIn("AIDispatchExecutionBoundary", text)
        self.assertIn("Does not invoke Connector", text)
        self.assertIn("foundationState", text)
        self.assertIn("boundaryReference", text)
        self.assertIn("transitionReasonCode", text)
        self.assertIn("provenanceReference", text)
        self.assertIn("REASON_POLICY", text)
        self.assertIn("REASON_VALIDATION", text)
        self.assertIn("REASON_CLOSE", text)

    def test_runtime_visible_contract_fields(self) -> None:
        text = read(SERVICE)
        for field in (
            "foundationState",
            "requestIdentity",
            "previousState",
            "boundaryReference",
            "transitionReasonCode",
            "provenanceReference",
            "updatedAt",
        ):
            self.assertIn(f"'{field}'", text)

    def test_isolation_no_connector_http_secrets_execution(self) -> None:
        blob = "\n".join(read(path) for path in (STATE, SERVICE, GUARD))
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            self.assertNotIn(marker, blob, msg=f"forbidden marker present: {marker}")

    def test_no_entitydefs_or_aijob_merge(self) -> None:
        blob = "\n".join(read(path) for path in (STATE, SERVICE, GUARD))
        for marker in (
            "entityDefs",
            "AIJob",
            "cancelReason",
            "EntityManager",
            "Jobs/",
            "CommercialBrief",
        ):
            self.assertNotIn(marker, blob)
        self.assertIn("no entity metadata / job-engine merge", read(SERVICE))
        self.assertIn("Does not define job/queue/worker/retry states", read(STATE))
        # CANCELLED may appear only as an explicitly forbidden/rejected label.
        self.assertIn("'CANCELLED'", read(STATE))
        self.assertNotIn("const CANCELLED", blob)

    def test_provider_binding_and_dispatch_unchanged_coupling(self) -> None:
        pb = read(PROVIDER_BINDING_SERVICE)
        dispatch = read(DISPATCH_SERVICE)
        for marker in (
            "AIFoundationState",
            "AIFoundationStateService",
            "AIFoundationStateTransitionGuard",
        ):
            self.assertNotIn(marker, pb)
            self.assertNotIn(marker, dispatch)

    def test_completion_capability_portfolio_unchanged(self) -> None:
        text = read(COMPLETION_BASE)
        match = re.search(
            r"class CompletionCapability\(Enum\):(.*?)(?:\nclass |\Z)",
            text,
            flags=re.S,
        )
        self.assertIsNotNone(match)
        assert match is not None
        names = set(re.findall(r'^\s+([A-Z_]+) = "', match.group(1), flags=re.M))
        self.assertEqual(names, COMPLETION_PORTFOLIO)
        self.assertNotIn("COMMERCIAL_BRIEF", names)

    def test_invariant_registry_statuses_unchanged(self) -> None:
        text = read(INVARIANT_REGISTRY)
        self.assertRegex(text, r"\|\s*C20-INV-02\s*\|.*\|\s*ACTIVE\s*\|")
        self.assertRegex(text, r"\|\s*C20-INV-03\s*\|.*\|\s*ACTIVE\s*\|")
        for inv in range(4, 14):
            self.assertRegex(
                text,
                rf"\|\s*C20-INV-{inv:02d}\s*\|.*\|\s*DEFERRED\s*\|",
                msg=f"C20-INV-{inv:02d} must remain DEFERRED",
            )


if __name__ == "__main__":
    unittest.main()
