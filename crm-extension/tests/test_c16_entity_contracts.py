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
MODULE_CLIENT_DEFS = MODULE / "Resources" / "metadata" / "clientDefs"
MODULE_LAYOUTS = MODULE / "Resources" / "layouts"
MODULE_I18N = MODULE / "Resources" / "i18n"
SURFACE_ENTITY_DEFS = EXTENSION / "Resources" / "entityDefs"
SURFACE_ACL_DEFS = EXTENSION / "Resources" / "acl"
SURFACE_LAYOUTS = EXTENSION / "Resources" / "layouts"

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
            "Approval": {
                "name",
                "status",
                "approvalLevel",
                "targetType",
                "targetId",
                "requestedBy",
                "approver",
                "decision",
                "reason",
                "decidedAt",
            },
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
        self.assertEqual(
            quote_links["proformaInvoices"],
            {"type": "hasMany", "entity": "ProformaInvoice", "foreign": "quote"},
        )

        item_links = load_json(MODULE_ENTITY_DEFS / "QuoteItem.json")["links"]
        self.assertEqual(item_links["quote"], {"type": "belongsTo", "entity": "Quote", "foreign": "quoteItems"})

        invoice_links = load_json(MODULE_ENTITY_DEFS / "ProformaInvoice.json")["links"]
        self.assertEqual(invoice_links["quote"], {"type": "belongsTo", "entity": "Quote", "foreign": "proformaInvoices"})
        self.assertEqual(invoice_links["approvals"], {"type": "hasMany", "entity": "Approval", "foreign": "proformaInvoice"})

        approval_links = load_json(MODULE_ENTITY_DEFS / "Approval.json")["links"]
        self.assertEqual(approval_links["quote"], {"type": "belongsTo", "entity": "Quote", "foreign": "approvals"})
        self.assertEqual(approval_links["proformaInvoice"], {"type": "belongsTo", "entity": "ProformaInvoice", "foreign": "approvals"})
        self.assertEqual(approval_links["requestedBy"], {"type": "belongsTo", "entity": "User"})
        self.assertEqual(approval_links["approver"], {"type": "belongsTo", "entity": "User"})

    def test_quote_item_relationship_integrity(self) -> None:
        quote = load_json(MODULE_ENTITY_DEFS / "Quote.json")
        item = load_json(MODULE_ENTITY_DEFS / "QuoteItem.json")

        self.assertEqual(quote["links"]["quoteItems"]["foreign"], "quote")
        self.assertEqual(item["links"]["quote"]["foreign"], "quoteItems")
        self.assertEqual(quote["links"]["quoteItems"]["entity"], "QuoteItem")
        self.assertEqual(item["links"]["quote"]["entity"], "Quote")

        self.assertTrue(item["fields"]["quote"]["required"])
        self.assertEqual(item["fields"]["quote"]["type"], "link")
        self.assertEqual(set(item["links"]), {"quote"})
        self.assertNotIn("opportunity", item["links"])
        self.assertNotIn("lead", item["links"])
        self.assertNotIn("proformaInvoice", item["links"])
        self.assertNotIn("approvals", item["links"])

        self.assertIn("quoteId", item["indexes"])
        self.assertEqual(item["indexes"]["quoteId"]["columns"], ["quoteId"])

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
        self.assertEqual(approval["targetType"]["options"], ["Quote", "ProformaInvoice"])
        self.assertTrue(approval["targetType"]["required"])
        self.assertTrue(approval["targetId"]["required"])

    def test_approval_audit_metadata_contract(self) -> None:
        fields = load_json(MODULE_ENTITY_DEFS / "Approval.json")["fields"]
        links = load_json(MODULE_ENTITY_DEFS / "Approval.json")["links"]
        indexes = load_json(MODULE_ENTITY_DEFS / "Approval.json")["indexes"]

        self.assertEqual(fields["requestedBy"], {"type": "link", "required": True})
        self.assertEqual(fields["approver"], {"type": "link", "required": False, "notNull": False})
        self.assertEqual(
            fields["decision"],
            {
                "type": "enum",
                "required": False,
                "notNull": False,
                "options": ["APPROVED", "REJECTED"],
                "displayAsLabel": True,
                "style": {"APPROVED": "success", "REJECTED": "danger"},
            },
        )
        self.assertEqual(fields["reason"], {"type": "text", "required": False, "notNull": False})
        self.assertEqual(fields["decidedAt"], {"type": "datetime", "required": False, "notNull": False})

        self.assertEqual(links["requestedBy"], {"type": "belongsTo", "entity": "User"})
        self.assertEqual(links["approver"], {"type": "belongsTo", "entity": "User"})
        self.assertEqual(indexes["requestedById"], {"columns": ["requestedById"]})
        self.assertEqual(indexes["approverId"], {"columns": ["approverId"]})

    def test_approval_audit_fields_are_state_compatible(self) -> None:
        fields = load_json(MODULE_ENTITY_DEFS / "Approval.json")["fields"]

        self.assertEqual(fields["status"]["options"], ["PENDING", "APPROVED", "REJECTED"])
        self.assertEqual(fields["status"]["default"], "PENDING")
        self.assertEqual(fields["decision"]["options"], ["APPROVED", "REJECTED"])
        self.assertNotIn("PENDING", fields["decision"]["options"])
        self.assertEqual(set(fields["decision"]["options"]), set(fields["status"]["options"]) - {"PENDING"})
        self.assertEqual(fields["approvalLevel"], {"type": "int", "required": True, "default": 1, "min": 1})
        self.assertEqual(fields["targetType"]["options"], ["Quote", "ProformaInvoice"])
        self.assertTrue(fields["targetId"]["required"])

    def test_pi_payment_status_is_separate_from_workflow_status(self) -> None:
        fields = load_json(MODULE_ENTITY_DEFS / "ProformaInvoice.json")["fields"]
        workflow = fields["status"]
        payment = fields["paymentStatus"]

        self.assertIsNot(workflow, payment)
        self.assertEqual(workflow["type"], "enum")
        self.assertEqual(payment["type"], "enum")
        self.assertNotEqual(workflow["options"], payment["options"])
        self.assertTrue(set(workflow["options"]).isdisjoint(set(payment["options"])))
        self.assertNotEqual(workflow["default"], payment["default"])
        self.assertIn("SENT", workflow["options"])
        self.assertNotIn("SENT", payment["options"])
        self.assertIn("PAID", payment["options"])
        self.assertNotIn("PAID", workflow["options"])
        self.assertNotIn("paymentStatus", workflow)
        self.assertNotIn("status", payment)

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

    def test_ui_metadata_contract(self) -> None:
        icons = {
            "Quote": "fas fa-file-signature",
            "QuoteItem": "fas fa-list",
            "ProformaInvoice": "fas fa-file-invoice",
            "Approval": "fas fa-user-check",
        }
        for entity, icon in icons.items():
            self.assertEqual(
                load_json(MODULE_CLIENT_DEFS / f"{entity}.json"),
                {"controller": "controllers/record", "iconClass": icon},
            )

        expected_layouts = {
            "Quote": {"list", "detail"},
            "QuoteItem": {"detail"},
            "ProformaInvoice": {"list", "detail"},
            "Approval": {"list", "detail"},
        }
        for entity, layout_names in expected_layouts.items():
            for layout_name in layout_names:
                module_layout = MODULE_LAYOUTS / entity / f"{layout_name}.json"
                surface_layout = SURFACE_LAYOUTS / entity / f"{layout_name}.json"
                self.assertTrue(module_layout.is_file(), msg=f"Missing module layout: {module_layout}")
                self.assertTrue(surface_layout.is_file(), msg=f"Missing surface layout: {surface_layout}")
                self.assertEqual(load_json(module_layout), load_json(surface_layout))

        self.assertFalse((MODULE_LAYOUTS / "QuoteItem" / "list.json").exists())
        self.assertFalse(load_json(MODULE_SCOPES / "QuoteItem.json")["tab"])

    def test_i18n_contract_has_language_key_parity_and_state_options(self) -> None:
        expected_fields = {
            "Quote": {"name", "status", "quoteNumber", "validUntil", "amount", "opportunity", "lead"},
            "QuoteItem": {"name", "quantity", "unitPrice", "amount"},
            "ProformaInvoice": {"name", "piNumber", "status", "paymentStatus", "quote"},
            "Approval": {
                "name",
                "status",
                "approvalLevel",
                "targetType",
                "requestedBy",
                "approver",
                "decision",
                "reason",
                "decidedAt",
            },
        }
        for entity, fields in expected_fields.items():
            english = load_json(MODULE_I18N / "en_US" / f"{entity}.json")
            chinese = load_json(MODULE_I18N / "zh_CN" / f"{entity}.json")
            self.assertEqual(set(english), set(chinese))
            for section in english:
                self.assertEqual(set(english[section]), set(chinese[section]), msg=f"{entity}.{section}")
            self.assertTrue(fields.issubset(english["fields"]))

        quote_options = load_json(MODULE_I18N / "en_US" / "Quote.json")["options"]["status"]
        self.assertEqual(set(quote_options), {"DRAFT", "IN_REVIEW", "APPROVED", "SENT", "ACCEPTED", "REJECTED", "EXPIRED"})
        invoice_options = load_json(MODULE_I18N / "en_US" / "ProformaInvoice.json")["options"]
        self.assertEqual(set(invoice_options["status"]), {"DRAFT", "ISSUED", "SENT", "VOID"})
        self.assertEqual(set(invoice_options["paymentStatus"]), {"UNPAID", "PARTIAL", "PAID", "OVERDUE"})
        approval_options = load_json(MODULE_I18N / "en_US" / "Approval.json")["options"]["status"]
        self.assertEqual(set(approval_options), {"PENDING", "APPROVED", "REJECTED"})
        approval_decisions = load_json(MODULE_I18N / "en_US" / "Approval.json")["options"]["decision"]
        self.assertEqual(set(approval_decisions), {"APPROVED", "REJECTED"})

    def test_quote_and_approval_do_not_reuse_draft_approval(self) -> None:
        draft_approval_path = MODULE_ENTITY_DEFS / "DraftApproval.json"
        approval_path = MODULE_ENTITY_DEFS / "Approval.json"
        self.assertTrue(draft_approval_path.is_file(), msg="C11 DraftApproval must remain an independent entity")
        self.assertTrue(approval_path.is_file(), msg="C16 Approval must exist as its own entity")
        self.assertNotEqual(load_json(draft_approval_path), load_json(approval_path))

        approval = load_json(approval_path)
        draft_approval = load_json(draft_approval_path)
        approval_fields = set(approval["fields"])
        draft_only_fields = {"draftId", "contentHash", "evidenceReference", "scoreSnapshot", "decisionReason"}
        self.assertTrue(draft_only_fields.issubset(draft_approval["fields"]))
        self.assertTrue(draft_only_fields.isdisjoint(approval_fields))
        self.assertIn("lead", draft_approval["links"])
        self.assertIn("sendExecutions", draft_approval["links"])
        self.assertNotIn("lead", approval["links"])
        self.assertNotIn("sendExecutions", approval["links"])
        self.assertIn("quote", approval["links"])
        self.assertIn("proformaInvoice", approval["links"])
        self.assertNotIn("quote", draft_approval["links"])
        self.assertNotIn("proformaInvoice", draft_approval["links"])

        quote_links = load_json(MODULE_ENTITY_DEFS / "Quote.json")["links"]
        self.assertIn("approvals", quote_links)
        self.assertEqual(quote_links["approvals"]["entity"], "Approval")
        self.assertNotIn("draftApprovals", quote_links)
        self.assertNotIn("sendExecutions", quote_links)
        self.assertNotEqual(quote_links["approvals"]["entity"], "DraftApproval")


if __name__ == "__main__":
    unittest.main()
