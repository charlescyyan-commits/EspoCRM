"""Offline archive and metadata preflight for the EspoCRM extension baseline."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTENSION = ROOT / "crm-extension"
MANIFEST = EXTENSION / "manifest.json"
PACKAGE_SCRIPT = EXTENSION / "scripts" / "build_release_package.py"
POWERSHELL_PACKAGE_SCRIPT = EXTENSION / "scripts" / "build_release_package.ps1"
FILES_ROOT = EXTENSION / "files"


def source_package_paths() -> set[str]:
    return {"manifest.json"} | {
        path.relative_to(EXTENSION).as_posix()
        for path in FILES_ROOT.rglob("*")
        if path.is_file()
    }


class ExtensionPackageBaselineTests(unittest.TestCase):
    def build_package(self, destination: Path) -> Path:
        result = subprocess.run(
            [
                sys.executable,
                str(PACKAGE_SCRIPT),
                "--output",
                str(destination),
                "--allow-noncanonical-output",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(destination.is_file(), "Package builder did not create an archive")
        return destination

    def build_powershell_package(self, destination: Path) -> Path:
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("PowerShell is unavailable; PowerShell/Python package parity cannot run")
        result = subprocess.run(
            [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(POWERSHELL_PACKAGE_SCRIPT),
                "-OutputPath",
                str(destination),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(destination.is_file(), "PowerShell package builder did not create an archive")
        return destination

    def test_all_extension_metadata_json_is_parseable(self) -> None:
        metadata_files = sorted(EXTENSION.rglob("*.json"))
        self.assertGreater(len(metadata_files), 0, "Expected extension metadata JSON files")
        for path in metadata_files:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                with path.open(encoding="utf-8") as handle:
                    self.assertIsInstance(json.load(handle), (dict, list))

    def test_package_builder_creates_an_install_preflight_archive(self) -> None:
        self.assertTrue(MANIFEST.is_file())
        self.assertTrue(FILES_ROOT.is_dir())
        self.assertTrue(PACKAGE_SCRIPT.is_file())
        self.assertTrue(POWERSHELL_PACKAGE_SCRIPT.is_file())

        with tempfile.TemporaryDirectory() as temporary_directory:
            archive_path = self.build_package(Path(temporary_directory) / "prospecting-extension.zip")
            with zipfile.ZipFile(archive_path) as archive:
                entries = [entry.filename for entry in archive.infolist() if not entry.is_dir()]
                self.assertIsNone(archive.testzip(), "Generated archive failed ZIP integrity verification")
                self.assertIn("manifest.json", entries)
                self.assertIn("files/custom/Espo/Modules/Prospecting/Resources/module.json", entries)
                self.assertTrue(all(not name.startswith(("/", "\\")) for name in entries))
                self.assertTrue(all(".." not in Path(name).parts for name in entries))
                self.assertEqual(len(entries), len(set(entries)), "Generated archive contains duplicate paths")

    def test_package_contents_match_current_install_tree_and_manifest(self) -> None:
        expected_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive_path = self.build_package(Path(temporary_directory) / "prospecting-extension.zip")
            with zipfile.ZipFile(archive_path) as archive:
                entries = {entry.filename for entry in archive.infolist() if not entry.is_dir()}
                self.assertEqual(entries, source_package_paths())
                self.assertEqual(json.loads(archive.read("manifest.json")), expected_manifest)
                for name in sorted(entry for entry in entries if entry.endswith(".json")):
                    with self.subTest(package_json=name):
                        self.assertIsInstance(json.loads(archive.read(name)), (dict, list))

    def test_python_builder_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            first = self.build_package(temporary_root / "first.zip")
            second = self.build_package(temporary_root / "second.zip")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(
                first.with_name(f"{first.name}.sha256").read_text(encoding="ascii").split("  ", 1)[0],
                second.with_name(f"{second.name}.sha256").read_text(encoding="ascii").split("  ", 1)[0],
            )

    def test_powershell_and_python_builders_have_source_content_parity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            python_archive = self.build_package(temporary_root / "python.zip")
            powershell_archive = self.build_powershell_package(temporary_root / "powershell.zip")
            with zipfile.ZipFile(python_archive) as python_zip, zipfile.ZipFile(powershell_archive) as powershell_zip:
                self.assertEqual(set(python_zip.namelist()), set(powershell_zip.namelist()))
                for name in sorted(python_zip.namelist()):
                    with self.subTest(entry=name):
                        self.assertEqual(python_zip.read(name), powershell_zip.read(name))
