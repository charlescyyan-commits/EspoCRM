"""Focused verification for the DP-WP0 Railway artifact manifest."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "generate_railway_artifact_manifest.py"
MANIFEST_PATH = REPOSITORY_ROOT / "deployment" / "railway" / "full-application-artifact-manifest.json"
CONTRACT_PATH = REPOSITORY_ROOT / "docs" / "deployment" / "RAILWAY_DP_WP0_DEPLOYMENT_CONTRACT.md"
RATIFICATION_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "audit"
    / "RAILWAY_DP_WP0_DEPLOYMENT_CONTRACT_RATIFICATION.md"
)
BASELINE_COMMIT = "6ef712134f581a12a18da5c98691884e73388b78"

SPEC = importlib.util.spec_from_file_location("railway_manifest_generator", SCRIPT_PATH)
assert SPEC and SPEC.loader
generator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = generator
SPEC.loader.exec_module(generator)


def _copy_manifest_inputs(temporary_root: Path) -> Path:
    for source in ("crm-extension", "deployment/provisioning", "deployment/navigation", "deployment/railway"):
        source_path = REPOSITORY_ROOT / source
        destination = temporary_root / source
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_path, destination, dirs_exist_ok=True)
    legacy_zip = REPOSITORY_ROOT / "deployment/prospecting-extension-1.9.13-alpha.zip"
    legacy_destination = temporary_root / "deployment/prospecting-extension-1.9.13-alpha.zip"
    legacy_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(legacy_zip, legacy_destination)
    for source in (
        "docs/deployment/RAILWAY_DP_WP0_DEPLOYMENT_CONTRACT.md",
        "scripts/generate_railway_artifact_manifest.py",
        "tests/test_railway_dp_wp0_artifact_manifest.py",
    ):
        destination = temporary_root / source
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPOSITORY_ROOT / source, destination)
    return temporary_root / "deployment/railway/full-application-artifact-manifest.json"


class TestRailwayDpWp0ArtifactManifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_railway_artifact_manifest_schema_and_release_identity(self) -> None:
        self.assertEqual(self.manifest["schemaVersion"], 1)
        self.assertEqual(self.manifest["release"]["gitCommit"], BASELINE_COMMIT)
        self.assertEqual(
            self.manifest["release"]["gitCommit"],
            generator.AUTHORIZED_SOURCE_BASELINE,
        )
        self.assertEqual(self.manifest["release"]["deploymentModel"], "deterministic-overlay")
        extension = json.loads((REPOSITORY_ROOT / "crm-extension/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(self.manifest["release"]["extensionName"], extension["extensionName"])
        self.assertEqual(self.manifest["release"]["extensionVersion"], extension["version"])
        for key in ("canonicalRoots", "requiredArtifacts", "files", "excludedPatterns", "forbiddenPatterns", "legacyArtifacts"):
            self.assertIn(key, self.manifest)

    def test_railway_artifact_manifest_is_deterministic_and_current(self) -> None:
        expected = generator.render_manifest(generator.build_manifest(REPOSITORY_ROOT))
        self.assertEqual(MANIFEST_PATH.read_bytes(), expected)
        first = MANIFEST_PATH.read_bytes()
        subprocess.run([sys.executable, str(SCRIPT_PATH)], cwd=REPOSITORY_ROOT, check=True)
        self.assertEqual(MANIFEST_PATH.read_bytes(), first)
        subprocess.run([sys.executable, str(SCRIPT_PATH), "--check"], cwd=REPOSITORY_ROOT, check=True)

    def test_railway_artifact_manifest_paths_hashes_and_required_artifacts(self) -> None:
        files = self.manifest["files"]
        paths = [entry["path"] for entry in files]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertTrue(all("\\" not in path and not path.startswith("/") and ".." not in Path(path).parts for path in paths))
        by_path = {entry["path"]: entry for entry in files}
        for entry in files:
            source = REPOSITORY_ROOT / entry["path"]
            self.assertTrue(source.is_file(), entry["path"])
            self.assertEqual(entry["bytes"], source.stat().st_size)
            self.assertEqual(entry["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        for required in self.manifest["requiredArtifacts"]:
            self.assertIn(required["path"], by_path)

    def test_railway_artifact_manifest_candidates_are_not_execution_authority(self) -> None:
        candidates = [entry for entry in self.manifest["files"] if entry["category"] in {"provisioning-candidate", "navigation-candidate"}]
        self.assertTrue(candidates)
        self.assertTrue(all(entry["required"] == "optional" for entry in candidates))
        self.assertTrue(all(entry["executionStatus"] == "candidate-pending-dp-wp2" for entry in candidates))
        self.assertIn("does not authorize", self.manifest["executionBoundary"])

    def test_railway_artifact_manifest_forbidden_and_local_runtime_paths_are_excluded(self) -> None:
        for entry in self.manifest["files"]:
            path = entry["path"]
            self.assertFalse(generator.is_forbidden_path(path), path)
            self.assertFalse(generator.is_mutable_governance_path(path), path)
            self.assertNotIn("/var/www/html/data", path)
            self.assertNotIn(":/", path)
            self.assertNotIn("docker-volume", path.lower())

    def test_railway_artifact_manifest_legacy_zip_isolated(self) -> None:
        self.assertEqual(len(self.manifest["legacyArtifacts"]), 1)
        legacy = self.manifest["legacyArtifacts"][0]
        self.assertEqual(legacy["path"], "deployment/prospecting-extension-1.9.13-alpha.zip")
        self.assertEqual(legacy["status"], "LEGACY — NOT A DEPLOYMENT SOURCE")
        self.assertEqual(legacy["fileCount"], 461)
        self.assertTrue(legacy["missingCanonicalFiles"] or legacy["extraArchiveFiles"])
        self.assertNotIn(legacy["path"], {entry["path"] for entry in self.manifest["files"]})

    def test_railway_artifact_manifest_check_detects_stale_output_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            stale_path = _copy_manifest_inputs(temporary_root)
            stale_path.write_text("{}\n", encoding="utf-8")
            result = generator.main(["--repo-root", str(temporary_root), "--check"])
            self.assertEqual(result, 1)
            self.assertEqual(stale_path.read_text(encoding="utf-8"), "{}\n")

    def test_railway_artifact_manifest_missing_required_file_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(generator.ManifestError, "required artifact missing"):
                generator.validate_required_artifacts(Path(directory))

    def test_railway_artifact_manifest_rejects_traversal_and_symlinks(self) -> None:
        with self.assertRaisesRegex(generator.ManifestError, "escapes repository"):
            generator.normalise_repo_path(REPOSITORY_ROOT.parent / "outside", REPOSITORY_ROOT)
        with mock.patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaisesRegex(generator.ManifestError, "symlink"):
                generator.ensure_not_symlink(REPOSITORY_ROOT / "crm-extension", "crm-extension")

    def test_railway_artifact_manifest_excludes_mutable_governance_status_files(self) -> None:
        paths = {entry["path"] for entry in self.manifest["files"]}
        ratification = generator.RATIFICATION_RECORD_PATH.as_posix()
        self.assertNotIn(ratification, paths)
        self.assertTrue(generator.is_mutable_governance_path(ratification))
        self.assertFalse(
            generator.is_mutable_governance_path(
                generator.DEPLOYMENT_CONTRACT_PATH.as_posix()
            )
        )
        self.assertTrue(
            any("*_RATIFICATION.md" in pattern for pattern in self.manifest["excludedPatterns"])
        )

    def test_railway_artifact_manifest_ratification_status_change_does_not_break_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            manifest_path = _copy_manifest_inputs(temporary_root)
            result = generator.main(["--repo-root", str(temporary_root)])
            self.assertEqual(result, 0)
            before = manifest_path.read_bytes()
            ratification = temporary_root / generator.RATIFICATION_RECORD_PATH
            ratification.parent.mkdir(parents=True, exist_ok=True)
            ratification.write_text(
                "# Temporary ratification mutation\n\nStatus: SYNTHETIC\n",
                encoding="utf-8",
            )
            check = generator.main(["--repo-root", str(temporary_root), "--check"])
            self.assertEqual(check, 0)
            self.assertEqual(manifest_path.read_bytes(), before)
            regenerated = generator.build_manifest(temporary_root)
            self.assertNotIn(
                generator.RATIFICATION_RECORD_PATH.as_posix(),
                {entry["path"] for entry in regenerated["files"]},
            )

    def test_railway_artifact_manifest_contract_technical_change_breaks_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            manifest_path = _copy_manifest_inputs(temporary_root)
            self.assertEqual(generator.main(["--repo-root", str(temporary_root)]), 0)
            before = manifest_path.read_bytes()
            contract = temporary_root / generator.DEPLOYMENT_CONTRACT_PATH
            contract.write_text(
                contract.read_text(encoding="utf-8") + "\n\n<!-- synthetic technical delta -->\n",
                encoding="utf-8",
            )
            check = generator.main(["--repo-root", str(temporary_root), "--check"])
            self.assertEqual(check, 1)
            self.assertEqual(manifest_path.read_bytes(), before)

    def test_railway_artifact_manifest_canonical_artifact_change_breaks_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            manifest_path = _copy_manifest_inputs(temporary_root)
            self.assertEqual(generator.main(["--repo-root", str(temporary_root)]), 0)
            before = manifest_path.read_bytes()
            target = (
                temporary_root
                / "crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/module.json"
            )
            target.write_text(
                target.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            check = generator.main(["--repo-root", str(temporary_root), "--check"])
            self.assertEqual(check, 1)
            self.assertEqual(manifest_path.read_bytes(), before)

    def test_railway_artifact_manifest_release_git_commit_is_authorized_baseline(self) -> None:
        self.assertEqual(generator.release_git_commit(REPOSITORY_ROOT), BASELINE_COMMIT)
        with mock.patch.object(generator, "git_commit", return_value="0" * 40):
            built = generator.build_manifest(REPOSITORY_ROOT)
        self.assertEqual(built["release"]["gitCommit"], BASELINE_COMMIT)


if __name__ == "__main__":
    unittest.main()
