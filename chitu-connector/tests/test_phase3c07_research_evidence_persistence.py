"""Offline tests for the Phase3C07.2 ResearchEvidence persistence adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence
from unittest import TestCase

from chitu_connector.espocrm_sync.research_evidence_persistence import (
    EvidencePersistenceStatus,
    ResearchEvidencePersistenceAdapter,
)
from chitu_connector.vendored.contracts.website_research import EvidenceItem


CAPTURED_AT = datetime(2026, 7, 13, 10, 11, 12, tzinfo=timezone.utc)


class FakeResearchEvidenceClient:
    def __init__(self, *, fail_create: bool = False) -> None:
        self.fail_create = fail_create
        self.records: list[dict[str, Any]] = []
        self.lookup_calls: list[tuple[str, str]] = []
        self.create_calls: list[dict[str, Any]] = []

    def find_research_evidence_for_snapshot(
        self,
        lead_id: str,
        snapshot_hash: str,
    ) -> Sequence[Mapping[str, Any]]:
        self.lookup_calls.append((lead_id, snapshot_hash))
        return tuple(
            dict(record)
            for record in self.records
            if record["leadId"] == lead_id and record["peSnapshotHash"] == snapshot_hash
        )

    def find_research_evidence_by_identity(
        self,
        lead_id: str,
        source_url: str,
        claim_type: str,
        claim: str,
    ) -> Sequence[Mapping[str, Any]]:
        return tuple(
            dict(record)
            for record in self.records
            if record["leadId"] == lead_id
            and record["peSourceUrl"] == source_url
            and record["peClaimType"] == claim_type
            and record["peClaim"] == claim
        )

    def create_research_evidence(self, body: Mapping[str, Any]) -> Mapping[str, Any]:
        if self.fail_create:
            raise RuntimeError("EspoCRM unavailable")
        record = dict(body)
        record["id"] = f"evidence-{len(self.records) + 1}"
        self.records.append(record)
        self.create_calls.append(dict(body))
        return {"id": record["id"]}


def evidence_item(**overrides: Any) -> EvidenceItem:
    values = {
        "evidence_id": "ev-products",
        "claim_type": "product",
        "claim": "The company lists industrial resin printers.",
        "source_url": "https://dealer.example/products",
        "page_title": "Products | Example Dealer",
        "evidence_text": "Industrial resin printers are listed in the public product catalog.",
        "evidence_type": "visible_text",
        "confidence": 0.85,
        "captured_at": CAPTURED_AT,
        "extractor_version": "c07-evidence-extraction-v1",
    }
    values.update(overrides)
    return EvidenceItem(**values)


class ResearchEvidencePersistenceAdapterTests(TestCase):
    def setUp(self) -> None:
        self.client = FakeResearchEvidenceClient()
        self.adapter = ResearchEvidencePersistenceAdapter(self.client)

    def test_persists_the_complete_c06_field_mapping_for_existing_lead(self) -> None:
        result = self.adapter.persist("lead-123", (evidence_item(),))

        self.assertEqual(result.status, EvidencePersistenceStatus.CREATED)
        self.assertEqual(result.crm_ids, ("evidence-1",))
        self.assertEqual(len(self.client.create_calls), 1)
        body = self.client.create_calls[0]
        self.assertEqual(
            body,
            {
                "name": "Evidence ev-products",
                "leadId": "lead-123",
                "peEvidenceId": "ev-products",
                "peClaim": "The company lists industrial resin printers.",
                "peClaimType": "product",
                "peEvidenceType": "visible_text",
                "peSourceUrl": "https://dealer.example/products",
                "peEvidenceText": "Industrial resin printers are listed in the public product catalog.",
                "peContentSummary": "The company lists industrial resin printers.",
                "peConfidence": 0.85,
                "peCapturedAt": "2026-07-13 10:11:12",
                "peSchemaVersion": "c07-evidence-extraction-v1",
                "peSnapshotHash": result.snapshot_hash,
            },
        )

    def test_skips_an_already_persisted_snapshot_for_the_same_lead(self) -> None:
        items = (evidence_item(),)
        first = self.adapter.persist("lead-123", items)
        second = self.adapter.persist("lead-123", items)

        self.assertEqual(first.status, EvidencePersistenceStatus.CREATED)
        self.assertEqual(second.status, EvidencePersistenceStatus.SKIPPED)
        self.assertEqual(second.snapshot_hash, first.snapshot_hash)
        self.assertEqual(second.crm_ids, ("evidence-1",))
        self.assertEqual(len(self.client.create_calls), 1)

    def test_recovers_a_partial_snapshot_without_recreating_existing_evidence(self) -> None:
        first_item = evidence_item(evidence_id="ev-products")
        second_item = evidence_item(evidence_id="ev-contact", claim_type="contact", claim="The company publishes a contact address.")
        first = self.adapter.persist("lead-123", (first_item, second_item))
        self.assertEqual(first.status, EvidencePersistenceStatus.CREATED)

        self.client.records.pop()
        second = self.adapter.persist("lead-123", (first_item, second_item))

        self.assertEqual(second.status, EvidencePersistenceStatus.CREATED)
        self.assertEqual(len(self.client.records), 2)
        self.assertEqual([record["peEvidenceId"] for record in self.client.records], ["ev-products", "ev-contact"])

    def test_allows_missing_optional_page_title_without_inventing_content(self) -> None:
        result = self.adapter.persist("lead-123", (evidence_item(page_title=""),))

        self.assertEqual(result.status, EvidencePersistenceStatus.CREATED)
        body = self.client.create_calls[0]
        self.assertEqual(body["peContentSummary"], body["peClaim"])
        self.assertNotIn("page_title", body)

    def test_reports_api_creation_failure_without_lead_side_effects(self) -> None:
        client = FakeResearchEvidenceClient(fail_create=True)
        result = ResearchEvidencePersistenceAdapter(client).persist("lead-123", (evidence_item(),))

        self.assertEqual(result.status, EvidencePersistenceStatus.FAILED)
        self.assertEqual(result.reason_code, "CREATE_FAILED")
        self.assertEqual(result.crm_ids, ())
        self.assertEqual(client.records, [])

    def test_rejects_malformed_evidence_before_lookup_or_create(self) -> None:
        malformed = evidence_item(source_url="not-a-url")
        result = self.adapter.persist("lead-123", (malformed,))

        self.assertEqual(result.status, EvidencePersistenceStatus.REJECTED)
        self.assertEqual(result.reason_code, "INVALID_SOURCE_URL")
        self.assertEqual(self.client.lookup_calls, [])
        self.assertEqual(self.client.create_calls, [])
