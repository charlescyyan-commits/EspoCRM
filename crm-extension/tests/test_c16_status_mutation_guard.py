"""Offline contracts for C16.3B-4R2 status ownership persistence guards."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "crm-extension" / "files" / "custom" / "Espo"
MODULE = CUSTOM / "Modules" / "Prospecting"
SERVICES = MODULE / "Services"
ENTITY_DEFS = MODULE / "Resources" / "metadata" / "entityDefs"
QUOTE_GUARD = CUSTOM / "Custom" / "Hooks" / "Quote" / "QuoteStatusMutationGuard.php"
APPROVAL_GUARD = CUSTOM / "Custom" / "Hooks" / "Approval" / "ApprovalStatusMutationGuard.php"
SAVE_OPTION = SERVICES / "StatusMutationSaveOption.php"
QUOTE_TRANSITION = SERVICES / "QuoteTransitionService.php"
APPROVAL_SERVICE = SERVICES / "ApprovalService.php"
APPROVAL_DECISION = SERVICES / "ApprovalDecisionService.php"
WORKFLOW_ACTION = SERVICES / "QuoteWorkflowActionService.php"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class C16StatusMutationGuardTests(unittest.TestCase):
    def test_status_metadata_is_read_only_without_changing_state_contracts(self) -> None:
        quote = json.loads((ENTITY_DEFS / "Quote.json").read_text(encoding="utf-8"))["fields"]["status"]
        approval = json.loads((ENTITY_DEFS / "Approval.json").read_text(encoding="utf-8"))["fields"]["status"]

        self.assertTrue(quote["readOnly"])
        self.assertTrue(approval["readOnly"])
        self.assertEqual(quote["default"], "DRAFT")
        self.assertEqual(approval["default"], "PENDING")
        self.assertEqual(quote["options"], ["DRAFT", "IN_REVIEW", "APPROVED", "SENT", "ACCEPTED", "REJECTED", "EXPIRED"])
        self.assertEqual(approval["options"], ["PENDING", "APPROVED", "REJECTED"])

    def test_marker_contract_uses_distinct_per_save_keys(self) -> None:
        source = read(SAVE_OPTION)

        self.assertIn("final class StatusMutationSaveOption", source)
        self.assertIn("'prospecting.quoteStatusMutationAuthorized'", source)
        self.assertIn("'prospecting.approvalStatusMutationAuthorized'", source)
        self.assertNotIn("statusAuthorized", source)
        self.assertNotIn("static", source)
        self.assertNotIn("SaveContext", source)

    def test_quote_guard_allows_only_draft_create_unchanged_save_or_marker(self) -> None:
        source = read(QUOTE_GUARD)

        self.assertIn("implements BeforeSave", source)
        self.assertIn("public static int $order = 1000;", source)
        self.assertIn("$entity->isNew()", source)
        self.assertIn("QuoteTransitionService::STATUS_DRAFT", source)
        self.assertIn("!$entity->isAttributeChanged('status')", source)
        self.assertIn("StatusMutationSaveOption::QUOTE_STATUS_MUTATION_AUTHORIZED", source)
        self.assertIn("=== true", source)
        self.assertIn("Quote status mutation must use QuoteTransitionService.", source)
        self.assertNotIn("isAdmin", source)
        self.assertNotIn("SKIP_HOOKS", source)
        self.assertNotIn("SKIP_ALL", source)

    def test_approval_guard_rejects_direct_creation_and_unmarked_status_changes(self) -> None:
        source = read(APPROVAL_GUARD)

        self.assertIn("implements BeforeSave", source)
        self.assertIn("public static int $order = 1000;", source)
        self.assertIn("StatusMutationSaveOption::APPROVAL_STATUS_MUTATION_AUTHORIZED", source)
        self.assertIn("!$entity->isNew() && !$entity->isAttributeChanged('status')", source)
        self.assertIn("Approval status mutation must use ApprovalService.", source)
        self.assertNotIn("isAdmin", source)
        self.assertNotIn("SKIP_HOOKS", source)
        self.assertNotIn("SKIP_ALL", source)

    def test_only_owner_services_supply_their_marker_to_save_entity(self) -> None:
        quote = read(QUOTE_TRANSITION)
        approval = read(APPROVAL_SERVICE)

        self.assertIn("$this->entityManager->saveEntity($quote, [", quote)
        self.assertEqual(quote.count("StatusMutationSaveOption::QUOTE_STATUS_MUTATION_AUTHORIZED => true"), 1)
        self.assertNotIn("APPROVAL_STATUS_MUTATION_AUTHORIZED", quote)

        self.assertEqual(approval.count("StatusMutationSaveOption::APPROVAL_STATUS_MUTATION_AUTHORIZED => true"), 3)
        self.assertNotIn("QUOTE_STATUS_MUTATION_AUTHORIZED", approval)

        for path in (APPROVAL_DECISION, WORKFLOW_ACTION):
            source = read(path)
            self.assertNotIn("StatusMutationSaveOption", source, msg=str(path))
            self.assertNotIn("saveEntity(", source, msg=str(path))

    def test_status_writers_are_limited_to_declared_owners(self) -> None:
        quote_writers: list[Path] = []
        approval_writers: list[Path] = []

        for path in CUSTOM.rglob("*.php"):
            source = read(path)
            if re.search(r"\$quote->set\(\s*['\"]status['\"]", source):
                quote_writers.append(path)
            if re.search(r"\$(?:approval|locked)->set\(\s*\[.*?['\"]status['\"]\s*=>", source, re.S):
                approval_writers.append(path)

        self.assertEqual(quote_writers, [QUOTE_TRANSITION])
        self.assertEqual(approval_writers, [APPROVAL_SERVICE])

    def test_no_status_bypass_mechanism_exists_in_production_extension_code(self) -> None:
        source = "\n".join(read(path) for path in CUSTOM.rglob("*.php"))

        for forbidden in ("SKIP_HOOKS", "SKIP_ALL", "SaveContext"):
            self.assertNotIn(forbidden, source)

        self.assertNotRegex(source, r"(?is)\bUPDATE\s+[^;\n]*(?:quote|approval)[^;\n]*\bstatus\b")
        self.assertNotRegex(source, r"(?is)->update\([^;\n]*(?:quote|approval|status)")


if __name__ == "__main__":
    unittest.main()
