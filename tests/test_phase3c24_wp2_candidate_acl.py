"""Phase3C24 WP2.2 OpportunityCandidate metadata and ACL foundation tests."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
METADATA = MODULE / "Resources" / "metadata"
I18N = MODULE / "Resources" / "i18n"
ENTITY = "OpportunityCandidate"

SCOPE = METADATA / "scopes" / f"{ENTITY}.json"
ACL_DEF = METADATA / "aclDefs" / f"{ENTITY}.json"
ENTITY_DEF = METADATA / "entityDefs" / f"{ENTITY}.json"
APP_ACL = METADATA / "app" / "acl.json"
PORTAL_ACL = METADATA / "app" / "aclPortal.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def metadata_blob() -> str:
    parts = [
        SCOPE.read_text(encoding="utf-8"),
        ACL_DEF.read_text(encoding="utf-8"),
        ENTITY_DEF.read_text(encoding="utf-8"),
        APP_ACL.read_text(encoding="utf-8"),
        PORTAL_ACL.read_text(encoding="utf-8"),
    ]
    for locale in ("en_US", "zh_CN"):
        parts.append((I18N / locale / "Global.json").read_text(encoding="utf-8"))
        parts.append((I18N / locale / f"{ENTITY}.json").read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_scope_metadata_exists() -> None:
    assert SCOPE.is_file()
    scope = load_json(SCOPE)
    assert scope["entity"] is True
    assert scope["acl"] is True
    assert scope["aclPortal"] is False
    assert scope["tab"] is False
    assert scope["customizable"] is False
    assert scope["importable"] is False
    assert scope["module"] == "Prospecting"
    assert scope["type"] == "Base"
    assert scope["statusField"] == "status"
    assert scope["object"] is False


def test_acl_metadata_exists() -> None:
    assert ACL_DEF.is_file()
    assert load_json(ACL_DEF) == {}


def test_internal_read_permission_exists() -> None:
    acl = load_json(APP_ACL)
    # WP1.2: read is governed by native role ACL with deny-by-default;
    # the scope is no longer force-disabled for every non-admin role.
    assert ENTITY not in acl["mandatory"]["scopeLevel"]
    rights = acl["adminMandatory"]["scopeLevel"][ENTITY]
    assert rights == {
        "create": "yes",
        "read": "all",
        "edit": "no",
        "delete": "no",
    }
    assert rights["read"] == "all"
    assert rights["create"] == "yes"


def test_portal_access_disabled() -> None:
    scope = load_json(SCOPE)
    portal_acl = load_json(PORTAL_ACL)
    assert scope["aclPortal"] is False
    assert portal_acl["mandatory"]["scopeLevel"][ENTITY] is False


def test_no_forbidden_relationships() -> None:
    definition = load_json(ENTITY_DEF)
    assert "links" not in definition
    assert "relationships" not in definition
    blob = metadata_blob().lower()
    forbidden_relationship_tokens = (
        '"entity": "opportunity"',
        '"entity": "account"',
        '"entity": "contact"',
        '"entity": "lead"',
        '"entity": "actiongate"',
        '"entity": "executionledger"',
        '"entity": "replysignal"',
        '"entity": "performancemetric"',
        "opportunityid",
        "accountid",
        "contactid",
    )
    for token in forbidden_relationship_tokens:
        assert token not in blob, token


def test_no_workflow_or_automation_acl() -> None:
    rights = load_json(APP_ACL)["adminMandatory"]["scopeLevel"][ENTITY]
    assert set(rights) == {"create", "read", "edit", "delete"}
    candidate_blob = "\n".join(
        [
            SCOPE.read_text(encoding="utf-8"),
            ACL_DEF.read_text(encoding="utf-8"),
            ENTITY_DEF.read_text(encoding="utf-8"),
            json.dumps({ENTITY: rights}, sort_keys=True),
            json.dumps(
                {ENTITY: load_json(PORTAL_ACL)["mandatory"]["scopeLevel"][ENTITY]},
                sort_keys=True,
            ),
            (I18N / "en_US" / f"{ENTITY}.json").read_text(encoding="utf-8"),
            (I18N / "zh_CN" / f"{ENTITY}.json").read_text(encoding="utf-8"),
        ]
    ).lower()
    forbidden = (
        "transitionpermission",
        "workflow",
        "scheduler",
        "scheduledaction",
        "automationrole",
        "serviceaccount",
        "cron",
        "queue",
        "worker",
        "autoapprove",
        "autocommit",
    )
    for token in forbidden:
        assert token not in candidate_blob, token
    assert not (MODULE / "Services" / "OpportunityCandidateService.php").exists()
    assert not (MODULE / "Views" / ENTITY).exists()


def test_no_crm_opportunity_coupling() -> None:
    blob = metadata_blob()
    assert '"entity": "Opportunity"' not in blob
    assert "use Espo\\Entities\\Opportunity" not in blob
    candidate_labels = "\n".join(
        [
            (I18N / "en_US" / f"{ENTITY}.json").read_text(encoding="utf-8"),
            (I18N / "zh_CN" / f"{ENTITY}.json").read_text(encoding="utf-8"),
            json.dumps(load_json(I18N / "en_US" / "Global.json")["scopeNames"][ENTITY]),
            json.dumps(load_json(I18N / "zh_CN" / "Global.json")["scopeNames"][ENTITY]),
            json.dumps(load_json(I18N / "en_US" / "Global.json")["scopeNamesPlural"][ENTITY]),
            json.dumps(load_json(I18N / "zh_CN" / "Global.json")["scopeNamesPlural"][ENTITY]),
        ]
    )
    assert re.search(r"(?i)forecast|pipeline stage|revenue commitment", candidate_labels) is None
    en_global = load_json(I18N / "en_US" / "Global.json")
    zh_global = load_json(I18N / "zh_CN" / "Global.json")
    assert en_global["scopeNames"][ENTITY] == "Opportunity Candidate"
    assert zh_global["scopeNames"][ENTITY] == "机会候选"
    assert en_global["scopeNamesPlural"][ENTITY] == "Opportunity Candidates"
    assert zh_global["scopeNamesPlural"][ENTITY] == "机会候选"
    assert set(en_global["scopeNames"]) == set(zh_global["scopeNames"])
    assert set(en_global["scopeNamesPlural"]) == set(zh_global["scopeNamesPlural"])


def test_extension_inventory_lists_metadata_and_acl_foundation() -> None:
    inventory = (EXT / "tests" / "test_extension_skeleton.py").read_text(encoding="utf-8")
    assert 'Entities" / "OpportunityCandidate.php"' in inventory
    assert 'Services" / "OpportunityCandidateLifecycleService.php"' in inventory
    assert 'Services" / "C24OpportunityCandidateSaveOption.php"' in inventory
    assert 'Hooks" / "OpportunityCandidate" / "OpportunityCandidateLifecycleGuard.php"' in inventory
    assert 'scopes" / "OpportunityCandidate.json"' in inventory
    assert 'aclDefs" / "OpportunityCandidate.json"' in inventory
