"""Phase3C25 WP2.2 CommercialBrief scoped implementation contracts.

Boundary / lifecycle / ACL / provenance — no runtime execution.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CI = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "CommercialIntelligence"
)
ENTITY = CI / "Entities" / "CommercialBrief.php"
ENTITY_DEFS = CI / "Resources" / "metadata" / "entityDefs" / "CommercialBrief.json"
SCOPES = CI / "Resources" / "metadata" / "scopes" / "CommercialBrief.json"
CLIENT_DEFS = CI / "Resources" / "metadata" / "clientDefs" / "CommercialBrief.json"
ACL_DEFS = CI / "Resources" / "metadata" / "aclDefs" / "CommercialBrief.json"
CONTROLLER = CI / "Controllers" / "CommercialBrief.php"
BINDING = CI / "Binding.php"
PROPOSAL_SERVICE = CI / "Services" / "CommercialBriefProposalService.php"
REVIEW_SERVICE = CI / "Services" / "CommercialBriefReviewService.php"
SAVE_OPTION = CI / "Services" / "CommercialBriefSaveOption.php"
PROVENANCE = CI / "Services" / "BriefProvenanceValidator.php"
IMMUTABLE_GUARD = (
    CI / "Hooks" / "CommercialBrief" / "CommercialBriefImmutabilityGuard.php"
)
REVIEW_GUARD = (
    CI / "Hooks" / "CommercialBrief" / "CommercialBriefReviewStatusGuard.php"
)
FIXTURE = (
    ROOT
    / "crm-extension"
    / "tests"
    / "fixtures"
    / "phase3c25_wp2_2_commercial_brief_proposal.json"
)

FORBIDDEN_RUNTIME_MARKERS = (
    "curl_init",
    "curl_exec",
    "GuzzleHttp",
    "file_get_contents",
    "fsockopen",
    "stream_socket_client",
    "chitu_connector",
    "ConnectorBoundary",
    "AIDispatchService",
    "AIDispatchWorker",
    "AIRetryPolicy",
    "IdempotencyReservation",
    "ProspectRun",
    "ExecutionLedger",
    "ActionGate",
    "subprocess",
)

PHP_SOURCES = [
    ENTITY,
    CONTROLLER,
    BINDING,
    PROPOSAL_SERVICE,
    REVIEW_SERVICE,
    SAVE_OPTION,
    PROVENANCE,
    IMMUTABLE_GUARD,
    REVIEW_GUARD,
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C25Wp22CommercialBriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entity_defs = json.loads(read(ENTITY_DEFS))
        cls.scopes = json.loads(read(SCOPES))
        cls.proposal = read(PROPOSAL_SERVICE)
        cls.review = read(REVIEW_SERVICE)
        cls.provenance = read(PROVENANCE)
        cls.immutable = read(IMMUTABLE_GUARD)
        cls.review_guard = read(REVIEW_GUARD)
        cls.controller = read(CONTROLLER)
        cls.fixture = json.loads(read(FIXTURE))

    def test_required_files_exist(self) -> None:
        for path in PHP_SOURCES + [ENTITY_DEFS, SCOPES, CLIENT_DEFS, ACL_DEFS, FIXTURE]:
            self.assertTrue(path.is_file(), msg=f"missing {path}")

    def test_boundary_no_runtime_or_connector_markers(self) -> None:
        for path in PHP_SOURCES:
            source = read(path)
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                self.assertNotIn(
                    marker,
                    source,
                    msg=f"{path.name} must not contain runtime marker {marker}",
                )

    def test_boundary_no_provider_or_aijob_executor(self) -> None:
        blob = "\n".join(read(p) for p in PHP_SOURCES)
        self.assertNotIn("ProviderBindingService", blob)
        self.assertNotIn("AIJobService", blob)
        self.assertNotIn("AIDispatchService", blob)
        self.assertNotIn("getEntity('AIJob'", blob)
        self.assertNotIn("ENTITY_TYPE = 'AIJob'", blob)
        self.assertNotIn("provider invoke", blob.lower())
        self.assertNotIn("HTTP outbound", blob)

    def test_lifecycle_states_and_matrix(self) -> None:
        options = self.entity_defs["fields"]["reviewStatus"]["options"]
        self.assertEqual(
            options,
            ["GENERATED", "REVIEWED", "ACCEPTED", "DISMISSED"],
        )
        self.assertIn("'GENERATED' => ['REVIEWED']", self.review_guard)
        self.assertIn("'REVIEWED' => ['ACCEPTED', 'DISMISSED']", self.review_guard)
        self.assertIn("'ACCEPTED' => []", self.review_guard)
        self.assertIn("'DISMISSED' => []", self.review_guard)
        self.assertIn("function markReviewed", self.review)
        self.assertIn("function accept", self.review)
        self.assertIn("function dismiss", self.review)
        # No direct GENERATED -> ACCEPTED/DISMISSED
        self.assertNotRegex(
            self.review_guard,
            r"'GENERATED'\s*=>\s*\[[^\]]*'ACCEPTED'",
        )
        self.assertNotRegex(
            self.review_guard,
            r"'GENERATED'\s*=>\s*\[[^\]]*'DISMISSED'",
        )

    def test_acl_ai_system_cannot_accept_or_dismiss(self) -> None:
        self.assertIn("assertHumanReviewer", self.review)
        self.assertIn("type === 'api'", self.review)
        self.assertIn("type === 'system'", self.review)
        self.assertIn("AI/system cannot accept, dismiss, or override review", self.review)
        self.assertIn("actorKind' => 'HUMAN'", self.review)
        self.assertIn("$actorKind !== 'HUMAN'", self.review_guard)

    def test_proposal_sources_are_fixture_manual_stub_only(self) -> None:
        sources = self.entity_defs["fields"]["proposalSource"]["options"]
        self.assertEqual(sources, ["FIXTURE", "MANUAL", "STUB"])
        self.assertIn("SOURCE_FIXTURE", self.proposal)
        self.assertIn("SOURCE_MANUAL", self.proposal)
        self.assertIn("SOURCE_STUB", self.proposal)
        self.assertNotIn("LIVE", self.proposal)
        self.assertNotIn("PROVIDER", self.proposal)

    def test_provenance_fields_required(self) -> None:
        fields = self.entity_defs["fields"]
        for key in (
            "sourceEvidenceReference",
            "generationContext",
            "capabilityReference",
            "purposeReference",
        ):
            self.assertTrue(fields[key]["required"], msg=f"{key} must be required")
        self.assertEqual(fields["capabilityReference"]["default"], "COMMERCIAL_BRIEF")
        self.assertEqual(
            fields["purposeReference"]["default"],
            "commercial_brief_generation",
        )
        self.assertIn("assertComplete", self.provenance)
        self.assertIn("CAPABILITY_COMMERCIAL_BRIEF", self.provenance)
        self.assertIn("PURPOSE_COMMERCIAL_BRIEF_GENERATION", self.provenance)
        # Acceptance path re-validates provenance
        self.assertIn("provenanceValidator->assertComplete", self.review)

    def test_fixture_preserves_evidence_references(self) -> None:
        self.assertEqual(self.fixture["proposalSource"], "FIXTURE")
        self.assertEqual(self.fixture["capabilityReference"], "COMMERCIAL_BRIEF")
        self.assertEqual(
            self.fixture["purposeReference"],
            "commercial_brief_generation",
        )
        self.assertTrue(self.fixture["sourceEvidenceReference"])
        self.assertTrue(self.fixture["generationContext"])

    def test_scopes_and_module_boundary(self) -> None:
        self.assertEqual(self.scopes["module"], "CommercialIntelligence")
        self.assertTrue(self.scopes["acl"])
        self.assertEqual(self.scopes["statusField"], "reviewStatus")
        self.assertIn("create", self.scopes["aclActionList"])
        self.assertIn("read", self.scopes["aclActionList"])

    def test_create_and_transition_require_save_options(self) -> None:
        self.assertIn("PROPOSAL_CREATE_AUTHORIZED", read(SAVE_OPTION))
        self.assertIn("REVIEW_TRANSITION_AUTHORIZED", read(SAVE_OPTION))
        self.assertIn("PROPOSAL_CREATE_AUTHORIZED", self.immutable)
        self.assertIn("REVIEW_TRANSITION_AUTHORIZED", self.review_guard)
        self.assertIn("CommercialBriefProposalService", self.immutable)
        self.assertIn("CommercialBriefReviewService", self.review_guard)

    def test_no_c22_lifecycle_ownership(self) -> None:
        blob = "\n".join(read(p) for p in PHP_SOURCES)
        for marker in (
            "ProspectCandidate",
            "ProspectRun",
            "ExecutionLedger",
            "outreach",
            "Lead::",
            "Opportunity::",
        ):
            self.assertNotIn(marker, blob)


if __name__ == "__main__":
    unittest.main()
