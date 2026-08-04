#!/usr/bin/env python3
"""Generate the deterministic Railway full-application artifact manifest.

This utility is deliberately an inventory and verification tool.  It does not
build an image, run installation hooks, execute provisioning, or contact
Railway.  The manifest is a release input for later, separately authorized
work packages.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
# Authorized source baseline for the DP-WP0 artifact set. This is release
# identity input, not the future closure commit that may contain the generated
# manifest (embedding that commit would create a self-reference cycle).
AUTHORIZED_SOURCE_BASELINE = "6ef712134f581a12a18da5c98691884e73388b78"
DEFAULT_OUTPUT = Path("deployment/railway/full-application-artifact-manifest.json")
MANIFEST_PATH = Path("crm-extension/manifest.json")
INSTALL_HOOK_PATH = Path("crm-extension/scripts/AfterInstall.php")
LEGACY_ZIP_PATH = Path("deployment/prospecting-extension-1.9.13-alpha.zip")
DEPLOYMENT_CONTRACT_PATH = Path("docs/deployment/RAILWAY_DP_WP0_DEPLOYMENT_CONTRACT.md")
RATIFICATION_RECORD_PATH = Path(
    "docs/audit/RAILWAY_DP_WP0_DEPLOYMENT_CONTRACT_RATIFICATION.md"
)

CANONICAL_ROOTS = (
    (Path("crm-extension/files/custom"), "application-code", "canonical-deployment-artifact"),
    (Path("crm-extension/files/client/custom"), "application-code", "canonical-deployment-artifact"),
)
CANDIDATE_ROOTS = (
    (Path("deployment/provisioning"), "provisioning-candidate", "candidate-pending-dp-wp2"),
    (Path("deployment/navigation"), "navigation-candidate", "candidate-pending-dp-wp2"),
)
SINGLE_ARTIFACTS = (
    (MANIFEST_PATH, "extension-identity", "required", "release-identity-only"),
    (INSTALL_HOOK_PATH, "installation-input", "required", "reviewed-input-not-executed"),
    (Path("deployment/railway/Dockerfile"), "railway-infrastructure", "required", "infrastructure-input-not-executed"),
    (Path("deployment/railway/docker-entrypoint-railway.sh"), "railway-infrastructure", "required", "infrastructure-input-not-executed"),
    (Path("deployment/railway/healthcheck.sh"), "railway-infrastructure", "required", "infrastructure-input-not-executed"),
    (Path("deployment/railway/railway.toml"), "railway-infrastructure", "required", "infrastructure-input-not-executed"),
    (Path("docs/deployment/RAILWAY_DP_WP0_DEPLOYMENT_CONTRACT.md"), "deployment-contract", "required", "governance-only"),
    (Path("scripts/generate_railway_artifact_manifest.py"), "validation-contract", "required", "generator-only"),
    (Path("tests/test_railway_dp_wp0_artifact_manifest.py"), "validation-contract", "required", "test-only"),
)

REQUIRED_ARTIFACTS = (
    ("crm-extension/manifest.json", "canonical extension identity"),
    ("crm-extension/scripts/AfterInstall.php", "reviewed installation hook input"),
    ("crm-extension/files/custom/Espo/Modules/AIPlatform/Resources/module.json", "AIPlatform module descriptor"),
    ("crm-extension/files/custom/Espo/Modules/Prospecting/Resources/module.json", "Prospecting module descriptor"),
    ("crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/module.json", "CommercialIntelligence module descriptor"),
    ("crm-extension/files/custom/Espo/Modules/AIPlatform/Resources/metadata/entityDefs/AIRequestLog.json", "AI platform metadata"),
    ("crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/ProspectCandidate.json", "ProspectCandidate metadata"),
    ("crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/ProspectRun.json", "ProspectRun metadata"),
    ("crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/SearchStrategy.json", "SearchStrategy metadata"),
    ("crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/ResearchEvidence.json", "ResearchEvidence metadata"),
    ("crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/AIQualificationInsight.json", "AIQualificationInsight metadata"),
    ("crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/SendExecution.json", "SendExecution metadata"),
    ("crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/ReplySignal.json", "ReplySignal metadata"),
    ("crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/OpportunityCandidate.json", "OpportunityCandidate metadata"),
    ("crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/entityDefs/CommercialBrief.json", "CommercialBrief metadata"),
    ("crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/entityDefs/CommercialInsight.json", "CommercialInsight metadata"),
    ("crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/entityDefs/BusinessReviewContext.json", "BusinessReviewContext metadata"),
    ("crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/entityDefs/DecisionSupportContext.json", "DecisionSupportContext metadata"),
    ("crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/entityDefs/PresentationFeedback.json", "PresentationFeedback metadata"),
    ("crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/entityDefs/HumanReviewDecisionRecord.json", "HumanReviewDecisionRecord metadata"),
    ("crm-extension/files/client/custom/src/controllers/commercial-intelligence-workspace.js", "Commercial Intelligence Workspace controller"),
    ("crm-extension/files/client/custom/src/views/commercial-intelligence/workspace.js", "Commercial Intelligence Workspace view"),
    ("crm-extension/files/client/custom/res/templates/commercial-intelligence/workspace.tpl", "Commercial Intelligence Workspace template"),
    ("crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/routes.json", "Commercial Intelligence Workspace routes"),
    ("crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/app/acl.json", "Prospecting ACL definition"),
    ("crm-extension/files/custom/Espo/Modules/AIPlatform/Resources/metadata/app/acl.json", "AIPlatform ACL definition"),
    ("deployment/railway/Dockerfile", "Railway Dockerfile input"),
    ("deployment/railway/docker-entrypoint-railway.sh", "Railway entrypoint input"),
    ("deployment/railway/healthcheck.sh", "Railway healthcheck input"),
    ("deployment/railway/railway.toml", "Railway configuration input"),
)

EXCLUDED_PATTERNS = (
    ".git/**",
    "**/__pycache__/**",
    "**/*.pyc",
    "data/cache/**",
    "data/logs/**",
    "data/session/**",
    "**/.pytest_cache/**",
    "**/.DS_Store",
    "**/Thumbs.db",
    "**/*~",
    "**/*.tmp",
    "**/*.bak",
    "**/screenshots/**",
    # Mutable governance-status records are not canonical deployment inputs.
    "docs/audit/**/*_RATIFICATION.md",
    "docs/audit/**/*_AMENDMENT.md",
    "docs/audit/**/RAILWAY_DP_WP0_DEPLOYMENT_CONTRACT_RATIFICATION.md",
)
FORBIDDEN_PATTERNS = (
    ".env",
    ".env.*",
    "**/.env",
    "**/.env.*",
    "**/*.pem",
    "**/*.key",
    "**/*.p12",
    "**/*.pfx",
    "**/*.sql",
    "**/*.sql.gz",
    "**/*.dump",
    "**/data/config.php",
    "**/config-internal.php",
    "**/uploads/**",
    "**/cookies/**",
    "**/sessions/**",
)


class ManifestError(RuntimeError):
    """Raised for a manifest contract violation."""


def repository_root_from_script() -> Path:
    return Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalise_repo_path(path: Path, repository_root: Path) -> str:
    try:
        relative = path.relative_to(repository_root)
    except ValueError as error:
        raise ManifestError(f"path escapes repository: {path}") from error
    normalised = relative.as_posix()
    if not normalised or normalised.startswith("/") or ".." in Path(normalised).parts:
        raise ManifestError(f"unsafe repository-relative path: {normalised!r}")
    return normalised


def ensure_not_symlink(path: Path, relative_path: str) -> None:
    # A release manifest must not encode a host-dependent link target.  Rejecting
    # all links is stricter than only rejecting escaping links and deterministic.
    if path.is_symlink():
        raise ManifestError(f"symlink is not permitted in a release artifact: {relative_path}")


def is_forbidden_path(relative_path: str) -> bool:
    lowered = relative_path.lower()
    name = Path(relative_path).name.lower()
    if name == ".env" or name.startswith(".env."):
        return True
    if name in {"config-internal.php", "config.php"} and "/data/" in f"/{lowered}":
        return True
    if any(part in {"uploads", "cookies", "sessions"} for part in Path(lowered).parts):
        return True
    if name.endswith((".pem", ".key", ".p12", ".pfx", ".sql", ".dump")) or name.endswith(".sql.gz"):
        return True
    return False


def is_mutable_governance_path(relative_path: str) -> bool:
    """Return True when a path is a mutable governance-status record.

    These documents may change during ratification without altering deployment
    inputs. They must never appear in the canonical hashed files inventory.
    """
    posix = relative_path.replace("\\", "/")
    name = Path(posix).name
    if not posix.startswith("docs/audit/"):
        return False
    if name.endswith("_RATIFICATION.md") or name.endswith("_AMENDMENT.md"):
        return True
    return posix == RATIFICATION_RECORD_PATH.as_posix()


def _entry(path: Path, repository_root: Path, category: str, required: str, execution_status: str, source_root: str) -> dict[str, Any]:
    relative = normalise_repo_path(path, repository_root)
    ensure_not_symlink(path, relative)
    if is_forbidden_path(relative):
        raise ManifestError(f"forbidden artifact path included: {relative}")
    if is_mutable_governance_path(relative):
        raise ManifestError(f"mutable governance-status path cannot be a release artifact: {relative}")
    return {
        "path": relative,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "category": category,
        "sourceRoot": source_root,
        "required": required,
        "executionStatus": execution_status,
    }


def _iter_root_files(repository_root: Path, root_relative: Path) -> Iterable[Path]:
    root = repository_root / root_relative
    if not root.is_dir():
        raise ManifestError(f"required source root missing: {root_relative.as_posix()}")
    ensure_not_symlink(root, root_relative.as_posix())
    candidates = sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())
    for candidate in candidates:
        relative = normalise_repo_path(candidate, repository_root)
        ensure_not_symlink(candidate, relative)
        if candidate.is_file():
            yield candidate


def validate_required_artifacts(repository_root: Path) -> None:
    for path_text, _purpose in REQUIRED_ARTIFACTS:
        candidate = repository_root / Path(path_text)
        if not candidate.is_file():
            raise ManifestError(f"required artifact missing: {path_text}")
        relative = normalise_repo_path(candidate, repository_root)
        ensure_not_symlink(candidate, relative)
        if is_forbidden_path(relative):
            raise ManifestError(f"required artifact is forbidden: {path_text}")


def read_extension_identity(repository_root: Path) -> dict[str, str]:
    identity_path = repository_root / MANIFEST_PATH
    try:
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestError(f"cannot parse extension manifest: {MANIFEST_PATH.as_posix()}") from error
    name = identity.get("extensionName") or identity.get("name")
    version = identity.get("version")
    if not isinstance(name, str) or not name:
        raise ManifestError("extension manifest has no extension name")
    if not isinstance(version, str) or not version:
        raise ManifestError("extension manifest has no version")
    return {"extensionName": name, "extensionVersion": version}


def git_commit(repository_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
            capture_output=True,
            check=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise ManifestError("cannot determine Git commit for release identity") from error
    commit = result.stdout.strip()
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise ManifestError(f"unexpected Git commit identity: {commit!r}")
    return commit


def release_git_commit(repository_root: Path) -> str:
    """Return the authorized source baseline for DP-WP0 release identity.

    ``release.gitCommit`` records the authorized source baseline used to
    generate this artifact set. It deliberately does not embed the future
    closure commit that may contain the generated manifest.
    """
    del repository_root  # Identity is contract-authorized, not HEAD-derived.
    return AUTHORIZED_SOURCE_BASELINE


def _zip_entry_bytes(archive: zipfile.ZipFile, name: str) -> bytes | None:
    try:
        return archive.read(name)
    except KeyError:
        return None


def legacy_zip_record(repository_root: Path, canonical_code_paths: set[str]) -> dict[str, Any]:
    archive_path = repository_root / LEGACY_ZIP_PATH
    if not archive_path.is_file():
        raise ManifestError(f"required legacy ZIP missing: {LEGACY_ZIP_PATH.as_posix()}")
    archive_relative = normalise_repo_path(archive_path, repository_root)
    ensure_not_symlink(archive_path, archive_relative)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            entries = sorted(entry.filename for entry in archive.infolist() if not entry.is_dir())
            manifest_bytes = _zip_entry_bytes(archive, "manifest.json")
            hook_bytes = _zip_entry_bytes(archive, "scripts/AfterInstall.php")
    except (OSError, zipfile.BadZipFile) as error:
        raise ManifestError(f"cannot inspect legacy ZIP: {archive_relative}") from error

    embedded_version: str | None = None
    if manifest_bytes is not None:
        try:
            embedded = json.loads(manifest_bytes.decode("utf-8"))
            value = embedded.get("version")
            embedded_version = value if isinstance(value, str) else None
        except (UnicodeDecodeError, json.JSONDecodeError):
            embedded_version = None

    archive_code_paths = {entry for entry in entries if entry.startswith("files/")}
    expected_archive_paths = {path.removeprefix("crm-extension/") for path in canonical_code_paths}
    missing = sorted(expected_archive_paths - archive_code_paths)
    extra = sorted(archive_code_paths - expected_archive_paths)
    current_manifest = (repository_root / MANIFEST_PATH).read_bytes()
    current_hook = (repository_root / INSTALL_HOOK_PATH).read_bytes()
    contains_c25 = any("CommercialIntelligence/" in entry for entry in entries)

    return {
        "path": archive_relative,
        "sha256": sha256_file(archive_path),
        "bytes": archive_path.stat().st_size,
        "fileCount": len(entries),
        "embeddedExtensionVersion": embedded_version,
        "containsCurrentManifest": manifest_bytes == current_manifest,
        "containsCurrentInstallHook": hook_bytes == current_hook,
        "containsC25CommercialIntelligence": contains_c25,
        "canonicalCodeFileCount": len(expected_archive_paths),
        "archiveCodeFileCount": len(archive_code_paths),
        "missingCanonicalFiles": missing,
        "extraArchiveFiles": extra,
        "status": "LEGACY — NOT A DEPLOYMENT SOURCE",
        "reason": "Historic ZIP inventory differs from canonical repository code and is not a verified release artifact.",
        "replacementPolicy": "DP-WP1 may create a new package only from a regenerated manifest after separate authorization.",
    }


def build_manifest(repository_root: Path, git_commit_value: str | None = None) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    validate_required_artifacts(repository_root)
    identity = read_extension_identity(repository_root)
    entries: list[dict[str, Any]] = []

    for root_relative, category, execution_status in CANONICAL_ROOTS:
        source_root = root_relative.as_posix()
        for candidate in _iter_root_files(repository_root, root_relative):
            entries.append(_entry(candidate, repository_root, category, "required", execution_status, source_root))

    for root_relative, category, execution_status in CANDIDATE_ROOTS:
        source_root = root_relative.as_posix()
        for candidate in _iter_root_files(repository_root, root_relative):
            entries.append(_entry(candidate, repository_root, category, "optional", execution_status, source_root))

    for relative_path, category, required, execution_status in SINGLE_ARTIFACTS:
        candidate = repository_root / relative_path
        if not candidate.is_file():
            raise ManifestError(f"required single artifact missing: {relative_path.as_posix()}")
        entries.append(_entry(candidate, repository_root, category, required, execution_status, relative_path.parent.as_posix()))

    entries.sort(key=lambda entry: entry["path"])
    paths = [entry["path"] for entry in entries]
    if len(paths) != len(set(paths)):
        raise ManifestError("duplicate artifact path detected")
    if paths != sorted(paths):
        raise ManifestError("artifact paths are not sorted")

    canonical_code_paths = {entry["path"] for entry in entries if entry["category"] == "application-code"}
    return {
        "schemaVersion": SCHEMA_VERSION,
        "release": {
            "extensionName": identity["extensionName"],
            "extensionVersion": identity["extensionVersion"],
            "gitCommit": git_commit_value or release_git_commit(repository_root),
            "deploymentModel": "deterministic-overlay",
        },
        "canonicalRoots": [
            {"path": root.as_posix(), "classification": classification}
            for root, _category, classification in CANONICAL_ROOTS
        ],
        "requiredArtifacts": [
            {"path": path, "purpose": purpose} for path, purpose in REQUIRED_ARTIFACTS
        ],
        "files": entries,
        "excludedPatterns": list(EXCLUDED_PATTERNS),
        "forbiddenPatterns": list(FORBIDDEN_PATTERNS),
        "legacyArtifacts": [legacy_zip_record(repository_root, canonical_code_paths)],
        "executionBoundary": "Inventory inclusion does not authorize execution, installation, provisioning, migration, deployment, or runtime mutation.",
    }


def render_manifest(manifest: dict[str, Any]) -> bytes:
    return (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def resolve_output_path(repository_root: Path, output_argument: str | None) -> Path:
    output_relative = Path(output_argument) if output_argument else DEFAULT_OUTPUT
    if output_relative.is_absolute() or ".." in output_relative.parts:
        raise ManifestError("output path must be repository-relative and traversal-free")
    output = repository_root / output_relative
    normalise_repo_path(output, repository_root)
    return output


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary_path = Path(handle.name)
        handle.write(payload)
    try:
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def check_manifest(path: Path, payload: bytes) -> bool:
    try:
        return path.read_bytes() == payload
    except FileNotFoundError:
        return False


def parse_args(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the current manifest differs from generated output")
    parser.add_argument("--repo-root", help="repository root for testing; defaults to the script's parent repository")
    parser.add_argument("--output", help="repository-relative manifest output path")
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    args = parse_args(arguments if arguments is not None else sys.argv[1:])
    repository_root = Path(args.repo_root).resolve() if args.repo_root else repository_root_from_script()
    try:
        output_path = resolve_output_path(repository_root, args.output)
        manifest = build_manifest(repository_root)
        payload = render_manifest(manifest)
        if args.check:
            if not check_manifest(output_path, payload):
                raise ManifestError(f"manifest is stale or missing: {normalise_repo_path(output_path, repository_root)}")
            return 0
        atomic_write(output_path, payload)
        return 0
    except ManifestError as error:
        print(f"artifact manifest error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
