"""Phase3C20 RT-WP2 ProviderBinding CRM policy surface contracts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_PLATFORM = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "AIPlatform"
ENTITY_DEF = AI_PLATFORM / "Resources" / "metadata" / "entityDefs" / "ProviderBinding.json"
SCOPE = AI_PLATFORM / "Resources" / "metadata" / "scopes" / "ProviderBinding.json"
ACL_DEF = AI_PLATFORM / "Resources" / "metadata" / "aclDefs" / "ProviderBinding.json"
ENTITY_ACL = AI_PLATFORM / "Resources" / "metadata" / "entityAcl" / "ProviderBinding.json"
APP_ACL = AI_PLATFORM / "Resources" / "metadata" / "app" / "acl.json"
APP_ACL_PORTAL = AI_PLATFORM / "Resources" / "metadata" / "app" / "aclPortal.json"
ADMIN_PANEL = AI_PLATFORM / "Resources" / "metadata" / "app" / "adminPanel.json"
SERVICE = AI_PLATFORM / "Services" / "ProviderBindingService.php"
SAVE_OPTION = AI_PLATFORM / "Services" / "ProviderBindingMutationSaveOption.php"
GUARD = AI_PLATFORM / "Hooks" / "ProviderBinding" / "ProviderBindingMutationGuard.php"
I18N_EN = AI_PLATFORM / "Resources" / "i18n" / "en_US" / "ProviderBinding.json"
I18N_ZH = AI_PLATFORM / "Resources" / "i18n" / "zh_CN" / "ProviderBinding.json"
LIST_LAYOUT = AI_PLATFORM / "Resources" / "layouts" / "ProviderBinding" / "list.json"
DETAIL_LAYOUT = AI_PLATFORM / "Resources" / "layouts" / "ProviderBinding" / "detail.json"
INVARIANT_REGISTRY = ROOT / "docs" / "adr" / "C20_INVARIANT_REGISTRY.md"
COMPLETION_BASE = (
    ROOT
    / "chitu-connector"
    / "chitu_connector"
    / "acquisition"
    / "providers"
    / "completion"
    / "base.py"
)

ALLOWED_FIELDS = {
    "name",
    "providerId",
    "adapterType",
    "priority",
    "enabled",
    "status",
    "supportedCapabilities",
    "allowedPurposes",
    "credentialReference",
    "approvedBy",
    "approvedAt",
    "provenanceReference",
    "description",
    "createdAt",
    "modifiedAt",
}
STATUS_OPTIONS = {"DRAFT", "ACTIVE", "DISABLED", "REVOKED"}
CAPABILITY_FAMILY = {"SEARCH", "ENRICHMENT", "COMPLETION"}
COMPLETION_PORTFOLIO = {
    "RESEARCH_EVIDENCE",
    "QUALIFICATION_INSIGHT",
    "DRAFT_ASSISTANCE",
    "REPLY_ASSISTANCE",
}
ELIGIBILITY_CLASSES = {
    "NOT_AUTHORIZED",
    "UNBOUND",
    "DISABLED",
    "PURPOSE_NOT_REGISTERED",
    "CAPABILITY_MISMATCH",
    "CREDENTIAL_REFERENCE_MISSING",
    "BOUND",
}
FORBIDDEN_SECRET_FIELDS = {
    "apiKey",
    "apiSecret",
    "token",
    "password",
    "secret",
    "plaintextCredential",
    "encryptedSecret",
    "accessToken",
    "refreshToken",
    "privateKey",
}
FORBIDDEN_EXECUTION_STATES = {
    "QUEUED",
    "RUNNING",
    "SUCCEEDED",
    "FAILED",
    "CANCELLED",
    "RETRY_PENDING",
    "DISPATCH_FAILED",
    "RESERVATION_CONFLICT",
    "EXECUTION_COMPLETED",
    "PROVIDER_TIMEOUT",
}
FORBIDDEN_RUNTIME_MARKERS = (
    "curl_init",
    "GuzzleHttp",
    "file_get_contents",
    "CapabilityRegistry",
    "AIDispatchService",
    "AIRetryPolicy",
    "IdempotencyReservation",
    "CommercialBrief",
    "subprocess",
    "chitu_connector",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict | list:
    return json.loads(read(path))


class Phase3C20RTWP2ProviderBindingTests(unittest.TestCase):
    def test_allowlist_files_exist(self) -> None:
        for path in (
            ENTITY_DEF,
            SCOPE,
            ACL_DEF,
            ENTITY_ACL,
            APP_ACL,
            APP_ACL_PORTAL,
            ADMIN_PANEL,
            SERVICE,
            SAVE_OPTION,
            GUARD,
            I18N_EN,
            I18N_ZH,
            LIST_LAYOUT,
            DETAIL_LAYOUT,
        ):
            self.assertTrue(path.is_file(), msg=str(path))

    def test_entity_field_contract(self) -> None:
        entity = load_json(ENTITY_DEF)
        assert isinstance(entity, dict)
        fields = entity["fields"]
        assert isinstance(fields, dict)
        self.assertEqual(set(fields), ALLOWED_FIELDS)
        self.assertEqual(set(fields["status"]["options"]), STATUS_OPTIONS)
        self.assertEqual(fields["status"]["default"], "DRAFT")
        self.assertTrue(fields["status"]["readOnly"])
        self.assertTrue(fields["enabled"]["readOnly"])
        self.assertEqual(fields["enabled"]["default"], False)
        self.assertEqual(set(fields["supportedCapabilities"]["options"]), CAPABILITY_FAMILY)
        self.assertEqual(fields["allowedPurposes"]["type"], "array")
        self.assertEqual(fields["credentialReference"]["type"], "varchar")
        self.assertTrue(fields["credentialReference"].get("readOnlyAfterCreate"))
        self.assertTrue(fields["providerId"].get("readOnlyAfterCreate"))
        self.assertTrue(fields["adapterType"].get("readOnlyAfterCreate"))
        for secret in FORBIDDEN_SECRET_FIELDS:
            self.assertNotIn(secret, fields)
        for state in FORBIDDEN_EXECUTION_STATES:
            self.assertNotIn(state, fields["status"]["options"])

    def test_scope_flags(self) -> None:
        scope = load_json(SCOPE)
        assert isinstance(scope, dict)
        self.assertEqual(scope["entity"], True)
        self.assertEqual(scope["object"], False)
        self.assertEqual(scope["tab"], False)
        self.assertEqual(scope["acl"], True)
        self.assertEqual(scope["aclPortal"], False)
        self.assertEqual(scope["customizable"], False)
        self.assertEqual(scope["importable"], False)
        self.assertEqual(scope["module"], "AIPlatform")
        self.assertEqual(scope["type"], "Base")
        self.assertIsNone(scope["statusField"])

    def test_acl_admin_and_portal_denial(self) -> None:
        acl = load_json(APP_ACL)
        portal = load_json(APP_ACL_PORTAL)
        assert isinstance(acl, dict) and isinstance(portal, dict)
        self.assertIs(acl["mandatory"]["scopeLevel"]["ProviderBinding"], False)
        self.assertEqual(
            acl["adminMandatory"]["scopeLevel"]["ProviderBinding"],
            {"create": "yes", "read": "all", "edit": "all", "delete": "no"},
        )
        self.assertIs(portal["mandatory"]["scopeLevel"]["ProviderBinding"], False)
        entity_acl = load_json(ENTITY_ACL)
        assert isinstance(entity_acl, dict)
        self.assertTrue(entity_acl["fields"]["credentialReference"]["internal"])

    def test_layouts_exclude_credential_reference(self) -> None:
        listing = json.dumps(load_json(LIST_LAYOUT))
        detail = json.dumps(load_json(DETAIL_LAYOUT))
        self.assertNotIn("credentialReference", listing)
        self.assertNotIn("credentialReference", detail)

    def test_admin_panel_entry(self) -> None:
        panel = load_json(ADMIN_PANEL)
        assert isinstance(panel, dict)
        urls = [item["url"] for item in panel["aiPlatform"]["itemList"]]
        self.assertIn("#ProviderBinding", urls)

    def test_save_option_token(self) -> None:
        text = read(SAVE_OPTION)
        self.assertIn("PROVIDER_BINDING_MUTATION_AUTHORIZED", text)
        self.assertIn("aiplatform.providerBindingMutationAuthorized", text)
        self.assertIn("does not authorize", text.lower())
        self.assertNotIn("AIDispatchService", text)

    def test_service_contract_surface(self) -> None:
        text = read(SERVICE)
        for method in (
            "function create(",
            "function approve(",
            "function updatePolicy(",
            "function disable(",
            "function revoke(",
            "function classifyEligibility(",
            "function registerPurpose(",
            "function toConnectorBindingShape(",
        ):
            self.assertIn(method, text)
        for constant in ELIGIBILITY_CLASSES:
            self.assertIn(f"CLASS_{constant}", text)
        for capability in COMPLETION_PORTFOLIO:
            self.assertIn(capability, text)
        self.assertIn("COMMERCIAL_BRIEF", text)
        self.assertIn("commercial_brief_generation", text)
        self.assertIn("not a registered purpose", text)
        self.assertIn("rejects credential-value fields", text)
        self.assertIn("credentialReference must be a custody reference only", text)
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            self.assertNotIn(marker, text)
        # No execution-state classifications.
        for state in (
            "PROVIDER_TIMEOUT",
            "DISPATCH_FAILED",
            "RETRY_PENDING",
            "RESERVATION_CONFLICT",
            "EXECUTION_COMPLETED",
        ):
            self.assertNotIn(state, text)

    def test_guard_enforces_service_ownership_and_immutability(self) -> None:
        text = read(GUARD)
        self.assertIn("implements BeforeSave", text)
        self.assertIn("PROVIDER_BINDING_MUTATION_AUTHORIZED", text)
        self.assertIn("immutable fields may not change after create", text)
        self.assertIn("DRAFT with enabled=false", text)
        self.assertIn("Applies to every role, including admin", text)
        for field in ("providerId", "adapterType", "credentialReference"):
            self.assertIn(f"'{field}'", text)
        for field in ("status", "enabled", "approvedById", "approvedAt", "provenanceReference"):
            self.assertIn(f"'{field}'", text)
        for marker in ("curl_init", "GuzzleHttp", "AIDispatchService"):
            self.assertNotIn(marker, text)

    def test_purpose_grammar_and_portfolio_mapping_rules(self) -> None:
        text = read(SERVICE)
        self.assertIn("/^[a-z][a-z0-9_]{0,63}$/", text)
        self.assertIn("exactly one of the four CompletionCapability values", text)
        self.assertIn("Purpose ID must not equal a capability value", text)

    def test_completion_capability_portfolio_unchanged(self) -> None:
        text = read(COMPLETION_BASE)
        match = re.search(
            r"class CompletionCapability\(Enum\):(.*?)(?:\nclass |\Z)",
            text,
            flags=re.S,
        )
        self.assertIsNotNone(match)
        assert match is not None
        names = set(re.findall(r'^\s+([A-Z_]+) = "', match.group(1), flags=re.M))
        self.assertEqual(names, COMPLETION_PORTFOLIO)
        self.assertNotIn("COMMERCIAL_BRIEF", names)

    def test_invariant_registry_statuses_unchanged(self) -> None:
        text = read(INVARIANT_REGISTRY)
        self.assertRegex(text, r"\|\s*C20-INV-02\s*\|.*\|\s*ACTIVE\s*\|")
        self.assertRegex(text, r"\|\s*C20-INV-03\s*\|.*\|\s*ACTIVE\s*\|")
        for inv in range(4, 14):
            self.assertRegex(
                text,
                rf"\|\s*C20-INV-{inv:02d}\s*\|.*\|\s*DEFERRED\s*\|",
                msg=f"C20-INV-{inv:02d} must remain DEFERRED",
            )

    def test_connector_binding_shape_compatibility(self) -> None:
        """CRM fixture shape matches frozen connector ProviderBinding fields."""
        from chitu_connector.acquisition.providers.capabilities import Capability
        from chitu_connector.acquisition.providers.registry import (
            ProviderBinding,
            ProviderHealthState,
        )

        service_text = read(SERVICE)
        self.assertIn("'provider_id'", service_text)
        self.assertIn("'adapter_type'", service_text)
        self.assertIn("'credential_reference'", service_text)
        self.assertIn("'supported_capabilities'", service_text)
        self.assertIn("'allowed_purposes'", service_text)

        # Test-scoped fixture only — no CRM dispatch and no secret.
        binding = ProviderBinding(
            provider_id="test_provider",
            adapter_type="COMPLETION_BRIDGE",
            priority=10,
            enabled=True,
            credential_reference="cred:test-ref-001",
            supported_capabilities=frozenset({Capability.COMPLETION}),
            health_state=ProviderHealthState.HEALTHY,
            allowed_purposes=frozenset({"test_research_purpose"}),
        )
        self.assertEqual(binding.provider_id, "test_provider")
        self.assertEqual(binding.credential_reference, "cred:test-ref-001")
        self.assertIn("test_research_purpose", binding.allowed_purposes)
        self.assertNotIn("commercial_brief_generation", binding.allowed_purposes)

    def test_no_secret_in_i18n_or_layouts(self) -> None:
        blob = "\n".join(
            read(path) for path in (I18N_EN, I18N_ZH, LIST_LAYOUT, DETAIL_LAYOUT)
        )
        for secret in ("apiKey", "apiSecret", "accessToken", "privateKey"):
            self.assertNotIn(secret, blob)

    def test_detail_layout_excludes_secret_and_shows_policy_fields(self) -> None:
        detail = json.dumps(load_json(DETAIL_LAYOUT))
        for field in ("name", "providerId", "adapterType", "status", "allowedPurposes"):
            self.assertIn(field, detail)
        self.assertNotIn("credentialReference", detail)


if __name__ == "__main__":
    unittest.main()
