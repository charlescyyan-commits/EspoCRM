"""Phase3C20 WP3 execution-governance integration verification.

The EspoPHP services are contract-tested in this repository.  This suite joins
their persisted contracts with the frozen, in-memory CapabilityRegistry using
only controlled fixture inputs.  It deliberately constructs no live provider
adapter and performs no network operation.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path

from chitu_connector.acquisition.providers.capabilities import Capability
from chitu_connector.acquisition.providers.registry import (
    AdapterRegistration,
    CapabilityRegistry,
    CapabilityResolutionRequest,
    ProviderBinding,
    ProviderHealthState,
)


ROOT = Path(__file__).resolve().parents[2]
AI_PLATFORM = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "AIPlatform"
INVARIANT_REGISTRY = ROOT / "docs" / "adr" / "C20_INVARIANT_REGISTRY.md"
WP3_DESIGN = ROOT / "docs" / "PHASE3C20_WP3_DETAILED_DESIGN_DECISIONS.md"
AI_JOB_DEF = AI_PLATFORM / "Resources" / "metadata" / "entityDefs" / "AIJob.json"
REQUEST_LOG_DEF = AI_PLATFORM / "Resources" / "metadata" / "entityDefs" / "AIRequestLog.json"
AI_JOB_SERVICE = AI_PLATFORM / "Services" / "AIJobService.php"
REQUEST_LOG_SERVICE = AI_PLATFORM / "Services" / "AIRequestLogService.php"
REQUEST_LOG_GUARD = AI_PLATFORM / "Hooks" / "AIRequestLog" / "AIRequestLogAppendOnlyGuard.php"
PROMPT_TEMPLATE_SERVICE = AI_PLATFORM / "Services" / "PromptTemplateService.php"
PROMPT_TEMPLATE_GUARD = AI_PLATFORM / "Hooks" / "PromptTemplate" / "PromptTemplateMutationGuard.php"

FORBIDDEN_EGRESS = (
    r"\bcurl(?:_[A-Za-z0-9_]+)?\b",
    r"\bGuzzle\b",
    r"\bHttpClient\b",
    r"\bfile_get_contents\b",
    r"\bstream_socket_client\b",
    r"\bfsockopen\b",
)
FORBIDDEN_BUSINESS_FIELDS = {
    "leadId",
    "opportunityId",
    "prospectId",
    "score",
    "qualification",
}
FORBIDDEN_SECRET_FIELDS = {"apiKey", "token", "password", "credential"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load(path: Path) -> dict[str, object]:
    return json.loads(read(path))


def controlled_resolution() -> tuple[CapabilityResolutionRequest, object]:
    """Resolve one CRM-authorized fixture binding without a provider call."""
    capability = Capability.COMPLETION
    binding = ProviderBinding(
        provider_id="controlled-fixture-provider",
        adapter_type="ControlledFixtureCompletion",
        priority=10,
        enabled=True,
        credential_reference="crm-ref-controlled-fixture",
        supported_capabilities=frozenset({capability}),
        health_state=ProviderHealthState.HEALTHY,
        allowed_purposes=frozenset({"draft_generation"}),
    )
    request = CapabilityResolutionRequest(
        capability=capability,
        purpose="draft_generation",
        allowed_provider_bindings=(binding,),
        credential_availability={"crm-ref-controlled-fixture": True},
        provider_health={"controlled-fixture-provider": ProviderHealthState.HEALTHY},
        policy_version="controlled-policy-v1",
        request_context={"trace_id": "controlled-wp3-integration"},
    )
    registry = CapabilityRegistry(
        (
            AdapterRegistration(
                provider_id="controlled-fixture-provider",
                adapter_type="ControlledFixtureCompletion",
                supported_capabilities=frozenset({capability}),
            ),
        )
    )

    return request, registry.resolve(request)


def evidence_fixture(
    *,
    ai_job_id: str,
    attempt_id: str,
    attempt_number: int,
    template_id: str,
    template_version: int,
    template_hash: str,
    provider: str,
) -> dict[str, object]:
    """Metadata-only fixture matching AIRequestLogService create input."""
    return {
        "name": f"{ai_job_id}-{attempt_id}",
        "aiJobId": ai_job_id,
        "attemptId": attempt_id,
        "attemptNumber": attempt_number,
        "capability": "COMPLETION",
        "purpose": "draft_generation",
        "provider": provider,
        "model": "controlled-fixture-model-v1",
        "promptTemplateId": template_id,
        "promptTemplateVersion": template_version,
        "promptTemplateHash": template_hash,
        "inputTokens": 7,
        "outputTokens": 11,
        "totalTokens": 18,
        "costAmount": 0.0,
        "costCurrency": "USD",
        "latencyMs": 0,
        "status": "SUCCEEDED",
        "errorClass": None,
        "failureCategory": None,
    }


def test_controlled_capability_resolution_is_governance_input_not_provider_execution() -> None:
    request, result = controlled_resolution()

    assert request.capability is Capability.COMPLETION
    assert request.purpose == "draft_generation"
    assert result.requested_capability is request.capability
    assert result.selected_provider_id == "controlled-fixture-provider"
    assert result.policy_version == "controlled-policy-v1"
    assert result.candidate_evaluations[0].eligible is True
    assert result.selected_credential_reference == "crm-ref-controlled-fixture"

    registry_source = read(Path(__import__("chitu_connector.acquisition.providers.registry", fromlist=["__file__"]).__file__))
    for pattern in FORBIDDEN_EGRESS:
        assert re.search(pattern, registry_source, re.I) is None


def test_dry_run_chain_accepts_controlled_resolution_and_metadata_only_evidence() -> None:
    _, resolution = controlled_resolution()
    template_hash = hashlib.sha256(b"template version one").hexdigest()
    ai_job = {
        "name": "controlled dry run",
        "capability": "COMPLETION",
        "purpose": "draft_generation",
        "executionMode": "DRY_RUN",
        "policyVersion": resolution.policy_version,
    }
    log = evidence_fixture(
        ai_job_id="ai-job-controlled-dry-run",
        attempt_id="attempt-controlled-1",
        attempt_number=1,
        template_id="prompt-template-controlled-v1",
        template_version=1,
        template_hash=template_hash,
        provider=resolution.selected_provider_id,
    )

    assert ai_job["executionMode"] == "DRY_RUN"
    assert ai_job["capability"] == resolution.requested_capability.name
    assert log["provider"] == resolution.selected_provider_id
    assert log["promptTemplateHash"] == template_hash
    assert "selected_credential_reference" not in log
    assert set(log).isdisjoint(FORBIDDEN_SECRET_FIELDS | FORBIDDEN_BUSINESS_FIELDS)

    job_service = read(AI_JOB_SERVICE)
    assert "public const EXECUTION_MODE_DRY_RUN = 'DRY_RUN'" in job_service
    assert re.search(r"->(?:send|dispatch|execute)\s*\(", job_service) is None


def test_one_aijob_can_emit_distinct_evidence_for_multiple_attempts() -> None:
    _, resolution = controlled_resolution()
    template_hash = hashlib.sha256(b"template version one").hexdigest()
    first = evidence_fixture(
        ai_job_id="ai-job-attempt-group",
        attempt_id="attempt-1",
        attempt_number=1,
        template_id="prompt-template-controlled-v1",
        template_version=1,
        template_hash=template_hash,
        provider=resolution.selected_provider_id,
    )
    second = evidence_fixture(
        ai_job_id="ai-job-attempt-group",
        attempt_id="attempt-2",
        attempt_number=2,
        template_id="prompt-template-controlled-v1",
        template_version=1,
        template_hash=template_hash,
        provider=resolution.selected_provider_id,
    )
    metadata = load(REQUEST_LOG_DEF)

    assert first["aiJobId"] == second["aiJobId"]
    assert (first["aiJobId"], first["attemptId"]) != (second["aiJobId"], second["attemptId"])
    assert (first["aiJobId"], first["attemptNumber"]) != (second["aiJobId"], second["attemptNumber"])
    assert metadata["links"]["aiJob"] == {"type": "belongsTo", "entity": "AIJob"}
    assert metadata["indexes"]["aiJobAttemptId"]["columns"] == ["aiJobId", "attemptId", "deleteId"]
    assert metadata["indexes"]["aiJobAttemptNumber"]["columns"] == ["aiJobId", "attemptNumber", "deleteId"]


def test_prompt_template_versioned_provenance_preserves_historical_log_reference() -> None:
    template_id = "prompt-template-controlled"
    version_one_hash = hashlib.sha256(b"template version one").hexdigest()
    version_two_hash = hashlib.sha256(b"template version two").hexdigest()
    historical_log = evidence_fixture(
        ai_job_id="ai-job-prompt-history",
        attempt_id="attempt-v1",
        attempt_number=1,
        template_id=template_id,
        template_version=1,
        template_hash=version_one_hash,
        provider="controlled-fixture-provider",
    )
    prompt_service = read(PROMPT_TEMPLATE_SERVICE)
    request_log_service = read(REQUEST_LOG_SERVICE)

    assert version_one_hash != version_two_hash
    assert historical_log["promptTemplateId"] == template_id
    assert historical_log["promptTemplateVersion"] == 1
    assert historical_log["promptTemplateHash"] == version_one_hash
    assert "public function createNewVersion(" in prompt_service
    assert "if ($version <= $currentVersion)" in prompt_service
    assert "assertPromptTemplateProvenance" in request_log_service
    assert "$this->promptTemplateService->markReferenced($template);" in request_log_service
    assert "templateBody" not in request_log_service


def test_append_only_evidence_rejects_update_and_delete_after_create() -> None:
    guard = read(REQUEST_LOG_GUARD)
    app_acl = load(AI_PLATFORM / "Resources" / "metadata" / "app" / "acl.json")

    assert "AIRequestLog creation must use AIRequestLogService." in guard
    assert "AIRequestLog is append-only and cannot be modified." in guard
    assert "AIRequestLog is append-only and cannot be deleted." in guard
    assert app_acl["adminMandatory"]["scopeLevel"]["AIRequestLog"] == {
        "create": "yes",
        "read": "all",
        "edit": "no",
        "delete": "no",
    }


def test_aijob_state_paths_are_limited_to_the_frozen_transition_matrix() -> None:
    service = read(AI_JOB_SERVICE)

    assert "self::STATUS_QUEUED => [self::STATUS_RUNNING, self::STATUS_CANCELLED]" in service
    assert "self::STATUS_RUNNING => [" in service
    assert "self::STATUS_SUCCEEDED," in service
    assert "self::STATUS_FAILED," in service
    assert "self::STATUS_FAILED => [self::STATUS_QUEUED]" in service
    assert "self::STATUS_SUCCEEDED => []" in service
    assert "self::STATUS_CANCELLED => []" in service


def test_job_has_no_provider_authority_and_evidence_has_no_business_or_secret_ownership() -> None:
    job_metadata = load(AI_JOB_DEF)
    log_metadata = load(REQUEST_LOG_DEF)
    job_source = read(AI_JOB_SERVICE)
    log_source = read(REQUEST_LOG_SERVICE)

    assert {"provider", "providerRoute", "providerPolicy", "adapter", "adapterType"}.isdisjoint(job_metadata["fields"])
    assert {"provider", "model"}.issubset(log_metadata["fields"])
    assert FORBIDDEN_BUSINESS_FIELDS.isdisjoint(job_metadata["fields"])
    assert FORBIDDEN_BUSINESS_FIELDS.isdisjoint(log_metadata["fields"])
    assert FORBIDDEN_SECRET_FIELDS.isdisjoint(job_metadata["fields"])
    assert FORBIDDEN_SECRET_FIELDS.isdisjoint(log_metadata["fields"])
    for source in (job_source, log_source):
        for pattern in FORBIDDEN_EGRESS:
            assert re.search(pattern, source, re.I) is None


def test_wp3_invariant_evidence_is_present_without_changing_invariant_registry_status() -> None:
    invariant_registry = read(INVARIANT_REGISTRY)
    design = read(WP3_DESIGN)
    job_guard = read(AI_PLATFORM / "Hooks" / "AIJob" / "AIJobStatusMutationGuard.php")
    request_guard = read(REQUEST_LOG_GUARD)

    for invariant in ("C20-INV-05", "C20-INV-06", "C20-INV-07", "C20-INV-08", "C20-INV-09", "C20-INV-14"):
        assert invariant in invariant_registry
    assert "WP3 implementation activates and verifies:" in design
    assert "AIJob lifecycle fields may only be written by AIJobService." in job_guard
    assert "AIRequestLog is append-only and cannot be modified." in request_guard
    assert "AIRequestLog is append-only and cannot be deleted." in request_guard
    assert "Referenced PromptTemplate field {$field} is immutable" in read(PROMPT_TEMPLATE_SERVICE)
    assert "canonical_score" not in "\n".join(read(path) for path in (AI_JOB_DEF, REQUEST_LOG_DEF, AI_JOB_SERVICE, REQUEST_LOG_SERVICE))


def test_controlled_resolution_trace_is_safe_fixture_metadata() -> None:
    request, result = controlled_resolution()
    trace = asdict(result)

    assert trace["requested_capability"] is Capability.COMPLETION
    assert trace["purpose"] == request.purpose
    assert trace["selected_provider_id"] == "controlled-fixture-provider"
    assert trace["candidate_evaluations"][0]["credential_available"] is True
    assert "api_key" not in trace
    assert "password" not in trace
    assert "token" not in trace
