"""Controlled, provider-neutral email-draft generation boundary.

The module creates draft data only.  It has no AI-provider, SMTP, campaign,
CRM, approval, or delivery dependency; a future provider can implement the
``EmailDraftGenerator`` protocol and return the same immutable contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

from chitu_connector.espocrm_sync.enrichment_gate import QualificationStatus
from chitu_connector.espocrm_sync.outreach_input_adapter import EvidenceBackedTalkingPoint, OutreachInput


GENERATION_VERSION = "c09-email-draft-boundary-v1"


@dataclass(frozen=True, slots=True)
class PersonalizationReference:
    """A direct business fact used by the draft, retained for auditability."""

    field: str
    value: str


@dataclass(frozen=True, slots=True)
class DraftEvidenceReference:
    """The source identity for a talking point retained by a draft."""

    evidence_id: str
    source_url: str


@dataclass(frozen=True, slots=True)
class EmailDraft:
    """Unsaved draft content with score, qualification, and evidence traceability."""

    subject: str
    body: str
    personalization_references: tuple[PersonalizationReference, ...]
    evidence_references: tuple[DraftEvidenceReference, ...]
    qualification_status: QualificationStatus
    qualification_reason: str
    score_tier: str | None
    recommended_product: str | None
    generation_version: str = GENERATION_VERSION


class EmailDraftGenerator(Protocol):
    """Provider injection seam; implementations only return a draft contract."""

    generation_version: str

    def generate(self, outreach_input: OutreachInput) -> EmailDraft: ...


class DeterministicEmailDraftGenerator:
    """Reference generator using only direct, source-backed OutreachInput facts."""

    generation_version = GENERATION_VERSION

    def generate(self, outreach_input: OutreachInput) -> EmailDraft:
        _validate_outreach_input(outreach_input)
        primary_point = outreach_input.talking_points[0]
        product = outreach_input.recommended_product
        subject = _subject(outreach_input.company_context.name, product)
        body = _body(outreach_input.company_context.name, primary_point.claim, product)
        return EmailDraft(
            subject=subject,
            body=body,
            personalization_references=_personalization_references(outreach_input),
            evidence_references=_evidence_references(outreach_input.talking_points),
            qualification_status=outreach_input.qualification_status,
            qualification_reason=outreach_input.qualification_reason,
            score_tier=outreach_input.score_tier,
            recommended_product=product,
        )


def _validate_outreach_input(value: object) -> None:
    if not isinstance(value, OutreachInput):
        raise TypeError("outreach_input must be an OutreachInput")
    if not value.company_context.name:
        raise ValueError("outreach_input requires company_context.name")
    if not value.talking_points:
        raise ValueError("outreach_input requires source-backed talking_points")
    for point in value.talking_points:
        if not _valid_talking_point(point):
            raise ValueError("outreach_input contains invalid evidence")


def _valid_talking_point(point: object) -> bool:
    if not isinstance(point, EvidenceBackedTalkingPoint):
        return False
    parsed = urlparse(point.source_url)
    return bool(
        point.evidence_id.strip()
        and point.claim.strip()
        and parsed.scheme in {"http", "https"}
        and parsed.netloc
    )


def _subject(company_name: str | None, product: str | None) -> str:
    assert company_name is not None  # validated above
    return f"{company_name}: {product}" if product else f"{company_name}: introduction"


def _body(company_name: str | None, claim: str, product: str | None) -> str:
    assert company_name is not None  # validated above
    lines = [f"Hello {company_name},", f"I noticed: {claim}"]
    if product:
        lines.append(f"The available product recommendation is {product}.")
    lines.append("Best regards,")
    return "\n\n".join(lines)


def _personalization_references(outreach_input: OutreachInput) -> tuple[PersonalizationReference, ...]:
    context = outreach_input.company_context
    values = (
        ("company.name", context.name),
        ("company.country", context.country),
        ("company.industry", context.industry),
        ("company.business_model", context.business_model),
        ("company.company_type", context.company_type),
        ("score.recommended_product", outreach_input.recommended_product),
    )
    return tuple(PersonalizationReference(field, value) for field, value in values if value is not None)


def _evidence_references(points: tuple[EvidenceBackedTalkingPoint, ...]) -> tuple[DraftEvidenceReference, ...]:
    references = {(point.evidence_id, point.source_url) for point in points}
    return tuple(DraftEvidenceReference(evidence_id, source_url) for evidence_id, source_url in sorted(references))
