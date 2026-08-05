"""Static safety checks for the DP-WP5 Railway execution scaffold."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import unittest
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAILWAY = ROOT / "deployment" / "railway"
FROZEN_MANIFEST_SHA256 = "9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649"


def load_verifier():
    spec = importlib.util.spec_from_file_location(
        "dp_wp5_verifier", RAILWAY / "verify_deployment_identity.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RailwayExecutionBoundaryTests(unittest.TestCase):
    def test_required_execution_boundary_files_exist(self) -> None:
        for name in (
            "Dockerfile",
            "docker-entrypoint-railway.sh",
            "healthcheck.sh",
            "docker-compose.staging.yml",
            ".env.example",
            "railway.toml",
            "README.md",
            "verify_deployment_identity.py",
        ):
            self.assertTrue((RAILWAY / name).is_file(), name)

    def test_dockerfile_requires_immutable_base_and_binds_dp_wp0_overlay(self) -> None:
        text = (RAILWAY / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("ARG ESPOCRM_BASE_IMAGE\nFROM ${ESPOCRM_BASE_IMAGE}", text)
        self.assertNotIn("FROM espocrm/espocrm:", text)
        self.assertIn("grep -Eq '^.+@sha256:[0-9a-f]{64}$'", text)
        self.assertIn(
            'sha256sum /opt/dp-wp0/full-application-artifact-manifest.json', text
        )
        self.assertIn('= "${DP_WP0_MANIFEST_SHA256}"', text)
        for binding in (
            f"ARG DP_WP0_MANIFEST_SHA256={FROZEN_MANIFEST_SHA256}",
            "ARG DP_WP0_SOURCE_COMMIT=6ef712134f581a12a18da5c98691884e73388b78",
            "COPY crm-extension/files/ /opt/crm-extension-overlay/",
            "COPY crm-extension/manifest.json /opt/dp-wp0/extension-manifest.json",
            "COPY deployment/railway/full-application-artifact-manifest.json /opt/dp-wp0/full-application-artifact-manifest.json",
            "io.chitu.dp-wp0.manifest-sha256",
            "io.chitu.dp-wp0.source-commit",
        ):
            self.assertIn(binding, text)

    def test_entrypoint_is_limited_to_guards_port_and_service_start(self) -> None:
        text = (RAILWAY / "docker-entrypoint-railway.sh").read_text(encoding="utf-8")
        for allowed in (
            "guard_staging_isolation",
            "reject_full_application_volume",
            "configure_apache_port",
            'exec "$@"',
        ):
            self.assertIn(allowed, text)
        lowered = text.lower()
        for forbidden in (
            "docker-entrypoint.sh",
            "bin/command",
            "install",
            "migrat",
            "rebuild",
            "afterinstall",
            "hook",
            "rsync",
            "cp -a",
            "rm -rf",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_healthcheck_is_read_only_http_availability_only(self) -> None:
        text = (RAILWAY / "healthcheck.sh").read_text(encoding="utf-8").lower()
        self.assertIn("curl", text)
        for forbidden in (
            "bin/command",
            "install",
            "migrat",
            "rebuild",
            "afterinstall",
            "hook",
            "rm ",
            "sed ",
            "touch ",
        ):
            self.assertNotIn(forbidden, text)

    def test_volume_policy_allows_data_only_and_rejects_root_masking(self) -> None:
        entrypoint = (RAILWAY / "docker-entrypoint-railway.sh").read_text(encoding="utf-8")
        compose = (RAILWAY / "docker-compose.staging.yml").read_text(encoding="utf-8")
        self.assertIn('grep -qxE "/var/www/html"', entrypoint)
        self.assertIn("/var/www/html/data", compose)
        self.assertNotIn("/var/www/html/custom", compose)
        self.assertNotIn("/var/www/html/client/custom", compose)
        self.assertNotIn("- espocrm-staging-data:/var/www/html\n", compose)

    def test_railway_has_no_release_or_lifecycle_command(self) -> None:
        text = "\n".join(
            line
            for line in (RAILWAY / "railway.toml").read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("#")
        ).lower()
        self.assertIn('builder = "dockerfile"', text)
        for forbidden in ("releasecommand", "release_command", "migration", "install", "rebuild"):
            self.assertNotIn(forbidden, text)

    def test_identity_verifier_accepts_matching_tiny_overlay(self) -> None:
        verifier = load_verifier()
        with self.subTest("matching manifest"):
            from tempfile import TemporaryDirectory

            with TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                overlay = root / "crm-extension" / "files" / "custom" / "example.txt"
                overlay.parent.mkdir(parents=True)
                overlay.write_text("verified bytes\n", encoding="utf-8")
                extension_manifest = root / "crm-extension" / "manifest.json"
                extension_manifest.write_text(
                    json.dumps(
                        {
                            "name": "Chitu Prospecting Integration",
                            "extensionName": "Chitu Prospecting Integration",
                            "version": "1.9.13-alpha",
                        }
                    ),
                    encoding="utf-8",
                )
                manifest = {
                    "release": {
                        "extensionName": "Chitu Prospecting Integration",
                        "extensionVersion": "1.9.13-alpha",
                        "gitCommit": "6ef712134f581a12a18da5c98691884e73388b78",
                    },
                    "files": [
                        {
                            "path": "crm-extension/files/custom/example.txt",
                            "sha256": sha256(overlay.read_bytes()).hexdigest(),
                        }
                    ],
                }
                manifest_path = root / "manifest.json"
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                self.assertEqual(
                    verifier.load_manifest(
                        root,
                        manifest_path,
                        sha256(manifest_path.read_bytes()).hexdigest(),
                    ),
                    manifest,
                )

    def test_identity_verifier_rejects_manifest_mismatch(self) -> None:
        verifier = load_verifier()
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temporary_directory:
            manifest_path = Path(temporary_directory) / "manifest.json"
            manifest_path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                verifier.load_manifest(Path(temporary_directory), manifest_path, "0" * 64)

    def test_frozen_manifest_checksum_passes_and_changed_manifest_fails(self) -> None:
        verifier = load_verifier()
        frozen = subprocess.check_output(
            ["git", "show", "HEAD:deployment/railway/full-application-artifact-manifest.json"],
            cwd=ROOT,
        )
        self.assertEqual(sha256(frozen).hexdigest(), FROZEN_MANIFEST_SHA256)

        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temporary_directory:
            manifest_path = Path(temporary_directory) / "manifest.json"
            manifest_path.write_bytes(frozen)
            verifier.verify_manifest_checksum(manifest_path, FROZEN_MANIFEST_SHA256)

            manifest_path.write_bytes(frozen + b"\nchanged")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                verifier.verify_manifest_checksum(manifest_path, FROZEN_MANIFEST_SHA256)

    def test_identity_verifier_requires_immutable_digests(self) -> None:
        verifier = load_verifier()
        verifier.require_digest("sha256:" + "a" * 64, "base image digest")
        with self.assertRaisesRegex(ValueError, "immutable"):
            verifier.require_digest("espocrm/espocrm:10.0.1", "base image digest")


if __name__ == "__main__":
    unittest.main()
