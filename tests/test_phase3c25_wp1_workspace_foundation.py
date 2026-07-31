"""Phase3C25 WP1 Commercial Intelligence Workspace foundation tests.

Boundary and contract tests for the C25 read-only workspace foundation
(ADR-C25-001, ADR-C25-005, ADR-C25-006). WP1 implements runtime context
assembly only: no entities, no persistence, no AI invocation, no writes to
any C20-C24 or CRM Core artifact.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "CommercialIntelligence"
RESOURCES = MODULE / "Resources"
METADATA = RESOURCES / "metadata"
CLIENT = EXT / "files" / "client" / "custom"
WORKSPACE_JS = CLIENT / "src" / "views" / "commercial-intelligence" / "workspace.js"
CONTROLLER_JS = CLIENT / "src" / "controllers" / "commercial-intelligence-workspace.js"
WORKSPACE_TPL = CLIENT / "res" / "templates" / "commercial-intelligence" / "workspace.tpl"
CLIENT_DEFS = (
    METADATA / "clientDefs" / "CommercialIntelligenceWorkspace.json"
)

CONTEXT = MODULE / "Context" / "CommercialContext.php"
SOURCE_REF = MODULE / "Context" / "SourceArtifactReference.php"
PARSER = MODULE / "Context" / "ArtifactReferenceParser.php"
ASSEMBLY = MODULE / "Services" / "ContextAssemblyService.php"
VISIBILITY = MODULE / "Services" / "VisibilityInheritanceService.php"
PROVENANCE = MODULE / "Services" / "ProvenancePresenter.php"
FRESHNESS = MODULE / "Services" / "FreshnessPresenter.php"
API_ACTION = MODULE / "Api" / "GetWorkspaceContext.php"
SOURCE_DETAIL_API = MODULE / "Api" / "GetGovernedSourceDetail.php"
ADAPTERS = {
    "C21": MODULE / "Services" / "Adapters" / "C21IntelligenceReadAdapter.php",
    "C22": MODULE / "Services" / "Adapters" / "C22ExecutionReadAdapter.php",
    "C23": MODULE / "Services" / "Adapters" / "C23OptimizationReadAdapter.php",
    "C24": MODULE / "Services" / "Adapters" / "C24RevenueReadAdapter.php",
    "CRM": MODULE / "Services" / "Adapters" / "CrmCoreAnchorReadAdapter.php",
    "C20": MODULE / "Services" / "Adapters" / "C20ProvenanceReadAdapter.php",
}

SUPPORTED_ENTITY_TYPES = {
    "AIJob",
    "AIRequestLog",
    "ResearchEvidence",
    "AIQualificationInsight",
    "HumanFeedback",
    "ProspectCandidate",
    "ProspectRun",
    "ExecutionLedger",
    "ReplyEvent",
    "OptimizationInsight",
    "PerformanceMetric",
    "FeedbackLearningObservation",
    "ReplySignal",
    "OpportunityCandidate",
    "RevenueInsight",
    "PipelineMetric",
    "Account",
    "Contact",
    "Opportunity",
}

MUTATION_CALLS = (
    "saveEntity(",
    "createEntity(",
    "deleteEntity(",
    "removeEntity(",
    "updateEntity(",
    "restoreEntity(",
)

EGRESS_TOKENS = (
    "curl",
    "guzzle",
    "httpclient",
    "file_get_contents",
    "sdk",
    "credential",
    "secret",
    "token",
    "provider",
    "webhook",
    "scheduler",
    "worker",
    "queue",
    "automation",
    "workflow",
)


def module_php() -> list[Path]:
    return sorted(MODULE.rglob("*.php"))


def module_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in module_php())


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def php_string_list(source: str, constant: str) -> list[str]:
    match = re.search(
        rf"\b{re.escape(constant)}\s*=\s*\[(.*?)\];",
        source,
        flags=re.DOTALL,
    )
    assert match, f"{constant} list not found"
    return re.findall(r"'([A-Za-z][A-Za-z0-9]*)'", match.group(1))


def parser_contract() -> tuple[set[str], int, int]:
    source = PARSER.read_text(encoding="utf-8")
    minimum = re.search(r"\bMIN_ENTITY_ID_LENGTH\s*=\s*(\d+);", source)
    maximum = re.search(r"\bMAX_ENTITY_ID_LENGTH\s*=\s*(\d+);", source)
    assert minimum and maximum
    return (
        set(php_string_list(source, "SUPPORTED_ENTITY_TYPES")),
        int(minimum.group(1)),
        int(maximum.group(1)),
    )


def parse_reference_contract(*values: object) -> list[dict[str, str]]:
    """Exercise the explicit PHP parser contract without a PHP runtime.

    This mirrors the parser's candidate boundary and immutable registry.
    Static parity assertions below bind the mirror to the PHP constants and
    validation expressions; live PHP smoke remains a separate release gate.
    """

    supported, minimum, maximum = parser_contract()
    candidate = re.compile(
        r"(?<![A-Za-z0-9_./\\:])"
        r"([A-Za-z][A-Za-z0-9]*):"
        r"""([^\s,;"'<>{}\[\]()]+)"""
    )
    entity_id = re.compile(rf"\A[A-Za-z0-9]{{{minimum},{maximum}}}\Z")
    found: dict[str, dict[str, str]] = {}

    for value in values:
        if not isinstance(value, str) or value == "":
            continue
        for entity_type, identifier in candidate.findall(value):
            if entity_type not in supported or not entity_id.fullmatch(identifier):
                continue
            key = f"{entity_type}:{identifier}"
            found[key] = {"entityType": entity_type, "entityId": identifier}

    return list(found.values())


# 1. CommercialContext persistence forbidden --------------------------------

def test_commercial_context_is_runtime_read_model_without_persistence() -> None:
    assert CONTEXT.is_file()
    source = CONTEXT.read_text(encoding="utf-8")
    assert "final class CommercialContext" in source
    assert "extends" not in source
    assert "Espo\\ORM\\Entity" not in source
    assert "runtime read model" in source
    assert "MUST NOT become" in source
    assert "ASSEMBLY_VERSION" in source


def test_module_has_no_entity_persistence_surface() -> None:
    assert MODULE.is_dir()
    assert not (MODULE / "Entities").exists(), "C25 WP1 must not define entities"
    assert not (MODULE / "Hooks").exists(), "C25 WP1 must not define hooks"
    assert not (METADATA / "entityDefs").exists(), "no entityDefs permitted"
    assert not (METADATA / "aclDefs").exists(), "no entity ACL defs permitted"
    source = module_source()
    assert "CREATE TABLE" not in source
    assert "Migration" not in source


# 2. No CRM write path --------------------------------------------------------

def test_no_crm_write_path_exists() -> None:
    source = module_source()
    for token in MUTATION_CALLS:
        assert token not in source, token
    crm = ADAPTERS["CRM"].read_text(encoding="utf-8")
    assert "getEntity" in crm
    assert "Account" in crm and "Contact" in crm and "Opportunity" in crm


# 3. No C20 provider / egress access -----------------------------------------

def test_no_provider_egress_or_automation_tokens() -> None:
    source = module_source().lower()
    for token in EGRESS_TOKENS:
        assert token not in source, token
    c20 = ADAPTERS["C20"].read_text(encoding="utf-8")
    assert "AIJob" in c20 and "AIRequestLog" in c20
    assert "getEntity" in c20


def test_wp1_performs_no_ai_invocation() -> None:
    source = module_source()
    assert "PromptTemplate" not in source
    assert "generateBrief" not in source
    assert "invokeModel" not in source
    # AIJob / AIRequestLog may appear only at the fixed parser/resolver boundary
    # and inside the read-only C20 adapter.
    for path in module_php():
        if path == ADAPTERS["C20"]:
            continue
        text = path.read_text(encoding="utf-8")
        assert "AIRequestLog" not in text or path in (
            PARSER,
            ASSEMBLY,
            SOURCE_DETAIL_API,
            PROVENANCE,
        ), path


# 4. No C21 mutation -----------------------------------------------------------

def test_no_c21_mutation_path() -> None:
    source = module_source()
    for token in MUTATION_CALLS:
        assert token not in source, token
    assert "ResearchEvidenceGovernanceService" not in source
    assert "ResearchEvidenceSaveOption" not in source
    adapter = ADAPTERS["C21"].read_text(encoding="utf-8")
    assert "ResearchEvidence" in adapter
    assert "AIQualificationInsight" in adapter
    assert "getEntity" in adapter
    assert "no scoring, ranking, or qualification" in adapter


# 5. No C22 execution influence -------------------------------------------------

def test_no_c22_execution_influence() -> None:
    source = module_source()
    for forbidden in (
        "ActionGate",
        "ExecutionOrchestrationService",
        "ProspectRunLifecycleService",
        "SendExecution",
        "OutreachExecution",
    ):
        assert forbidden not in source, forbidden
    adapter = ADAPTERS["C22"].read_text(encoding="utf-8")
    assert "ProspectCandidate" in adapter
    assert "ExecutionLedger" in adapter
    assert "execution authorization point" in adapter


# 6. No C23 optimization mutation ------------------------------------------------

def test_no_c23_optimization_mutation() -> None:
    source = module_source()
    for forbidden in (
        "OptimizationInsightService",
        "OptimizationAssistantService",
        "PerformanceMetricService",
    ):
        assert forbidden not in source, forbidden
    adapter = ADAPTERS["C23"].read_text(encoding="utf-8")
    assert "OptimizationInsight" in adapter
    assert "PerformanceMetric" in adapter
    assert "getEntity" in adapter


# 7. No C24 lifecycle mutation ---------------------------------------------------

def test_no_c24_lifecycle_mutation() -> None:
    source = module_source()
    for forbidden in (
        "OpportunityCandidateLifecycleService",
        "C24OpportunityCandidateSaveOption",
        "LifecycleGuard",
        "transition(",
    ):
        assert forbidden not in source, forbidden
    adapter = ADAPTERS["C24"].read_text(encoding="utf-8")
    assert "ReplySignal" in adapter
    assert "OpportunityCandidate" in adapter
    assert "RevenueInsight" in adapter
    assert "PipelineMetric" in adapter
    assert "no status change, field update, transition" in adapter


# 8. ACL visibility inheritance ----------------------------------------------------

def test_visibility_inheritance_service_enforces_source_permission() -> None:
    source = VISIBILITY.read_text(encoding="utf-8")
    assert "final class VisibilityInheritanceService" in source
    assert "isPortal" in source
    assert "checkScope" in source
    assert "checkEntityRead" in source
    assert "Forbidden" in source
    assert "MUST NOT exceed source visibility" in source


def test_acl_metadata_restricts_portal_and_declares_workspace_scope() -> None:
    scope = load_json(METADATA / "scopes" / "CommercialIntelligenceWorkspace.json")
    assert scope["entity"] is False
    assert scope["acl"] == "boolean"
    assert scope["module"] == "CommercialIntelligence"
    portal = load_json(METADATA / "app" / "aclPortal.json")
    assert portal["mandatory"]["scopeLevel"]["CommercialIntelligenceWorkspace"] is False


def test_assembly_applies_visibility_filter_and_api_gates_workspace() -> None:
    assembly = ASSEMBLY.read_text(encoding="utf-8")
    assert "canReadSource" in assembly
    api = API_ACTION.read_text(encoding="utf-8")
    assert "assertWorkspaceAccess" in api
    assert "final class GetWorkspaceContext implements Action" in api


# 9. Provenance preservation --------------------------------------------------------

def test_source_artifact_reference_preserves_provenance_elements() -> None:
    source = SOURCE_REF.read_text(encoding="utf-8")
    for field in (
        "entityType",
        "entityId",
        "layer",
        "revision",
        "freshnessStatus",
        "validationState",
        "evidenceReference",
    ):
        assert field in source, field
    assert "MUST NOT rewrite source meaning" in source


def test_provenance_presenter_carries_values_unchanged() -> None:
    source = PROVENANCE.read_text(encoding="utf-8")
    assert "MUST NOT rewrite evidence meaning" in source
    assert "evidenceRevision" in source
    assert "'#CommercialIntelligenceWorkspace/source/entityType='" in source
    assert "'#' . $entityType . '/view/' . rawurlencode($entityId)" in source
    assembly = ASSEMBLY.read_text(encoding="utf-8")
    assert "provenancePresenter->present" in assembly


# 10. Freshness preservation ---------------------------------------------------------

def test_freshness_is_passed_through_and_warnings_surfaced() -> None:
    source = FRESHNESS.read_text(encoding="utf-8")
    assert "STALE" in source and "ARCHIVAL" in source
    assert "never suppressed" in source
    assert "stalenessWarning" in source
    module = module_source()
    for forbidden in ("strtotime", "->diff(", "ARCHIVAL_THRESHOLD", "recompute", "recalculat"):
        assert forbidden not in module, forbidden


# 11. D2 presentation boundary --------------------------------------------------------

def test_d2_markers_present_in_workspace_template() -> None:
    tpl = WORKSPACE_TPL.read_text(encoding="utf-8")
    assert "c25-ai-assembled" in tpl
    assert "c25-boundary-divider" in tpl
    assert "c25-boundary-label" in tpl
    assert "c25-evidence-link" in tpl
    assert 'data-c25-region="assembled-intelligence"' in tpl
    assert 'data-c25-region="crm-records"' in tpl


def test_workspace_client_is_read_only_get() -> None:
    js = WORKSPACE_JS.read_text(encoding="utf-8")
    assert "getRequest" in js
    for forbidden in ("ajaxPost", "postRequest", "putRequest", "patchRequest", "deleteRequest"):
        assert forbidden not in js, forbidden
    context = CONTEXT.read_text(encoding="utf-8")
    assert "ADVISORY_DESIGNATION" in context
    assert "AI_ASSEMBLED_CONTEXT" in context
    i18n = load_json(RESOURCES / "i18n" / "en_US" / "CommercialIntelligenceWorkspace.json")
    assert "advisoryDesignation" in i18n["labels"]


# Module registration and scope containment -----------------------------------

def test_workspace_scope_resolves_the_packaged_custom_controller() -> None:
    client_defs = load_json(CLIENT_DEFS)
    assert client_defs == {
        "controller": "custom:controllers/commercial-intelligence-workspace"
    }
    assert CONTROLLER_JS.is_file()


def test_module_registration_and_read_only_routes() -> None:
    module_meta = load_json(RESOURCES / "module.json")
    assert module_meta["order"] == 7
    routes = load_json(RESOURCES / "routes.json")
    assert isinstance(routes, list) and len(routes) == 2
    assert {
        (route["method"], route["route"], route["actionClassName"])
        for route in routes
    } == {
        (
            "get",
            "/CommercialIntelligence/workspace/:candidateId",
            "Espo\\Modules\\CommercialIntelligence\\Api\\GetWorkspaceContext",
        ),
        (
            "get",
            "/CommercialIntelligence/source/:entityType/:entityId",
            "Espo\\Modules\\CommercialIntelligence\\Api\\GetGovernedSourceDetail",
        ),
    }
    assert API_ACTION.is_file()


def test_no_wp2_wp3_wp4_implementation_leakage() -> None:
    for path in MODULE.rglob("*"):
        name = path.name
        for forbidden in ("Brief", "Assistant", "Decision", "Audit"):
            assert forbidden not in name, f"WP2/WP3/WP4 artifact leaked into WP1: {path}"
    tpl = WORKSPACE_TPL.read_text(encoding="utf-8")
    assert 'data-c25-slot="assistant"' in tpl
    assert 'data-c25-slot="brief"' in tpl
    assert "upcoming" in tpl.lower()


def test_human_request_only_trigger_boundary() -> None:
    source = ASSEMBLY.read_text(encoding="utf-8")
    assert "HUMAN_REQUEST_ONLY" in source
    assert "TRIGGER" in source


def test_reference_following_without_fk_coupling() -> None:
    assert PARSER.is_file()
    source = PARSER.read_text(encoding="utf-8")
    assert "no foreign-key coupling" in source
    assert "EntityType:entityId" in source


# WP1.1 parser boundary hardening ---------------------------------------------

def test_parser_supported_types_exactly_match_all_six_adapter_allowlists() -> None:
    parser_types, _, _ = parser_contract()
    adapter_types: list[str] = []
    for path in ADAPTERS.values():
        adapter_types.extend(
            php_string_list(path.read_text(encoding="utf-8"), "ENTITY_TYPES")
        )

    assert parser_types == SUPPORTED_ENTITY_TYPES
    assert set(adapter_types) == SUPPORTED_ENTITY_TYPES
    assert len(adapter_types) == len(set(adapter_types))


def test_parser_accepts_every_supported_wp1_entity_type() -> None:
    references = [
        f"{entity_type}:Abcdef12"
        for entity_type in sorted(SUPPORTED_ENTITY_TYPES)
    ]
    parsed = parse_reference_contract(", ".join(references))
    assert {item["entityType"] for item in parsed} == SUPPORTED_ENTITY_TYPES


def test_parser_rejects_unknown_lowercase_namespaced_and_path_like_types() -> None:
    invalid = (
        "UnknownEntity:Abcdef12",
        "account:Abcdef12",
        r"Espo\Account:Abcdef12",
        "Espo/Account:Abcdef12",
        "../Account:Abcdef12",
        "Espo.Account:Abcdef12",
        "Espo:Account:Abcdef12",
    )
    assert parse_reference_contract(*invalid) == []


def test_parser_enforces_repository_compatible_id_bounds() -> None:
    _, minimum, maximum = parser_contract()
    assert (minimum, maximum) == (8, 36)
    assert parse_reference_contract(f"Account:{'A' * (minimum - 1)}") == []
    assert parse_reference_contract(f"Account:{'A' * minimum}") == [
        {"entityType": "Account", "entityId": "A" * minimum}
    ]
    assert parse_reference_contract(f"Account:{'A' * maximum}") == [
        {"entityType": "Account", "entityId": "A" * maximum}
    ]
    assert parse_reference_contract(f"Account:{'A' * (maximum + 1)}") == []


def test_parser_rejects_non_alphanumeric_id_characters() -> None:
    invalid_ids = (
        "Abcd:ef12",
        "Abcd/ef12",
        r"Abcd\ef12",
        "Abcd.ef12",
        "Abcd ef12",
        "Abcd\tef12",
        "Abcd\nef12",
        "Abcd\x01ef12",
        "Abcd_ef12",
        "Abcd-ef12",
    )
    assert parse_reference_contract(
        *(f"Account:{identifier}" for identifier in invalid_ids)
    ) == []


def test_parser_ignores_malformed_items_without_losing_valid_siblings() -> None:
    value = (
        "UnknownEntity:Abcdef12, "
        "Account:Abcd/ef12, "
        "Contact:Valid123, "
        "Opportunity:AlsoValid456"
    )
    assert parse_reference_contract(value) == [
        {"entityType": "Contact", "entityId": "Valid123"},
        {"entityType": "Opportunity", "entityId": "AlsoValid456"},
    ]


def test_parser_deduplicates_valid_references() -> None:
    assert parse_reference_contract(
        "Account:Duplicate123, Contact:Contact123",
        "Account:Duplicate123",
    ) == [
        {"entityType": "Account", "entityId": "Duplicate123"},
        {"entityType": "Contact", "entityId": "Contact123"},
    ]


def test_parser_validation_is_fail_closed_and_exception_free() -> None:
    source = PARSER.read_text(encoding="utf-8")
    assert "SUPPORTED_ENTITY_TYPES" in source
    assert "in_array($entityType, self::SUPPORTED_ENTITY_TYPES, true)" in source
    assert r"\A[A-Za-z0-9]+\z" in source
    assert "$length >= self::MIN_ENTITY_ID_LENGTH" in source
    assert "$length <= self::MAX_ENTITY_ID_LENGTH" in source
    assert "$matchCount === false || $matchCount === 0" in source
    assert "throw " not in source
    assert "new SourceArtifactReference" not in source


def test_supported_references_route_only_through_fixed_adapter_resolution() -> None:
    assembly = ASSEMBLY.read_text(encoding="utf-8")
    for adapter_class in (
        "C24RevenueReadAdapter",
        "C21IntelligenceReadAdapter",
        "C22ExecutionReadAdapter",
        "C23OptimizationReadAdapter",
        "CrmCoreAnchorReadAdapter",
        "C20ProvenanceReadAdapter",
    ):
        assert (
            f"in_array($entityType, {adapter_class}::ENTITY_TYPES, true)"
            in assembly
        )
    assert "[$layer, $entity] = $this->resolve(" in assembly
    assert "return [null, null];" in assembly
    assert "get_class" not in assembly
    assert "class_exists" not in assembly
    assert "getRepository($entityType)" not in assembly


def test_unsupported_references_are_removed_before_adapter_resolution() -> None:
    assert parse_reference_contract(
        "User:Unsupported123, Account:Supported123"
    ) == [{"entityType": "Account", "entityId": "Supported123"}]
    assembly = ASSEMBLY.read_text(encoding="utf-8")
    assert assembly.index("ArtifactReferenceParser::parse(") < assembly.index(
        "foreach ($references as $reference)"
    )
    assert assembly.index("foreach ($references as $reference)") < assembly.index(
        "[$layer, $entity] = $this->resolve("
    )


def test_traversal_depth_cycle_and_fixed_root_guards_remain_intact() -> None:
    assembly = ASSEMBLY.read_text(encoding="utf-8")
    assert "private const MAX_DEPTH = 2;" in assembly
    assert "if ($depth >= self::MAX_DEPTH)" in assembly
    assert "if (isset($visited[$key]))" in assembly
    assert "$visited[$key] = true;" in assembly
    assert "$this->assembleReferences($context, $entity, $depth + 1, $visited)" in assembly
    assert "$this->c24Revenue->read('OpportunityCandidate', $candidateId)" in assembly
    assert "$context->setAnchor('OpportunityCandidate'" in assembly
