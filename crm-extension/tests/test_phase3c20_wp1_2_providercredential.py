"""Phase3C20 WP1.2 ProviderCredential reference-custody contracts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_PLATFORM = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "AIPlatform"
ENTITY_DEFS = AI_PLATFORM / "Resources" / "metadata" / "entityDefs"
ENTITY_DEF = ENTITY_DEFS / "ProviderCredential.json"
AI_JOB_ENTITY_DEF = ENTITY_DEFS / "AIJob.json"
AI_REQUEST_LOG_ENTITY_DEF = ENTITY_DEFS / "AIRequestLog.json"
PROMPT_TEMPLATE_ENTITY_DEF = ENTITY_DEFS / "PromptTemplate.json"
SCOPE = AI_PLATFORM / "Resources" / "metadata" / "scopes" / "ProviderCredential.json"
AI_JOB_SCOPE = AI_PLATFORM / "Resources" / "metadata" / "scopes" / "AIJob.json"
AI_REQUEST_LOG_SCOPE = AI_PLATFORM / "Resources" / "metadata" / "scopes" / "AIRequestLog.json"
PROMPT_TEMPLATE_SCOPE = AI_PLATFORM / "Resources" / "metadata" / "scopes" / "PromptTemplate.json"
ACL_DEF = AI_PLATFORM / "Resources" / "metadata" / "aclDefs" / "ProviderCredential.json"
AI_JOB_ACL_DEF = AI_PLATFORM / "Resources" / "metadata" / "aclDefs" / "AIJob.json"
AI_REQUEST_LOG_ACL_DEF = AI_PLATFORM / "Resources" / "metadata" / "aclDefs" / "AIRequestLog.json"
PROMPT_TEMPLATE_ACL_DEF = AI_PLATFORM / "Resources" / "metadata" / "aclDefs" / "PromptTemplate.json"
ENTITY_ACL = AI_PLATFORM / "Resources" / "metadata" / "entityAcl" / "ProviderCredential.json"
PROMPT_TEMPLATE_ENTITY_ACL = (
    AI_PLATFORM / "Resources" / "metadata" / "entityAcl" / "PromptTemplate.json"
)
APP_ACL = AI_PLATFORM / "Resources" / "metadata" / "app" / "acl.json"
APP_ACL_PORTAL = AI_PLATFORM / "Resources" / "metadata" / "app" / "aclPortal.json"
ADMIN_PANEL = AI_PLATFORM / "Resources" / "metadata" / "app" / "adminPanel.json"
BINDING = AI_PLATFORM / "Binding.php"
MODULE_METADATA = AI_PLATFORM / "Resources" / "module.json"
ADMIN_I18N_EN = AI_PLATFORM / "Resources" / "i18n" / "en_US" / "Admin.json"
GLOBAL_I18N_EN = AI_PLATFORM / "Resources" / "i18n" / "en_US" / "Global.json"
ADMIN_I18N_ZH = AI_PLATFORM / "Resources" / "i18n" / "zh_CN" / "Admin.json"
GLOBAL_I18N_ZH = AI_PLATFORM / "Resources" / "i18n" / "zh_CN" / "Global.json"
ENTITY_I18N_EN = AI_PLATFORM / "Resources" / "i18n" / "en_US" / "ProviderCredential.json"
ENTITY_I18N_ZH = AI_PLATFORM / "Resources" / "i18n" / "zh_CN" / "ProviderCredential.json"
LIST_LAYOUT = AI_PLATFORM / "Resources" / "layouts" / "ProviderCredential" / "list.json"
DETAIL_LAYOUT = AI_PLATFORM / "Resources" / "layouts" / "ProviderCredential" / "detail.json"
AI_JOB_SERVICE = AI_PLATFORM / "Services" / "AIJobService.php"
AI_JOB_SAVE_OPTION = AI_PLATFORM / "Services" / "AIJobStatusMutationSaveOption.php"
AI_JOB_GUARD = AI_PLATFORM / "Hooks" / "AIJob" / "AIJobStatusMutationGuard.php"
AI_REQUEST_LOG_ENTITY = AI_PLATFORM / "Entities" / "AIRequestLog.php"
AI_REQUEST_LOG_SERVICE = AI_PLATFORM / "Services" / "AIRequestLogService.php"
AI_REQUEST_LOG_SAVE_OPTION = AI_PLATFORM / "Services" / "AIRequestLogSaveOption.php"
AI_REQUEST_LOG_GUARD = AI_PLATFORM / "Hooks" / "AIRequestLog" / "AIRequestLogAppendOnlyGuard.php"
PROMPT_TEMPLATE_ENTITY = AI_PLATFORM / "Entities" / "PromptTemplate.php"
PROMPT_TEMPLATE_SERVICE = AI_PLATFORM / "Services" / "PromptTemplateService.php"
PROMPT_TEMPLATE_SAVE_OPTION = AI_PLATFORM / "Services" / "PromptTemplateSaveOption.php"
PROMPT_TEMPLATE_GUARD = (
    AI_PLATFORM / "Hooks" / "PromptTemplate" / "PromptTemplateMutationGuard.php"
)
PROVIDER_BINDING_ENTITY_DEF = ENTITY_DEFS / "ProviderBinding.json"
PROVIDER_BINDING_SCOPE = AI_PLATFORM / "Resources" / "metadata" / "scopes" / "ProviderBinding.json"
PROVIDER_BINDING_ACL_DEF = AI_PLATFORM / "Resources" / "metadata" / "aclDefs" / "ProviderBinding.json"
PROVIDER_BINDING_ENTITY_ACL = (
    AI_PLATFORM / "Resources" / "metadata" / "entityAcl" / "ProviderBinding.json"
)
PROVIDER_BINDING_SERVICE = AI_PLATFORM / "Services" / "ProviderBindingService.php"
PROVIDER_BINDING_SAVE_OPTION = (
    AI_PLATFORM / "Services" / "ProviderBindingMutationSaveOption.php"
)
PROVIDER_BINDING_GUARD = (
    AI_PLATFORM / "Hooks" / "ProviderBinding" / "ProviderBindingMutationGuard.php"
)
PROVIDER_BINDING_I18N_EN = AI_PLATFORM / "Resources" / "i18n" / "en_US" / "ProviderBinding.json"
PROVIDER_BINDING_I18N_ZH = AI_PLATFORM / "Resources" / "i18n" / "zh_CN" / "ProviderBinding.json"
PROVIDER_BINDING_LIST_LAYOUT = (
    AI_PLATFORM / "Resources" / "layouts" / "ProviderBinding" / "list.json"
)
PROVIDER_BINDING_DETAIL_LAYOUT = (
    AI_PLATFORM / "Resources" / "layouts" / "ProviderBinding" / "detail.json"
)

# RT-WP3–WP7 Lite foundation surfaces (vocabulary / boundary validation only).
AI_DISPATCH_REQUEST = AI_PLATFORM / "Services" / "AIDispatchRequest.php"
AI_DISPATCH_BOUNDARY = AI_PLATFORM / "Services" / "AIDispatchExecutionBoundary.php"
AI_DISPATCH_GUARDS = AI_PLATFORM / "Services" / "AIDispatchRuntimeGuardsLite.php"
AI_DISPATCH_SERVICE = AI_PLATFORM / "Services" / "AIDispatchService.php"
AI_FOUNDATION_STATE = AI_PLATFORM / "Services" / "AIFoundationState.php"
AI_FOUNDATION_STATE_SERVICE = AI_PLATFORM / "Services" / "AIFoundationStateService.php"
AI_FOUNDATION_STATE_GUARD = AI_PLATFORM / "Services" / "AIFoundationStateTransitionGuard.php"
AI_FAILURE_METADATA = AI_PLATFORM / "Services" / "AIFailureMetadata.php"
AI_FAILURE_METADATA_SERVICE = AI_PLATFORM / "Services" / "AIFailureMetadataService.php"
AI_FAILURE_METADATA_GUARD = AI_PLATFORM / "Services" / "AIFailureMetadataGuard.php"
AI_RESERVATION_METADATA = AI_PLATFORM / "Services" / "AIReservationMetadata.php"
AI_RESERVATION_METADATA_SERVICE = AI_PLATFORM / "Services" / "AIReservationMetadataService.php"
AI_RESERVATION_METADATA_GUARD = AI_PLATFORM / "Services" / "AIReservationMetadataGuard.php"
AI_GUARD_RULE = AI_PLATFORM / "Services" / "AIGuardRule.php"
AI_GUARD_RESULT = AI_PLATFORM / "Services" / "AIGuardValidationResult.php"
AI_GUARD_SERVICE = AI_PLATFORM / "Services" / "AIGuardService.php"

RUNTIME_LITE_FOUNDATION_FILES = {
    AI_DISPATCH_REQUEST,
    AI_DISPATCH_BOUNDARY,
    AI_DISPATCH_GUARDS,
    AI_DISPATCH_SERVICE,
    AI_FOUNDATION_STATE,
    AI_FOUNDATION_STATE_SERVICE,
    AI_FOUNDATION_STATE_GUARD,
    AI_FAILURE_METADATA,
    AI_FAILURE_METADATA_SERVICE,
    AI_FAILURE_METADATA_GUARD,
    AI_RESERVATION_METADATA,
    AI_RESERVATION_METADATA_SERVICE,
    AI_RESERVATION_METADATA_GUARD,
    AI_GUARD_RULE,
    AI_GUARD_RESULT,
    AI_GUARD_SERVICE,
}

# Reject-list / boundary-validation surfaces may name secret/Opportunity terms
# only to deny them. That is not secret custody or lifecycle authority.
REJECT_VOCABULARY_FILES = RUNTIME_LITE_FOUNDATION_FILES | {
    PROVIDER_BINDING_SERVICE,
    PROVIDER_BINDING_GUARD,
}
REJECT_LIST_ISOLATION_TERMS = {"Opportunity"}

APPROVED_MODULE_FILES = {
    BINDING,
    MODULE_METADATA,
    ENTITY_DEF,
    SCOPE,
    ACL_DEF,
    ENTITY_ACL,
    APP_ACL,
    APP_ACL_PORTAL,
    ADMIN_PANEL,
    ADMIN_I18N_EN,
    GLOBAL_I18N_EN,
    ADMIN_I18N_ZH,
    GLOBAL_I18N_ZH,
    ENTITY_I18N_EN,
    ENTITY_I18N_ZH,
    LIST_LAYOUT,
    DETAIL_LAYOUT,
    AI_JOB_ENTITY_DEF,
    AI_JOB_SCOPE,
    AI_JOB_ACL_DEF,
    AI_JOB_SERVICE,
    AI_JOB_SAVE_OPTION,
    AI_JOB_GUARD,
    AI_REQUEST_LOG_ENTITY_DEF,
    AI_REQUEST_LOG_SCOPE,
    AI_REQUEST_LOG_ACL_DEF,
    AI_REQUEST_LOG_ENTITY,
    AI_REQUEST_LOG_SERVICE,
    AI_REQUEST_LOG_SAVE_OPTION,
    AI_REQUEST_LOG_GUARD,
    PROMPT_TEMPLATE_ENTITY_DEF,
    PROMPT_TEMPLATE_SCOPE,
    PROMPT_TEMPLATE_ACL_DEF,
    PROMPT_TEMPLATE_ENTITY_ACL,
    PROMPT_TEMPLATE_ENTITY,
    PROMPT_TEMPLATE_SERVICE,
    PROMPT_TEMPLATE_SAVE_OPTION,
    PROMPT_TEMPLATE_GUARD,
    PROVIDER_BINDING_ENTITY_DEF,
    PROVIDER_BINDING_SCOPE,
    PROVIDER_BINDING_ACL_DEF,
    PROVIDER_BINDING_ENTITY_ACL,
    PROVIDER_BINDING_SERVICE,
    PROVIDER_BINDING_SAVE_OPTION,
    PROVIDER_BINDING_GUARD,
    PROVIDER_BINDING_I18N_EN,
    PROVIDER_BINDING_I18N_ZH,
    PROVIDER_BINDING_LIST_LAYOUT,
    PROVIDER_BINDING_DETAIL_LAYOUT,
    *RUNTIME_LITE_FOUNDATION_FILES,
}

ALLOWED_FIELDS = {
    "providerKey",
    "credentialReference",
    "displayName",
    "fingerprint",
    "lastFour",
    "environment",
    "ownerUser",
    "rotationDueAt",
    "lastRotatedAt",
    "description",
}
EXPECTED_TYPES = {
    "providerKey": "varchar",
    "credentialReference": "varchar",
    "displayName": "varchar",
    "fingerprint": "varchar",
    "lastFour": "varchar",
    "environment": "varchar",
    "ownerUser": "link",
    "rotationDueAt": "date",
    "lastRotatedAt": "datetime",
    "description": "text",
}
FORBIDDEN_SECRET_FIELDS = {
    "apiKey",
    "apiSecret",
    "token",
    "password",
    "secret",
    "plaintextCredential",
    "encryptedSecret",
    "decryptedValue",
    "rawCredential",
    "privateKey",
    "accessToken",
    "refreshToken",
}
FORBIDDEN_LIFECYCLE_TERMS = {
    "status",
    "state",
    "active",
    "inactive",
    "revoked",
    "expired",
    "pending",
    "activate",
    "deactivate",
    "rotate",
    "transition",
}
ISOLATION_TERMS = (
    "Prospecting",
    "Lead",
    "Opportunity",
    "SendExecution",
    "ReplyEvent",
    "Chitu",
)
FORBIDDEN_PROVIDER_CREDENTIAL_RUNTIME_PATHS = (
    AI_PLATFORM / "Services" / "ProviderCredentialService.php",
    AI_PLATFORM / "Hooks" / "ProviderCredential",
    AI_PLATFORM / "Api" / "ProviderCredential",
    AI_PLATFORM / "Controllers" / "ProviderCredential.php",
)
FORBIDDEN_RUNTIME_TERMS = (
    r"\bProvider\b",
    r"\bResolver\b",
    r"\bRegistry\b",
    r"\bAdapter\b",
    r"\bTransport\b",
    r"\bConnector\b",
    r"\bGuzzle\b",
    r"\bHTTP\b",
    r"\bcurl\b",
    r"\bfile_get_contents\b",
    r"\bCredentialService\b",
    r"\bProviderCredentialService\b",
    r"\bRotationService\b",
    r"\bAuditService\b",
    r"\bSecretService\b",
)
FORBIDDEN_REFERENCE_RUNTIME_TERMS = (
    "resolveCredential",
    "getSecret",
    "decryptCredential",
    "decryptSecret",
    "loadProviderKey",
    "readSecret",
)
FORBIDDEN_EGRESS_PATTERNS = (
    r"\bcurl(?:_[A-Za-z0-9_]+)?\b",
    r"\bGuzzle\b",
    r"\bHttpClient\b",
    r"\bHTTP\s+client\b",
    r"\bexternal\s+request\b",
    r"\bconnector\s+invocation\b",
    r"\bfile_get_contents\b",
    r"\bstream_socket_client\b",
    r"\bfsockopen\b",
)
FORBIDDEN_RUNTIME_SURFACE_TERMS = (
    "CredentialService",
    "ProviderCredentialService",
    "RotationService",
    "AuditService",
    "SecretService",
    "Controller",
    "Action",
    "Job",
    "Hook",
    "Workflow",
)
WP_BOUNDARY_TERMS = (
    "Prospecting",
    "SendExecution",
    "ReplyEvent",
    "MutationGuard",
    "canonical_score",
    "AIQualificationInsight",
)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_entity_def() -> dict[str, object]:
    return load_json(ENTITY_DEF)


def module_source_files() -> list[Path]:
    return sorted(
        path
        for path in AI_PLATFORM.rglob("*")
        if path.is_file() and path.suffix in {".json", ".php"}
    )


def runtime_contract_files() -> list[Path]:
    return [
        path
        for path in module_source_files()
        if not {"i18n", "layouts"}.intersection(path.relative_to(AI_PLATFORM).parts)
    ]


class Phase3C20WP12ProviderCredentialTests(unittest.TestCase):
    def test_entity_definition_has_exact_reference_metadata_fields(self) -> None:
        self.assertTrue(ENTITY_DEF.is_file())
        self.assertEqual(
            set(ENTITY_DEFS.glob("*.json")),
            {
                ENTITY_DEF,
                AI_JOB_ENTITY_DEF,
                AI_REQUEST_LOG_ENTITY_DEF,
                PROMPT_TEMPLATE_ENTITY_DEF,
                PROVIDER_BINDING_ENTITY_DEF,
            },
        )

        metadata = load_entity_def()
        fields = metadata["fields"]
        self.assertEqual(set(fields), ALLOWED_FIELDS)
        self.assertEqual({name: value["type"] for name, value in fields.items()}, EXPECTED_TYPES)
        self.assertEqual(fields["lastFour"]["maxLength"], 4)
        self.assertEqual(
            metadata["links"]["ownerUser"],
            {"type": "belongsTo", "entity": "User"},
        )

    def test_forbidden_secret_fields_are_absent(self) -> None:
        metadata = load_entity_def()
        fields = metadata["fields"]
        self.assertTrue(FORBIDDEN_SECRET_FIELDS.isdisjoint(fields))

        source = ENTITY_DEF.read_text(encoding="utf-8")
        for field_name in FORBIDDEN_SECRET_FIELDS:
            self.assertIsNone(
                re.search(rf'"{re.escape(field_name)}"\s*:', source),
                msg=f"Forbidden secret field declared: {field_name}",
            )

    def test_forbidden_secret_identifiers_are_absent_from_all_module_sources(self) -> None:
        offenders: list[str] = []
        for path in module_source_files():
            if path in REJECT_VOCABULARY_FILES:
                # Reject-list tokens (e.g. "secret") deny custody; they are not fields.
                continue
            source = path.read_text(encoding="utf-8")
            for identifier in FORBIDDEN_SECRET_FIELDS:
                if re.search(rf"\b{re.escape(identifier)}\b", source, flags=re.IGNORECASE):
                    offenders.append(f"{path.relative_to(AI_PLATFORM).as_posix()}: {identifier}")
        self.assertEqual(offenders, [])

    def test_credential_reference_is_metadata_only(self) -> None:
        metadata = load_entity_def()
        field = metadata["fields"]["credentialReference"]
        self.assertEqual(field["type"], "varchar")
        self.assertTrue(field["required"])
        self.assertNotIn("default", field)
        self.assertNotIn("collection", metadata)
        self.assertNotIn("indexes", metadata)

        for path in FORBIDDEN_PROVIDER_CREDENTIAL_RUNTIME_PATHS:
            self.assertFalse(path.exists(), msg=str(path))
        for path in (ENTITY_DEF, ENTITY_ACL):
            source = path.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_RUNTIME_TERMS:
                self.assertIsNone(re.search(pattern, source, flags=re.IGNORECASE), msg=f"{path}: {pattern}")

        reference_paths = {
            path
            for path in module_source_files()
            if "credentialReference" in path.read_text(encoding="utf-8")
        }
        self.assertEqual(
            reference_paths,
            {
                ENTITY_DEF,
                ENTITY_ACL,
                ENTITY_I18N_EN,
                ENTITY_I18N_ZH,
                PROVIDER_BINDING_ENTITY_DEF,
                PROVIDER_BINDING_ENTITY_ACL,
                PROVIDER_BINDING_I18N_EN,
                PROVIDER_BINDING_I18N_ZH,
                PROVIDER_BINDING_SERVICE,
                PROVIDER_BINDING_GUARD,
                # RT-WP3 Lite passes the custody reference through the boundary
                # without resolving it.
                AI_DISPATCH_BOUNDARY,
                AI_DISPATCH_SERVICE,
            },
        )

    def test_credential_reference_has_no_runtime_resolution_path(self) -> None:
        offenders: list[str] = []
        for path in module_source_files():
            source = path.read_text(encoding="utf-8")
            for term in FORBIDDEN_REFERENCE_RUNTIME_TERMS:
                if re.search(rf"\b{re.escape(term)}\b", source, flags=re.IGNORECASE):
                    offenders.append(f"{path.relative_to(AI_PLATFORM).as_posix()}: {term}")
        self.assertEqual(offenders, [])

    def test_provider_egress_is_absent(self) -> None:
        offenders: list[str] = []
        for path in module_source_files():
            source = path.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_EGRESS_PATTERNS:
                if re.search(pattern, source, flags=re.IGNORECASE):
                    offenders.append(f"{path.relative_to(AI_PLATFORM).as_posix()}: {pattern}")
        self.assertEqual(offenders, [])

    def test_lifecycle_is_absent(self) -> None:
        metadata = load_entity_def()
        fields = metadata["fields"]
        self.assertTrue(FORBIDDEN_LIFECYCLE_TERMS.isdisjoint(fields))

        source = ENTITY_DEF.read_text(encoding="utf-8")
        for term in FORBIDDEN_LIFECYCLE_TERMS:
            self.assertIsNone(re.search(rf"\b{re.escape(term)}\b", source, flags=re.IGNORECASE))

    def test_namespace_isolation_is_preserved(self) -> None:
        offenders: list[str] = []
        for path in AI_PLATFORM.rglob("*"):
            if not path.is_file():
                continue
            source = path.read_text(encoding="utf-8")
            for term in ISOLATION_TERMS:
                if not re.search(rf"\b{re.escape(term)}\b", source):
                    continue
                if path in REJECT_VOCABULARY_FILES and term in REJECT_LIST_ISOLATION_TERMS:
                    continue
                offenders.append(f"{path.relative_to(ROOT)}: {term}")
        self.assertEqual(offenders, [])

    def test_scope_exists_with_acl_enabled_and_no_public_surface(self) -> None:
        self.assertEqual(
            set(SCOPE.parent.glob("*.json")),
            {
                SCOPE,
                AI_JOB_SCOPE,
                AI_REQUEST_LOG_SCOPE,
                PROMPT_TEMPLATE_SCOPE,
                PROVIDER_BINDING_SCOPE,
            },
        )
        scope = load_json(SCOPE)
        self.assertEqual(
            scope,
            {
                "entity": True,
                "object": False,
                "tab": False,
                "acl": True,
                "aclPortal": False,
                "customizable": False,
                "importable": False,
                "module": "AIPlatform",
                "type": "Base",
                "statusField": None,
            },
        )

    def test_acl_forces_admin_only_crud_and_portal_denial(self) -> None:
        self.assertEqual(
            set(ACL_DEF.parent.glob("*.json")),
            {
                ACL_DEF,
                AI_JOB_ACL_DEF,
                AI_REQUEST_LOG_ACL_DEF,
                PROMPT_TEMPLATE_ACL_DEF,
                PROVIDER_BINDING_ACL_DEF,
            },
        )
        self.assertEqual(
            set(ENTITY_ACL.parent.glob("*.json")),
            {ENTITY_ACL, PROMPT_TEMPLATE_ENTITY_ACL, PROVIDER_BINDING_ENTITY_ACL},
        )
        self.assertEqual(
            set(APP_ACL.parent.glob("*.json")),
            {APP_ACL, APP_ACL_PORTAL, ADMIN_PANEL},
        )
        self.assertEqual(load_json(ACL_DEF), {})

        acl = load_json(APP_ACL)
        self.assertFalse(acl["mandatory"]["scopeLevel"]["ProviderCredential"])
        self.assertEqual(
            acl["adminMandatory"]["scopeLevel"]["ProviderCredential"],
            {"create": "yes", "read": "all", "edit": "all", "delete": "all"},
        )

        portal_acl = load_json(APP_ACL_PORTAL)
        self.assertFalse(portal_acl["mandatory"]["scopeLevel"]["ProviderCredential"])

    def test_credential_reference_is_internal_write_only_metadata(self) -> None:
        self.assertEqual(
            load_json(ENTITY_ACL),
            {"fields": {"credentialReference": {"internal": True}}},
        )

    def test_owner_user_does_not_create_record_ownership_acl(self) -> None:
        metadata = load_entity_def()
        self.assertEqual(set(metadata["links"]), {"ownerUser"})
        self.assertNotIn("assignedUser", metadata["fields"])
        self.assertNotIn("teams", metadata["fields"])

        acl_def = load_json(ACL_DEF)
        self.assertNotIn("readOwnerUserField", acl_def)
        self.assertNotIn("ownershipCheckerClassName", acl_def)
        acl_text = APP_ACL.read_text(encoding="utf-8")
        self.assertNotRegex(acl_text, r'"(?:own|team)"')

    def test_no_ui_or_runtime_metadata_surface_is_created(self) -> None:
        forbidden_paths = (
            AI_PLATFORM / "Resources" / "metadata" / "clientDefs",
            AI_PLATFORM / "Resources" / "views",
            AI_PLATFORM / "Views",
            AI_PLATFORM / "Resources" / "metadata" / "navigation",
            AI_PLATFORM / "Resources" / "metadata" / "dashlets",
        )
        for path in forbidden_paths:
            self.assertFalse(path.exists(), msg=str(path))
        self.assertEqual(
            set((AI_PLATFORM / "Resources" / "layouts").rglob("*.json")),
            {
                LIST_LAYOUT,
                DETAIL_LAYOUT,
                PROVIDER_BINDING_LIST_LAYOUT,
                PROVIDER_BINDING_DETAIL_LAYOUT,
            },
        )
        for path in FORBIDDEN_PROVIDER_CREDENTIAL_RUNTIME_PATHS:
            self.assertFalse(path.exists(), msg=str(path))

    def test_no_service_or_runtime_surface_is_declared(self) -> None:
        self.assertEqual(set(module_source_files()), APPROVED_MODULE_FILES)

        self.assertEqual(
            set((AI_PLATFORM / "Services").glob("*.php")),
            {
                AI_JOB_SERVICE,
                AI_JOB_SAVE_OPTION,
                AI_REQUEST_LOG_SERVICE,
                AI_REQUEST_LOG_SAVE_OPTION,
                PROMPT_TEMPLATE_SERVICE,
                PROMPT_TEMPLATE_SAVE_OPTION,
                PROVIDER_BINDING_SERVICE,
                PROVIDER_BINDING_SAVE_OPTION,
                *RUNTIME_LITE_FOUNDATION_FILES,
            },
        )
        self.assertEqual(
            set((AI_PLATFORM / "Hooks" / "AIJob").glob("*.php")),
            {AI_JOB_GUARD},
        )
        self.assertEqual(
            set((AI_PLATFORM / "Hooks" / "AIRequestLog").glob("*.php")),
            {AI_REQUEST_LOG_GUARD},
        )
        self.assertEqual(
            set((AI_PLATFORM / "Hooks" / "PromptTemplate").glob("*.php")),
            {PROMPT_TEMPLATE_GUARD},
        )
        self.assertEqual(
            set((AI_PLATFORM / "Hooks" / "ProviderBinding").glob("*.php")),
            {PROVIDER_BINDING_GUARD},
        )
        for path in (
            AI_JOB_SERVICE,
            AI_JOB_SAVE_OPTION,
            AI_JOB_GUARD,
            AI_REQUEST_LOG_ENTITY,
            AI_REQUEST_LOG_SERVICE,
            AI_REQUEST_LOG_SAVE_OPTION,
            AI_REQUEST_LOG_GUARD,
            PROMPT_TEMPLATE_ENTITY,
            PROMPT_TEMPLATE_SERVICE,
            PROMPT_TEMPLATE_SAVE_OPTION,
            PROMPT_TEMPLATE_GUARD,
        ):
            self.assertNotIn("ProviderCredential", path.read_text(encoding="utf-8"))

    def test_wp_boundaries_and_workflow_mutation_remain_absent(self) -> None:
        offenders: list[str] = []
        for path in module_source_files():
            source = path.read_text(encoding="utf-8")
            for term in WP_BOUNDARY_TERMS:
                if not re.search(rf"\b{re.escape(term)}\b", source, flags=re.IGNORECASE):
                    continue
                if path in REJECT_VOCABULARY_FILES and term in REJECT_LIST_ISOLATION_TERMS:
                    continue
                offenders.append(f"{path.relative_to(AI_PLATFORM).as_posix()}: {term}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
