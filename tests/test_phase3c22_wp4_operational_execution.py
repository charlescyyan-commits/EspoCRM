"""Phase3C22 WP4 operator workspace and control-boundary contracts."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "crm-extension"
MODULE = (
    EXTENSION
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "Prospecting"
)
RESOURCES = MODULE / "Resources"
CLIENT_DEFS = RESOURCES / "metadata" / "clientDefs"
SELECT_DEFS = RESOURCES / "metadata" / "selectDefs"
SCOPES = RESOURCES / "metadata" / "scopes"
LAYOUTS = RESOURCES / "layouts"
I18N_EN = RESOURCES / "i18n" / "en_US"

WORKSPACE_SCOPE = SCOPES / "ExecutionWorkspace.json"
WORKSPACE_CLIENT = CLIENT_DEFS / "ExecutionWorkspace.json"
WORKSPACE_CONTROLLER = (
    EXTENSION
    / "files"
    / "client"
    / "custom"
    / "src"
    / "controllers"
    / "execution-workspace.js"
)
WORKSPACE_VIEW = (
    EXTENSION
    / "files"
    / "client"
    / "custom"
    / "src"
    / "views"
    / "prospecting"
    / "execution-workspace.js"
)
WORKSPACE_TEMPLATE = (
    EXTENSION
    / "files"
    / "client"
    / "custom"
    / "res"
    / "templates"
    / "prospecting"
    / "execution-workspace.tpl"
)
DECISION_HANDLER = (
    EXTENSION
    / "files"
    / "client"
    / "custom"
    / "src"
    / "handlers"
    / "action-gate"
    / "decision.js"
)
DECISION_API = MODULE / "Api" / "PostActionGateDecision.php"
GATE_SERVICE = MODULE / "Services" / "ActionGateService.php"
LEDGER_GUARD = (
    MODULE
    / "Hooks"
    / "ExecutionLedger"
    / "ExecutionLedgerAppendOnlyGuard.php"
)
APP_ACL = RESOURCES / "metadata" / "app" / "acl.json"
PORTAL_ACL = RESOURCES / "metadata" / "app" / "aclPortal.json"
ROUTES = RESOURCES / "routes.json"

VENDOR_NAMES = {
    "apify",
    "apollo",
    "hunter",
    "deepseek",
    "openai",
    "instantly",
    "brevo",
    "smtp",
}
SECRET_TERMS = {
    "apiKey",
    "apiSecret",
    "accessToken",
    "refreshToken",
    "password",
    "secretValue",
    "plaintextCredential",
    "encryptedSecret",
    "privateKey",
}
EGRESS_PATTERNS = (
    r"\bcurl(?:_[A-Za-z0-9_]+)?\b",
    r"\bGuzzleHttp\b",
    r"\bfile_get_contents\s*\(",
    r"\bHttpClient\b",
    r"\bClientInterface\b",
    r"\bstream_socket_client\b",
    r"\bfsockopen\b",
    r"\b(?:requests|urllib3|httpx|aiohttp)\b",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(read(path))


def wp4_sources() -> dict[str, str]:
    files = [
        DECISION_API,
        DECISION_HANDLER,
        WORKSPACE_CONTROLLER,
        WORKSPACE_VIEW,
        WORKSPACE_TEMPLATE,
        GATE_SERVICE,
    ]
    for directory in ("ProspectRun", "ActionGate", "ExecutionLedger"):
        files.extend(
            (
                MODULE
                / "Classes"
                / "Select"
                / directory
                / "PrimaryFilters"
            ).glob("*.php")
        )

    return {
        path.relative_to(ROOT).as_posix(): read(path)
        for path in files
    }


def test_execution_workspace_is_read_oriented_and_acl_filtered() -> None:
    scope = load_json(WORKSPACE_SCOPE)
    client = load_json(WORKSPACE_CLIENT)
    view = read(WORKSPACE_VIEW)
    template = read(WORKSPACE_TEMPLATE)

    assert scope == {
        "entity": False,
        "object": False,
        "tab": True,
        "acl": False,
        "module": "Prospecting",
        "type": "Base",
    }
    assert client["controller"] == "custom:controllers/execution-workspace"
    assert WORKSPACE_CONTROLLER.is_file()
    assert "custom:views/prospecting/execution-workspace" in read(
        WORKSPACE_CONTROLLER
    )
    assert "getAcl().check" in view
    assert "countRecords" in view
    assert "postRequest" not in view
    assert "execute" not in view.casefold()

    for surface in (
        "runsActive",
        "pendingApproval",
        "runsCompleted",
        "runsFailed",
        "executionFailures",
    ):
        assert surface in view or surface in template


def test_approval_queue_displays_required_governance_fields() -> None:
    client = load_json(CLIENT_DEFS / "ActionGate.json")
    detail = load_json(LAYOUTS / "ActionGate" / "detail.json")
    list_layout = load_json(LAYOUTS / "ActionGate" / "list.json")
    select = load_json(SELECT_DEFS / "ActionGate.json")

    assert client["filterList"] == [{"name": "pendingApproval"}]
    assert set(select["primaryFilterClassNameMap"]) == {
        "pendingApproval"
    }
    pending_filter = read(
        MODULE
        / "Classes"
        / "Select"
        / "ActionGate"
        / "PrimaryFilters"
        / "PendingApproval.php"
    )
    assert "$queryBuilder->where(['decision' => 'PENDING'])" in pending_filter

    detail_fields = {
        cell["name"]
        for section in detail
        for row in section["rows"]
        for cell in row
    }
    list_fields = {field["name"] for field in list_layout}
    assert {
        "actionType",
        "actionReference",
        "createdAt",
        "decision",
    }.issubset(detail_fields)
    assert {
        "actionType",
        "actionReference",
        "createdAt",
        "decision",
    }.issubset(list_fields)


def test_operator_decisions_are_explicit_and_use_action_gate_service() -> None:
    client = load_json(CLIENT_DEFS / "ActionGate.json")
    actions = client["detailActionList"][1:]
    api = read(DECISION_API)
    handler = read(DECISION_HANDLER)
    service = read(GATE_SERVICE)
    routes = load_json(ROUTES)

    assert {
        action["actionFunction"]
        for action in actions
    } == {"approve", "deny", "defer"}
    assert all(action["acl"] == "edit" for action in actions)
    assert all(
        action["handler"] == "custom:handlers/action-gate/decision"
        for action in actions
    )
    assert all(
        action["checkVisibilityFunction"] == "isDecisionVisible"
        for action in actions
    )

    assert "private ActionGateService $service" in api
    assert "private Acl $acl" in api
    assert "$this->acl->checkEntityRead($gate)" in api
    assert "$this->service->decide(" in api
    assert "ExecutionOrchestrationService" not in api
    assert "ConnectorBoundary" not in api
    assert "$this->acl->checkEntityEdit($gate)" in service

    assert "this.view.getAcl().check('ActionGate', 'edit')" in handler
    assert "this.view.model.get('decision') === 'PENDING'" in handler
    assert "Prospecting/action-gate/" in handler
    assert "/decision/" in handler
    assert "/execute" not in handler

    assert {
        "route": "/Prospecting/action-gate/:id/decision/:decision",
        "method": "post",
        "actionClassName":
            "Espo\\Modules\\Prospecting\\Api\\PostActionGateDecision",
    } in routes


def test_read_and_decision_permissions_are_separate() -> None:
    workspace = read(WORKSPACE_VIEW)
    handler = read(DECISION_HANDLER)
    app_acl = load_json(APP_ACL)
    portal_acl = load_json(PORTAL_ACL)

    assert "acl.check(card.entityType, 'read')" in workspace
    assert "this.view.getAcl().check('ActionGate', 'edit')" in handler

    gate_acl = app_acl["adminMandatory"]["scopeLevel"]["ActionGate"]
    ledger_acl = app_acl["adminMandatory"]["scopeLevel"]["ExecutionLedger"]
    assert gate_acl["read"] == "all"
    assert gate_acl["edit"] == "all"
    assert ledger_acl == {
        "create": "yes",
        "read": "all",
        "edit": "no",
        "delete": "no",
    }
    assert portal_acl["mandatory"]["scopeLevel"]["ActionGate"] is False
    assert portal_acl["mandatory"]["scopeLevel"]["ExecutionLedger"] is False


def test_run_monitoring_and_failure_review_use_existing_records() -> None:
    run_client = load_json(CLIENT_DEFS / "ProspectRun.json")
    run_select = load_json(SELECT_DEFS / "ProspectRun.json")
    run_detail = load_json(LAYOUTS / "ProspectRun" / "detail.json")
    ledger_detail = load_json(LAYOUTS / "ExecutionLedger" / "detail.json")
    ledger_list = load_json(LAYOUTS / "ExecutionLedger" / "list.json")
    ledger_select = load_json(SELECT_DEFS / "ExecutionLedger.json")

    assert set(run_select["primaryFilterClassNameMap"]) == {
        "runsActive",
        "runsCompleted",
        "runsFailed",
    }
    assert set(run_client["relationshipPanels"]) == {
        "candidates",
        "actionGates",
        "ledgerEntries",
    }
    assert all(
        panel["create"] is False and panel["select"] is False
        for panel in run_client["relationshipPanels"].values()
    )

    run_fields = {
        cell["name"]
        for section in run_detail
        for row in section["rows"]
        for cell in row
    }
    assert {"status", "createdAt", "runKey"}.issubset(run_fields)

    ledger_fields = {
        cell["name"]
        for section in ledger_detail
        for row in section["rows"]
        for cell in row
    }
    assert {
        "failureCategory",
        "actionGate",
        "eventType",
        "outcome",
        "occurredAt",
    }.issubset(ledger_fields)
    assert {
        "failureCategory",
        "actionGate",
        "eventType",
        "outcome",
        "occurredAt",
    }.issubset({field["name"] for field in ledger_list})
    assert set(ledger_select["primaryFilterClassNameMap"]) == {
        "executionFailures"
    }


def test_execution_ledger_ui_and_persistence_remain_read_only() -> None:
    client = load_json(CLIENT_DEFS / "ExecutionLedger.json")
    gate_client = load_json(CLIENT_DEFS / "ActionGate.json")
    guard = read(LEDGER_GUARD)

    assert "detailActionList" not in client
    assert "edit" not in json.dumps(client)
    ledger_panel = gate_client["relationshipPanels"]["ledgerEntries"]
    assert ledger_panel["create"] is False
    assert ledger_panel["select"] is False
    assert "append-only and cannot be modified" in guard
    assert "append-only and cannot be deleted" in guard


def test_wp4_creates_no_duplicate_execution_entities() -> None:
    for forbidden_entity in (
        "ApprovalRequest",
        "ExecutionHistory",
        "AgentTask",
    ):
        assert not (
            RESOURCES
            / "metadata"
            / "entityDefs"
            / f"{forbidden_entity}.json"
        ).exists()
        assert not (
            MODULE / "Entities" / f"{forbidden_entity}.php"
        ).exists()


def test_wp4_has_no_provider_runtime_vendor_or_secret_surface() -> None:
    for file_name, source in wp4_sources().items():
        lowered = source.casefold()
        for vendor in VENDOR_NAMES:
            assert vendor not in lowered, f"{file_name}: {vendor}"
        for pattern in EGRESS_PATTERNS:
            assert not re.search(
                pattern,
                source,
                flags=re.IGNORECASE,
            ), f"{file_name}: {pattern}"
        for secret in SECRET_TERMS:
            assert secret.casefold() not in lowered, f"{file_name}: {secret}"

    metadata_paths = [
        CLIENT_DEFS / "ExecutionWorkspace.json",
        CLIENT_DEFS / "ProspectRun.json",
        CLIENT_DEFS / "ActionGate.json",
        CLIENT_DEFS / "ExecutionLedger.json",
        LAYOUTS / "ProspectRun" / "detail.json",
        LAYOUTS / "ProspectRun" / "list.json",
        LAYOUTS / "ActionGate" / "detail.json",
        LAYOUTS / "ActionGate" / "list.json",
        LAYOUTS / "ExecutionLedger" / "detail.json",
        LAYOUTS / "ExecutionLedger" / "list.json",
    ]
    metadata_sources = "\n".join(read(path) for path in metadata_paths)
    for secret in SECRET_TERMS:
        assert secret.casefold() not in metadata_sources.casefold()


def test_wp4_has_no_crm_mutation_or_autonomous_loop() -> None:
    sources = "\n".join(wp4_sources().values())

    for forbidden in (
        "getNewEntity('Lead')",
        'getNewEntity("Lead")',
        "getNewEntity('Opportunity')",
        'getNewEntity("Opportunity")',
        "saveEntity($lead",
        "saveEntity($opportunity",
        "salesStage",
        "canonical_score",
        "ExecutionOrchestrationService",
        "ConnectorBoundary",
    ):
        assert forbidden not in sources

    for loop_pattern in (
        r"\bwhile\s*\(",
        r"\bdo\s*\{",
        r"\bsleep\s*\(",
        r"\busleep\s*\(",
    ):
        assert not re.search(loop_pattern, sources, flags=re.IGNORECASE)

    for forbidden_path in (
        MODULE / "Jobs" / "ExecutionWorkspace.php",
        MODULE / "Workers" / "ExecutionWorkspace.php",
        MODULE / "Schedulers" / "ExecutionWorkspace.php",
    ):
        assert not forbidden_path.exists()
