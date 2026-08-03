"""Phase3C20 RT-WP6 Lite Ownership & Reservation Metadata Foundation contracts."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_PLATFORM = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "AIPlatform"
SERVICES = AI_PLATFORM / "Services"

METADATA = SERVICES / "AIReservationMetadata.php"
SERVICE = SERVICES / "AIReservationMetadataService.php"
GUARD = SERVICES / "AIReservationMetadataGuard.php"

FAILURE_METADATA = SERVICES / "AIFailureMetadata.php"
FOUNDATION_STATE = SERVICES / "AIFoundationState.php"
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

LITE_INTENTS = {
    "NONE",
    "DECLARED",
    "HELD_METADATA",
    "CONFLICT",
    "RELEASED_METADATA",
}

FORBIDDEN_LABELS = {
    "ACQUIRED",
    "LOCKED",
    "LEASED",
    "QUEUED",
    "CLAIMED_BY_WORKER",
    "PROVIDER_RESERVED",
    "RETRY_PENDING",
    "RECOVERING",
    "RESERVATION_EXECUTING",
    "COMMERCIAL_BRIEF",
}

COMPLETION_PORTFOLIO = {
    "RESEARCH_EVIDENCE",
    "QUALIFICATION_INSIGHT",
    "DRAFT_ASSISTANCE",
    "REPLY_ASSISTANCE",
    "COMMERCIAL_BRIEF",
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
    "Predis\\",
    "->saveEntity(",
    "registerPurpose(",
    "->create(",
    "->approve(",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C20RTWP6ReservationMetadataTests(unittest.TestCase):
    def test_allowlist_files_exist(self) -> None:
        for path in (METADATA, SERVICE, GUARD):
            self.assertTrue(path.is_file(), msg=str(path))

    def test_five_intent_vocabulary(self) -> None:
        text = read(METADATA)
        for intent in LITE_INTENTS:
            self.assertIn(f"const {intent}", text)
            self.assertIn(f"'{intent}'", text)
        self.assertIn("function assertValid(", text)
        self.assertIn("function isKnown(", text)
        self.assertIn("function requiresOwner(", text)
        self.assertIn("Reservation metadata ≠ reservation execution", text)
        for label in FORBIDDEN_LABELS:
            self.assertIn(f"'{label}'", text)

    def test_guard_transitions_owner_and_secrets(self) -> None:
        text = read(GUARD)
        self.assertIn("function assertTransition(", text)
        self.assertIn("function assertOwnerReference(", text)
        self.assertIn("function assertSafeMutationPayload(", text)
        self.assertIn("illegal intent transition", text)
        self.assertIn("requires ownerReference when reservationIntent is not NONE", text)
        self.assertIn("secret or lock/execution-control mutation", text)
        self.assertIn("AIReservationMetadata::CONFLICT => [AIReservationMetadata::RELEASED_METADATA]", text)
        self.assertIn("'lockToken'", text)
        self.assertIn("'mutexKey'", text)
        self.assertIn("'redisLock'", text)

    def test_service_ownership_intent_conflict_audit(self) -> None:
        text = read(SERVICE)
        self.assertIn("function begin(", text)
        self.assertIn("function transition(", text)
        self.assertIn("function declare(", text)
        self.assertIn("function holdMetadata(", text)
        self.assertIn("function releaseMetadata(", text)
        self.assertIn("function get(", text)
        self.assertIn("OWNER_MISMATCH", text)
        self.assertIn("acquire locks", text)
        self.assertIn("no entity metadata / Redis / job-engine merge", text)
        self.assertIn("Reservation metadata ≠ reservation execution", text)
        for field in (
            "requestIdentity",
            "ownerReference",
            "reservationIntent",
            "ownershipScope",
            "correlationReference",
            "conflictReference",
            "conflictReasonCode",
            "recordedAt",
        ):
            self.assertIn(f"'{field}'", text)

    def test_isolation_no_lock_queue_connector_http(self) -> None:
        blob = "\n".join(read(path) for path in (METADATA, SERVICE, GUARD))
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            self.assertNotIn(marker, blob, msg=f"forbidden marker present: {marker}")

    def test_no_entitydefs_or_execution_engine_merge(self) -> None:
        blob = "\n".join(read(path) for path in (METADATA, SERVICE, GUARD))
        for marker in (
            "entityDefs",
            "AIJob",
            "EntityManager",
            "Jobs/",
            "CommercialBrief",
            "flock(",
            "sem_acquire",
            "SETNX",
        ):
            self.assertNotIn(marker, blob)
        self.assertIn("Does not define lock", read(METADATA))

    def test_upstream_wp_files_unmodified_coupling(self) -> None:
        for path in (FAILURE_METADATA, FOUNDATION_STATE, DISPATCH_SERVICE, PROVIDER_BINDING_SERVICE):
            text = read(path)
            for marker in (
                "AIReservationMetadata",
                "AIReservationMetadataService",
                "AIReservationMetadataGuard",
            ):
                self.assertNotIn(marker, text)

    def test_completion_capability_portfolio_includes_commercial_brief_identity(self) -> None:
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
        self.assertIn("COMMERCIAL_BRIEF", names)

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
