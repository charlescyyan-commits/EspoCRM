"""Typed contracts for the three-layer business qualification system.

This is NOT a garbage filter. It is an opportunity discovery system:

  Layer 1 — Identity Classification:  What IS this entity?
  Layer 2 — Business Qualification:   Is it worth developing NOW?
  Layer 3 — CRM Visibility:           Does it enter CRM?

Key principles (V2):
  - MANUFACTURER != EXCLUDED — must evaluate product fit
  - No entity type triggers automatic deletion
  - Identity is preserved even when qualification is EXCLUDED
  - Industry tags survive for future re-evaluation
  - Qualification Gate sits BEFORE scoring
  - Partner Manufacturer scoring uses PARTNER_FIT_SCORE, not Dealer Ranking
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


# ═══════════════════════════════════════════════════════════════════════
# Layer 1: Identity Classification — What IS this entity?
# ═══════════════════════════════════════════════════════════════════════

class EntityType(StrEnum):
    """Identity Classification — descriptive, not judgmental.

    No entity type triggers automatic exclusion. Every identity is
    preserved with tags even if current-phase qualification is LOW.
    """

    TARGET_DEALER = "TARGET_DEALER"
    PARTNER_MANUFACTURER = "PARTNER_MANUFACTURER"
    SERVICE_PROVIDER = "SERVICE_PROVIDER"
    INDUSTRIAL_AM_MANUFACTURER = "INDUSTRIAL_AM_MANUFACTURER"
    DIRECTORY_PLATFORM = "DIRECTORY_PLATFORM"
    MARKETPLACE = "MARKETPLACE"
    LOW_RELEVANCE_BUSINESS = "LOW_RELEVANCE_BUSINESS"
    UNKNOWN_IDENTITY = "UNKNOWN_IDENTITY"


class BusinessRole(StrEnum):
    """Specific business role within an entity type."""

    MULTI_BRAND_RETAILER = "MULTI_BRAND_RETAILER"
    MULTI_BRAND_DISTRIBUTOR = "MULTI_BRAND_DISTRIBUTOR"
    SINGLE_BRAND_RETAILER = "SINGLE_BRAND_RETAILER"
    PARTNER_ELIGIBLE_BRAND_OWNER = "PARTNER_ELIGIBLE_BRAND_OWNER"
    PRINT_SERVICE_PROVIDER = "PRINT_SERVICE_PROVIDER"
    CNC_SERVICE_PROVIDER = "CNC_SERVICE_PROVIDER"
    CONTRACT_MANUFACTURER = "CONTRACT_MANUFACTURER"
    WORKSHOP = "WORKSHOP"
    HOBBY_STORE = "HOBBY_STORE"
    OTHER = "OTHER"


# ═══════════════════════════════════════════════════════════════════════
# Layer 2: Business Qualification — Is it worth developing NOW?
# ═══════════════════════════════════════════════════════════════════════

class BusinessQualification(StrEnum):
    """Business Qualification — current-phase development decision.

    This is about NOW, not forever. An INDUSTRY_INTELLIGENCE entity
    today could become a QUALIFIED_SALES_TARGET tomorrow if product
    lines expand.
    """

    QUALIFIED_SALES_TARGET = "QUALIFIED_SALES_TARGET"
    PARTNER_CANDIDATE = "PARTNER_CANDIDATE"
    INDUSTRY_INTELLIGENCE = "INDUSTRY_INTELLIGENCE"
    RESEARCH_LATER = "RESEARCH_LATER"
    LOW_PRIORITY = "LOW_PRIORITY"
    EXCLUDED = "EXCLUDED"


class BusinessFit(StrEnum):
    """Product/solution fit assessment for current phase."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW_FOR_CURRENT_PHASE = "LOW_FOR_CURRENT_PHASE"
    NO_FIT = "NO_FIT"
    NEEDS_EVALUATION = "NEEDS_EVALUATION"


# ═══════════════════════════════════════════════════════════════════════
# Layer 3: CRM Visibility
# ═══════════════════════════════════════════════════════════════════════

class CrmVisibility(StrEnum):
    """CRM Visibility — independent of identity and qualification.

    PARTNER_MANUFACTURER can be CRM:YES even though it doesn't enter
    dealer scoring. INDUSTRIAL_AM_MANUFACTURER can be CRM:NO but
    still preserved in industry intelligence.
    """

    YES = "YES"
    NO = "NO"


# ═══════════════════════════════════════════════════════════════════════
# Evidence & Routing
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class EvidenceRequirement:
    """Specific evidence needed to confirm an identity or qualification."""

    requirement_id: str
    description: str
    satisfied: bool = False
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "description": self.description,
            "satisfied": self.satisfied,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True, slots=True)
class RoutingInstruction:
    """What pipelines this candidate can/cannot enter.

    Separate from qualification — an entity can be CRM:YES on a
    partnership track without entering dealer scoring.
    """

    allow_dealer_scoring: bool = False
    allow_partner_scoring: bool = False
    allow_enrichment: bool = False
    allow_outreach: bool = False
    allow_partnership_evaluation: bool = False
    require_manual_review: bool = True
    score_type: str | None = None  # "DEALER_OPPORTUNITY" | "PARTNER_FIT_SCORE" | None
    retention: str = "audit_only"

    def to_dict(self) -> dict[str, Any]:
        return {
            "allow_dealer_scoring": self.allow_dealer_scoring,
            "allow_partner_scoring": self.allow_partner_scoring,
            "allow_enrichment": self.allow_enrichment,
            "allow_outreach": self.allow_outreach,
            "allow_partnership_evaluation": self.allow_partnership_evaluation,
            "require_manual_review": self.require_manual_review,
            "score_type": self.score_type,
            "retention": self.retention,
        }


# ── Routing presets ──────────────────────────────────────────────────

def _dealer() -> RoutingInstruction:
    return RoutingInstruction(
        allow_dealer_scoring=True, allow_partner_scoring=False,
        allow_enrichment=True, allow_outreach=True,
        allow_partnership_evaluation=False, require_manual_review=True,
        score_type="DEALER_OPPORTUNITY", retention="full_pipeline",
    )


def _partner() -> RoutingInstruction:
    return RoutingInstruction(
        allow_dealer_scoring=False, allow_partner_scoring=True,
        allow_enrichment=False, allow_outreach=False,
        allow_partnership_evaluation=True, require_manual_review=True,
        score_type="PARTNER_FIT_SCORE", retention="partnership_track",
    )


def _intelligence() -> RoutingInstruction:
    return RoutingInstruction(
        allow_dealer_scoring=False, allow_partner_scoring=False,
        allow_enrichment=False, allow_outreach=False,
        allow_partnership_evaluation=False, require_manual_review=False,
        score_type=None, retention="industry_intelligence",
    )


def _excluded() -> RoutingInstruction:
    return RoutingInstruction(
        allow_dealer_scoring=False, allow_partner_scoring=False,
        allow_enrichment=False, allow_outreach=False,
        allow_partnership_evaluation=False, require_manual_review=False,
        score_type=None, retention="audit_only",
    )


ROUTING_DEALER = _dealer()
ROUTING_PARTNERSHIP = _partner()
ROUTING_INTELLIGENCE = _intelligence()
ROUTING_EXCLUDED = _excluded()


# ═══════════════════════════════════════════════════════════════════════
# Main Result Type
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class BusinessQualificationResult:
    """Three-layer business qualification output for one candidate.

    Layer 1 — Identity:    entity_type, business_role, industry_tag, technology_tag
    Layer 2 — Qualification: qualification, business_fit, partner_eligible,
                             sales_candidate, industry_intelligence
    Layer 3 — CRM:         crm_visibility
    """

    candidate_id: str
    canonical_domain: str

    # ── Layer 1: Identity Classification ──────────────────────────
    entity_type: EntityType
    business_role: str | None = None
    industry_tag: str | None = None
    technology_tag: str | None = None
    business_segment: str | None = None

    # ── Layer 2: Business Qualification ───────────────────────────
    qualification: BusinessQualification = BusinessQualification.EXCLUDED
    business_fit: str | None = None
    partner_eligible: bool = False
    sales_candidate: bool = False
    industry_intelligence: bool = False

    # ── Layer 3: CRM Visibility ───────────────────────────────────
    crm_visibility: CrmVisibility = CrmVisibility.NO

    # ── Supporting ────────────────────────────────────────────────
    routing: RoutingInstruction = ROUTING_EXCLUDED
    evidence_requirements: tuple[EvidenceRequirement, ...] = ()
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    matched_benchmark_domain: str | None = None
    rule_version: str = "business-qualification-v2"

    # ── Convenience properties ────────────────────────────────────

    @property
    def is_sales_target(self) -> bool:
        return self.qualification == BusinessQualification.QUALIFIED_SALES_TARGET

    @property
    def is_partner_candidate(self) -> bool:
        return self.qualification == BusinessQualification.PARTNER_CANDIDATE

    @property
    def enters_crm(self) -> bool:
        return self.crm_visibility == CrmVisibility.YES

    @property
    def enters_scoring(self) -> bool:
        return self.routing.allow_dealer_scoring or self.routing.allow_partner_scoring

    @property
    def is_excluded(self) -> bool:
        return self.qualification == BusinessQualification.EXCLUDED

    @property
    def needs_evidence(self) -> bool:
        return any(not req.satisfied for req in self.evidence_requirements)

    @property
    def all_evidence_satisfied(self) -> bool:
        return all(req.satisfied for req in self.evidence_requirements)

    # ── Serialization ─────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "canonical_domain": self.canonical_domain,
            # Layer 1
            "entity_type": self.entity_type.value,
            "business_role": self.business_role,
            "industry_tag": self.industry_tag,
            "technology_tag": self.technology_tag,
            "business_segment": self.business_segment,
            # Layer 2
            "qualification": self.qualification.value,
            "business_fit": self.business_fit,
            "partner_eligible": self.partner_eligible,
            "sales_candidate": self.sales_candidate,
            "industry_intelligence": self.industry_intelligence,
            # Layer 3
            "crm_visibility": self.crm_visibility.value,
            # Supporting
            "routing": self.routing.to_dict(),
            "evidence_requirements": [req.to_dict() for req in self.evidence_requirements],
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "matched_benchmark_domain": self.matched_benchmark_domain,
            "rule_version": self.rule_version,
            # Computed
            "is_sales_target": self.is_sales_target,
            "is_partner_candidate": self.is_partner_candidate,
            "enters_crm": self.enters_crm,
            "enters_scoring": self.enters_scoring,
            "is_excluded": self.is_excluded,
            "needs_evidence": self.needs_evidence,
        }
