"""CC-0B provisioning hardening contracts for Sales Development Command Center."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROVISIONER = ROOT / "deployment" / "provisioning" / "phase3c17_provision_sales_development_command_center.php"
LEGACY_B07 = ROOT / "deployment" / "provisioning" / "phase3b07_provision_operations_dashboards.php"
LEGACY_C01 = ROOT / "deployment" / "provisioning" / "phase3c01_provision_acquisition_workspace.php"
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
ACL_DEFS = MODULE / "Resources" / "metadata" / "aclDefs"


def extract_php_function(source: str, name: str) -> str:
    marker = f"function {name}("
    start = source.index(marker)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"Could not extract function {name}")


class Phase3C17CC0BProvisioningHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PROVISIONER.read_text(encoding="utf-8")
        cls.b07 = LEGACY_B07.read_text(encoding="utf-8")
        cls.c01 = LEGACY_C01.read_text(encoding="utf-8")

    def test_user_all_resolves_eligible_users_and_prints_count(self) -> None:
        resolve_all = extract_php_function(self.source, "phase3c17ResolveEligibleUserNames")
        self.assertIn("'isActive' => true", resolve_all)
        self.assertIn("'type!=' => ['portal', 'api', 'system']", resolve_all)
        self.assertIn("'userName!=' => 'system'", resolve_all)
        self.assertIn("Users selected:", self.source)
        parse = extract_php_function(self.source, "phase3c17ParseUserSelection")
        self.assertIn("'all'", parse)
        self.assertNotIn("return ['admin', 'manager_test', 'sales_test'];", parse)

    def test_portal_api_system_users_excluded_from_all(self) -> None:
        resolve_all = extract_php_function(self.source, "phase3c17ResolveEligibleUserNames")
        for excluded in ("portal", "api", "system"):
            self.assertIn(f"'{excluded}'", resolve_all)

    def test_default_execution_requires_explicit_user_selection(self) -> None:
        parse = extract_php_function(self.source, "phase3c17ParseUserSelection")
        self.assertIn("User selection required", parse)
        self.assertIn("--dev-defaults", parse)
        self.assertIn("PHASE3C17_DEV_DEFAULT_USERS", self.source)
        self.assertNotIn(
            "return ['admin', 'manager_test', 'sales_test'];",
            extract_php_function(self.source, "phase3c17ResolveTargetUsers"),
        )

    def test_missing_users_warn_and_continue_with_summary(self) -> None:
        provision = extract_php_function(self.source, "phase3c17ProvisionCommandCenter")
        self.assertIn("WARNING: user not found, skipping:", provision)
        self.assertIn("return 'skipped';", provision)
        self.assertNotIn(
            'throw new \\RuntimeException("Required local user is missing',
            provision,
        )
        self.assertIn("Processed:", self.source)
        self.assertIn("Skipped:", self.source)
        self.assertIn("Failed:", self.source)

    def test_command_center_inserted_as_first_dashboard_tab(self) -> None:
        builder = extract_php_function(self.source, "phase3c17BuildDashboardLayout")
        self.assertIn("array_merge([$commandCenterTab], $preservedTabs)", builder)
        self.assertIn("'name' => PHASE3C17_COMMAND_CENTER", builder)
        self.assertNotIn("$preservedTabs[] = [", builder)

    def test_personal_dashboards_preserved_and_legacy_managed_tabs_removed(self) -> None:
        self.assertIn("PHASE3C17_LEGACY_TABS", self.source)
        for legacy in ("Prospecting Operations", "Acquisition", "Prospecting Home"):
            self.assertIn(legacy, self.source)
        builder = extract_php_function(self.source, "phase3c17BuildDashboardLayout")
        self.assertIn("$preservedTabs[] = $tab;", builder)
        self.assertIn("phase3c17IsManagedDashletId", builder)

    def test_repeated_execution_does_not_duplicate_command_center_tab(self) -> None:
        legacy_block = self.source.split("PHASE3C17_LEGACY_TABS")[1].split("];")[0]
        self.assertIn("PHASE3C17_COMMAND_CENTER", legacy_block)
        builder = extract_php_function(self.source, "phase3c17BuildDashboardLayout")
        self.assertEqual(builder.count("array_merge([$commandCenterTab], $preservedTabs)"), 1)
        ids = re.findall(r"'id' => '(phase3c17-command-[^']+)'", self.source)
        self.assertEqual(len(ids), len(set(ids)), msg="managed dashlet ids must be unique")

    def test_no_acl_or_workflow_files_changed_by_provisioner(self) -> None:
        for forbidden in (
            "aclDefs",
            "ApprovalService",
            "ApprovalDecisionService",
            "QuoteTransitionService",
            "tabList",
            "navigation.json",
            "ConfigWriter",
        ):
            self.assertNotIn(forbidden, self.source)
        self.assertTrue(ACL_DEFS.is_dir())

    def test_legacy_wrappers_remain_compatible(self) -> None:
        self.assertIn("phase3c17_provision_sales_development_command_center.php", self.b07)
        self.assertIn("phase3c17_provision_sales_development_command_center.php", self.c01)
        self.assertIn("--user=all", self.b07)
        self.assertIn("--user=", self.c01)

    def test_new_user_strategy_documents_native_path_without_login_hook(self) -> None:
        self.assertIn("New-user strategy", self.source)
        self.assertIn("Dashboard Templates", self.source)
        self.assertIn("--user=all", self.source)
        self.assertIn("defaultDashboardLayouts", self.source)
        self.assertNotIn("afterLogin", self.source.lower())
        self.assertNotIn("login hook", self.source.lower())


if __name__ == "__main__":
    unittest.main()
