"""Safe projection of an unsaved C09 draft into existing Lead preparation fields."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, Protocol
from urllib.parse import urlparse

from chitu_connector.espocrm_sync.email_draft_generation import DraftEvidenceReference, EmailDraft
from chitu_connector.espocrm_sync.enrichment_gate import QualificationStatus


DRAFT_PREPARATION_CAMPAIGN = "C09 Draft Preparation"
_PROJECTABLE_FIELDS = frozenset({
    "peEmailStatus",
    "peEmailCampaignName",
    "peRecommendedApproach",
})


class LeadCampaignProjectionClient(Protocol):
    """Existing-Lead update operation; it intentionally has no create or send API."""

    def update_lead_campaign_projection(self, lead_id: str, fields: Mapping[str, Any]) -> Mapping[str, Any]: ...


class CampaignProjectionStatus(StrEnum):
    PROJECTED = "PROJECTED"
    SKIPPED = "SKIPPED"
    DENIED = "DENIED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class CampaignProjectionResult:
    status: CampaignProjectionStatus
    lead_id: str | None
    updated_fields: tuple[str, ...] = ()
    draft_generation_version: str | None = None
    evidence_reference_count: int = 0
    qualification_status: QualificationStatus | None = None
    reason_code: str | None = None


class CampaignProjectionAdapter:
    """Project draft-preparation metadata without storing content or acting on it."""

    def __init__(self, client: LeadCampaignProjectionClient) -> None:
        self.client = client

    def project(
        self,
        lead_id: str,
        email_draft: EmailDraft,
        campaign_name: str = DRAFT_PREPARATION_CAMPAIGN,
    ) -> CampaignProjectionResult:
        if not isinstance(lead_id, str) or not lead_id.strip():
            return CampaignProjectionResult(CampaignProjectionStatus.SKIPPED, None, reason_code="INVALID_LEAD_ID")
        fields, reason_code = _projection_fields(email_draft, campaign_name)
        if reason_code:
            return _skipped(lead_id, email_draft, reason_code)
        try:
            self.client.update_lead_campaign_projection(lead_id, fields)
        except PermissionError:
            return _result(CampaignProjectionStatus.DENIED, lead_id, email_draft, reason_code="CRM_PERMISSION_DENIED")
        except Exception:
            return _result(CampaignProjectionStatus.FAILED, lead_id, email_draft, reason_code="CRM_UPDATE_FAILED")
        return _result(CampaignProjectionStatus.PROJECTED, lead_id, email_draft, tuple(fields))


def _projection_fields(email_draft: Any, campaign_name: Any) -> tuple[dict[str, str], str | None]:
    if not isinstance(email_draft, EmailDraft):
        return {}, "MISSING_DRAFT"
    if (
        not isinstance(email_draft.subject, str)
        or not email_draft.subject.strip()
        or not isinstance(email_draft.body, str)
        or not email_draft.body.strip()
    ):
        return {}, "MISSING_DRAFT_CONTENT"
    if not isinstance(email_draft.generation_version, str) or not email_draft.generation_version.strip():
        return {}, "MISSING_DRAFT_VERSION"
    if not isinstance(email_draft.qualification_status, QualificationStatus):
        return {}, "INVALID_QUALIFICATION_STATE"
    if not _valid_evidence_references(email_draft):
        return {}, "INVALID_DRAFT_EVIDENCE"
    if not isinstance(campaign_name, str) or not campaign_name.strip() or len(campaign_name.strip()) > 255:
        return {}, "INVALID_CAMPAIGN_NAME"
    return {
        "peEmailStatus": "DRAFT_READY",
        "peEmailCampaignName": campaign_name.strip(),
        "peRecommendedApproach": _recommended_approach(email_draft.recommended_product),
    }, None


def _valid_evidence_references(email_draft: EmailDraft) -> bool:
    if not email_draft.evidence_references:
        return False
    for reference in email_draft.evidence_references:
        if (
            not isinstance(reference, DraftEvidenceReference)
            or not isinstance(reference.evidence_id, str)
            or not isinstance(reference.source_url, str)
        ):
            return False
        parsed = urlparse(reference.source_url)
        if not reference.evidence_id.strip() or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return False
    return True


def _recommended_approach(recommended_product: str | None) -> str:
    if isinstance(recommended_product, str) and recommended_product.strip():
        return f"Evidence-backed first touch for {recommended_product.strip()}."
    return "Evidence-backed first touch."


def _skipped(lead_id: str, email_draft: Any, reason_code: str) -> CampaignProjectionResult:
    return _result(CampaignProjectionStatus.SKIPPED, lead_id, email_draft, reason_code=reason_code)


def _result(
    status: CampaignProjectionStatus,
    lead_id: str,
    email_draft: Any,
    updated_fields: tuple[str, ...] = (),
    reason_code: str | None = None,
) -> CampaignProjectionResult:
    if isinstance(email_draft, EmailDraft):
        return CampaignProjectionResult(
            status=status,
            lead_id=lead_id,
            updated_fields=updated_fields,
            draft_generation_version=email_draft.generation_version,
            evidence_reference_count=len(email_draft.evidence_references),
            qualification_status=email_draft.qualification_status,
            reason_code=reason_code,
        )
    return CampaignProjectionResult(status=status, lead_id=lead_id, reason_code=reason_code)


def allowed_campaign_projection_fields() -> frozenset[str]:
    """Expose the exact existing-Lead field allowlist for transport and tests."""
    return _PROJECTABLE_FIELDS
