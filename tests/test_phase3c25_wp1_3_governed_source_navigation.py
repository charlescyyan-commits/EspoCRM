"""Phase3C25 WP1.3 governed source navigation boundary tests."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension" / "files"
MODULE = EXT / "custom" / "Espo" / "Modules" / "CommercialIntelligence"
PROSPECTING_METADATA = (
    EXT
    / "custom"
    / "Espo"
    / "Modules"
    / "Prospecting"
    / "Resources"
    / "metadata"
)
CLIENT = EXT / "client" / "custom"

API = MODULE / "Api" / "GetGovernedSourceDetail.php"
VISIBILITY = MODULE / "Services" / "VisibilityInheritanceService.php"
PROVENANCE = MODULE / "Services" / "ProvenancePresenter.php"
ROUTES = MODULE / "Resources" / "routes.json"
WORKSPACE_JS = CLIENT / "src" / "views" / "commercial-intelligence" / "workspace.js"
SOURCE_JS = (
    CLIENT / "src" / "views" / "commercial-intelligence" / "source-detail.js"
)
CONTROLLER_JS = CLIENT / "src" / "controllers" / "commercial-intelligence-workspace.js"
WORKSPACE_TPL = (
    CLIENT / "res" / "templates" / "commercial-intelligence" / "workspace.tpl"
)
SOURCE_TPL = (
    CLIENT / "res" / "templates" / "commercial-intelligence" / "source-detail.tpl"
)

GOVERNED_TYPES = {
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
}
C24_TYPES = {
    "OpportunityCandidate",
    "ReplySignal",
    "RevenueInsight",
    "PipelineMetric",
}
CRM_CORE_TYPES = {"Account", "Contact", "Opportunity"}
WRITE_TOKENS = (
    "ajaxPost",
    "postRequest",
    "putRequest",
    "patchRequest",
    "deleteRequest",
    "saveEntity(",
    "createEntity(",
    "deleteEntity(",
    "removeEntity(",
    "updateEntity(",
)


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def php_map_keys(source: str, constant: str) -> set[str]:
    match = re.search(
        rf"\b{re.escape(constant)}\s*=\s*\[(.*?)\n    \];",
        source,
        flags=re.DOTALL,
    )
    assert match, f"{constant} map not found"
    return set(
        re.findall(r"^\s{8}'([A-Za-z][A-Za-z0-9]*)'\s*=>\s*\[", match.group(1), re.MULTILINE)
    )


def js_list(source: str, variable: str) -> set[str]:
    match = re.search(
        rf"\b{re.escape(variable)}\s*=\s*\[(.*?)\];",
        source,
        flags=re.DOTALL,
    )
    assert match, f"{variable} list not found"
    return set(re.findall(r"'([A-Za-z][A-Za-z0-9]*)'", match.group(1)))


def test_only_explicit_governed_entity_allowlist_is_navigable() -> None:
    api = API.read_text(encoding="utf-8")
    assert php_map_keys(api, "ENTITY_FIELDS") == GOVERNED_TYPES
    assert C24_TYPES <= GOVERNED_TYPES

    source_js = SOURCE_JS.read_text(encoding="utf-8")
    workspace_js = WORKSPACE_JS.read_text(encoding="utf-8")
    assert js_list(source_js, "GOVERNED_SOURCE_TYPES") == GOVERNED_TYPES
    assert js_list(workspace_js, "GOVERNED_SOURCE_TYPES") == GOVERNED_TYPES
    assert js_list(workspace_js, "CRM_CORE_TYPES") == CRM_CORE_TYPES


def test_arbitrary_entity_type_and_malformed_id_are_rejected_before_lookup() -> None:
    api = API.read_text(encoding="utf-8")
    assert "isset(self::ENTITY_FIELDS[$entityType])" in api
    assert r"preg_match('/\A[A-Za-z0-9]+\z/D', $entityId)" in api
    assert "MIN_ENTITY_ID_LENGTH = 8" in api
    assert "MAX_ENTITY_ID_LENGTH = 36" in api
    assert api.index("isAllowedRequest($entityType, $entityId)") < api.index(
        "getEntity($entityType, $entityId)"
    )
    assert "throw new NotFound()" in api


def test_readable_source_uses_native_entity_read_and_returns_bounded_fields() -> None:
    api = API.read_text(encoding="utf-8")
    visibility = VISIBILITY.read_text(encoding="utf-8")
    assert "$this->visibility->canReadSource($entity)" in api
    assert "checkEntityRead($entity)" in visibility
    assert "'fields' => $this->presentFields($entityType, $entity)" in api
    assert "ENTITY_FIELDS[$entityType]" in api
    assert "is_string($value)" in api
    assert "is_int($value)" in api
    assert "is_float($value)" in api


def test_unreadable_or_missing_source_is_not_found_without_field_leakage() -> None:
    api = API.read_text(encoding="utf-8")
    denied = "$entity === null || !$this->visibility->canReadSource($entity)"
    assert denied in api
    assert api.index(denied) < api.index("ResponseComposer::json")
    assert "throw new NotFound();" in api


def test_workspace_permission_and_portal_denial_run_before_source_resolution() -> None:
    api = API.read_text(encoding="utf-8")
    visibility = VISIBILITY.read_text(encoding="utf-8")
    assert api.index("$this->visibility->assertWorkspaceAccess()") < api.index(
        "getRouteParam('entityType')"
    )
    assert "isPortal()" in visibility
    assert "checkScope(self::WORKSPACE_SCOPE, 'read')" in visibility
    assert "throw new Forbidden" in visibility


def test_routes_are_get_only_and_add_no_create_edit_or_delete_endpoint() -> None:
    routes = load_json(ROUTES)
    assert {route["method"] for route in routes} == {"get"}
    assert {
        route["route"] for route in routes
    } == {
        "/CommercialIntelligence/workspace/:candidateId",
        "/CommercialIntelligence/source/:entityType/:entityId",
    }
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (API, SOURCE_JS, CONTROLLER_JS)
    )
    for token in WRITE_TOKENS:
        assert token not in combined


def test_hidden_governed_entities_gain_no_generic_list_tab_or_controller() -> None:
    for entity_type in C24_TYPES:
        scope = load_json(PROSPECTING_METADATA / "scopes" / f"{entity_type}.json")
        assert scope["object"] is False
        assert scope["tab"] is False
        assert scope["aclActionList"] == ["read"]
        assert not (
            PROSPECTING_METADATA / "clientDefs" / f"{entity_type}.json"
        ).exists()


def test_provenance_links_use_governed_route_and_crm_core_stays_native() -> None:
    provenance = PROVENANCE.read_text(encoding="utf-8")
    workspace_js = WORKSPACE_JS.read_text(encoding="utf-8")
    assert php_map_keys(API.read_text(encoding="utf-8"), "ENTITY_FIELDS") == GOVERNED_TYPES
    assert "'#CommercialIntelligenceWorkspace/source/entityType='" in provenance
    assert "in_array($entityType, self::CRM_CORE_TYPES, true)" in provenance
    assert "'#' . $entityType . '/view/' . rawurlencode($entityId)" in provenance
    assert "candidateId=" in workspace_js


def test_unsupported_source_renders_non_clickable_instead_of_broken_anchor() -> None:
    workspace_js = WORKSPACE_JS.read_text(encoding="utf-8")
    template = WORKSPACE_TPL.read_text(encoding="utf-8")
    assert "return null;" in workspace_js
    assert "{{#if isNavigable}}" in template
    assert 'data-c25-action="source-unavailable"' in template
    assert "Source evidence unavailable" in template


def test_source_detail_is_read_only_has_back_link_and_no_mutation_controls() -> None:
    template = SOURCE_TPL.read_text(encoding="utf-8")
    assert 'data-c25-marker="read-only-governed-source"' in template
    assert 'data-c25-marker="truth-boundary"' in template
    assert 'data-c25-action="back-to-workspace"' in template
    assert "{{backHref}}" in template
    for forbidden in (
        "<form",
        "<button",
        "Save",
        "Edit",
        "Delete",
        "Mass",
        "Import",
        "Export",
        "Lifecycle action",
    ):
        assert forbidden not in template


def test_source_field_values_use_handlebars_escaping() -> None:
    template = SOURCE_TPL.read_text(encoding="utf-8")
    assert "{{value}}" in template
    assert "{{source.displayName}}" in template
    assert "{{{" not in template
    assert "white-space: pre-wrap" in template


def test_existing_workspace_d2_and_read_only_behavior_remain_intact() -> None:
    workspace = WORKSPACE_TPL.read_text(encoding="utf-8")
    source = SOURCE_TPL.read_text(encoding="utf-8")
    source_js = SOURCE_JS.read_text(encoding="utf-8")
    assert 'data-c25-marker="ai-assembled"' in workspace
    assert 'data-c25-marker="boundary-divider"' in workspace
    assert 'data-c25-slot="assistant"' in workspace
    assert 'data-c25-slot="brief"' in workspace
    assert "table-responsive" in source
    assert "getRequest" in source_js
    for token in WRITE_TOKENS:
        assert token not in source_js
