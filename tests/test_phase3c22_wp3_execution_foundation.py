"""Phase3C22 WP3 controlled execution foundation contracts."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "Prospecting"
)
ENTITY_DEFS = MODULE / "Resources" / "metadata" / "entityDefs"
SCOPES = MODULE / "Resources" / "metadata" / "scopes"
SERVICES = MODULE / "Services"
HOOKS = MODULE / "Hooks"
EXECUTION = MODULE / "Execution"
PROVIDER_BOUNDARY = MODULE / "ProviderBoundary"

ACTION = EXECUTION / "ExecutionAction.php"
REPLY_BOUNDARY = EXECUTION / "ReplyDetectionBoundary.php"
RUN_SERVICE = SERVICES / "ProspectRunLifecycleService.php"
ORCHESTRATOR = SERVICES / "ExecutionOrchestrationService.php"
GATE_SERVICE = SERVICES / "ActionGateService.php"
LEDGER_SERVICE = SERVICES / "ExecutionLedgerService.php"
RUN_GUARD = HOOKS / "ProspectRun" / "ProspectRunStatusGuard.php"
LEDGER_GUARD = (
    HOOKS
    / "ExecutionLedger"
    / "ExecutionLedgerAppendOnlyGuard.php"
)

PROVIDER_TYPES = {
    "SEARCH",
    "ENRICHMENT",
    "AI_RESEARCH",
    "OUTREACH",
}
RUN_STATES = [
    "CREATED",
    "PLANNING",
    "WAITING_APPROVAL",
    "EXECUTING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
]
REQUIRED_EVENTS = {
    "ACTION_REQUESTED",
    "APPROVAL_GRANTED",
    "EXECUTION_STARTED",
    "EXECUTION_COMPLETED",
    "EXECUTION_FAILED",
}
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
EGRESS_PATTERNS = (
    r"\bcurl(?:_[A-Za-z0-9_]+)?\b",
    r"\bGuzzleHttp\b",
    r"\bfile_get_contents\s*\(",
    r"\bHttpClient\b",
    r"\bClientInterface\b",
    r"\bstream_socket_client\b",
    r"\bfsockopen\b",
    r"\$(?:httpClient|client|transport)->\s*(?:request|post|send)\s*\(",
    r"\b(?:requests|urllib3|httpx|aiohttp)\b",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(read(path))


def wp3_php_sources() -> dict[str, str]:
    paths = (
        ACTION,
        REPLY_BOUNDARY,
        RUN_SERVICE,
        ORCHESTRATOR,
        GATE_SERVICE,
        LEDGER_SERVICE,
        RUN_GUARD,
        LEDGER_GUARD,
    )
    return {
        path.relative_to(MODULE).as_posix(): read(path)
        for path in paths
    }


def test_execution_action_is_owned_by_candidate_and_run_without_new_entity() -> None:
    source = read(ACTION)

    assert "final class ExecutionAction" in source
    assert "private string $actionId" in source
    assert "private string $prospectCandidateId" in source
    assert "private string $prospectRunId" in source
    assert "private string $providerType" in source
    assert "private ProviderExecutionRequest $request" in source
    assert "ProviderTypeRegistry::assertAllowed" in source
    assert "$request->providerType() !== $this->providerType" in source

    assert not (ENTITY_DEFS / "ExecutionAction.json").exists()
    assert not (MODULE / "Entities" / "ExecutionAction.php").exists()


def test_execution_action_types_are_controlled_capabilities_only() -> None:
    registry = read(PROVIDER_BOUNDARY / "ProviderTypeRegistry.php")
    declared = {
        value
        for _, value in re.findall(
            r"public const ([A-Z_]+) = '([A-Z_]+)';",
            registry,
        )
    }
    assert declared == PROVIDER_TYPES

    gate_service = read(GATE_SERVICE)
    assert "ProviderTypeRegistry::assertAllowed" in gate_service
    assert "controlled provider type" in gate_service


def test_prospect_run_has_closed_lifecycle_and_service_only_mutation() -> None:
    definition = load_json(ENTITY_DEFS / "ProspectRun.json")
    status = definition["fields"]["status"]

    assert status["type"] == "enum"
    assert status["options"] == RUN_STATES
    assert status["default"] == "CREATED"
    assert status["readOnly"] is True
    assert load_json(SCOPES / "ProspectRun.json")["statusField"] == "status"

    service = read(RUN_SERVICE)
    for state in RUN_STATES:
        assert f"STATUS_{state} = '{state}'" in service
    assert "private const TRANSITIONS" in service
    assert "STATUS_WAITING_APPROVAL => [" in service
    assert "STATUS_EXECUTING," in service
    assert "STATUS_COMPLETED => []" in service
    assert "STATUS_FAILED => []" in service
    assert "STATUS_CANCELLED => []" in service

    guard = read(RUN_GUARD)
    assert "PROSPECT_RUN_STATUS_MUTATION_AUTHORIZED" in guard
    assert "must use ProspectRunLifecycleService" in guard


def test_action_gate_approval_is_mandatory_before_connector_execution() -> None:
    lifecycle = read(RUN_SERVICE)
    orchestrator = read(ORCHESTRATOR)

    executing_branch = lifecycle.split(
        "if ($targetStatus === self::STATUS_EXECUTING)",
        1,
    )[1].split("$run->set('status'", 1)[0]
    assert "$this->actionGateService->assertApprovedForExecution($gate)" in executing_branch
    assert "Approved ActionGate must belong to the ProspectRun." in executing_branch

    approval_check = (
        "$this->actionGateService->assertApprovedForExecution($gate);"
    )
    connector_call = (
        "$this->connectorBoundary->execute($action->request())"
    )
    assert approval_check in orchestrator
    assert connector_call in orchestrator
    assert orchestrator.index(approval_check) < orchestrator.index(connector_call)

    gate_service = read(GATE_SERVICE)
    assert "DECISION_DENIED = 'DENIED'" in gate_service
    assert "DECISION_DEFERRED = 'DEFERRED'" in gate_service
    assert (
        "No C22 execution is permitted without an APPROVED ActionGate."
        in gate_service
    )


def test_required_execution_events_are_appended_by_orchestration() -> None:
    definition = load_json(ENTITY_DEFS / "ExecutionLedger.json")
    assert REQUIRED_EVENTS.issubset(
        set(definition["fields"]["eventType"]["options"])
    )

    ledger = read(LEDGER_SERVICE)
    orchestrator = read(ORCHESTRATOR)
    for event in REQUIRED_EVENTS:
        constant = f"EVENT_{event}"
        assert f"{constant} = '{event}'" in ledger
        assert f"ExecutionLedgerService::{constant}" in orchestrator

    assert orchestrator.count(
        "$this->executionLedgerService->append(["
    ) >= len(REQUIRED_EVENTS)


def test_execution_ledger_remains_service_created_and_append_only() -> None:
    guard = read(LEDGER_GUARD)

    assert "implements BeforeSave, BeforeRemove" in guard
    assert "if (!$entity->isNew())" in guard
    assert "append-only and cannot be modified" in guard
    assert "append-only and cannot be deleted" in guard
    assert "EXECUTION_LEDGER_CREATE_AUTHORIZED" in guard
    assert "creation must use ExecutionLedgerService" in guard


def test_orchestrator_uses_only_wp2_connector_contract() -> None:
    source = read(ORCHESTRATOR)

    assert (
        "use Espo\\Modules\\Prospecting\\ProviderBoundary\\ConnectorBoundary;"
        in source
    )
    assert (
        "use Espo\\Modules\\Prospecting\\ProviderBoundary\\ProviderResultEnvelope;"
        in source
    )
    assert "private ConnectorBoundary $connectorBoundary" in source
    assert "$this->connectorBoundary->execute($action->request())" in source
    assert "ProviderAdapterSkeleton" not in source
    assert "new ProviderResultEnvelope" not in source


def test_reply_detection_is_an_immutable_boundary_without_crm_authority() -> None:
    source = read(REPLY_BOUNDARY)

    assert "final class ReplyDetectionBoundary" in source
    assert "private string $replyEventReference" in source
    assert "private string $replyStatus" in source
    assert "private DateTimeImmutable $timestamp" in source
    assert "public function replyEventReference(): string" in source
    assert "public function replyStatus(): string" in source
    assert "public function timestamp(): DateTimeImmutable" in source
    assert "EntityManager" not in source
    assert "saveEntity" not in source


def test_wp3_has_no_provider_egress_vendor_or_sdk_implementation() -> None:
    for file_name, source in wp3_php_sources().items():
        lowered = source.casefold()
        for vendor_name in VENDOR_NAMES:
            assert vendor_name not in lowered, f"{file_name}: {vendor_name}"
        for pattern in EGRESS_PATTERNS:
            assert not re.search(
                pattern,
                source,
                flags=re.IGNORECASE,
            ), f"{file_name}: {pattern}"
        assert not re.search(
            r"^\s*(?:use|require|include).*(?:Sdk|Client)",
            source,
            flags=re.MULTILINE,
        ), file_name


def test_wp3_has_no_crm_lifecycle_or_c21_intelligence_mutation() -> None:
    sources = "\n".join(wp3_php_sources().values())

    for forbidden_call in (
        "getNewEntity('Lead')",
        'getNewEntity("Lead")',
        "getNewEntity('Opportunity')",
        'getNewEntity("Opportunity")',
        "saveEntity($lead",
        "saveEntity($opportunity",
        "salesStage",
        "canonical_score",
    ):
        assert forbidden_call not in sources

    for protected_entity in (
        "ResearchEvidence",
        "AIQualificationInsight",
        "HumanFeedback",
    ):
        assert protected_entity not in sources


def test_wp3_has_no_autonomous_loop_worker_or_scheduler() -> None:
    sources = "\n".join(wp3_php_sources().values())

    for control_pattern in (
        r"\bwhile\s*\(",
        r"\bdo\s*\{",
        r"\bsleep\s*\(",
        r"\busleep\s*\(",
    ):
        assert not re.search(control_pattern, sources, flags=re.IGNORECASE)

    for forbidden_path in (
        MODULE / "Jobs" / "ExecutionOrchestration.php",
        MODULE / "Workers" / "ExecutionOrchestration.php",
        MODULE / "Schedulers" / "ExecutionOrchestration.php",
    ):
        assert not forbidden_path.exists()
