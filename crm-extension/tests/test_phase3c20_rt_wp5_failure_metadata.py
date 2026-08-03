"""Phase3C20 RT-WP5 Lite Failure Metadata Foundation contracts."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_PLATFORM = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "AIPlatform"
SERVICES = AI_PLATFORM / "Services"

METADATA = SERVICES / "AIFailureMetadata.php"
SERVICE = SERVICES / "AIFailureMetadataService.php"
GUARD = SERVICES / "AIFailureMetadataGuard.php"

FOUNDATION_STATE = SERVICES / "AIFoundationState.php"
FOUNDATION_SERVICE = SERVICES / "AIFoundationStateService.php"
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

LITE_CODES = {
    "VALIDATION_FAILED",
    "POLICY_REJECTED",
    "BOUNDARY_REJECTED",
    "TIMEOUT_METADATA",
    "UNKNOWN_FAILURE",
}

FORBIDDEN_LABELS = {
    "RETRY_PENDING",
    "RETRY_SCHEDULED",
    "QUEUED",
    "RUNNING",
    "NETWORK",
    "PROVIDER",
    "AUTH",
    "RATE_LIMIT",
    "QUOTA",
    "CONTENT_FILTER",
    "COMMERCIAL_BRIEF",
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
    "->saveEntity(",
    "registerPurpose(",
    "->create(",
    "->approve(",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C20RTWP5FailureMetadataTests(unittest.TestCase):
    def test_allowlist_files_exist(self) -> None:
        for path in (METADATA, SERVICE, GUARD):
            self.assertTrue(path.is_file(), msg=str(path))

    def test_five_code_vocabulary(self) -> None:
        text = read(METADATA)
        for code in LITE_CODES:
            self.assertIn(f"const {code}", text)
            self.assertIn(f"'{code}'", text)
        self.assertIn("function assertValid(", text)
        self.assertIn("function isKnown(", text)
        for label in FORBIDDEN_LABELS:
            self.assertIn(f"'{label}'", text)

    def test_guard_correlation_and_secrets(self) -> None:
        text = read(GUARD)
        self.assertIn("function assertCorrelation(", text)
        self.assertIn("function assertSafeMutationPayload(", text)
        self.assertIn("FAILED or BLOCKED", text)
        self.assertIn("secret or retry-control mutation", text)
        self.assertIn("AIFoundationState::FAILED", text)
        self.assertIn("AIFoundationState::BLOCKED", text)
        self.assertIn("VALIDATION_FAILED", text)
        self.assertIn("POLICY_REJECTED", text)
        self.assertIn("BOUNDARY_REJECTED", text)
        # Retry-control fields appear only as blocked mutation names (reject list).
        self.assertIn("'nextRetryAt'", text)
        self.assertIn("'attemptCount'", text)
        self.assertIn("'retryCount'", text)
        self.assertIn("'retryPolicy'", text)

    def test_service_record_classify_correlate(self) -> None:
        text = read(SERVICE)
        self.assertIn("function classify(", text)
        self.assertIn("function record(", text)
        self.assertIn("function recordFromFoundationState(", text)
        self.assertIn("function get(", text)
        self.assertIn("Does not invoke Connector", text)
        self.assertIn("no entity metadata / job-engine merge", text)
        for field in (
            "failureCode",
            "correlatedFoundationState",
            "requestIdentity",
            "failureMessageSafe",
            "correlationReference",
            "sourceLayer",
            "recordedAt",
        ):
            self.assertIn(f"'{field}'", text)

    def test_isolation_no_connector_http_retry_secrets(self) -> None:
        blob = "\n".join(read(path) for path in (METADATA, SERVICE, GUARD))
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            self.assertNotIn(marker, blob, msg=f"forbidden marker present: {marker}")

    def test_no_entitydefs_or_aijob_retry_merge(self) -> None:
        blob = "\n".join(read(path) for path in (METADATA, SERVICE, GUARD))
        for marker in (
            "entityDefs",
            "AIJob",
            "EntityManager",
            "Jobs/",
            "CommercialBrief",
            "FAILED → QUEUED",
            "backoff",
        ):
            self.assertNotIn(marker, blob)
        self.assertIn("Does not define retry", read(METADATA))

    def test_rt_wp4_consume_only_no_mutation_of_foundation_files(self) -> None:
        # WP5 files may reference AIFoundationState; WP4 files must not reference WP5.
        for path in (FOUNDATION_STATE, FOUNDATION_SERVICE):
            text = read(path)
            for marker in (
                "AIFailureMetadata",
                "AIFailureMetadataService",
                "AIFailureMetadataGuard",
            ):
                self.assertNotIn(marker, text)

    def test_provider_binding_and_dispatch_unchanged_coupling(self) -> None:
        pb = read(PROVIDER_BINDING_SERVICE)
        dispatch = read(DISPATCH_SERVICE)
        for marker in (
            "AIFailureMetadata",
            "AIFailureMetadataService",
            "AIFailureMetadataGuard",
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
