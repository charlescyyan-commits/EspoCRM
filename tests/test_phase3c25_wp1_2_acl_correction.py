"""Phase3C25 WP1.2 governed source ACL correction tests.

Proves the native-ACL correction for the four C24 governed source scopes
(OpportunityCandidate, ReplySignal, RevenueInsight, PipelineMetric):

- the scopes are eligible for native role read ACL (no mandatory force-off);
- read is declarable independently of create/edit/delete (aclActionList);
- hidden (object/tab false) posture is preserved and does not remove the
  scope from native role ACL eligibility;
- the C25 workspace permission never substitutes for source ACL;
- root and nested source ACL remain mandatory in the assembly path;
- portal remains blocked;
- no generic CRUD exposure was introduced;
- C24 lifecycle and mutation boundaries are unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
PROSPECTING = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
METADATA = PROSPECTING / "Resources" / "metadata"
APP_ACL = METADATA / "app" / "acl.json"
PORTAL_ACL = METADATA / "app" / "aclPortal.json"
C25 = EXT / "files" / "custom" / "Espo" / "Modules" / "CommercialIntelligence"

C24_SCOPES = (
    "OpportunityCandidate",
    "ReplySignal",
    "RevenueInsight",
    "PipelineMetric",
)

# C20-C23 governed scopes whose mandatory-hidden posture is unchanged.
UNCHANGED_HIDDEN_SCOPES = (
    "ResearchEvidence",
    "AIQualificationInsight",
    "HumanFeedback",
    "ProspectCandidate",
    "ProspectRun",
    "ActionGate",
    "ExecutionLedger",
    "OptimizationInsight",
    "PerformanceMetric",
    "FeedbackLearningObservation",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def scope_meta(scope: str) -> dict:
    return load_json(METADATA / "scopes" / f"{scope}.json")


def test_c24_scopes_eligible_for_native_role_read_acl() -> None:
    """1. Affected C24 scopes are eligible for native role read ACL."""
    acl = load_json(APP_ACL)
    for scope in C24_SCOPES:
        assert scope not in acl["mandatory"]["scopeLevel"], scope
        meta = scope_meta(scope)
        assert meta["entity"] is True, scope
        assert meta["acl"] is True, scope
        assert not meta.get("disabled"), scope


def test_read_declared_independently_of_write_actions() -> None:
    """2. Read is declarable independently of create/edit/delete."""
    for scope in C24_SCOPES:
        assert scope_meta(scope)["aclActionList"] == ["read"], scope


def test_hidden_posture_preserved_without_losing_acl_eligibility() -> None:
    """3. Hidden/non-tab status does not remove the scope from role ACL."""
    for scope in C24_SCOPES:
        meta = scope_meta(scope)
        assert meta["object"] is False, scope
        assert meta["tab"] is False, scope
        assert meta["customizable"] is False, scope
        assert meta["importable"] is False, scope
        assert meta["acl"] is True, scope


def test_workspace_permission_does_not_replace_source_acl() -> None:
    """4. CommercialIntelligenceWorkspace permission is not a source ACL."""
    api = (C25 / "Api" / "GetWorkspaceContext.php").read_text(encoding="utf-8")
    assembly = (C25 / "Services" / "ContextAssemblyService.php").read_text(
        encoding="utf-8"
    )
    visibility = (C25 / "Services" / "VisibilityInheritanceService.php").read_text(
        encoding="utf-8"
    )
    # The API gates the workspace scope; the assembly independently checks
    # source read access. Two distinct checks, no substitution.
    assert "assertWorkspaceAccess" in api
    assert "canReadSource" in assembly
    assert "checkEntityRead" in visibility
    assert "WORKSPACE_SCOPE" in visibility


def test_root_source_acl_remains_mandatory() -> None:
    """5. Root OpportunityCandidate requires native checkEntityRead."""
    assembly = (C25 / "Services" / "ContextAssemblyService.php").read_text(
        encoding="utf-8"
    )
    assert "canReadSource($anchor)" in assembly
    assert "NotFound" in assembly


def test_nested_source_acl_remains_mandatory() -> None:
    """6. Every nested source artifact passes a native read check."""
    assembly = (C25 / "Services" / "ContextAssemblyService.php").read_text(
        encoding="utf-8"
    )
    assert "canReadSource($entity)" in assembly
    assert "continue;" in assembly


def test_portal_remains_blocked() -> None:
    """7. Portal access stays denied at metadata and service level."""
    portal = load_json(PORTAL_ACL)
    for scope in C24_SCOPES:
        assert scope_meta(scope)["aclPortal"] is False, scope
        assert portal["mandatory"]["scopeLevel"][scope] is False, scope
    visibility = (C25 / "Services" / "VisibilityInheritanceService.php").read_text(
        encoding="utf-8"
    )
    assert "isPortal" in visibility


def test_no_generic_crud_exposure_introduced() -> None:
    """8. No generic CRUD surface was introduced by the correction."""
    for scope in C24_SCOPES:
        meta = scope_meta(scope)
        # Hidden from generic object surfaces; no navigation tab; no import.
        assert meta["object"] is False, scope
        assert meta["tab"] is False, scope
        assert meta["importable"] is False, scope
    # No clientDefs controller was added for the C24 scopes by C25.
    clientdefs_dir = C25 / "Resources" / "metadata" / "clientDefs"
    if clientdefs_dir.is_dir():
        for path in clientdefs_dir.glob("*.json"):
            assert path.stem not in C24_SCOPES, path
    # C24 immutable/lifecycle guards remain in place.
    for guard in (
        PROSPECTING / "Hooks" / "OpportunityCandidate" / "OpportunityCandidateImmutableGuard.php",
        PROSPECTING / "Hooks" / "OpportunityCandidate" / "OpportunityCandidateLifecycleGuard.php",
        PROSPECTING / "Hooks" / "ReplySignal" / "ReplySignalImmutableGuard.php",
    ):
        assert guard.is_file(), guard
        text = guard.read_text(encoding="utf-8")
        assert "BeforeSave" in text or "beforeSave" in text


def test_c24_lifecycle_and_mutation_boundaries_unchanged() -> None:
    """9. C24 lifecycle authority and admin capabilities are unchanged."""
    acl = load_json(APP_ACL)
    admin = acl["adminMandatory"]["scopeLevel"]
    # Admin capabilities (used by C24 lifecycle services) are preserved.
    assert admin["ReplySignal"] == {
        "create": "yes",
        "read": "all",
        "edit": "all",
        "delete": "no",
    }
    for scope in ("OpportunityCandidate", "RevenueInsight", "PipelineMetric"):
        assert admin[scope] == {
            "create": "yes",
            "read": "all",
            "edit": "no",
            "delete": "no",
        }, scope
    # C24 lifecycle service files are untouched by the correction.
    lifecycle = PROSPECTING / "Services" / "OpportunityCandidateLifecycleService.php"
    assert lifecycle.is_file()
    assert "LIFECYCLE_TRANSITION_AUTHORIZED" in lifecycle.read_text(encoding="utf-8")


def test_other_governed_scopes_keep_hidden_mandatory_posture() -> None:
    """C20-C23 governed scopes remain mandatory-hidden (correction is bounded)."""
    acl = load_json(APP_ACL)
    for scope in UNCHANGED_HIDDEN_SCOPES:
        assert acl["mandatory"]["scopeLevel"][scope] is False, scope


def test_mandatory_scope_level_contains_only_unchanged_scopes() -> None:
    """The mandatory map now holds exactly the ten unchanged scopes."""
    acl = load_json(APP_ACL)
    assert set(acl["mandatory"]["scopeLevel"]) == set(UNCHANGED_HIDDEN_SCOPES)


def test_workspace_scope_itself_unchanged() -> None:
    """The C25 workspace scope definition is untouched by the correction."""
    workspace = load_json(
        C25 / "Resources" / "metadata" / "scopes" / "CommercialIntelligenceWorkspace.json"
    )
    assert workspace["entity"] is False
    assert workspace["acl"] == "boolean"
    portal = load_json(C25 / "Resources" / "metadata" / "app" / "aclPortal.json")
    assert portal["mandatory"]["scopeLevel"]["CommercialIntelligenceWorkspace"] is False
