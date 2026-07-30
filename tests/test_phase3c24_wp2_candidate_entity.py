"""Phase3C24 WP2.1 OpportunityCandidate entity foundation tests."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
METADATA = MODULE / "Resources" / "metadata"
ENTITY = "OpportunityCandidate"

ENTITY_CLASS = MODULE / "Entities" / f"{ENTITY}.php"
ENTITY_DEF = METADATA / "entityDefs" / f"{ENTITY}.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_opportunity_candidate_entity_exists() -> None:
    assert ENTITY_CLASS.is_file()
    assert ENTITY_DEF.is_file()
    source = ENTITY_CLASS.read_text(encoding="utf-8")
    assert f"final class {ENTITY}" in source
    assert f"ENTITY_TYPE = '{ENTITY}'" in source
    assert "governance artifact" in source.lower()


def test_entity_has_exactly_the_approved_field_contract() -> None:
    definition = load_json(ENTITY_DEF)
    assert set(definition["fields"]) == {
        "name",
        "provenanceReference",
        "status",
        "reviewContext",
        "commercialSignalSummary",
        "transitionHistory",
        "lastTransitionBy",
        "lastTransitionAt",
        "outcomeReference",
        "outcomeNote",
        "outcomeRecordedAt",
        "createdAt",
        "createdBy",
    }
    assert "links" not in definition
    assert "relationships" not in definition
    assert all(field.get("readOnly") for field in definition["fields"].values())


def test_status_declares_the_approved_governance_state_space() -> None:
    status = load_json(ENTITY_DEF)["fields"]["status"]
    assert status["default"] == "IDENTIFIED"
    assert status["options"] == [
        "IDENTIFIED",
        "REVIEW_PENDING",
        "ACCEPTED",
        "ACTIVE",
        "WON",
        "LOST",
        "REJECTED",
    ]
    assert not (MODULE / "Services" / "OpportunityCandidateService.php").exists()


def test_forbidden_crm_execution_and_automation_fields_are_absent() -> None:
    fields = set(load_json(ENTITY_DEF)["fields"])
    forbidden = {
        "salesStage",
        "stage",
        "closeDate",
        "probability",
        "forecastAmount",
        "forecastCommitment",
        "pipelineValue",
        "opportunityId",
        "accountId",
        "contactId",
        "assignedUser",
        "actionGate",
        "executionStatus",
        "sendStatus",
        "autoApprove",
        "aiDecision",
        "confidenceScoreForAcceptance",
    }
    assert not fields & forbidden


def test_entity_has_no_cross_layer_or_crm_relationship_reference() -> None:
    definition_source = ENTITY_DEF.read_text(encoding="utf-8")
    entity_source = ENTITY_CLASS.read_text(encoding="utf-8")
    for value in (
        '"entity": "Opportunity"',
        '"entity": "ActionGate"',
        '"entity": "ExecutionLedger"',
        '"entity": "AIQualificationInsight"',
        '"entity": "PerformanceMetric"',
        "use Espo\\Entities\\Opportunity",
    ):
        assert value not in definition_source + entity_source, value


def test_no_runtime_security_or_automation_surface_exists() -> None:
    source = ENTITY_CLASS.read_text(encoding="utf-8") + "\n" + ENTITY_DEF.read_text(encoding="utf-8")
    forbidden = (
        "curl",
        "guzzlehttp",
        "file_get_contents",
        "httpclient",
        "sdk",
        "provider",
        "credential",
        "scheduler",
        "queue",
        "worker",
        "secret",
    )
    lower_source = source.lower()
    for value in forbidden:
        assert value not in lower_source, value
    assert not re.search(r"(?i)https?://", source)


def test_extension_inventory_lists_the_entity_class() -> None:
    inventory = (EXT / "tests" / "test_extension_skeleton.py").read_text(encoding="utf-8")
    assert ENTITY_CLASS.name in inventory
