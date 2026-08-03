"""Phase3C20 RT-WP3 Dispatch Foundation Lite + Runtime Guards Lite contracts."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_PLATFORM = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "AIPlatform"
SERVICES = AI_PLATFORM / "Services"

DISPATCH_SERVICE = SERVICES / "AIDispatchService.php"
DISPATCH_REQUEST = SERVICES / "AIDispatchRequest.php"
DISPATCH_BOUNDARY = SERVICES / "AIDispatchExecutionBoundary.php"
DISPATCH_GUARDS = SERVICES / "AIDispatchRuntimeGuardsLite.php"
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

COMPLETION_PORTFOLIO = {
    "RESEARCH_EVIDENCE",
    "QUALIFICATION_INSIGHT",
    "DRAFT_ASSISTANCE",
    "REPLY_ASSISTANCE",
    "COMMERCIAL_BRIEF",
}

ELIGIBILITY_CLASSES = {
    "NOT_AUTHORIZED",
    "UNBOUND",
    "DISABLED",
    "PURPOSE_NOT_REGISTERED",
    "CAPABILITY_MISMATCH",
    "CREDENTIAL_REFERENCE_MISSING",
    "BOUND",
}

FORBIDDEN_EXECUTION_STATES = {
    "QUEUED",
    "RUNNING",
    "RETRY_PENDING",
    "DISPATCH_FAILED",
    "RESERVATION_CONFLICT",
    "PROVIDER_TIMEOUT",
    "EXECUTION_COMPLETED",
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
    "->saveEntity(",
)

FORBIDDEN_PROVIDER_BINDING_MUTATION = (
    "->create(",
    "->approve(",
    "->updatePolicy(",
    "->disable(",
    "->revoke(",
    "registerPurpose(",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C20RTWP3DispatchFoundationTests(unittest.TestCase):
    def test_allowlist_files_exist(self) -> None:
        for path in (
            DISPATCH_SERVICE,
            DISPATCH_REQUEST,
            DISPATCH_BOUNDARY,
            DISPATCH_GUARDS,
        ):
            self.assertTrue(path.is_file(), msg=str(path))

    def test_request_contract_fields(self) -> None:
        text = read(DISPATCH_REQUEST)
        for field in (
            "requestIdentity",
            "purposeReference",
            "capabilityReference",
            "providerBindingReference",
            "provenanceReference",
        ):
            self.assertIn(field, text)
        self.assertIn("function fromArray(", text)
        self.assertIn("function toArray(", text)
        self.assertIn("Does not execute", text)
        self.assertIn("rejectSecretShapedInput", text)

    def test_execution_boundary_is_references_only(self) -> None:
        text = read(DISPATCH_BOUNDARY)
        self.assertIn("References-only execution boundary", text)
        self.assertIn("credentialReference", text)
        self.assertIn("providerBindingReferences", text)
        self.assertIn("Does not invoke", text)
        for marker in ("curl_init", "GuzzleHttp", "ConnectorBoundary", "execute("):
            self.assertNotIn(marker, text)

    def test_capability_portfolio_accepts_commercial_brief_identity_only(self) -> None:
        text = read(DISPATCH_GUARDS)
        for capability in COMPLETION_PORTFOLIO:
            self.assertIn(capability, text)
        self.assertIn("rejectInvalidCapability", text)
        self.assertIn("five CompletionCapability values", text)
        self.assertNotIn("FORBIDDEN_CAPABILITY", text)

        live = read(COMPLETION_BASE)
        match = re.search(
            r"class CompletionCapability\(Enum\):(.*?)(?:\nclass |\Z)",
            live,
            flags=re.S,
        )
        self.assertIsNotNone(match)
        assert match is not None
        names = set(re.findall(r'^\s+([A-Z_]+) = "', match.group(1), flags=re.M))
        self.assertEqual(names, COMPLETION_PORTFOLIO)
        self.assertIn("COMMERCIAL_BRIEF", names)

    def test_purpose_unknown_rejected(self) -> None:
        text = read(DISPATCH_SERVICE)
        self.assertIn("assertPurposeRegistered", text)
        self.assertIn("Purpose is not registered for Dispatch Foundation Lite", text)
        self.assertIn("commercial_brief_generation", text)
        self.assertIn("do not infer purpose", text.lower())
        # Lite dispatch still hard-stops commercial_brief_generation before connector.
        self.assertIn(
            "$purpose === 'commercial_brief_generation'",
            text,
        )
        self.assertIn("stopped_before_connector_invocation", text)

    def test_missing_binding_rejected(self) -> None:
        guards = read(DISPATCH_GUARDS)
        service = read(DISPATCH_SERVICE)
        self.assertIn("rejectMissingBinding", guards)
        self.assertIn("ProviderBinding is required and must resolve", guards)
        self.assertIn("rejectMissingBinding", service)
        self.assertIn("lookupProviderBinding", service)

    def test_secret_shaped_input_rejected(self) -> None:
        text = read(DISPATCH_GUARDS)
        self.assertIn("rejectSecretShapedInput", text)
        self.assertIn("secret-shaped input fields", text)
        self.assertIn("secret-shaped input values", text)
        self.assertIn("sk" + "-", text.replace("'sk' . '-'", "sk-").replace("'sk'.'-'", "sk-"))
        # Source uses concatenation to avoid secret-looking literals in one piece.
        self.assertIn("'sk'", text)
        self.assertIn("'bearer'", text)

    def test_service_resolution_flow_and_stop_before_execution(self) -> None:
        text = read(DISPATCH_SERVICE)
        self.assertIn("function resolve(", text)
        self.assertIn("AIDispatchRequest::fromArray", text)
        self.assertIn("rejectInvalidCapability", text)
        self.assertIn("assertPurposeRegistered", text)
        self.assertIn("lookupProviderBinding", text)
        self.assertIn("classifyEligibility", text)
        self.assertIn("assembleBoundary", text)
        self.assertIn("stopped_before_connector_invocation", text)
        self.assertIn("CLASS_BOUND", text)
        for eligibility in ELIGIBILITY_CLASSES:
            self.assertIn(f"CLASS_{eligibility}", text)
        for state in FORBIDDEN_EXECUTION_STATES:
            self.assertNotIn(state, text)

    def test_provider_binding_consume_only_no_mutation(self) -> None:
        text = read(DISPATCH_SERVICE)
        self.assertIn("ProviderBindingService", text)
        self.assertIn("getPurposeCatalog", text)
        self.assertIn("Read/consume only", text)
        self.assertIn("never persist or mutate ProviderBinding", text)
        for marker in FORBIDDEN_PROVIDER_BINDING_MUTATION:
            self.assertNotIn(marker, text)
        # Must not rewrite ProviderBindingService itself.
        pb = read(PROVIDER_BINDING_SERVICE)
        self.assertNotIn("AIDispatchRuntimeGuardsLite", pb)

    def test_isolation_no_connector_no_http(self) -> None:
        blob = "\n".join(
            read(path)
            for path in (
                DISPATCH_SERVICE,
                DISPATCH_REQUEST,
                DISPATCH_BOUNDARY,
                DISPATCH_GUARDS,
            )
        )
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            self.assertNotIn(marker, blob, msg=f"forbidden marker present: {marker}")

    def test_provider_binding_service_unchanged_by_dispatch_markers(self) -> None:
        """RT-WP2 surface must remain free of dispatch/execution coupling."""
        text = read(PROVIDER_BINDING_SERVICE)
        for marker in (
            "AIDispatchService",
            "AIDispatchRequest",
            "AIDispatchExecutionBoundary",
            "AIDispatchRuntimeGuardsLite",
            "curl_init",
            "GuzzleHttp",
        ):
            self.assertNotIn(marker, text)

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

    def test_no_jobs_api_requestlog_or_c25_coupling_in_allowlist(self) -> None:
        blob = "\n".join(
            read(path)
            for path in (
                DISPATCH_SERVICE,
                DISPATCH_REQUEST,
                DISPATCH_BOUNDARY,
                DISPATCH_GUARDS,
            )
        )
        for marker in (
            "AIDispatchWorker",
            "PostAIDispatch",
            "AIRequestLogService",
            "CommercialBrief",
            "Jobs/",
            "Api/",
        ):
            self.assertNotIn(marker, blob)


if __name__ == "__main__":
    unittest.main()
