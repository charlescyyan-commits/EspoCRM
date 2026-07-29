"""Phase3C22 WP2 provider governance boundary contracts."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROSPECTING = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "Prospecting"
)
BOUNDARY = PROSPECTING / "ProviderBoundary"
AI_PLATFORM = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "AIPlatform"
)
CREDENTIAL_DEF = (
    AI_PLATFORM
    / "Resources"
    / "metadata"
    / "entityDefs"
    / "ProviderCredential.json"
)
CREDENTIAL_ACL = (
    AI_PLATFORM
    / "Resources"
    / "metadata"
    / "entityAcl"
    / "ProviderCredential.json"
)

BOUNDARY_FILES = {
    "ProviderTypeRegistry.php",
    "ProviderCapabilityDeclaration.php",
    "CredentialReference.php",
    "ProviderExecutionRequest.php",
    "ProviderResultEnvelope.php",
    "ProviderContract.php",
    "ConnectorBoundary.php",
    "ProviderAdapterSkeleton.php",
}
PROVIDER_TYPES = {
    "SEARCH",
    "ENRICHMENT",
    "AI_RESEARCH",
    "OUTREACH",
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
SECRET_IDENTIFIERS = {
    "apiKey",
    "apiSecret",
    "accessToken",
    "refreshToken",
    "password",
    "secret",
    "secretValue",
    "tokenValue",
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
    r"->\s*(?:request|post|send)\s*\(",
    r"\b(?:requests|urllib3|httpx|aiohttp)\b",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def boundary_sources() -> dict[str, str]:
    return {
        path.name: read(path)
        for path in sorted(BOUNDARY.glob("*.php"))
    }


def load_json(path: Path) -> dict:
    return json.loads(read(path))


def test_provider_contract_and_envelopes_exist() -> None:
    assert BOUNDARY.is_dir()
    assert {path.name for path in BOUNDARY.glob("*.php")} == BOUNDARY_FILES

    contract = read(BOUNDARY / "ProviderContract.php")
    request = read(BOUNDARY / "ProviderExecutionRequest.php")
    result = read(BOUNDARY / "ProviderResultEnvelope.php")

    assert "interface ProviderContract" in contract
    assert "public function providerType(): string;" in contract
    assert (
        "public function capabilities(): ProviderCapabilityDeclaration;"
        in contract
    )
    assert "final class ProviderExecutionRequest" in request
    assert "final class ProviderResultEnvelope" in result
    for reference in (
        "requestId",
        "providerType",
        "credentialReference",
        "authorizationReference",
        "auditReference",
        "policyReference",
        "inputReference",
    ):
        assert reference in request
    assert "resultReference" in result
    assert "failureCategory" in result


def test_provider_categories_are_closed_and_provider_neutral() -> None:
    registry = read(BOUNDARY / "ProviderTypeRegistry.php")
    constants = set(
        re.findall(
            r"public const ([A-Z_]+) = '([A-Z_]+)';",
            registry,
        )
    )

    assert constants == {(provider_type, provider_type) for provider_type in PROVIDER_TYPES}
    assert "private const TYPES" in registry
    assert "assertAllowed" in registry
    assert "in_array($providerType, self::TYPES, true)" in registry

    capability = read(BOUNDARY / "ProviderCapabilityDeclaration.php")
    assert "ProviderTypeRegistry::assertAllowed" in capability
    assert "ProviderTypeRegistry::all()" in capability


def test_no_vendor_ownership_leaks_into_boundary() -> None:
    for file_name, source in boundary_sources().items():
        lowered = source.casefold()
        for vendor_name in VENDOR_NAMES:
            assert vendor_name not in lowered, f"{file_name}: {vendor_name}"
        for vendor_field in ("providerKey", "providerName", "vendorType", "vendorName"):
            assert vendor_field not in source, f"{file_name}: {vendor_field}"


def test_credential_reference_reuses_c20_without_secret_storage() -> None:
    credential = load_json(CREDENTIAL_DEF)
    fields = credential["fields"]
    assert set(fields) == {
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
    assert SECRET_IDENTIFIERS.isdisjoint(fields)
    assert credential["links"] == {
        "ownerUser": {"type": "belongsTo", "entity": "User"}
    }
    assert load_json(CREDENTIAL_ACL) == {
        "fields": {"credentialReference": {"internal": True}}
    }

    reference = read(BOUNDARY / "CredentialReference.php")
    assert "private string $referenceId" in reference
    assert "private string $ownerUserId" in reference
    assert "private ProviderCapabilityDeclaration $capabilities" in reference
    for identifier in SECRET_IDENTIFIERS:
        assert not re.search(
            rf"\${re.escape(identifier)}\b",
            reference,
            flags=re.IGNORECASE,
        )

    assert not any(
        path.name == "ProviderCredential.php"
        for path in (PROSPECTING / "Entities").glob("*.php")
    )
    assert not (BOUNDARY / "ProviderCredential.php").exists()


def test_connector_boundary_is_interface_and_adapter_is_abstract_only() -> None:
    connector = read(BOUNDARY / "ConnectorBoundary.php")
    adapter = read(BOUNDARY / "ProviderAdapterSkeleton.php")

    assert "interface ConnectorBoundary" in connector
    assert (
        "ProviderExecutionRequest $request"
        in connector
        and "ProviderResultEnvelope;" in connector
    )
    assert "abstract class ProviderAdapterSkeleton" in adapter
    assert "ProviderContract," in adapter
    assert "ConnectorBoundary" in adapter
    assert re.search(
        r"abstract public function execute\s*\("
        r"\s*ProviderExecutionRequest \$request\s*"
        r"\): ProviderResultEnvelope;",
        adapter,
    )
    assert "new ProviderResultEnvelope" not in adapter


def test_provider_boundary_has_no_egress_or_sdk_loading() -> None:
    for file_name, source in boundary_sources().items():
        for pattern in EGRESS_PATTERNS:
            assert not re.search(
                pattern,
                source,
                flags=re.IGNORECASE,
            ), f"{file_name}: {pattern}"

    imports = "\n".join(boundary_sources().values())
    assert "use InvalidArgumentException;" in imports
    assert not re.search(r"^\s*(?:use|require|include).*(?:Sdk|Client)", imports, re.MULTILINE)


def test_c20_d3_ownership_boundary_is_preserved() -> None:
    sources = "\n".join(boundary_sources().values())

    # CRM owns references and governance context.
    for governance_reference in (
        "CredentialReference",
        "authorizationReference",
        "auditReference",
        "policyReference",
    ):
        assert governance_reference in sources

    # Connector execution is represented by a port, never a concrete CRM service.
    assert "interface ConnectorBoundary" in sources
    assert "abstract class ProviderAdapterSkeleton" in sources
    assert "class ProviderAdapter " not in sources
    assert "EntityManager" not in sources
    assert "saveEntity" not in sources
    assert "getEntity(" not in sources


def test_c21_intelligence_records_are_outside_provider_write_boundary() -> None:
    sources = "\n".join(boundary_sources().values())
    for entity_type in (
        "ResearchEvidence",
        "AIQualificationInsight",
        "HumanFeedback",
    ):
        assert entity_type not in sources
    for mutation in ("create", "update", "delete", "persist"):
        assert not re.search(
            rf"\b{mutation}{'(?:Entity|Record)' if mutation == 'create' else ''}\b",
            sources,
            flags=re.IGNORECASE,
        )


def test_wp2_does_not_create_c22_provider_runtime_or_automation() -> None:
    sources = "\n".join(boundary_sources().values())
    for forbidden_surface in (
        "OutreachExecution",
        "ReplyDetection",
        "AutomationLoop",
        "AutomationRule",
        "Worker",
        "Queue",
        "Scheduler",
    ):
        assert forbidden_surface not in sources

    for forbidden_directory in (
        BOUNDARY / "Api",
        BOUNDARY / "Controllers",
        BOUNDARY / "Jobs",
        BOUNDARY / "Hooks",
    ):
        assert not forbidden_directory.exists()
