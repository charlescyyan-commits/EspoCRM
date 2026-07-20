"""Permanent Phase3S01 release-integrity regression gate."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTENSION = ROOT / "crm-extension"
MANIFEST = EXTENSION / "manifest.json"
BUILDER_PATH = EXTENSION / "scripts" / "build_release_package.py"
DEPLOYMENT = ROOT / "deployment"
HISTORICAL = ROOT / "archive" / "deployment" / "historical-packages"
RELEASE_VERSION = "1.9.6-alpha"
CANONICAL_ARCHIVE = DEPLOYMENT / f"prospecting-extension-{RELEASE_VERSION}.zip"
TEXT_SOURCE_SUFFIXES = frozenset({".php", ".py", ".js", ".json", ".tpl", ".md", ".css", ".html", ".xml", ".yml", ".yaml", ".txt"})


def load_builder():
    specification = importlib.util.spec_from_file_location("phase3s01_release_builder", BUILDER_PATH)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


BUILDER = load_builder()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def canonical_text_bytes(path: Path) -> bytes:
    source = path.read_bytes()
    if path.suffix.lower() not in TEXT_SOURCE_SUFFIXES:
        return source
    return source.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


class ReleaseIntegrityTests(unittest.TestCase):
    def test_manifest_and_release_policy_use_one_current_version(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], RELEASE_VERSION)
        self.assertIn(f"**Current packaged release:** `{RELEASE_VERSION}`", (ROOT / "docs" / "release" / "VERSION_POLICY.md").read_text(encoding="utf-8"))
        self.assertIn(f"| `version` | `{RELEASE_VERSION}` |", (ROOT / "docs" / "deployment" / "VERSIONING.md").read_text(encoding="utf-8"))

    def test_deployment_has_only_the_canonical_release_archive_and_sidecar(self) -> None:
        self.assertEqual(sorted(path.name for path in DEPLOYMENT.glob("prospecting-extension-*.zip")), [CANONICAL_ARCHIVE.name])
        self.assertTrue(CANONICAL_ARCHIVE.is_file())
        self.assertTrue(BUILDER.sidecar_path(CANONICAL_ARCHIVE).is_file())

    def test_archive_name_matches_manifest_contract(self) -> None:
        self.assertEqual(CANONICAL_ARCHIVE, BUILDER.canonical_archive_path(BUILDER.load_manifest()))

    def test_archive_contains_every_source_entity_definition(self) -> None:
        source_entity_defs = {
            path.relative_to(EXTENSION).as_posix()
            for path in (EXTENSION / "files").rglob("*.json")
            if "/metadata/entityDefs/" in path.relative_to(EXTENSION).as_posix()
        }
        with zipfile.ZipFile(CANONICAL_ARCHIVE) as archive:
            self.assertTrue(source_entity_defs)
            self.assertTrue(source_entity_defs.issubset(set(archive.namelist())))

    def test_archive_bytes_and_sidecar_match_source(self) -> None:
        self.assertEqual(BUILDER.check(CANONICAL_ARCHIVE), digest(CANONICAL_ARCHIVE))

    def test_archive_uses_canonical_text_bytes_without_crlf_drift(self) -> None:
        expected_entries = BUILDER.source_entries()
        with zipfile.ZipFile(CANONICAL_ARCHIVE) as archive:
            for entry_name, source_path in expected_entries.items():
                packaged = archive.read(entry_name)
                with self.subTest(entry=entry_name):
                    self.assertEqual(packaged, canonical_text_bytes(source_path))
                    if source_path.suffix.lower() in TEXT_SOURCE_SUFFIXES:
                        self.assertNotIn(b"\r\n", packaged)

    def test_builder_text_normalization_is_explicit_and_binary_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            text_source = temporary_root / "source.json"
            binary_source = temporary_root / "source.bin"
            text_source.write_bytes(b"first\r\nsecond\rthird\n")
            binary_source.write_bytes(b"\x00\r\n\xff")
            self.assertEqual(BUILDER.canonical_source_bytes(text_source), b"first\nsecond\nthird\n")
            self.assertEqual(BUILDER.canonical_source_bytes(binary_source), b"\x00\r\n\xff")

    def test_release_documents_describe_the_current_artifact_and_root_commands(self) -> None:
        install = (ROOT / "docs" / "deployment" / "INSTALL.md").read_text(encoding="utf-8")
        release_index = (ROOT / "docs" / "release" / "README.md").read_text(encoding="utf-8")
        notes = (ROOT / "docs" / "release" / f"RELEASE_NOTES_{RELEASE_VERSION}.md").read_text(encoding="utf-8")
        for document in (install, release_index, notes):
            self.assertIn(RELEASE_VERSION, document)
            self.assertIn(CANONICAL_ARCHIVE.name, document)
        self.assertNotIn("D:\\EspoCRM-Production", install)
        self.assertIn("python crm-extension/scripts/build_release_package.py --check", install)

    def test_resource_mirrors_match_packaged_module_sources(self) -> None:
        surface = EXTENSION / "Resources"
        module = EXTENSION / "files" / "custom" / "Espo" / "Modules" / "Prospecting" / "Resources"
        mappings = (
            (surface / "entityDefs", module / "metadata" / "entityDefs"),
            (surface / "acl", module / "metadata" / "aclDefs"),
            (surface / "layouts", module / "layouts"),
            (surface / "metadata" / "formula", module / "metadata" / "formula"),
        )
        for source_root, target_root in mappings:
            for source_path in source_root.rglob("*"):
                if source_path.is_file():
                    target_path = target_root / source_path.relative_to(source_root)
                    with self.subTest(source=source_path.relative_to(surface).as_posix()):
                        self.assertTrue(target_path.is_file())
                        self.assertEqual(
                            json.loads(source_path.read_text(encoding="utf-8")),
                            json.loads(target_path.read_text(encoding="utf-8")),
                        )
        self.assertEqual(
            json.loads((surface / "routes.json").read_text(encoding="utf-8")),
            json.loads((module / "routes.json").read_text(encoding="utf-8")),
        )

    def test_historical_package_checksum_manifest_is_complete_and_valid(self) -> None:
        lines = (HISTORICAL / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines()
        expected_archives = sorted(path.name for path in HISTORICAL.glob("*.zip"))
        recorded: dict[str, str] = {}
        for line in lines:
            value, name = line.split("  ", 1)
            self.assertRegex(value, r"^[A-F0-9]{64}$")
            recorded[name] = value
        self.assertEqual(sorted(recorded), expected_archives)
        for name, expected in recorded.items():
            with self.subTest(package=name):
                self.assertEqual(digest(HISTORICAL / name), expected)

    def test_python_builder_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            first = temporary_root / "first.zip"
            second = temporary_root / "second.zip"
            BUILDER.build(first, allow_noncanonical_output=True)
            BUILDER.build(second, allow_noncanonical_output=True)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_builder_cli_is_cwd_independent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "cwd-independent.zip"
            result = subprocess.run(
                [sys.executable, str(BUILDER_PATH), "--output", str(output), "--allow-noncanonical-output"],
                cwd=EXTENSION,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(BUILDER.check(output, allow_noncanonical_output=True), digest(output))


if __name__ == "__main__":
    unittest.main()
