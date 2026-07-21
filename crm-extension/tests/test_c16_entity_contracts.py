"""Offline contract tests for the C16.1A metadata-only entity foundation."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTENSION = ROOT / "crm-extension"
MODULE = EXTENSION / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
MODULE_ENTITY_DEFS = MODULE / "Resources" / "metadata" / "entityDefs"
MODULE_SCOPES = MODULE / "Resources" / "metadata" / "scopes"
MODULE_ACL_DEFS = MODULE / "Resources" / "metadata" / "aclDefs"
SURFACE_ENTITY_DEFS = EXTENSION / "Resources" / "entityDefs"
SURFACE_ACL_DEFS = EXTENSION / "Resources" / "acl"

C16_ENTITIES = ("Quote", "QuoteItem", "ProformaInvoice", "Approval")


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


class C16EntityContractTests(unittest.TestCase):
    def test_all_c16_entities_are_registered_and_surface_mirrored(self) -> None:
        for entity in C16_ENTITIES:
            module_path = MODULE_ENTITY_DEFS / f"{entity}.json"
            surface_path = SURFACE_ENTITY_DEFS / f"{entity}.json"
            self.assertTrue(module_path.is_file(), msg=f"Missing entity definition: {module_path}")
            self.assertTrue(surface_path.is_file(), msg=f"Missing surface mirror: {surface_path}")
            self.assertEqual(load_json(module_path), load_json(surface_path), msg=f"Parity mismatch: {entity}")

    def test_field_contract(self) -> None:
        contracts = {
            "Quote": {"name", "status", "quoteNumber", "validUntil", "amount", "opportunity", "lead"},
            "QuoteItem": {"name", "quantity", "unitPrice", "amount", "quote"},
            "ProformaInvoice": {"name", "piNumber", "status", "paymentStatus", "quote"},
            "Approval": {"name", "status", "approvalLevel", "targetType", "targetId"},
        }
        for entity, required_fields in contracts.items():
            fields = load_json(MODULE_ENTITY_DEFS / f"{entity}.json")["fields"]
            self.assertTrue(required_fields.issubset(fields), msg=f"{entity} is missing {required_fields - set(fields)}")

        quote = load_json(MODULE_ENTITY_DEFS / "Quote.json")["fields"]
        self.assertEqual(quote["opportunity"]["type"], "link")
        self.assertEqual(quote["lead"]["type"], "link")
        self.assertEqual(quote["amount"]["type"], "currency")
        self.assertEqual(quote["quoteNumber"]["maxLength"], 32)

        item = load_json(MODULE_ENTITY_DEFS / "QuoteItem.json")["fields"]
        self.assertEqual(item["quantity"]["type"], "float")
        self.assertEqual(item["unitPrice"]["type"], "currency")
        self.assertEqual(item["amount"]["type"], "currency")

        invoice = load_json(MODULE_ENTITY_DEFS / "ProformaInvoice.json")["fields"]
        self.assertEqual(invoice["quote"]["type"], "link")
        self.assertEqual(invoice["piNumber"]["maxLength"], 32)

    def test_relationship_contract(self) -> None:
        quote_links = load_json(MODULE_ENTITY_DEFS / "Quote.json")["links"]
        self.assertEqual(quote_links["opportunity"], {"type": "belongsTo", "entity": "Opportunity"})
        self.assertEqual(quote_links["lead"], {"type": "belongsTo", "entity": "Lead"})
        self.assertEqual(quote_links["quoteItems"], {"type": "hasMany", "entity": "QuoteItem", "foreign": "quote"})
        self.assertEqual(quote_links["approvals"], {"type": "hasMany", "entity": "Approval", "foreign": "quote"})

        item_links = load_json(MODULE_ENTITY_DEFS / "QuoteItem.json")["links"]
        self.assertEqual(item_links["quote"], {"type": "belongsTo", "entity": "Quote", "foreign": "quoteItems"})

        invoice_links = load_json(MODULE_ENTITY_DEFS / "ProformaInvoice.json")["links"]
        self.assertEqual(invoice_links["quote"], {"type": "belongsTo", "entity": "Quote", "foreign": "proformaInvoices"})
        self.assertEqual(invoice_links["approvals"], {"type": "hasMany", "entity": "Approval", "foreign": "proformaInvoice"})

        approval_links = load_json(MODULE_ENTITY_DEFS / "Approval.json")["links"]
        self.assertEqual(approval_links["quote"], {"type": "belongsTo", "entity": "Quote", "foreign": "approvals"})
        self.assertEqual(approval_links["proformaInvoice"], {"type": "belongsTo", "entity": "ProformaInvoice", "foreign": "approvals"})

    def test_state_contract(self) -> None:
        quote = load_json(MODULE_ENTITY_DEFS / "Quote.json")["fields"]["status"]
        self.assertEqual(quote["options"], ["DRAFT", "IN_REVIEW", "APPROVED", "SENT", "ACCEPTED", "REJECTED", "EXPIRED"])
        self.assertEqual(quote["default"], "DRAFT")

        invoice_fields = load_json(MODULE_ENTITY_DEFS / "ProformaInvoice.json")["fields"]
        self.assertEqual(invoice_fields["status"]["options"], ["DRAFT", "ISSUED", "SENT", "VOID"])
        self.assertEqual(invoice_fields["status"]["default"], "DRAFT")
        self.assertEqual(invoice_fields["paymentStatus"]["options"], ["UNPAID", "PARTIAL", "PAID", "OVERDUE"])
        self.assertEqual(invoice_fields["paymentStatus"]["default"], "UNPAID")

        approval = load_json(MODULE_ENTITY_DEFS / "Approval.json")["fields"]
        self.assertEqual(approval["status"]["options"], ["PENDING", "APPROVED", "REJECTED"])
        self.assertEqual(approval["status"]["default"], "PENDING")
        self.assertEqual(approval["approvalLevel"], {"type": "int", "required": True, "default": 1, "min": 1})

    def test_scope_and_acl_contract(self) -> None:
        for entity in C16_ENTITIES:
            scope = load_json(MODULE_SCOPES / f"{entity}.json")
            self.assertTrue(scope["entity"])
            self.assertTrue(scope["object"])
            self.assertTrue(scope["acl"])
            self.assertEqual(scope["module"], "Prospecting")
            self.assertEqual(scope["type"], "Base")
            self.assertEqual(load_json(MODULE_ACL_DEFS / f"{entity}.json"), {"Prospecting": {entity: True}})
            self.assertEqual(load_json(SURFACE_ACL_DEFS / f"{entity}.json"), {"Prospecting": {entity: True}})

        self.assertFalse(load_json(MODULE_SCOPES / "QuoteItem.json")["tab"])
        for entity in ("Quote", "ProformaInvoice", "Approval"):
            self.assertTrue(load_json(MODULE_SCOPES / f"{entity}.json")["tab"])

    def test_boundary_contract_keeps_c16_crm_owned(self) -> None:
        forbidden_references = ("DraftApproval", "SendExecution", "chitu_connector", "ChituSyncService")
        for entity in C16_ENTITIES:
            definition = (MODULE_ENTITY_DEFS / f"{entity}.json").read_text(encoding="utf-8")
            for forbidden in forbidden_references:
                self.assertNotIn(forbidden, definition, msg=f"{entity} must not reuse or depend on {forbidden}")


if __name__ == "__main__":
    unittest.main()
