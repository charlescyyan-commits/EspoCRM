"""Phase3C24 WP1 reply-intelligence governance boundary tests."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
METADATA = MODULE / "Resources" / "metadata"
ENTITY = "ReplySignal"

ENTITY_CLASS = MODULE / "Entities" / f"{ENTITY}.php"
SERVICE = MODULE / "Services" / f"{ENTITY}Service.php"
SAVE_OPTION = MODULE / "Services" / "C24ReplySignalSaveOption.php"
IMMUTABLE_GUARD = MODULE / "Hooks" / ENTITY / f"{ENTITY}ImmutableGuard.php"
LIFECYCLE_GUARD = MODULE / "Hooks" / ENTITY / f"{ENTITY}LifecycleGuard.php"
ENTITY_DEF = METADATA / "entityDefs" / f"{ENTITY}.json"
SCOPE = METADATA / "scopes" / f"{ENTITY}.json"
ACL_DEF = METADATA / "aclDefs" / f"{ENTITY}.json"
WP1_PHP = [
    ENTITY_CLASS,
    SERVICE,
    SAVE_OPTION,
    IMMUTABLE_GUARD,
    LIFECYCLE_GUARD,
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def wp1_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in WP1_PHP)


def test_reply_signal_entity_exists_and_is_advisory() -> None:
    assert ENTITY_CLASS.is_file()
    assert ENTITY_DEF.is_file()
    source = ENTITY_CLASS.read_text(encoding="utf-8")
    assert f"final class {ENTITY}" in source
    assert f"ENTITY_TYPE = '{ENTITY}'" in source
    assert "advisory" in source.lower()


def test_entity_has_only_governed_reply_intelligence_fields() -> None:
    definition = load_json(ENTITY_DEF)
    fields = set(definition["fields"])
    assert fields == {
        "name",
        "sourceReference",
        "interpretation",
        "confidence",
        "provenance",
        "freshnessStatus",
        "status",
        "transitionedAt",
        "transitionedByReference",
        "decisionNote",
        "lifecycleAudit",
        "createdAt",
    }
    forbidden = {
        "actionGateId",
        "executionCommand",
        "workflowId",
        "providerId",
        "credentialId",
        "leadId",
        "opportunityId",
        "acceptedOpportunityId",
        "salesStage",
        "qualificationScore",
        "rankingScore",
        "optimizationInsightId",
        "performanceMetricId",
    }
    assert not fields & forbidden
    assert "links" not in definition
    assert "relationships" not in definition
    assert all(field.get("readOnly") for field in definition["fields"].values())


def test_provenance_freshness_and_review_lifecycle_are_governed() -> None:
    fields = load_json(ENTITY_DEF)["fields"]
    assert fields["sourceReference"]["required"]
    assert fields["provenance"]["required"]
    assert set(fields["freshnessStatus"]["options"]) == {
        "CURRENT",
        "AGING",
        "STALE",
        "ARCHIVAL",
    }
    assert fields["status"]["default"] == "RECEIVED"
    assert fields["status"]["options"] == [
        "RECEIVED",
        "INTERPRETED",
        "REVIEWED",
        "CONVERTED",
        "DISMISSED",
    ]
    source = SERVICE.read_text(encoding="utf-8")
    assert "ReplyDetection reference" in source
    assert "interpretation must be advisory" in source
    assert "lifecycle audit" in source.lower()


def test_immutable_guard_blocks_update_delete_and_direct_creation() -> None:
    source = IMMUTABLE_GUARD.read_text(encoding="utf-8")
    assert "BeforeSave" in source
    assert "BeforeRemove" in source
    assert "!$entity->isNew()" in source
    assert "REPLY_SIGNAL_CREATE_AUTHORIZED" in source
    assert "LIFECYCLE_MUTATION_AUTHORIZED" in source
    assert "cannot be deleted" in source


def test_lifecycle_is_closed_human_governed_and_auditable() -> None:
    source = LIFECYCLE_GUARD.read_text(encoding="utf-8")
    for transition in (
        "'RECEIVED' => ['INTERPRETED']",
        "'INTERPRETED' => ['REVIEWED']",
        "'REVIEWED' => ['CONVERTED', 'DISMISSED']",
        "'CONVERTED' => []",
        "'DISMISSED' => []",
    ):
        assert transition in source
    assert "transitionedAt" in source
    assert "transitionedByReference" in source
    assert "lifecycleAudit" in source
    assert "interpretation is immutable after interpretation" in source
    assert "Dismissed ReplySignal requires a decisionNote" in source


def test_service_has_only_governed_create_read_and_lifecycle_methods() -> None:
    source = SERVICE.read_text(encoding="utf-8")
    public_methods = set(re.findall(r"public function\s+(\w+)", source))
    assert public_methods == {
        "__construct",
        "create",
        "interpret",
        "review",
        "convert",
        "dismiss",
        "read",
        "validate",
    }
    assert "checkEntityRead" in source
    assert "checkEntityEdit" in source
    assert "authenticated human" in source.lower()
    assert not re.search(r"function\s+(execute|approve|trigger|send)\b", source, re.I)


def test_acl_allows_authorized_read_and_service_governed_review_only() -> None:
    scope = load_json(SCOPE)
    acl = load_json(METADATA / "app" / "acl.json")
    portal_acl = load_json(METADATA / "app" / "aclPortal.json")
    assert scope["entity"] is True
    assert scope["acl"] is True
    assert scope["aclPortal"] is False
    assert scope["tab"] is False
    assert load_json(ACL_DEF) == {}
    assert acl["mandatory"]["scopeLevel"][ENTITY] is False
    assert acl["adminMandatory"]["scopeLevel"][ENTITY] == {
        "create": "yes",
        "read": "all",
        "edit": "all",
        "delete": "no",
    }
    assert portal_acl["mandatory"]["scopeLevel"][ENTITY] is False
    assert "must use its governance service" in IMMUTABLE_GUARD.read_text(encoding="utf-8")


def test_c22_c23_and_crm_boundaries_are_reference_only() -> None:
    source = wp1_source()
    assert "'ReplyDetection'" in source
    forbidden = (
        "ActionGateService",
        "ExecutionLedgerService",
        "ProspectRunLifecycleService",
        "OptimizationInsight",
        "PerformanceMetric",
        "OpportunityCandidate",
        "getEntity('Lead')",
        "getEntity('Opportunity')",
        "ACCEPTED",
    )
    for value in forbidden:
        assert value not in source, value
    assert not re.search(r"saveEntity\([^)]*(ActionGate|ProspectRun|ExecutionLedger)", source)


def test_no_autonomy_egress_vendor_or_secret_leakage() -> None:
    source = wp1_source().lower()
    forbidden = (
        "replyagent",
        "autoreplyengine",
        "opportunitycreator",
        "salesagent",
        "curl",
        "guzzlehttp",
        "file_get_contents",
        "httpclient",
        "sdk",
        "provider",
        "credential",
        "secret",
        "scheduler",
        "worker",
        "queue",
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


def test_extension_inventory_lists_every_new_php_file() -> None:
    inventory = (EXT / "tests" / "test_extension_skeleton.py").read_text(encoding="utf-8")
    for path in WP1_PHP:
        assert path.name in inventory
