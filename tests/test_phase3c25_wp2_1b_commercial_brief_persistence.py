"""Phase3C25 WP2.1B CommercialBrief persistence static contract tests.

Authorized scope: CommercialBrief persistence layer only (Plan §28.1).
No runtime / provider / generation / audit-writer / deployment verification.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "CommercialIntelligence"
METADATA = MODULE / "Resources" / "metadata"
I18N = MODULE / "Resources" / "i18n"

ENTITY = "CommercialBrief"

ENTITY_CLASS = MODULE / "Entities" / f"{ENTITY}.php"
SAVE_OPTION = MODULE / "Services" / "CommercialBriefSaveOption.php"
AUTH_SERVICE = MODULE / "Services" / "CommercialBriefAuthorizationService.php"
IMMUTABLE_GUARD = (
    MODULE / "Hooks" / "CommercialBrief" / "CommercialBriefImmutableGuard.php"
)
STATE_GUARD = MODULE / "Hooks" / "CommercialBrief" / "CommercialBriefStateGuard.php"

# Historical WP2.2 names — retained, not adopted as WP2.1B baseline (C1).
HISTORICAL_IMMUTABLE = (
    MODULE / "Hooks" / "CommercialBrief" / "CommercialBriefImmutabilityGuard.php"
)
HISTORICAL_REVIEW = (
    MODULE / "Hooks" / "CommercialBrief" / "CommercialBriefReviewStatusGuard.php"
)

ENTITY_DEF = METADATA / "entityDefs" / f"{ENTITY}.json"
SCOPE = METADATA / "scopes" / f"{ENTITY}.json"
ACL_DEF = METADATA / "aclDefs" / f"{ENTITY}.json"
APP_ACL = METADATA / "app" / "acl.json"
PORTAL_ACL = METADATA / "app" / "aclPortal.json"
WORKFLOW = METADATA / "app" / "commercialBriefWorkflow.json"
I18N_EN = I18N / "en_US" / f"{ENTITY}.json"
I18N_ZH = I18N / "zh_CN" / f"{ENTITY}.json"

ALLOWED_FIELDS = {
    "opportunityCandidate",
    "reportingPeriod",
    "generatedAt",
    "generationVersion",
    "customerSituation",
    "commercialSignals",
    "riskFactors",
    "suggestedReviewPoints",
    "sourceEvidence",
    "evidenceSetHash",
    "claimSourceMap",
    "sourceAIJob",
    "sourceAIRequestLog",
    "provider",
    "model",
    "promptTemplateId",
    "promptTemplateVersion",
    "capability",
    "purpose",
    "advisoryDesignation",
    "legalDesignation",
    "reviewStatus",
    "acceptanceScope",
    "outcomeReason",
    "validityDisposition",
    "retentionDisposition",
    "supersedesBrief",
    "createdAt",
    "createdBy",
    "modifiedAt",
}

# Nine immutable provenance fields (Charter §9.1 + Plan §8.1).
PROVENANCE_ATTRS = {
    "sourceAIJobId",
    "sourceAIRequestLogId",
    "provider",
    "model",
    "generationVersion",
    "promptTemplateId",
    "promptTemplateVersion",
    "capability",
    "purpose",
}

FORBIDDEN_FIELDS = {
    "score",
    "priority",
    "ranking",
    "rank",
    "probability",
    "closeProbability",
    "revenueImpact",
    "forecast",
    "commit",
    "forecastCategory",
    "amount",
    "stage",
    "lifecycleStage",
    "salesStage",
    "closeDate",
    "expectedClose",
    "nextStep",
    "send",
    "execute",
    "approvedForOutreach",
    "actionGateDecision",
    "executionCommand",
    "sendInstruction",
    "providerRoute",
    "readyToCreateOpportunity",
    "createLead",
    "createOpportunity",
    "autoAccept",
    "acceptanceScore",
    "autoCloseDate",
    "closeTrigger",
    "approvalRule",
    "opportunityId",
    "accountId",
    "leadId",
    "contactId",
    "providerCredential",
    "providerSecret",
    "promptText",
    "rawCompletionPayload",
    "isCurrent",
    "isLatest",
    "legalHold",
    "auditHold",
    "hold",
    "assignedUser",
    "teams",
    # Historical WP2.2 field names must not remain on the ratified contract.
    "proposalContent",
    "proposalSource",
    "sourceEvidenceReference",
    "generationContext",
    "capabilityReference",
    "purposeReference",
    "transitionHistory",
    "name",
}

SAVE_OPTION_CONSTANTS = {
    "GENERATION_AUTHORIZED",
    "STATUS_MUTATION_AUTHORIZED",
    "VALIDITY_DISPOSITION_AUTHORIZED",
    "RETENTION_DISPOSITION_AUTHORIZED",
    "DELETION_AUTHORIZED",
    "AUDIT_WRITE_AUTHORIZED",
}

BRIEF_ACTIONS = {
    "brief.generate",
    "brief.regenerate",
    "brief.review",
    "brief.accept",
    "brief.dismiss",
    "brief.invalidate",
    "brief.archive",
    "brief.delete",
}

WP21B_PHP = [
    ENTITY_CLASS,
    SAVE_OPTION,
    AUTH_SERVICE,
    IMMUTABLE_GUARD,
    STATE_GUARD,
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def wp21b_blob() -> str:
    parts = [path.read_text(encoding="utf-8") for path in WP21B_PHP]
    for path in (
        ENTITY_DEF,
        SCOPE,
        ACL_DEF,
        APP_ACL,
        PORTAL_ACL,
        WORKFLOW,
        I18N_EN,
        I18N_ZH,
    ):
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_allowlist_files_exist() -> None:
    for path in WP21B_PHP:
        assert path.is_file(), path
    for path in (
        ENTITY_DEF,
        SCOPE,
        ACL_DEF,
        APP_ACL,
        PORTAL_ACL,
        WORKFLOW,
        I18N_EN,
        I18N_ZH,
    ):
        assert path.is_file(), path


def test_entity_contract_and_nine_provenance_fields() -> None:
    source = ENTITY_CLASS.read_text(encoding="utf-8")
    assert "final class CommercialBrief" in source
    assert "ENTITY_TYPE = 'CommercialBrief'" in source
    assert "PROVENANCE_FIELDS" in source
    for field in PROVENANCE_ATTRS:
        assert f"'{field}'" in source, field
    match = re.search(
        r"PROVENANCE_FIELDS\s*=\s*\[(.*?)\];",
        source,
        flags=re.S,
    )
    assert match is not None
    listed = re.findall(r"'([^']+)'", match.group(1))
    assert len(listed) == 9
    assert set(listed) == PROVENANCE_ATTRS


def test_entitydefs_field_allowlist_and_anchor() -> None:
    defs = load_json(ENTITY_DEF)
    assert set(defs["fields"]) == ALLOWED_FIELDS
    assert all(field.get("readOnly") is True for field in defs["fields"].values())
    assert defs["deleteId"] is True
    links = defs["links"]
    assert links["opportunityCandidate"]["entity"] == "OpportunityCandidate"
    assert links["opportunityCandidate"]["type"] == "belongsTo"
    assert links["supersedesBrief"]["entity"] == "CommercialBrief"
    assert links["sourceAIJob"]["entity"] == "AIJob"
    assert links["sourceAIRequestLog"]["entity"] == "AIRequestLog"
    linked = {meta["entity"] for meta in links.values()}
    assert not linked & {"Opportunity", "Lead", "Account", "Contact", "Quote"}


def test_review_and_disposition_enums() -> None:
    fields = load_json(ENTITY_DEF)["fields"]
    assert fields["reviewStatus"]["options"] == [
        "GENERATED",
        "REVIEWED",
        "ACCEPTED",
        "DISMISSED",
    ]
    assert fields["reviewStatus"]["default"] == "GENERATED"
    assert "SUPERSEDED" not in fields["reviewStatus"]["options"]
    assert fields["validityDisposition"]["options"] == ["NONE", "INVALIDATED"]
    assert fields["retentionDisposition"]["options"] == ["ACTIVE", "ARCHIVED"]
    assert fields["acceptanceScope"]["options"] == [
        "",
        "DECISION_SUPPORT_MATERIAL_ONLY",
    ]


def test_forbidden_fields_absent() -> None:
    fields = set(load_json(ENTITY_DEF)["fields"])
    assert not fields & FORBIDDEN_FIELDS


def test_scopes_acl_portal_and_workflow_metadata() -> None:
    scope = load_json(SCOPE)
    assert scope == {
        "entity": True,
        "object": False,
        "tab": False,
        "acl": True,
        "aclPortal": False,
        "customizable": False,
        "importable": False,
        "module": "CommercialIntelligence",
        "type": "Base",
        "statusField": None,
        "aclActionList": ["read"],
    }
    # Plan §11.3: aclDefs is empty object (C24 precedent).
    assert load_json(ACL_DEF) == {}

    acl = load_json(APP_ACL)
    assert "CommercialBrief" not in acl.get("mandatory", {}).get("scopeLevel", {})
    rights = acl["adminMandatory"]["scopeLevel"]["CommercialBrief"]
    assert rights == {
        "create": "no",
        "read": "all",
        "edit": "no",
        "delete": "no",
    }

    portal = load_json(PORTAL_ACL)
    assert portal["mandatory"]["scopeLevel"]["CommercialBrief"] is False

    workflow = load_json(WORKFLOW)
    assert workflow["version"] == 1
    assert set(workflow["actionRoleBindings"]) == BRIEF_ACTIONS


def test_i18n_key_parity() -> None:
    en = load_json(I18N_EN)
    zh = load_json(I18N_ZH)
    assert set(en["fields"]) == set(zh["fields"]) == ALLOWED_FIELDS
    assert set(en["options"]) == set(zh["options"])
    assert set(en["options"]["reviewStatus"]) == set(zh["options"]["reviewStatus"])
    assert set(en["labels"]) == set(zh["labels"])


def test_save_option_has_six_channel_constants_including_audit_token() -> None:
    source = SAVE_OPTION.read_text(encoding="utf-8")
    for name in SAVE_OPTION_CONSTANTS:
        assert f"public const {name}" in source, name
    assert "c25.briefAuditWriteAuthorized" in source
    assert "c25.briefGenerationAuthorized" in source
    assert "PROPOSAL_CREATE_AUTHORIZED" not in source
    assert "REVIEW_TRANSITION_AUTHORIZED" not in source


def test_authorization_service_is_persistence_only() -> None:
    source = AUTH_SERVICE.read_text(encoding="utf-8")
    assert "final class CommercialBriefAuthorizationService" in source
    for action in BRIEF_ACTIONS:
        assert action in source
    assert "commercialBriefWorkflow" in source
    assert "checkEntityRead" in source
    assert "isPortal" in source
    for token in (
        "CompletionRequest",
        "ProviderBinding",
        "CommercialBriefAuditWriter",
        "saveEntity",
        "createEntity",
        "curl",
        "guzzle",
    ):
        assert token not in source, token


def test_wp21b_guards_exist_under_plan_names() -> None:
    immutable = IMMUTABLE_GUARD.read_text(encoding="utf-8")
    state = STATE_GUARD.read_text(encoding="utf-8")
    assert "final class CommercialBriefImmutableGuard" in immutable
    assert "public static int $order = 1000" in immutable
    assert "GENERATION_AUTHORIZED" in immutable
    assert "opportunityCandidateId" in immutable
    assert "sourceAIJobId" in immutable
    assert "capability" in immutable
    assert "purpose" in immutable

    assert "final class CommercialBriefStateGuard" in state
    assert "public static int $order = 1010" in state
    assert "'GENERATED' => ['REVIEWED']" in state
    assert "'REVIEWED' => ['ACCEPTED', 'DISMISSED']" in state
    assert "STATUS_MUTATION_AUTHORIZED" in state
    assert "VALIDITY_DISPOSITION_AUTHORIZED" in state
    assert "RETENTION_DISPOSITION_AUTHORIZED" in state
    assert "DELETION_AUTHORIZED" in state


def test_historical_hooks_retained_but_not_adopted() -> None:
    """C1: historical WP2.2 hooks remain; WP2.1B uses Plan §28.1 names.

    Disposition of historical hooks is a separate governance action. Active
    intended WP2.1B hooks are CommercialBriefImmutableGuard and
    CommercialBriefStateGuard. Historical files are not deleted by WP2.1B.
    """
    assert HISTORICAL_IMMUTABLE.is_file()
    assert HISTORICAL_REVIEW.is_file()
    assert IMMUTABLE_GUARD.is_file()
    assert STATE_GUARD.is_file()
    historical = (
        HISTORICAL_IMMUTABLE.read_text(encoding="utf-8")
        + "\n"
        + HISTORICAL_REVIEW.read_text(encoding="utf-8")
    )
    assert "CommercialBriefImmutabilityGuard" in historical
    assert "CommercialBriefReviewStatusGuard" in historical
    allowlist = "\n".join(path.read_text(encoding="utf-8") for path in WP21B_PHP)
    assert "CommercialBriefImmutabilityGuard" not in allowlist
    assert "CommercialBriefReviewStatusGuard" not in allowlist
    assert "CommercialBriefProposalService" not in allowlist
    assert "CommercialBriefReviewService" not in allowlist


def test_no_audit_writer_or_audit_entity_in_wp21b_scope() -> None:
    blob = wp21b_blob()
    for token in (
        "CommercialBriefAuditWriter",
        "CommercialBriefAuditEvent",
        "CommercialBriefAuditGuard",
        "CommercialBriefAuditEventAppendOnlyGuard",
    ):
        assert token not in blob, token
    assert not (MODULE / "Services" / "CommercialBriefAuditWriter.php").exists()
    assert not (MODULE / "Entities" / "CommercialBriefAuditEvent.php").exists()


def test_no_generation_provider_or_runtime_surface_in_wp21b() -> None:
    blob = wp21b_blob().lower()
    for token in (
        "completionrequest",
        "providerbinding",
        "providerroute",
        "guzzle",
        "curl_exec",
        "file_get_contents",
        "httpclient",
        "scheduler",
        "webhook",
        "worker",
        "queue",
    ):
        assert token not in blob, token
    assert not (
        MODULE / "Services" / "CommercialBriefGenerationService.php"
    ).exists()
    assert not (MODULE / "Api" / "PostBriefGenerate.php").exists()


def test_no_migration_sql_or_afterinstall_for_commercial_brief() -> None:
    assert list(EXT.rglob("*CommercialBrief*migration*")) == []
    assert list(EXT.rglob("*CommercialBrief*.sql")) == []
    after_install = EXT / "scripts" / "AfterInstall.php"
    if after_install.is_file():
        text = after_install.read_text(encoding="utf-8")
        assert "CommercialBrief" not in text


def test_wp21b_does_not_rely_on_controller_or_clientdefs() -> None:
    """Option A: no custom controller / clientDefs in WP2.1B deliverables.

    Historical controller/clientDefs may still exist as unauthorized orphans;
    WP2.1B allowlist PHP must not reference them.
    """
    allowlist = "\n".join(path.read_text(encoding="utf-8") for path in WP21B_PHP)
    assert "Controllers\\CommercialBrief" not in allowlist
    assert "clientDefs/CommercialBrief" not in allowlist
    scope = load_json(SCOPE)
    assert scope["tab"] is False
    assert scope["object"] is False
    assert scope["aclActionList"] == ["read"]


def test_no_crm_core_write_or_lifecycle_authority_markers() -> None:
    blob = wp21b_blob()
    for value in (
        '"entity": "Opportunity"',
        '"entity": "Lead"',
        '"entity": "Account"',
        '"entity": "Contact"',
        "ActionGate",
        "ExecutionLedger",
        "saveEntity($opportunity",
        "createEntity('Lead'",
        "createEntity('Opportunity'",
    ):
        assert value not in blob, value
