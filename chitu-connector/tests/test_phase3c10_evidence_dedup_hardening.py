"""Production-grade, offline deduplication checks for C10 ResearchEvidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence
from unittest import TestCase

from chitu_connector.espocrm_sync.research_evidence_persistence import (
    EvidencePersistenceStatus,
    ResearchEvidencePersistenceAdapter,
    evidence_identity_key,
)
from chitu_connector.vendored.contracts.website_research import EvidenceItem


CAPTURED_AT = datetime(2026, 7, 14, 9, 0, 0, tzinfo=timezone.utc)


class InMemoryResearchEvidenceClient:
    """Evidence-only target; it cannot create Leads or other CRM records."""

    def __init__(self, *, fail_on_create_call: int | None = None) -> None:
        self.fail_on_create_call = fail_on_create_call
        self.records: list[dict[str, Any]] = []
        self.create_calls: list[dict[str, Any]] = []
        self.identity_lookups: list[tuple[str, str, str, str]] = []

    def find_research_evidence_for_snapshot(
        self,
        lead_id: str,
        snapshot_hash: str,
    ) -> Sequence[Mapping[str, Any]]:
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
        self.identity_lookups.append((lead_id, source_url, claim_type, claim))
        return tuple(
            dict(record)
            for record in self.records
            if record["leadId"] == lead_id
            and record["peSourceUrl"] == source_url
            and record["peClaimType"] == claim_type
            and record["peClaim"] == claim
        )

    def create_research_evidence(self, body: Mapping[str, Any]) -> Mapping[str, Any]:
        next_call = len(self.create_calls) + 1
        if self.fail_on_create_call == next_call:
            raise RuntimeError("synthetic create failure")
        record = dict(body)
        record["id"] = f"research-evidence-{len(self.records) + 1}"
        self.records.append(record)
        self.create_calls.append(dict(body))
        return {"id": record["id"]}


def evidence_item(**overrides: Any) -> EvidenceItem:
    values = {
        "evidence_id": "ev-product-catalog",
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


class C10ResearchEvidenceDedupHardeningTests(TestCase):
    def setUp(self) -> None:
        self.client = InMemoryResearchEvidenceClient()
        self.adapter = ResearchEvidencePersistenceAdapter(self.client)

    def test_same_lead_same_evidence_is_skipped_across_different_snapshots(self) -> None:
        first = self.adapter.persist("lead-1", (evidence_item(),))
        repeated_fact = evidence_item(
            evidence_id="ev-product-catalog-retry",
            evidence_text="A later crawl observed the same factual product claim.",
            captured_at=datetime(2026, 7, 14, 10, 0, 0, tzinfo=timezone.utc),
        )
        second = self.adapter.persist("lead-1", (repeated_fact,))

        self.assertEqual(first.status, EvidencePersistenceStatus.CREATED)
        self.assertEqual(second.status, EvidencePersistenceStatus.SKIPPED)
        self.assertNotEqual(first.snapshot_hash, second.snapshot_hash)
        self.assertEqual(len(self.client.records), 1)
        self.assertEqual(len(self.client.create_calls), 1)

    def test_same_lead_different_evidence_is_created(self) -> None:
        first = self.adapter.persist("lead-1", (evidence_item(),))
        second = self.adapter.persist(
            "lead-1",
            (evidence_item(
                evidence_id="ev-contact",
                claim_type="contact",
                claim="The company publishes a public contact address.",
                source_url="https://dealer.example/contact",
                evidence_text="Contact our sales team at the published address.",
            ),),
        )

        self.assertEqual(first.status, EvidencePersistenceStatus.CREATED)
        self.assertEqual(second.status, EvidencePersistenceStatus.CREATED)
        self.assertEqual(len(self.client.records), 2)

    def test_different_lead_same_evidence_is_created(self) -> None:
        first = self.adapter.persist("lead-1", (evidence_item(),))
        second = self.adapter.persist("lead-2", (evidence_item(),))

        self.assertEqual(first.status, EvidencePersistenceStatus.CREATED)
        self.assertEqual(second.status, EvidencePersistenceStatus.CREATED)
        self.assertEqual([record["leadId"] for record in self.client.records], ["lead-1", "lead-2"])

    def test_partial_failure_retry_creates_only_missing_evidence(self) -> None:
        client = InMemoryResearchEvidenceClient(fail_on_create_call=2)
        adapter = ResearchEvidencePersistenceAdapter(client)
        first_item = evidence_item()
        second_item = evidence_item(
            evidence_id="ev-contact",
            claim_type="contact",
            claim="The company publishes a public contact address.",
            source_url="https://dealer.example/contact",
            evidence_text="Contact our sales team at the published address.",
        )

        failed = adapter.persist("lead-1", (first_item, second_item))
        client.fail_on_create_call = None
        retried = adapter.persist("lead-1", (first_item, second_item))

        self.assertEqual(failed.status, EvidencePersistenceStatus.FAILED)
        self.assertEqual(retried.status, EvidencePersistenceStatus.CREATED)
        self.assertEqual([record["peEvidenceId"] for record in client.records], ["ev-product-catalog", "ev-contact"])
        self.assertEqual(len(client.records), 2)

    def test_identity_generation_is_deterministic_and_canonical(self) -> None:
        first = evidence_identity_key(
            "lead-1",
            "HTTPS://DEALER.EXAMPLE:443/products/?b=2&a=1#catalog",
            "Product",
            "The   company lists industrial resin printers.\n",
        )
        second = evidence_identity_key(
            "lead-1",
            "https://dealer.example/products?a=1&b=2",
            "product",
            "The company lists industrial resin printers.",
        )

        self.assertEqual(first, second)
        self.assertNotEqual(first, evidence_identity_key(
            "lead-2",
            "https://dealer.example/products?a=1&b=2",
            "product",
            "The company lists industrial resin printers.",
        ))
