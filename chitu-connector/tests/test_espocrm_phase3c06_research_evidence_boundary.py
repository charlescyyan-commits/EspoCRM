"""Phase3C06 offline fixtures: ResearchEvidence / enrichment boundary.

Protects the frozen Engine → sync-contract → ResearchEvidence mapping path.
Uses the same inline fixture pattern as ``test_espocrm_sync_adapter.py``
(no second fixture system). No production code is modified.
"""

from __future__ import annotations

import ast
import inspect
from datetime import datetime, timezone
from pathlib import Path
from unittest import TestCase

from chitu_connector.acquisition.website_research import WebsiteResearchPipelineResult
from chitu_connector.espocrm_sync import (
    AuditStatus,
    EspoCRMSyncAdapter,
    EspoCRMSyncMapper,
    MockEspoCRMClient,
    MockSyncStatus,
    SyncContractPayload,
    evaluate_sync_gate,
    validate_sync_contract,
)
from chitu_connector.espocrm_sync.idempotency import evidence_snapshot_hash
from chitu_connector.vendored.config.search_sources import SearchSource
from chitu_connector.vendored.contracts.website_research import EvidenceItem, ResearchFailureCode, WebsiteResearchResult
from chitu_connector.vendored.domain.models import Candidate, ProspectState


NOW = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)
_FORBIDDEN_IMPORT_ROOTS = {
    "requests",
    "httpx",
    "aiohttp",
    "urllib3",
    "openai",
    "anthropic",
    "selenium",
    "playwright",
    "apify_client",
}


# ---------------------------------------------------------------------------
# Fixtures (same convention as test_espocrm_sync_adapter.build_source)
# ---------------------------------------------------------------------------


def evidence_item(
    evidence_id: str = "ev-fixture-1",
    *,
    claim_type: str = "product",
    claim: str = "Resin printer catalog",
    source_url: str = "https://dealer.example/products",
    page_title: str = "Products",
    evidence_text: str = "Public resin printer range listed on site.",
    evidence_type: str = "visible_text",
    confidence: float = 0.9,
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id,
        claim_type,
        claim,
        source_url,
        page_title,
        evidence_text,
        evidence_type,
        confidence,
        NOW,
    )


def normal_evidence_bundle() -> tuple[EvidenceItem, ...]:
    return (
        evidence_item(
            "ev-country",
            claim_type="company_country",
            claim="Germany",
            source_url="https://dealer.example/contact",
            page_title="Contact",
            evidence_text="Registered office in Germany.",
        ),
        evidence_item(
            "ev-product",
            claim_type="product",
            claim="resin printer",
            source_url="https://dealer.example/products",
            page_title="Products",
            evidence_text="Resin printer range on public catalog.",
        ),
    )


def build_source(
    *,
    state: ProspectState = ProspectState.OUTREACH_READY,
    score_rules_version: str = "canonical-scoring-v4.0",
    evidence: tuple[EvidenceItem, ...] | None = None,
    official_brand_excluded: bool = False,
    failure_code: ResearchFailureCode | None = None,
    website_accessible: bool | None = None,
    evidence_coverage: float = 0.76,
    aggregate_confidence: float = 0.86,
    research_output_hash: str = "r" * 64,
    candidate_id: str = "candidate-c06-1",
    domain: str = "dealer.example",
) -> object:
    from chitu_connector.espocrm_sync.models import SyncSource

    items = normal_evidence_bundle() if evidence is None else evidence
    accessible = website_accessible if website_accessible is not None else failure_code is None
    candidate = Candidate(
        id=candidate_id,
        job_id="job-c06-1",
        company_name="Example Dealer",
        raw_url=f"https://{domain}",
        canonical_domain=domain,
        country="Germany",
        source=SearchSource.GOOGLE_SEARCH,
        source_url="https://search.example/result",
        raw_payload={},
        current_state=state,
    )
    research = WebsiteResearchResult(
        candidate_id=candidate.id,
        website_url=f"https://{domain}",
        final_url=f"https://{domain}",
        website_accessible=accessible,
        http_status=200 if accessible else None,
        page_title="Example Dealer",
        meta_description="3D printer dealer",
        company_summary="Dealer",
        detected_brands=("Brand A",),
        detected_products=("resin printer",),
        customer_type_candidates=(),
        business_signals=("dealer",),
        contact_page_urls=(),
        public_emails=(),
        public_phones=(),
        evidence_items=items,
        visited_pages=(f"https://{domain}",),
        technical_warnings=(),
        failure_code=failure_code,
        failure_message=None,
        researched_at=NOW,
        adapter_version="test-research-v1",
        payload_hash="p" * 64,
        company_country="Germany",
        company_country_code="DE",
        company_country_evidence_ids=("ev-country",) if any(i.evidence_id == "ev-country" for i in items) else (),
        research_output_hash=research_output_hash,
    )
    score = {
        "opportunity_score": 82.5,
        "score_tier": "A",
        "aggregate_confidence": aggregate_confidence,
        "evidence_coverage": evidence_coverage,
        "rules_version": score_rules_version,
        "result_hash": "s" * 64,
        "best_first_product": "Resin Tank",
        "score_reasons": ("STRONG_PRODUCT_FIT",),
    }
    return SyncSource(
        candidate=candidate,
        research=research,
        score=score,
        engine_version="prospecting-engine-v1",
        cross_sell_path=("Filament Dryer",),
        official_brand_excluded=official_brand_excluded,
        official_brand_registry_version="1.0",
    )


def payload_for(source) -> SyncContractPayload:
    return EspoCRMSyncMapper().build(source, requested_at=NOW)


def mutate_evidence(payload: SyncContractPayload, mutator) -> SyncContractPayload:
    data = payload.to_dict()
    evidence = [dict(item) for item in data["evidence"]]
    mutator(evidence)
    data["evidence"] = evidence
    return SyncContractPayload(
        contract_version=data["contract_version"],
        identity=data["identity"],
        qualification=data["qualification"],
        company=data["company"],
        source=data["source"],
        research=data["research"],
        score=data["score"],
        recommendation=data["recommendation"],
        evidence=tuple(evidence),
        provenance=data["provenance"],
        sync=data["sync"],
    )


# ---------------------------------------------------------------------------
# 1. Normal evidence flow
# ---------------------------------------------------------------------------


class NormalEvidenceFlowTests(TestCase):
    def test_website_research_result_maps_to_preserved_evidence_fields(self) -> None:
        source = build_source()
        payload = payload_for(source)
        data = payload.to_dict()

        self.assertEqual(validate_sync_contract(data), ())
        self.assertEqual(len(data["evidence"]), 2)
        first = data["evidence"][0]
        self.assertEqual(first["evidence_id"], "ev-country")
        self.assertEqual(first["claim_type"], "company_country")
        self.assertEqual(first["claim"], "Germany")
        self.assertEqual(first["source_url"], "https://dealer.example/contact")
        self.assertEqual(first["evidence_text"], "Registered office in Germany.")
        self.assertEqual(first["confidence"], 0.9)
        self.assertEqual(first["schema_version"], "1.1")
        self.assertEqual(first["captured_at"], NOW.isoformat())

    def test_source_channel_and_source_url_retained_on_contract(self) -> None:
        data = payload_for(build_source()).to_dict()
        self.assertEqual(data["source"]["channel"], "WEB_SEARCH")
        self.assertEqual(data["source"]["source_url"], "https://search.example/result")
        self.assertEqual(data["company"]["website"], "https://dealer.example")

    def test_normal_flow_is_deterministic_across_builds(self) -> None:
        first = payload_for(build_source()).to_dict()
        second = payload_for(build_source()).to_dict()
        self.assertEqual(first["sync"]["idempotency_key"], second["sync"]["idempotency_key"])
        self.assertEqual(first["sync"]["payload_hash"], second["sync"]["payload_hash"])
        self.assertEqual(first["evidence"], second["evidence"])
        self.assertEqual(first["provenance"]["evidence_snapshot_hash"], second["provenance"]["evidence_snapshot_hash"])

    def test_adapter_syncs_normal_evidence_through_mock_client_only(self) -> None:
        adapter = EspoCRMSyncAdapter()
        result = adapter.sync(build_source())
        self.assertEqual(result.status, AuditStatus.SYNCED)
        self.assertEqual(result.lead_id, "mock-lead-1")
        self.assertEqual(len(adapter.client.mock_sync_history), 1)
        self.assertEqual(adapter.client.mock_sync_history[0]["status"], MockSyncStatus.SUCCESS.value)


# ---------------------------------------------------------------------------
# 2. Empty research result
# ---------------------------------------------------------------------------


class EmptyResearchResultTests(TestCase):
    def test_accessible_site_with_no_evidence_is_explicit_empty_rejection(self) -> None:
        source = build_source(evidence=(), website_accessible=True)
        payload = payload_for(source)
        self.assertEqual(payload.to_dict()["evidence"], [])
        self.assertEqual(evaluate_sync_gate(source, payload).reason_code, "MISSING_EVIDENCE")
        self.assertIn("MISSING_EVIDENCE", validate_sync_contract(payload.to_dict()))

    def test_empty_evidence_does_not_create_fake_evidence_or_call_client(self) -> None:
        adapter = EspoCRMSyncAdapter()
        result = adapter.sync(build_source(evidence=()))
        self.assertEqual(result.status, AuditStatus.REJECTED)
        self.assertEqual(result.reason_code, "MISSING_EVIDENCE")
        self.assertEqual(adapter.client.mock_sync_history, [])
        self.assertEqual(result.payload["evidence"], [])

    def test_empty_evidence_mapping_is_stable(self) -> None:
        first = payload_for(build_source(evidence=())).to_dict()["evidence"]
        second = payload_for(build_source(evidence=())).to_dict()["evidence"]
        self.assertEqual(first, [])
        self.assertEqual(first, second)


# ---------------------------------------------------------------------------
# 3. Missing source information
# ---------------------------------------------------------------------------


class MissingSourceInformationTests(TestCase):
    def test_invalid_evidence_source_url_is_rejected(self) -> None:
        source = build_source(
            evidence=(evidence_item(source_url="not-a-url", evidence_id="ev-bad-source"),),
        )
        errors = validate_sync_contract(payload_for(source).to_dict())
        self.assertTrue(any(code.startswith("INVALID_EVIDENCE_URL:") for code in errors))

    def test_blank_evidence_source_url_is_rejected(self) -> None:
        source = build_source(
            evidence=(evidence_item(source_url="", evidence_id="ev-blank-source"),),
        )
        errors = validate_sync_contract(payload_for(source).to_dict())
        self.assertTrue(any(code.startswith("INVALID_EVIDENCE_URL:") for code in errors))

    def test_missing_source_url_field_is_rejected(self) -> None:
        payload = mutate_evidence(
            payload_for(build_source()),
            lambda items: items[0].pop("source_url"),
        )
        errors = validate_sync_contract(payload.to_dict())
        self.assertIn("MISSING_EVIDENCE_FIELD:0.source_url", errors)

    def test_adapter_rejects_invalid_source_without_crm_write(self) -> None:
        adapter = EspoCRMSyncAdapter()
        source = build_source(evidence=(evidence_item(source_url="ftp://dealer.example/file"),))
        result = adapter.sync(source)
        self.assertEqual(result.status, AuditStatus.REJECTED)
        self.assertTrue(str(result.reason_code).startswith("INVALID_EVIDENCE_URL:"))
        self.assertEqual(adapter.client.mock_sync_history, [])


# ---------------------------------------------------------------------------
# 4. Malformed evidence
# ---------------------------------------------------------------------------


class MalformedEvidenceTests(TestCase):
    def test_missing_required_evidence_fields_are_reported(self) -> None:
        payload = mutate_evidence(
            payload_for(build_source()),
            lambda items: [items[0].pop(name) for name in ("claim", "evidence_text", "confidence")],
        )
        errors = validate_sync_contract(payload.to_dict())
        self.assertIn("MISSING_EVIDENCE_FIELD:0.claim", errors)
        self.assertIn("MISSING_EVIDENCE_FIELD:0.evidence_text", errors)
        self.assertIn("MISSING_EVIDENCE_FIELD:0.confidence", errors)

    def test_unexpected_evidence_field_is_rejected(self) -> None:
        payload = mutate_evidence(
            payload_for(build_source()),
            lambda items: items[0].__setitem__("raw_html", "<html>forbidden</html>"),
        )
        errors = validate_sync_contract(payload.to_dict())
        self.assertIn("UNKNOWN_EVIDENCE_FIELD:0.raw_html", errors)

    def test_invalid_evidence_types_are_rejected(self) -> None:
        data = payload_for(build_source()).to_dict()
        data["evidence"] = [
            "not-a-mapping",
            {
                "evidence_id": "ev-bad-type",
                "claim_type": "product",
                "claim": "x",
                "source_url": "https://dealer.example/products",
                "evidence_text": "text",
                "confidence": "high",
                "captured_at": "not-a-timestamp",
                "schema_version": "1.1",
            },
        ]
        errors = validate_sync_contract(data)
        self.assertIn("INVALID_EVIDENCE:0", errors)
        self.assertIn("INVALID_EVIDENCE_CONFIDENCE:1", errors)
        self.assertIn("INVALID_EVIDENCE_TIMESTAMP:1", errors)

    def test_empty_evidence_text_is_meaningful_failure(self) -> None:
        source = build_source(evidence=(evidence_item(evidence_text="   "),))
        errors = validate_sync_contract(payload_for(source).to_dict())
        self.assertIn("INVALID_EVIDENCE_TEXT:0", errors)

    def test_mock_client_returns_validation_error_for_malformed_payload(self) -> None:
        data = payload_for(build_source()).to_dict()
        data["evidence"] = [{"evidence_id": "only-id"}]
        invalid = SyncContractPayload(
            contract_version=data["contract_version"],
            identity=data["identity"],
            qualification=data["qualification"],
            company=data["company"],
            source=data["source"],
            research=data["research"],
            score=data["score"],
            recommendation=data["recommendation"],
            evidence=tuple(data["evidence"]),
            provenance=data["provenance"],
            sync=data["sync"],
        )
        result = MockEspoCRMClient().create_lead(invalid)
        self.assertEqual(result.status, MockSyncStatus.VALIDATION_ERROR)
        self.assertIsNotNone(result.reason_code)


# ---------------------------------------------------------------------------
# 5. Duplicate evidence
# ---------------------------------------------------------------------------


class DuplicateEvidenceTests(TestCase):
    def test_resubmitting_same_payload_is_duplicate_not_amplified(self) -> None:
        adapter = EspoCRMSyncAdapter()
        source = build_source()
        first = adapter.sync(source)
        second = adapter.sync(source)
        self.assertEqual(first.status, AuditStatus.SYNCED)
        self.assertEqual(second.status, AuditStatus.DUPLICATE)
        self.assertEqual(first.lead_id, second.lead_id)
        self.assertEqual(len(adapter.client.mock_sync_history), 2)
        self.assertEqual(
            [entry["status"] for entry in adapter.client.mock_sync_history],
            [MockSyncStatus.SUCCESS.value, MockSyncStatus.DUPLICATE.value],
        )

    def test_duplicate_evidence_ids_in_one_payload_remain_deterministic(self) -> None:
        duplicate_items = (
            evidence_item("ev-dup", claim="first"),
            evidence_item("ev-dup", claim="second", evidence_text="Second public claim text."),
        )
        first = payload_for(build_source(evidence=duplicate_items)).to_dict()
        second = payload_for(build_source(evidence=duplicate_items)).to_dict()
        self.assertEqual(len(first["evidence"]), 2)
        self.assertEqual(first["evidence"][0]["evidence_id"], "ev-dup")
        self.assertEqual(first["evidence"][1]["evidence_id"], "ev-dup")
        self.assertEqual(first["evidence"], second["evidence"])
        self.assertEqual(first["sync"]["payload_hash"], second["sync"]["payload_hash"])
        # Current contract does not collapse duplicate IDs; it must not invent extras.
        self.assertEqual([item["claim"] for item in first["evidence"]], ["first", "second"])

    def test_evidence_snapshot_hash_is_stable_for_identical_lists(self) -> None:
        evidence = [
            {
                "evidence_id": "ev-1",
                "claim_type": "product",
                "claim": "a",
                "source_url": "https://dealer.example/a",
                "evidence_text": "text-a",
                "confidence": 0.8,
                "captured_at": NOW.isoformat(),
                "schema_version": "1.1",
            }
        ]
        self.assertEqual(evidence_snapshot_hash(evidence), evidence_snapshot_hash(list(evidence)))


# ---------------------------------------------------------------------------
# 6. Partial research result
# ---------------------------------------------------------------------------


class PartialResearchResultTests(TestCase):
    def test_single_evidence_with_sufficient_coverage_is_accepted(self) -> None:
        source = build_source(
            evidence=(evidence_item("ev-only-product"),),
            evidence_coverage=0.55,
            aggregate_confidence=0.65,
            research_output_hash="",
        )
        payload = payload_for(source)
        self.assertEqual(validate_sync_contract(payload.to_dict()), ())
        decision = evaluate_sync_gate(source, payload)
        self.assertTrue(decision.accepted)
        self.assertEqual(len(payload.to_dict()["evidence"]), 1)

    def test_partial_evidence_below_coverage_threshold_is_rejected(self) -> None:
        source = build_source(
            evidence=(evidence_item("ev-thin"),),
            evidence_coverage=0.49,
        )
        decision = evaluate_sync_gate(source, payload_for(source))
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason_code, "INSUFFICIENT_EVIDENCE_COVERAGE")

    def test_accessible_site_with_partial_fields_does_not_invent_country(self) -> None:
        source = build_source(evidence=(evidence_item("ev-product-only"),), research_output_hash="")
        # Remove country evidence linkage so mapper must leave country null when inference-only.
        object.__setattr__(source.research, "company_country_evidence_ids", ())
        object.__setattr__(source.research, "company_country_inference", True)
        object.__setattr__(source.research, "company_country_code", "DE")
        fields = EspoCRMSyncMapper.lead_fields(payload_for(source))
        self.assertIsNone(fields["country"])

    def test_research_technical_failure_with_leftover_evidence_is_rejected(self) -> None:
        source = build_source(
            evidence=normal_evidence_bundle(),
            failure_code=ResearchFailureCode.READ_TIMEOUT,
            website_accessible=False,
        )
        decision = evaluate_sync_gate(source, payload_for(source))
        self.assertEqual(decision.reason_code, "FAILED_TECHNICAL")


# ---------------------------------------------------------------------------
# 7. Boundary protection
# ---------------------------------------------------------------------------


class BoundaryProtectionTests(TestCase):
    def test_c05_pipeline_result_does_not_emit_research_evidence_items(self) -> None:
        self.assertFalse(hasattr(WebsiteResearchPipelineResult, "evidence_items"))
        fields = {item.name for item in WebsiteResearchPipelineResult.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        self.assertNotIn("evidence_items", fields)
        self.assertNotIn("evidence", fields)

    def test_rejected_sync_never_writes_to_mock_crm(self) -> None:
        adapter = EspoCRMSyncAdapter()
        result = adapter.sync(build_source(evidence=()))
        self.assertEqual(result.status, AuditStatus.REJECTED)
        self.assertEqual(adapter.client.mock_sync_history, [])

    def test_sync_boundary_modules_do_not_import_network_or_ai_clients(self) -> None:
        root = Path(inspect.getfile(EspoCRMSyncMapper)).resolve().parent
        forbidden_hits: list[str] = []
        for path in sorted(root.glob("*.py")):
            if path.name in {"real_client.py", "real_sync.py", "connector_api.py", "brevo_api.py", "feedback_api.py"}:
                # Live HTTP clients exist for separately gated phases; enrichment boundary under test
                # is mapper/gate/contract/client(mock)/adapter only.
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [alias.name.split(".")[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module.split(".")[0]]
                for name in names:
                    if name in _FORBIDDEN_IMPORT_ROOTS:
                        forbidden_hits.append(f"{path.name}:{name}")
        self.assertEqual(forbidden_hits, [])

    def test_normal_sync_payload_excludes_raw_research_and_secrets(self) -> None:
        serialized = str(payload_for(build_source()).to_dict())
        for token in ("raw_html", "crawler_logs", "cookies", "Authorization", "api_key", "APIFY", "DeepSeek"):
            self.assertNotIn(token, serialized)

    def test_evidence_references_remain_compact_for_crm_projection(self) -> None:
        refs = EspoCRMSyncMapper.evidence_references(payload_for(build_source()))
        self.assertEqual(refs[0], {"evidence_id": "ev-country", "claim_type": "company_country"})
        self.assertTrue(all(set(ref) == {"evidence_id", "claim_type"} for ref in refs))
