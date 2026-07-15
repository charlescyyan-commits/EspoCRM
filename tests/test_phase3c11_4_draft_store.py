"""Offline contract tests for the C11.4 DraftStore boundary."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from chitu_connector.espocrm_sync.draft_store import (
    DraftContentReference,
    DraftSnapshotInput,
    DraftStore,
    InMemoryDraftStore,
)
from chitu_connector.espocrm_sync.email_draft_generation import DraftEvidenceReference


ROOT = Path(__file__).resolve().parents[1]
STORE_SOURCE = ROOT / "chitu-connector" / "chitu_connector" / "espocrm_sync" / "draft_store.py"
CREATED_AT = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)


def draft_input(*, draft_id: str = "draft-c11-4-001", body: str = "Hello Acme,\n\nWe noticed your verified service network.") -> DraftSnapshotInput:
    return DraftSnapshotInput(
        draft_id=draft_id,
        lead_id="lead-c11-4-001",
        subject="Acme: introduction",
        body=body,
        metadata={"campaign": "Q3 outreach", "locale": "en-US"},
        evidence_references=(DraftEvidenceReference("evidence-001", "https://example.test/evidence/001"),),
        score_snapshot_reference="score-snapshot-001",
        generated_at=CREATED_AT,
    )


class DraftStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store: DraftStore = InMemoryDraftStore()

    def test_save_creates_retrievable_snapshot(self) -> None:
        saved = self.store.save(draft_input())

        self.assertEqual(self.store.get(saved.draft_id), saved)
        self.assertEqual(self.store.get_content_hash(saved.draft_id), saved.content_hash)
        self.assertEqual(len(saved.content_hash), 64)

    def test_saving_same_draft_twice_is_idempotent(self) -> None:
        first = self.store.save(draft_input())
        second = self.store.save(draft_input())

        self.assertEqual(first, second)
        self.assertEqual(first.content_hash, second.content_hash)
        self.assertEqual(self.store.snapshot_count, 1)  # type: ignore[attr-defined]

    def test_identical_content_has_the_same_stable_hash(self) -> None:
        first = self.store.save(draft_input(draft_id="draft-c11-4-identical-001"))
        second = self.store.save(draft_input(draft_id="draft-c11-4-identical-002"))

        self.assertEqual(first.content_hash, second.content_hash)

    def test_content_change_produces_a_different_hash(self) -> None:
        original = self.store.save(draft_input(draft_id="draft-c11-4-original"))
        revised = self.store.save(draft_input(draft_id="draft-c11-4-revised", body="Hello Acme,\n\nYour verified reseller network stands out."))

        self.assertNotEqual(original.content_hash, revised.content_hash)

    def test_approval_and_send_references_verify_matching_snapshot(self) -> None:
        saved = self.store.save(draft_input())
        approved = DraftContentReference(saved.draft_id, saved.content_hash)
        send_execution = DraftContentReference(saved.draft_id, saved.content_hash)

        result = self.store.verify_snapshot(approved, send_execution)

        self.assertTrue(result.verified)
        self.assertIsNone(result.reason_code)

    def test_modified_content_after_approval_fails_snapshot_verification(self) -> None:
        approved = self.store.save(draft_input())

        result = self.store.verify_snapshot(
            DraftContentReference(approved.draft_id, approved.content_hash),
            DraftContentReference(approved.draft_id, "0" * 64),
        )

        self.assertFalse(result.verified)
        self.assertEqual(result.reason_code, "CONTENT_HASH_MISMATCH")

    def test_forbidden_reasoning_or_prompt_content_is_rejected(self) -> None:
        for metadata in (
            {"internal_prompt": "Do not persist this."},
            {"audit": {"model_reasoning": "Hidden analysis."}},
            {"note": "This contains AI reasoning that must not be stored."},
        ):
            with self.subTest(metadata=metadata):
                value = draft_input()
                unsafe = DraftSnapshotInput(
                    draft_id=value.draft_id,
                    lead_id=value.lead_id,
                    subject=value.subject,
                    body=value.body,
                    metadata=metadata,
                    evidence_references=value.evidence_references,
                    score_snapshot_reference=value.score_snapshot_reference,
                    generated_at=value.generated_at,
                )
                with self.assertRaisesRegex(ValueError, "forbidden reasoning or prompt"):
                    self.store.save(unsafe)

    def test_same_draft_id_cannot_replace_immutable_snapshot(self) -> None:
        self.store.save(draft_input())

        with self.assertRaisesRegex(ValueError, "different snapshot"):
            self.store.save(draft_input(body="Replacement content is not allowed for the same draft id."))

    def test_boundary_has_no_external_side_effect_dependencies(self) -> None:
        source = STORE_SOURCE.read_text(encoding="utf-8")
        self.assertIn("class DraftStore(Protocol)", source)
        self.assertIn("class InMemoryDraftStore", source)
        for forbidden_import in (
            "real_client",
            "send_execution",
            "send_provider",
            "human_approval",
            "reply_tracking",
            "requests",
            "subprocess",
        ):
            self.assertNotIn(f"import {forbidden_import}", source)
            self.assertNotIn(f"from chitu_connector.espocrm_sync.{forbidden_import}", source)


if __name__ == "__main__":
    unittest.main()
