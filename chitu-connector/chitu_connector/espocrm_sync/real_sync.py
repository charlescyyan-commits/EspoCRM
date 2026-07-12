"""One-shot synthetic local EspoCRM integration test workflow."""

from __future__ import annotations

from datetime import datetime, timezone

from chitu_connector.espocrm_sync.gate import evaluate_sync_gate
from chitu_connector.espocrm_sync.mapper import EspoCRMSyncMapper
from chitu_connector.espocrm_sync.models import SyncSource
from chitu_connector.espocrm_sync.real_client import LocalEspoCRMClient, RealSyncResult, RealSyncStatus, SYNTHETIC_LEAD_NAME
from chitu_connector.vendored.config.search_sources import SearchSource
from chitu_connector.vendored.contracts.website_research import EvidenceItem, WebsiteResearchResult
from chitu_connector.vendored.domain.models import Candidate, ProspectState


def build_synthetic_source() -> SyncSource:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0)
    candidate = Candidate(
        id="synthetic_test_dealer_v1", job_id="phase3a22b-local", company_name=SYNTHETIC_LEAD_NAME,
        raw_url="https://synthetic-dealer.example", canonical_domain="synthetic-dealer.example", country="Germany",
        source=SearchSource.CUSTOM_IMPORT, source_url="https://synthetic-dealer.example/discovery", raw_payload={},
        current_state=ProspectState.OUTREACH_READY,
    )
    evidence = EvidenceItem(
        "test-ev-001", "company_type", "Synthetic 3D dealer", "https://synthetic-dealer.example/about",
        "Synthetic test source", "Synthetic test evidence only.", "synthetic", 1.0, timestamp,
    )
    research = WebsiteResearchResult(
        candidate_id=candidate.id, website_url=candidate.raw_url, final_url=candidate.raw_url, website_accessible=True,
        http_status=200, page_title=SYNTHETIC_LEAD_NAME, meta_description="Synthetic test only", company_summary="Synthetic",
        detected_brands=(), detected_products=("Resin Tank",), customer_type_candidates=(), business_signals=("synthetic",),
        contact_page_urls=(), public_emails=(), public_phones=(), evidence_items=(evidence,), visited_pages=(candidate.raw_url,),
        technical_warnings=(), failure_code=None, failure_message=None, researched_at=timestamp, adapter_version="synthetic-test-v1",
        payload_hash="a" * 64, company_country="Germany", company_country_code="DE", company_country_evidence_ids=(evidence.evidence_id,),
        evidence_schema_version="1.1", research_output_hash="b" * 64,
    )
    score = {
        "opportunity_score": 80.0, "score_tier": "A", "aggregate_confidence": 1.0, "evidence_coverage": 0.75,
        "rules_version": "canonical-scoring-v4.0", "result_hash": "c" * 64, "best_first_product": "Resin Tank",
        "score_reasons": ("SYNTHETIC_TEST_ONLY",),
    }
    return SyncSource(
        candidate=candidate, research=research, score=score, engine_version="prospecting-engine-test",
        official_brand_excluded=False, official_brand_registry_version="1.0",
    )


def run_local_synthetic_sync() -> RealSyncResult:
    source = build_synthetic_source()
    mapper = EspoCRMSyncMapper()
    payload = mapper.build(source)
    gate = evaluate_sync_gate(source, payload)
    if not gate.accepted:
        raise RuntimeError(f"synthetic sync gate rejected: {gate.reason_code}")
    client = LocalEspoCRMClient.from_environment()
    client.authenticate()
    client.preflight()
    stale = client.find_synthetic_lead()
    if stale:
        client.rollback(str(stale["id"]))
        client.verify_rollback()
    result = client.sync_payload(payload)
    if result.status != RealSyncStatus.CREATED:
        raise RuntimeError("first synthetic sync did not create a Lead")
    try:
        client.verify(result, payload)
        duplicate = client.sync_payload(payload)
        if duplicate.status != RealSyncStatus.DUPLICATE or duplicate.lead_id != result.lead_id:
            raise RuntimeError("second synthetic sync did not return the existing Lead")
        return result
    finally:
        client.rollback(result.lead_id, result.evidence_ids)
        client.verify_rollback()
