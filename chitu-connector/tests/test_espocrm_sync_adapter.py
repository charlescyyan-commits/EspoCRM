from __future__ import annotations

from datetime import datetime, timezone
from unittest import TestCase

from chitu_connector.espocrm_sync import (
    AuditStatus,
    EspoCRMSyncAdapter,
    EspoCRMSyncMapper,
    MockEspoCRMClient,
    MockSyncStatus,
    SyncContractPayload,
    SyncSource,
    evaluate_sync_gate,
    validate_sync_contract,
)
from chitu_connector.vendored.config.search_sources import SearchSource
from chitu_connector.vendored.contracts.website_research import EvidenceItem, ResearchFailureCode, WebsiteResearchResult
from chitu_connector.vendored.domain.models import Candidate, ProspectState


NOW = datetime(2026, 7, 10, tzinfo=timezone.utc)


def build_source(
    *,
    state: ProspectState = ProspectState.OUTREACH_READY,
    score_rules_version: str = "canonical-scoring-v4.0",
    evidence: tuple[EvidenceItem, ...] | None = None,
    official_brand_excluded: bool = False,
    failure_code: ResearchFailureCode | None = None,
) -> SyncSource:
    items = evidence if evidence is not None else (
        EvidenceItem("ev-country", "company_country", "Germany", "https://dealer.example/contact", "Dealer", "Registered in Germany", "visible_text", 0.9, NOW),
        EvidenceItem("ev-product", "product", "resin printer", "https://dealer.example/products", "Products", "Resin printer range", "visible_text", 0.9, NOW),
    )
    candidate = Candidate(
        id="candidate-1", job_id="job-1", company_name="Example Dealer", raw_url="https://dealer.example",
        canonical_domain="dealer.example", country="Germany", source=SearchSource.GOOGLE_SEARCH,
        source_url="https://search.example/result", raw_payload={}, current_state=state,
    )
    research = WebsiteResearchResult(
        candidate_id=candidate.id, website_url="https://dealer.example", final_url="https://dealer.example",
        website_accessible=failure_code is None, http_status=200 if failure_code is None else None,
        page_title="Example Dealer", meta_description="3D printer dealer", company_summary="Dealer",
        detected_brands=("Brand A",), detected_products=("resin printer",), customer_type_candidates=(),
        business_signals=("dealer",), contact_page_urls=(), public_emails=(), public_phones=(),
        evidence_items=items, visited_pages=("https://dealer.example",), technical_warnings=(),
        failure_code=failure_code, failure_message=None, researched_at=NOW, adapter_version="test-research-v1",
        payload_hash="p" * 64, company_country="Germany", company_country_code="DE",
        company_country_evidence_ids=("ev-country",), research_output_hash="r" * 64,
    )
    score = {
        "opportunity_score": 82.5, "score_tier": "A", "aggregate_confidence": 0.86,
        "evidence_coverage": 0.76, "rules_version": score_rules_version, "result_hash": "s" * 64,
        "best_first_product": "Resin Tank", "score_reasons": ("STRONG_PRODUCT_FIT",),
    }
    return SyncSource(
        candidate=candidate, research=research, score=score, engine_version="prospecting-engine-v1",
        cross_sell_path=("Filament Dryer",), official_brand_excluded=official_brand_excluded,
        official_brand_registry_version="1.0",
    )


def payload_for(source: SyncSource) -> SyncContractPayload:
    return EspoCRMSyncMapper().build(source, requested_at=NOW)


class ContractTests(TestCase):
    def test_valid_payload_passes_structural_validation(self) -> None:
        self.assertEqual(validate_sync_contract(payload_for(build_source()).to_dict()), ())

    def test_schema_validation_rejects_unknown_field(self) -> None:
        data = payload_for(build_source()).to_dict()
        data["raw_html"] = "forbidden"
        self.assertIn("UNKNOWN_FIELD:raw_html", validate_sync_contract(data))


class GateTests(TestCase):
    def test_outreach_ready_is_allowed(self) -> None:
        source = build_source()
        self.assertTrue(evaluate_sync_gate(source, payload_for(source)).accepted)

    def test_not_ready_is_rejected(self) -> None:
        source = build_source(state=ProspectState.SCORED)
        self.assertEqual(evaluate_sync_gate(source, payload_for(source)).reason_code, "NOT_OUTREACH_READY")

    def test_v3_score_is_rejected(self) -> None:
        source = build_source(score_rules_version="decision-engine-v3")
        self.assertEqual(evaluate_sync_gate(source, payload_for(source)).reason_code, "INVALID_SCORE_VERSION")

    def test_missing_evidence_is_rejected(self) -> None:
        source = build_source(evidence=())
        self.assertEqual(evaluate_sync_gate(source, payload_for(source)).reason_code, "MISSING_EVIDENCE")

    def test_official_brand_is_rejected(self) -> None:
        source = build_source(official_brand_excluded=True)
        self.assertEqual(evaluate_sync_gate(source, payload_for(source)).reason_code, "OFFICIAL_BRAND_EXCLUDED")

    def test_failed_technical_is_rejected(self) -> None:
        source = build_source(failure_code=ResearchFailureCode.READ_TIMEOUT)
        self.assertEqual(evaluate_sync_gate(source, payload_for(source)).reason_code, "FAILED_TECHNICAL")

    def test_rejected_business_is_rejected(self) -> None:
        source = build_source(state=ProspectState.REJECTED_BUSINESS)
        self.assertEqual(evaluate_sync_gate(source, payload_for(source)).reason_code, "REJECTED_BUSINESS")


class MapperTests(TestCase):
    def test_company_mapping_uses_direct_evidence_country(self) -> None:
        payload = payload_for(build_source())
        fields = EspoCRMSyncMapper.lead_fields(payload)
        self.assertEqual((fields["name"], fields["website"], fields["country"]), ("Example Dealer", "https://dealer.example", "DE"))

    def test_score_mapping_uses_v4_fields(self) -> None:
        fields = EspoCRMSyncMapper.lead_fields(payload_for(build_source()))
        self.assertEqual((fields["peOpportunityScoreV4"], fields["peScoreTier"], fields["peConfidence"], fields["peEvidenceCoverage"]), (82.5, "A", 0.86, 0.76))

    def test_evidence_reference_mapping_is_compact(self) -> None:
        references = EspoCRMSyncMapper.evidence_references(payload_for(build_source()))
        self.assertEqual(references[0], {"evidence_id": "ev-country", "claim_type": "company_country"})
        self.assertTrue(all(set(reference) == {"evidence_id", "claim_type"} for reference in references))

    def test_payload_excludes_raw_research_fields(self) -> None:
        data = payload_for(build_source()).to_dict()
        serialized = str(data)
        self.assertNotIn("raw_html", serialized)
        self.assertNotIn("crawler_logs", serialized)
        self.assertNotIn("cookies", serialized)


class IdempotencyTests(TestCase):
    def test_same_input_has_same_idempotency_key(self) -> None:
        first = payload_for(build_source()).to_dict()["sync"]["idempotency_key"]
        second = payload_for(build_source()).to_dict()["sync"]["idempotency_key"]
        self.assertEqual(first, second)

    def test_different_domain_has_different_idempotency_key(self) -> None:
        first = payload_for(build_source()).to_dict()["sync"]["idempotency_key"]
        source = build_source()
        source.candidate.canonical_domain = "other-dealer.example"
        second = payload_for(source).to_dict()["sync"]["idempotency_key"]
        self.assertNotEqual(first, second)


class MockClientTests(TestCase):
    def test_mock_success(self) -> None:
        client = MockEspoCRMClient()
        result = client.create_lead(payload_for(build_source()))
        self.assertEqual((result.status, result.lead_id), (MockSyncStatus.SUCCESS, "mock-lead-1"))

    def test_mock_duplicate(self) -> None:
        client = MockEspoCRMClient()
        payload = payload_for(build_source())
        client.create_lead(payload)
        self.assertEqual(client.create_lead(payload).status, MockSyncStatus.DUPLICATE)

    def test_mock_validation_failure(self) -> None:
        payload = payload_for(build_source())
        data = payload.to_dict()
        data["company"]["website"] = "not-a-url"
        invalid = SyncContractPayload(
            contract_version=data["contract_version"], identity=data["identity"], qualification=data["qualification"],
            company=data["company"], source=data["source"], research=data["research"], score=data["score"],
            recommendation=data["recommendation"], evidence=tuple(data["evidence"]), provenance=data["provenance"], sync=data["sync"],
        )
        self.assertEqual(MockEspoCRMClient().create_lead(invalid).status, MockSyncStatus.VALIDATION_ERROR)


class AdapterAuditTests(TestCase):
    def test_adapter_records_ready_and_synced(self) -> None:
        adapter = EspoCRMSyncAdapter()
        result = adapter.sync(build_source())
        self.assertEqual(result.status, AuditStatus.SYNCED)
        self.assertEqual(tuple(entry.status for entry in result.audit_entries), (AuditStatus.READY, AuditStatus.SYNCED))

    def test_adapter_rejection_does_not_call_mock_client(self) -> None:
        adapter = EspoCRMSyncAdapter()
        result = adapter.sync(build_source(state=ProspectState.SCORED))
        self.assertEqual(result.status, AuditStatus.REJECTED)
        self.assertEqual(adapter.client.mock_sync_history, [])
