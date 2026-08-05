#!/usr/bin/env python3
"""Offline DP-WP5 identity verifier; it does not build or run an image."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


EXPECTED_RELEASE = {
    "extensionName": "Chitu Prospecting Integration",
    "extensionVersion": "1.9.13-alpha",
    "gitCommit": "6ef712134f581a12a18da5c98691884e73388b78",
}
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_digest(value: str, label: str) -> None:
    if not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{label} must be an immutable sha256:<64 lowercase hex> digest")


def verify_manifest_checksum(manifest_path: Path, expected_hash: str) -> None:
    if sha256(manifest_path) != expected_hash:
        raise ValueError("manifest SHA-256 does not match the supplied frozen identity")


def load_manifest(repo_root: Path, manifest_path: Path, expected_hash: str) -> dict:
    verify_manifest_checksum(manifest_path, expected_hash)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    release = manifest.get("release")
    if not isinstance(release, dict):
        raise ValueError("manifest release identity is absent")
    for key, expected in EXPECTED_RELEASE.items():
        if release.get(key) != expected:
            raise ValueError(f"manifest release {key} does not match the approved identity")

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("manifest file inventory is absent")
    for entry in files:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError("manifest contains an invalid file entry")
        path = (repo_root / entry["path"]).resolve()
        try:
            path.relative_to(repo_root.resolve())
        except ValueError as exc:
            raise ValueError(f"manifest path escapes the repository: {entry['path']}") from exc
        if not path.is_file() or sha256(path) != entry.get("sha256"):
            raise ValueError(f"overlay file does not match manifest: {entry['path']}")

    extension_manifest = repo_root / "crm-extension" / "manifest.json"
    try:
        extension_identity = json.loads(extension_manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("extension manifest is unreadable") from exc
    if (
        extension_identity.get("name") != EXPECTED_RELEASE["extensionName"]
        or extension_identity.get("extensionName") != EXPECTED_RELEASE["extensionName"]
        or extension_identity.get("version") != EXPECTED_RELEASE["extensionVersion"]
    ):
        raise ValueError("extension manifest does not match the approved identity")
    return manifest


def verify_dockerfile(dockerfile: Path, manifest_hash: str) -> str:
    text = dockerfile.read_text(encoding="utf-8")
    required = (
        "ARG ESPOCRM_BASE_IMAGE\nFROM ${ESPOCRM_BASE_IMAGE}",
        "COPY crm-extension/files/ /opt/crm-extension-overlay/",
        "COPY crm-extension/manifest.json /opt/dp-wp0/extension-manifest.json",
        "COPY deployment/railway/full-application-artifact-manifest.json /opt/dp-wp0/full-application-artifact-manifest.json",
        f"ARG DP_WP0_MANIFEST_SHA256={manifest_hash}",
        "io.chitu.dp-wp0.manifest-sha256=\"${DP_WP0_MANIFEST_SHA256}\"",
        "io.chitu.dp-wp0.source-commit=\"${DP_WP0_SOURCE_COMMIT}\"",
    )
    for item in required:
        if item not in text:
            raise ValueError(f"Dockerfile binding is missing: {item}")
    return sha256(dockerfile)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--base-image-digest", required=True)
    parser.add_argument("--built-image-digest", required=True)
    args = parser.parse_args()

    try:
        require_digest(args.base_image_digest, "base image digest")
        require_digest(args.built_image_digest, "built image digest")
        repo_root = args.repo_root.resolve()
        manifest_path = args.manifest.resolve()
        manifest = load_manifest(repo_root, manifest_path, args.manifest_sha256)
        dockerfile_hash = verify_dockerfile(
            repo_root / "deployment" / "railway" / "Dockerfile",
            args.manifest_sha256,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"DP-WP5 identity verification failed: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "verified": True,
                "manifestSha256": args.manifest_sha256,
                "sourceCommit": manifest["release"]["gitCommit"],
                "extensionName": manifest["release"]["extensionName"],
                "extensionVersion": manifest["release"]["extensionVersion"],
                "extensionManifestSha256": sha256(repo_root / "crm-extension" / "manifest.json"),
                "dockerfileSha256": dockerfile_hash,
                "baseImageDigest": args.base_image_digest,
                "builtImageDigest": args.built_image_digest,
                "overlayFileCount": len(manifest["files"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
