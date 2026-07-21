"""Permanent static contract: reject invalid Espo PHP namespace imports."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PHP_ROOT = ROOT / "crm-extension" / "files"

# Collapsed / typo namespaces that must never appear in packaged PHP.
FORBIDDEN_NAMESPACE_PREFIXES = (
    r"Espo\\CoreExceptions\\",
)

# Known-valid Espo roots discovered from this repository's packaged PHP.
ALLOWED_NAMESPACE_PREFIXES = (
    "Espo\\Core\\",
    "Espo\\ORM\\",
    "Espo\\Entities\\",
    "Espo\\Modules\\Prospecting\\",
    "Espo\\Custom\\",
)

USE_OR_NAMESPACE = re.compile(
    r"(?m)^\s*(?:use|namespace)\s+(Espo\\[A-Za-z0-9_\\]+)\s*[;{]"
)


def php_sources() -> list[Path]:
    return sorted(PHP_ROOT.rglob("*.php"))


def extract_espo_references(source: str) -> list[str]:
    return [match.group(1) for match in USE_OR_NAMESPACE.finditer(source)]


class EspoPhpNamespaceContractTests(unittest.TestCase):
    def test_packaged_php_rejects_invalid_core_exception_namespace(self) -> None:
        violations: list[str] = []
        for path in php_sources():
            text = path.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_NAMESPACE_PREFIXES:
                for match in re.finditer(forbidden, text):
                    relative = path.relative_to(ROOT).as_posix()
                    violations.append(f"{relative}: forbidden namespace fragment {match.group(0)!r}")
        self.assertEqual(violations, [], msg="\n".join(violations))

    def test_packaged_php_espo_imports_use_known_valid_prefixes(self) -> None:
        unknown: list[str] = []
        for path in php_sources():
            text = path.read_text(encoding="utf-8")
            for reference in extract_espo_references(text):
                if any(reference.startswith(prefix) for prefix in ALLOWED_NAMESPACE_PREFIXES):
                    continue
                # Namespace declarations for Espo\Modules\Prospecting itself are allowed.
                if reference == "Espo\\Modules\\Prospecting" or reference.startswith("Espo\\Modules\\Prospecting\\"):
                    continue
                relative = path.relative_to(ROOT).as_posix()
                unknown.append(f"{relative}: unrecognized Espo namespace {reference}")
        self.assertEqual(unknown, [], msg="\n".join(unknown))

    def test_quote_workflow_action_service_imports_core_exceptions_correctly(self) -> None:
        path = (
            PHP_ROOT
            / "custom"
            / "Espo"
            / "Modules"
            / "Prospecting"
            / "Services"
            / "QuoteWorkflowActionService.php"
        )
        source = path.read_text(encoding="utf-8")
        self.assertNotIn("Espo\\CoreExceptions\\", source)
        self.assertIn("use Espo\\Core\\Exceptions\\BadRequest;", source)
        self.assertIn("use Espo\\Core\\Exceptions\\Forbidden;", source)
        self.assertIn("use Espo\\Core\\Exceptions\\NotFound;", source)


if __name__ == "__main__":
    unittest.main()
