"""Contract tests for the PHP ResearchEvidence production-write alignment."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from unittest import TestCase
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[2]
PHP_SERVICE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting" / "Services" / "ChituSyncService.php"
ENTITY_DEF = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting" / "Resources" / "metadata" / "entityDefs" / "ResearchEvidence.json"
SYNC_CONTRACT = ROOT / "docs" / "sync-contracts" / "ESPOCRM_SYNC_CONTRACT_V1.json"


def canonical_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    hostname = (parsed.hostname or "").lower()
    port = parsed.port
    default_port = (parsed.scheme.lower() == "https" and port == 443) or (parsed.scheme.lower() == "http" and port == 80)
    netloc = hostname if not port or default_port else f"{hostname}:{port}"
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
    return urlunsplit((parsed.scheme.lower(), netloc, path, query, ""))


def normalized_text(value: str) -> str:
    return " ".join(value.split())


def identity(lead_id: str, item: dict[str, object]) -> tuple[str, str, str, str]:
    evidence_type = item.get("evidence_type")
    stored_type = evidence_type.strip() if isinstance(evidence_type, str) and evidence_type.strip() else "LEGACY_UNKNOWN"
    claim = item["claim"]
    assert isinstance(claim, str)
    return (
        lead_id,
        canonical_url(str(item["source_url"])),
        normalized_text(stored_type).lower(),
        sha256(normalized_text(claim).encode("utf-8")).hexdigest(),
    )


@dataclass
class InMemoryPhpSyncEvidenceContract:
    """Test-local model of the C10.6 PHP create-or-update contract."""

    records: dict[tuple[str, str, str, str], dict[str, object]]

    def sync(self, lead_id: str, item: dict[str, object], snapshot_hash: str) -> tuple[dict[str, object], bool]:
        key = identity(lead_id, item)
        evidence_type = item.get("evidence_type")
        stored_type = evidence_type.strip() if isinstance(evidence_type, str) and evidence_type.strip() else "LEGACY_UNKNOWN"
        created = key not in self.records
        record = self.records.setdefault(key, {})
        record.update(
            {
                "leadId": lead_id,
                "peEvidenceId": item["evidence_id"],
                "peClaim": item["claim"],
                "peClaimType": item["claim_type"],
                "peEvidenceType": stored_type,
                "peSourceUrl": item["source_url"],
                "peSnapshotHash": snapshot_hash,
                "peCanonicalUrl": key[1],
                "peEvidenceTypeNormalized": key[2],
                "peClaimHash": key[3],
            }
        )
        return record, created


def evidence(*, claim: str = "Offers industrial resin printers.", snapshot_id: str = "ev-c10-6-1", evidence_type: str = "CUSTOMER_CASE") -> dict[str, object]:
    return {
        "evidence_id": snapshot_id,
        "claim_type": "PRODUCT",
        "evidence_type": evidence_type,
        "claim": claim,
        "source_url": "HTTPS://Example.test:443/products/?b=2&a=1",
    }


class EvidenceProductionAlignmentTests(TestCase):
    def setUp(self) -> None:
        self.writer = InMemoryPhpSyncEvidenceContract({})

    def test_same_evidence_payload_twice_creates_one_record(self) -> None:
        first, first_created = self.writer.sync("lead-c10-6", evidence(), "snapshot-one")
        second, second_created = self.writer.sync("lead-c10-6", evidence(), "snapshot-one")

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertIs(first, second)
        self.assertEqual(len(self.writer.records), 1)

    def test_same_url_with_different_claim_hash_creates_two_records(self) -> None:
        self.writer.sync("lead-c10-6", evidence(claim="Offers industrial resin printers."), "snapshot-one")
        self.writer.sync("lead-c10-6", evidence(claim="Publishes an authorized distributor program.", snapshot_id="ev-c10-6-2"), "snapshot-one")

        self.assertEqual(len(self.writer.records), 2)

    def test_evidence_type_never_uses_claim_type(self) -> None:
        record, _ = self.writer.sync("lead-c10-6", evidence(evidence_type="CUSTOMER_CASE"), "snapshot-one")

        self.assertEqual(record["peClaimType"], "PRODUCT")
        self.assertEqual(record["peEvidenceType"], "CUSTOMER_CASE")
        self.assertNotEqual(record["peEvidenceType"], record["peClaimType"])

    def test_duplicate_sync_updates_snapshot_metadata_without_creation(self) -> None:
        first, _ = self.writer.sync("lead-c10-6", evidence(), "snapshot-old")
        updated, created = self.writer.sync("lead-c10-6", evidence(snapshot_id="ev-c10-6-retry"), "snapshot-new")

        self.assertFalse(created)
        self.assertIs(updated, first)
        self.assertEqual(len(self.writer.records), 1)
        self.assertEqual(updated["peEvidenceId"], "ev-c10-6-retry")
        self.assertEqual(updated["peSnapshotHash"], "snapshot-new")

    def test_idempotent_retry_preserves_one_identity(self) -> None:
        for _ in range(3):
            self.writer.sync("lead-c10-6", evidence(), "snapshot-retry")

        self.assertEqual(len(self.writer.records), 1)
        record = next(iter(self.writer.records.values()))
        self.assertEqual(record["peEvidenceTypeNormalized"], "customer_case")
        self.assertEqual(record["peClaimHash"], sha256("Offers industrial resin printers.".encode("utf-8")).hexdigest())

    def test_php_handler_contract_and_schema_guard_match_the_alignment(self) -> None:
        source = PHP_SERVICE.read_text(encoding="utf-8")
        entity_def = json.loads(ENTITY_DEF.read_text(encoding="utf-8"))
        contract = json.loads(SYNC_CONTRACT.read_text(encoding="utf-8"))

        self.assertIn("findEvidenceByIdentity", source)
        self.assertIn("'peEvidenceType' => $this->evidenceType($item)", source)
        self.assertNotIn("'peEvidenceType' => $item['claim_type']", source)
        self.assertIn("'peSnapshotHash' => $payload['provenance']['evidence_snapshot_hash']", source)
        self.assertIn("'peCanonicalUrl' => $identity['canonicalUrl']", source)
        self.assertIn("'peEvidenceTypeNormalized' => $identity['normalizedEvidenceType']", source)
        self.assertIn("'peClaimHash' => $identity['claimHash']", source)
        self.assertEqual(
            entity_def["indexes"]["c10EvidenceIdentity"],
            {
                "type": "unique",
                "columns": ["leadId", "peCanonicalUrl", "peEvidenceTypeNormalized", "peClaimHash", "deleteId"],
            },
        )
        self.assertTrue(entity_def["deleteId"])
        self.assertIn("peEvidenceType", entity_def["fields"])
        evidence_schema = contract["properties"]["evidence"]["items"]
        self.assertIn("evidence_type", evidence_schema["properties"])
        self.assertNotIn("evidence_type", evidence_schema["required"])
