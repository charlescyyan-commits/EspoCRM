"""Phase3C23 WP2 feedback-learning governance boundary tests."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
METADATA = MODULE / "Resources" / "metadata"
ENTITY = "FeedbackLearningObservation"

ENTITY_CLASS = MODULE / "Entities" / f"{ENTITY}.php"
SERVICE = MODULE / "Services" / f"{ENTITY}Service.php"
SAVE_OPTION = MODULE / "Services" / "C23FeedbackLearningSaveOption.php"
GUARD = MODULE / "Hooks" / ENTITY / f"{ENTITY}ImmutableGuard.php"
ENTITY_DEF = METADATA / "entityDefs" / f"{ENTITY}.json"
SCOPE = METADATA / "scopes" / f"{ENTITY}.json"
ACL_DEF = METADATA / "aclDefs" / f"{ENTITY}.json"
WP2_PHP = [ENTITY_CLASS, SERVICE, SAVE_OPTION, GUARD]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def wp2_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in WP2_PHP)


def test_feedback_learning_observation_entity_exists() -> None:
    assert ENTITY_CLASS.is_file()
    assert ENTITY_DEF.is_file()
    assert f"final class {ENTITY}" in ENTITY_CLASS.read_text(encoding="utf-8")
    assert f"ENTITY_TYPE = '{ENTITY}'" in ENTITY_CLASS.read_text(encoding="utf-8")


def test_entity_contains_only_approved_governance_fields() -> None:
    definition = load_json(ENTITY_DEF)
    assert set(definition["fields"]) == {
        "name",
        "observationType",
        "description",
        "sourceReference",
        "feedbackReference",
        "metricReference",
        "aggregationPeriodStart",
        "aggregationPeriodEnd",
        "confidence",
        "sampleSize",
        "freshnessStatus",
        "status",
        "createdAt",
    }
    forbidden = {
        "actionId",
        "actionGateId",
        "executionCommand",
        "approvalDecision",
        "workflowId",
        "providerId",
        "leadId",
        "opportunityId",
        "prospectId",
        "qualificationScore",
        "rankingScore",
        "policyChange",
    }
    assert not (set(definition["fields"]) & forbidden)
    assert "links" not in definition
    assert "relationships" not in definition
    assert all(field.get("readOnly") for field in definition["fields"].values())


def test_sample_freshness_and_initial_status_are_governed() -> None:
    definition = load_json(ENTITY_DEF)["fields"]
    assert definition["sampleSize"]["min"] == 2
    assert set(definition["freshnessStatus"]["options"]) == {
        "CURRENT",
        "AGING",
        "STALE",
        "ARCHIVAL",
    }
    assert definition["status"]["default"] == "OBSERVED"
    assert definition["status"]["options"] == ["OBSERVED"]
    source = SERVICE.read_text(encoding="utf-8")
    assert "sampleSize must be at least 2" in source
    assert "new records must be OBSERVED" in source


def test_immutable_guard_blocks_update_delete_and_direct_creation() -> None:
    source = GUARD.read_text(encoding="utf-8")
    assert "BeforeSave" in source
    assert "BeforeRemove" in source
    assert "!$entity->isNew()" in source
    assert "OBSERVATION_CREATE_AUTHORIZED" in source
    assert "cannot be deleted" in source


def test_acl_allows_authorized_read_and_disables_edit_delete_portal() -> None:
    scope = load_json(SCOPE)
    acl = load_json(METADATA / "app" / "acl.json")
    portal_acl = load_json(METADATA / "app" / "aclPortal.json")
    assert scope["acl"] is True
    assert scope["aclPortal"] is False
    assert scope["tab"] is False
    assert load_json(ACL_DEF) == {}
    assert acl["mandatory"]["scopeLevel"][ENTITY] is False
    assert acl["adminMandatory"]["scopeLevel"][ENTITY] == {
        "create": "yes",
        "read": "all",
        "edit": "no",
        "delete": "no",
    }
    assert portal_acl["mandatory"]["scopeLevel"][ENTITY] is False


def test_c21_sources_are_reference_only_and_never_mutated() -> None:
    source = SERVICE.read_text(encoding="utf-8")
    assert "['HumanFeedback']" in source
    for entity in ("AIQualificationInsight", "ResearchEvidence", "HumanFeedback"):
        assert not re.search(
            rf"get(?:New)?Entity\(\s*['\"]{entity}['\"]",
            source,
        )
        assert not re.search(rf"saveEntity\([^)]*{entity}", source, re.IGNORECASE)


def test_c22_outcomes_are_aggregate_references_without_authority() -> None:
    source = SERVICE.read_text(encoding="utf-8")
    assert "'ProspectRun'" in source
    assert "'ExecutionLedger'" in source
    assert "'ActionGate'" not in source
    for entity in ("ProspectRun", "ExecutionLedger", "ActionGate"):
        assert not re.search(
            rf"get(?:New)?Entity\(\s*['\"]{entity}['\"]",
            source,
        )
    assert "ActionGateService" not in source
    assert "decide(" not in source


def test_service_is_create_validate_read_and_advisory_only() -> None:
    source = SERVICE.read_text(encoding="utf-8")
    public_methods = set(re.findall(r"public function\s+(\w+)", source))
    assert public_methods == {"__construct", "create", "read", "validate"}
    assert "checkEntityRead" in source
    assert "must be observational" in source
    assert not re.search(
        r"function\s+(execute|apply|approve|trigger|mutate)\b",
        source,
        re.IGNORECASE,
    )


def test_no_automation_egress_vendor_or_secret_leakage() -> None:
    source = wp2_source().lower()
    forbidden = (
        "learningagent",
        "autooptimizer",
        "scheduler",
        "worker",
        "queue",
        "automation",
        "curl",
        "guzzlehttp",
        "file_get_contents",
        "httpclient",
        "http://",
        "https://",
        "sdk",
        "credential",
        "secret",
        "api key",
        "access token",
        "apify",
        "apollo",
        "hunter",
        "deepseek",
        "openai",
        "instantly",
        "brevo",
        "smtp",
    )
    for value in forbidden:
        assert value not in source, value


def test_extension_inventory_registers_all_wp2_php_files() -> None:
    inventory = (
        EXT / "tests" / "test_extension_skeleton.py"
    ).read_text(encoding="utf-8")
    for path in WP2_PHP:
        assert path.name in inventory
