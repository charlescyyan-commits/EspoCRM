"""Phase3C23 WP3 OptimizationInsight lifecycle governance tests."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
METADATA = MODULE / "Resources" / "metadata"

ENTITY_DEF = METADATA / "entityDefs" / "OptimizationInsight.json"
SCOPE = METADATA / "scopes" / "OptimizationInsight.json"
APP_ACL = METADATA / "app" / "acl.json"
PORTAL_ACL = METADATA / "app" / "aclPortal.json"
CREATE_SERVICE = MODULE / "Services" / "OptimizationInsightService.php"
REVIEW_SERVICE = MODULE / "Services" / "OptimizationInsightReviewService.php"
SAVE_OPTION = (
    MODULE / "Services" / "C23OptimizationInsightLifecycleSaveOption.php"
)
IMMUTABLE_GUARD = (
    MODULE
    / "Hooks"
    / "OptimizationInsight"
    / "OptimizationInsightImmutableGuard.php"
)
LIFECYCLE_GUARD = (
    MODULE
    / "Hooks"
    / "OptimizationInsight"
    / "OptimizationInsightLifecycleGuard.php"
)
WP3_PHP = [REVIEW_SERVICE, SAVE_OPTION, LIFECYCLE_GUARD]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_lifecycle_states_and_review_fields_exist() -> None:
    fields = load_json(ENTITY_DEF)["fields"]
    assert set(fields["status"]["options"]) == {
        "GENERATED",
        "REVIEWED",
        "ACCEPTED",
        "REJECTED",
    }
    assert fields["status"]["default"] == "GENERATED"
    for field in (
        "reviewedAt",
        "reviewedByReference",
        "decisionNote",
        "supersedesInsightId",
    ):
        assert fields[field]["readOnly"] is True


def test_review_service_exposes_only_governed_lifecycle_operations() -> None:
    source = REVIEW_SERVICE.read_text(encoding="utf-8")
    public_methods = set(re.findall(r"public function\s+(\w+)", source))
    assert public_methods == {"__construct", "review", "accept", "reject", "read"}
    assert "STATUS_GENERATED" in source
    assert "STATUS_REVIEWED" in source
    assert "STATUS_ACCEPTED" in source
    assert "STATUS_REJECTED" in source
    assert "checkEntityRead" in source
    assert "checkEntityEdit" in source


def test_valid_transitions_are_closed_and_terminal() -> None:
    source = LIFECYCLE_GUARD.read_text(encoding="utf-8")
    assert "'GENERATED' => ['REVIEWED']" in source
    assert "'REVIEWED' => ['ACCEPTED', 'REJECTED']" in source
    assert "'ACCEPTED' => []" in source
    assert "'REJECTED' => []" in source
    review = REVIEW_SERVICE.read_text(encoding="utf-8")
    assert "self::STATUS_GENERATED" in review
    assert "self::STATUS_REVIEWED" in review
    assert "self::STATUS_ACCEPTED" in review
    assert "self::STATUS_REJECTED" in review


def test_invalid_transitions_and_direct_edits_are_blocked() -> None:
    lifecycle = LIFECYCLE_GUARD.read_text(encoding="utf-8")
    immutable = IMMUTABLE_GUARD.read_text(encoding="utf-8")
    assert "transition {$from} to {$to} is forbidden" in lifecycle
    assert "LIFECYCLE_MUTATION_AUTHORIZED" in lifecycle
    assert "LIFECYCLE_MUTATION_AUTHORIZED" in immutable
    assert "mutation must use its review service" in immutable
    assert "cannot be deleted" in immutable


def test_recommendation_and_provenance_content_remain_immutable() -> None:
    source = LIFECYCLE_GUARD.read_text(encoding="utf-8")
    protected = {
        "recommendation",
        "evidenceReference",
        "sourcePeriodStart",
        "sourcePeriodEnd",
        "generatedAt",
        "supersedesInsightId",
    }
    for field in protected:
        assert f"'{field}'" in source
    assert "isAttributeChanged($field)" in source
    assert "content field {$field} is immutable" in source


def test_supersession_creates_a_new_record_and_prevents_branching() -> None:
    definition = load_json(ENTITY_DEF)
    source = CREATE_SERVICE.read_text(encoding="utf-8")
    assert definition["fields"]["supersedesInsightId"]["readOnly"] is True
    assert "supersedesInsightId" in definition["indexes"]
    assert "assertSupersession" in source
    assert "getNewEntity(self::ENTITY_TYPE)" in source
    assert "predecessor already has a successor" in source
    assert "new records must be GENERATED" in source


def test_no_execution_or_approval_state_exists() -> None:
    definition_text = ENTITY_DEF.read_text(encoding="utf-8")
    forbidden = (
        "EXECUTE",
        "APPROVED_FOR_EXECUTION",
        "TRIGGERED",
        "AUTOMATED",
        "executionCommand",
        "approvalDecision",
    )
    for value in forbidden:
        assert value not in definition_text
    source = REVIEW_SERVICE.read_text(encoding="utf-8")
    assert not re.search(
        r"public function\s+(execute|apply|approve|trigger)",
        source,
        re.IGNORECASE,
    )


def test_no_action_gate_c21_or_c22_mutation_path_exists() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in WP3_PHP)
    forbidden = (
        "ActionGate",
        "ExecutionLedger",
        "ProspectRun",
        "AIQualificationInsight",
        "ResearchEvidence",
        "HumanFeedback",
        "Lead",
        "Opportunity",
    )
    for value in forbidden:
        assert value not in source
    assert "links" not in load_json(ENTITY_DEF)


def test_acl_authorizes_guarded_review_not_arbitrary_edit_or_portal() -> None:
    scope = load_json(SCOPE)
    acl = load_json(APP_ACL)["adminMandatory"]["scopeLevel"]["OptimizationInsight"]
    portal = load_json(PORTAL_ACL)["mandatory"]["scopeLevel"]
    assert scope["acl"] is True
    assert scope["aclPortal"] is False
    assert acl == {
        "create": "yes",
        "read": "all",
        "edit": "all",
        "delete": "no",
    }
    assert portal["OptimizationInsight"] is False
    assert "LIFECYCLE_MUTATION_AUTHORIZED" in IMMUTABLE_GUARD.read_text(
        encoding="utf-8"
    )


def test_no_egress_credentials_vendor_or_automation_runtime() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in WP3_PHP).lower()
    forbidden = (
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
        "automationrule",
        "scheduler",
        "worker",
        "queue",
    )
    for value in forbidden:
        assert value not in source, value


def test_extension_inventory_registers_wp3_php_files() -> None:
    inventory = (
        EXT / "tests" / "test_extension_skeleton.py"
    ).read_text(encoding="utf-8")
    for path in WP3_PHP:
        assert path.name in inventory
