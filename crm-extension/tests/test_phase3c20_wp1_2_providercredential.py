"""Phase3C20 WP1.2.1 ProviderCredential reference-custody contracts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_PLATFORM = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "AIPlatform"
ENTITY_DEFS = AI_PLATFORM / "Resources" / "metadata" / "entityDefs"
ENTITY_DEF = ENTITY_DEFS / "ProviderCredential.json"

ALLOWED_FIELDS = {
    "providerKey",
    "credentialReference",
    "displayName",
    "fingerprint",
    "lastFour",
    "environment",
    "ownerUser",
    "rotationDueAt",
    "lastRotatedAt",
    "description",
}
EXPECTED_TYPES = {
    "providerKey": "varchar",
    "credentialReference": "varchar",
    "displayName": "varchar",
    "fingerprint": "varchar",
    "lastFour": "varchar",
    "environment": "varchar",
    "ownerUser": "link",
    "rotationDueAt": "date",
    "lastRotatedAt": "datetime",
    "description": "text",
}
FORBIDDEN_SECRET_FIELDS = {
    "apiKey",
    "apiSecret",
    "token",
    "password",
    "secret",
    "plaintextCredential",
    "encryptedSecret",
    "decryptedValue",
    "rawCredential",
    "privateKey",
    "accessToken",
    "refreshToken",
}
FORBIDDEN_LIFECYCLE_TERMS = {
    "status",
    "state",
    "active",
    "inactive",
    "revoked",
    "expired",
    "pending",
    "activate",
    "deactivate",
    "rotate",
    "transition",
}
ISOLATION_TERMS = (
    "Prospecting",
    "Lead",
    "Opportunity",
    "SendExecution",
    "ReplyEvent",
    "Chitu",
)
FORBIDDEN_RUNTIME_DIRECTORIES = (
    "Api",
    "Controllers",
    "Entities",
    "Services",
)
FORBIDDEN_RUNTIME_TERMS = (
    r"\bResolver\b",
    r"\bHTTP\b",
    r"\bcurl\b",
    r"\bfile_get_contents\b",
    r"\bCredentialService\b",
    r"\bProviderCredentialService\b",
    r"\bRotationService\b",
    r"\bAuditService\b",
)


def load_entity_def() -> dict[str, object]:
    return json.loads(ENTITY_DEF.read_text(encoding="utf-8"))


class Phase3C20WP12ProviderCredentialTests(unittest.TestCase):
    def test_entity_definition_has_exact_reference_metadata_fields(self) -> None:
        self.assertTrue(ENTITY_DEF.is_file())
        self.assertEqual(set(ENTITY_DEFS.glob("*.json")), {ENTITY_DEF})

        metadata = load_entity_def()
        fields = metadata["fields"]
        self.assertEqual(set(fields), ALLOWED_FIELDS)
        self.assertEqual({name: value["type"] for name, value in fields.items()}, EXPECTED_TYPES)
        self.assertEqual(fields["lastFour"]["maxLength"], 4)
        self.assertEqual(
            metadata["links"]["ownerUser"],
            {"type": "belongsTo", "entity": "User"},
        )

    def test_forbidden_secret_fields_are_absent(self) -> None:
        metadata = load_entity_def()
        fields = metadata["fields"]
        self.assertTrue(FORBIDDEN_SECRET_FIELDS.isdisjoint(fields))

        source = ENTITY_DEF.read_text(encoding="utf-8")
        for field_name in FORBIDDEN_SECRET_FIELDS:
            self.assertIsNone(
                re.search(rf'"{re.escape(field_name)}"\s*:', source),
                msg=f"Forbidden secret field declared: {field_name}",
            )

    def test_credential_reference_is_metadata_only(self) -> None:
        metadata = load_entity_def()
        field = metadata["fields"]["credentialReference"]
        self.assertEqual(field["type"], "varchar")
        self.assertTrue(field["required"])
        self.assertNotIn("default", field)
        self.assertNotIn("collection", metadata)
        self.assertNotIn("indexes", metadata)

        for directory in FORBIDDEN_RUNTIME_DIRECTORIES:
            self.assertFalse((AI_PLATFORM / directory).exists(), msg=directory)
        for path in AI_PLATFORM.rglob("*"):
            if not path.is_file():
                continue
            source = path.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_RUNTIME_TERMS:
                self.assertIsNone(re.search(pattern, source, flags=re.IGNORECASE), msg=f"{path}: {pattern}")

    def test_lifecycle_is_absent(self) -> None:
        metadata = load_entity_def()
        fields = metadata["fields"]
        self.assertTrue(FORBIDDEN_LIFECYCLE_TERMS.isdisjoint(fields))

        source = ENTITY_DEF.read_text(encoding="utf-8")
        for term in FORBIDDEN_LIFECYCLE_TERMS:
            self.assertIsNone(
                re.search(rf"\b{re.escape(term)}\b", source, flags=re.IGNORECASE),
                msg=f"Forbidden lifecycle term declared: {term}",
            )

    def test_namespace_isolation_is_preserved(self) -> None:
        offenders: list[str] = []
        for path in AI_PLATFORM.rglob("*"):
            if not path.is_file():
                continue
            source = path.read_text(encoding="utf-8")
            for term in ISOLATION_TERMS:
                if re.search(rf"\b{re.escape(term)}\b", source):
                    offenders.append(f"{path.relative_to(ROOT)}: {term}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
