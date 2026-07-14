"""Maps existing Engine output into the immutable V1 sync contract."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from chitu_connector.espocrm_sync.contract import CONTRACT_VERSION, SyncContractPayload
from chitu_connector.espocrm_sync.idempotency import evidence_snapshot_hash, idempotency_key, payload_hash, record_identity_key
from chitu_connector.espocrm_sync.models import SyncSource


_SOURCE_CHANNELS = {
    "GOOGLE_SEARCH": "WEB_SEARCH",
    "GOOGLE_MAPS": "WEB_SEARCH",
    "INDUSTRY_DIRECTORY": "WEB_SEARCH",
    "CUSTOM_IMPORT": "CONTROLLED_MANUAL_INPUT",
}


class EspoCRMSyncMapper:
    def build(self, source: SyncSource, requested_at: datetime | None = None) -> SyncContractPayload:
        domain = (source.candidate.canonical_domain or "").lower().removeprefix("www.")
        score = dict(source.score)
        evidence = [self._map_evidence(item, source.research.evidence_schema_version) for item in source.research.evidence_items]
        snapshot_hash = source.research.research_output_hash
        if len(snapshot_hash) < 32:
            snapshot_hash = evidence_snapshot_hash(evidence)
        source_value = source.candidate.source.value if hasattr(source.candidate.source, "value") else str(source.candidate.source)
        timestamp = (requested_at or datetime.now(timezone.utc).replace(microsecond=0)).isoformat()
        payload = SyncContractPayload(
            contract_version=CONTRACT_VERSION,
            identity={
                "candidate_id": source.candidate.id,
                "canonical_domain": domain,
                "record_identity_key": record_identity_key(domain),
            },
            qualification={
                "status": source.effective_qualification_status,
                "customer_type": source.effective_customer_type,
            },
            company={
                "name": source.candidate.company_name,
                "website": source.research.final_url or source.candidate.raw_url,
                "country_code": self._country_code(source),
            },
            source={
                "channel": _SOURCE_CHANNELS.get(source_value, "APPROVED_IMPORT"),
                "source_url": source.candidate.source_url or None,
            },
            research={
                "status": "COMPLETE" if source.research.failure_code is None and source.research.website_accessible else "TECHNICAL_FAILURE",
                "website_accessible": source.research.website_accessible,
                "failure_code": source.research.failure_code.value if source.research.failure_code else None,
            },
            score={
                "value": score.get("opportunity_score", score.get("normalized_score")),
                "score_tier": score.get("score_tier"),
                "aggregate_confidence": score.get("aggregate_confidence"),
                "evidence_coverage": score.get("evidence_coverage"),
                "rules_version": score.get("rules_version"),
                "result_hash": score.get("result_hash"),
            },
            recommendation={
                "best_first_product": score.get("best_first_product"),
                "cross_sell_path": list(source.cross_sell_path),
                "reason_codes": list(score.get("score_reasons", ())),
            },
            evidence=tuple(evidence),
            provenance={
                "engine_version": source.engine_version,
                "evidence_schema_version": source.research.evidence_schema_version,
                "evidence_snapshot_hash": snapshot_hash,
                "official_brand_excluded": source.official_brand_excluded,
                "official_brand_registry_version": source.official_brand_registry_version,
            },
            sync={
                "idempotency_key": idempotency_key(domain, source.engine_version, str(score.get("rules_version", ""))),
                "payload_hash": "",
                "requested_at": timestamp,
            },
        )
        data = payload.to_dict()
        data["sync"]["payload_hash"] = payload_hash(data)
        return SyncContractPayload(
            contract_version=data["contract_version"], identity=data["identity"], qualification=data["qualification"],
            company=data["company"], source=data["source"], research=data["research"], score=data["score"],
            recommendation=data["recommendation"], evidence=tuple(data["evidence"]), provenance=data["provenance"], sync=data["sync"],
        )

    @staticmethod
    def lead_fields(payload: SyncContractPayload) -> dict[str, Any]:
        data = payload.to_dict()
        return {
            "name": data["company"]["name"], "website": data["company"]["website"],
            "country": data["company"]["country_code"], "leadSource": data["source"]["channel"],
            "peCanonicalDomain": data["identity"]["canonical_domain"],
            "peQualificationStatus": data["qualification"]["status"],
            "peResearchStatus": _map_research_status(data["research"]["status"]),
            "peSyncStatus": "SYNCED",
            "peSourceSystem": "Chitu Intelligence",
            "peCandidateId": data["identity"]["candidate_id"],
            "peLastSyncAt": _espo_datetime(data["sync"]["requested_at"]),
            "peResearchSummary": _research_summary(data),
            "peKeyEvidence": _key_evidence(data),
            "peRecommendedApproach": _recommended_approach(data),
            "addressCountry": data["company"]["country_code"],
            "peCustomerType": data["qualification"]["customer_type"], "peOpportunityScoreV4": data["score"]["value"],
            "peScoreTier": data["score"]["score_tier"], "peConfidence": data["score"]["aggregate_confidence"],
            "peEvidenceCoverage": data["score"]["evidence_coverage"], "peBestFirstProduct": data["recommendation"]["best_first_product"],
            "peCrossSellPath": data["recommendation"]["cross_sell_path"], "peEngineVersion": data["provenance"]["engine_version"],
            "peScoreRulesVersion": data["score"]["rules_version"], "peEvidenceSchemaVersion": data["provenance"]["evidence_schema_version"],
            "peRegistryVersion": data["provenance"]["official_brand_registry_version"],
            "peEvidenceSnapshotHash": data["provenance"]["evidence_snapshot_hash"],
        }

    @staticmethod
    def evidence_references(payload: SyncContractPayload) -> tuple[dict[str, str], ...]:
        return tuple(
            {"evidence_id": str(item["evidence_id"]), "claim_type": str(item["claim_type"])}
            for item in payload.to_dict()["evidence"]
        )

    @staticmethod
    def _country_code(source: SyncSource) -> str | None:
        research = source.research
        if research.company_country_evidence_ids and not research.company_country_inference and research.company_country_code:
            return research.company_country_code.upper()
        return None

    @staticmethod
    def _map_evidence(item: Any, schema_version: str) -> dict[str, Any]:
        return {
            "evidence_id": item.evidence_id,
            "claim_type": item.claim_type,
            "evidence_type": item.evidence_type,
            "claim": item.claim,
            "source_url": item.source_url,
            "evidence_text": item.evidence_text,
            "confidence": item.confidence,
            "captured_at": item.captured_at.isoformat(),
            "schema_version": schema_version,
        }


def _map_research_status(status: str | None) -> str:
    if status == "COMPLETE":
        return "COMPLETED"
    if status in {"NONE", "RESEARCHING", "COMPLETED", "FAILED"}:
        return str(status)
    return "FAILED" if status else "NONE"


def _espo_datetime(value: str | None) -> str | None:
    if not value:
        return None
    normalized = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).strftime("%Y-%m-%d %H:%M:%S")


def _research_summary(data: dict[str, Any]) -> str:
    company = data["company"]["name"]
    product = data["recommendation"].get("best_first_product") or "N/A"
    tier = data["score"].get("score_tier") or "?"
    score = data["score"].get("value")
    return f"{company}: tier {tier}, score {score}. Recommended first product: {product}."


def _key_evidence(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for item in data.get("evidence", ())[:5]:
        claim = item.get("claim") or ""
        claim_type = item.get("claim_type") or ""
        lines.append(f"- [{claim_type}] {claim}")
    return "\n".join(lines)


def _recommended_approach(data: dict[str, Any]) -> str:
    product = data["recommendation"].get("best_first_product")
    if not product:
        return "Review research evidence, then choose a product-aligned first touch."
    return (
        f"Open with {product} relevance based on public site evidence. "
        "Keep the ask reply-oriented; do not push a meeting in the first email."
    )
