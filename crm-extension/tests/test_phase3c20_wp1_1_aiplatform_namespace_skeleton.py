"""Phase3C20 WP1.1.1 AIPlatform namespace skeleton contracts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_PLATFORM = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "AIPlatform"
BINDING = AI_PLATFORM / "Binding.php"
MODULE_METADATA = AI_PLATFORM / "Resources" / "module.json"
GOVERNANCE_MARKER = "adr-c20-aiplatform-v1"

PROSPECTING_REFERENCES = (
    r"Espo\\Modules\\Prospecting",
    r"\bSendExecution\b",
    r"\bReplyEvent\b",
    r"\bOpportunity\b",
    r"\bLead\b",
    r"\bChitu\b",
)
FORBIDDEN_PATH_TOKENS = (
    "AIJob",
    "Provider",
    "Adapter",
    "Transport",
    "Credential",
    "Prompt",
    "Score",
)
FORBIDDEN_DIRECTORIES = (
    "Api",
    "Controllers",
    "Entities",
    "Services",
    "layouts",
    "clientDefs",
    "entityDefs",
    "scopes",
    "aclDefs",
)
FORBIDDEN_RUNTIME_REFERENCES = (
    r"\bProvider\b",
    r"\bAdapter\b",
    r"\bTransport\b",
    r"\bHTTP\b",
    r"\bConnector\b",
    r"\bCapability\b",
    r"\bResolver\b",
    r"\bRegistry\b",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C20WP11AIPlatformNamespaceSkeletonTests(unittest.TestCase):
    def test_namespace_module_exists_with_existing_module_conventions(self) -> None:
        self.assertTrue(AI_PLATFORM.is_dir())
        self.assertTrue(BINDING.is_file())
        self.assertTrue(MODULE_METADATA.is_file())
        self.assertEqual(json.loads(read(MODULE_METADATA)), {"order": 6})

        binding = read(BINDING)
        self.assertIn("namespace Espo\\Modules\\AIPlatform;", binding)
        self.assertIn("final class Binding implements BindingProcessor", binding)
        self.assertIn("public function process(Binder $binder): void", binding)

    def test_module_is_isolated_from_prospecting_and_connector_terms(self) -> None:
        offenders: list[str] = []
        for path in AI_PLATFORM.rglob("*"):
            if not path.is_file():
                continue
            text = read(path)
            for pattern in PROSPECTING_REFERENCES:
                if re.search(pattern, text):
                    offenders.append(f"{path.relative_to(ROOT)}: {pattern}")
        self.assertEqual(offenders, [])

    def test_governance_marker_is_defined_only_at_module_boundary(self) -> None:
        marker_paths = [
            path.relative_to(AI_PLATFORM).as_posix()
            for path in AI_PLATFORM.rglob("*")
            if path.is_file() and GOVERNANCE_MARKER in read(path)
        ]
        self.assertEqual(marker_paths, ["Binding.php"])
        self.assertIn(GOVERNANCE_MARKER, read(BINDING))

    def test_no_forbidden_artifacts_or_runtime_references_exist(self) -> None:
        offenders: list[str] = []
        for path in AI_PLATFORM.rglob("*"):
            relative = path.relative_to(AI_PLATFORM).as_posix()
            if any(token in path.name for token in FORBIDDEN_PATH_TOKENS):
                offenders.append(relative)
            if path.is_dir() and path.name in FORBIDDEN_DIRECTORIES:
                offenders.append(relative)
            if not path.is_file():
                continue
            text = read(path)
            for pattern in FORBIDDEN_RUNTIME_REFERENCES:
                if re.search(pattern, text):
                    offenders.append(f"{relative}: {pattern}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
