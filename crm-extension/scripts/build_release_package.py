#!/usr/bin/env python3
"""Build and verify the deterministic EspoCRM extension release archive.

The script is deliberately anchored to its own location.  It can therefore be
run from the repository root, the extension directory, or an automation
workspace without changing which files are packaged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import date
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parent
EXTENSION_ROOT = SCRIPT_ROOT.parent
REPOSITORY_ROOT = EXTENSION_ROOT.parent
MANIFEST_PATH = EXTENSION_ROOT / "manifest.json"
FILES_ROOT = EXTENSION_ROOT / "files"
DEPLOYMENT_ROOT = REPOSITORY_ROOT / "deployment"
ZIP_COMPRESSION = zipfile.ZIP_DEFLATED
ZIP_COMPRESSLEVEL = 9
ZIP_FILE_MODE = 0o100644


class ReleaseIntegrityError(ValueError):
    """A release archive or release input violates the package contract."""


def load_manifest() -> dict[str, object]:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseIntegrityError(f"Cannot read manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ReleaseIntegrityError("Manifest must contain a JSON object")
    for field in ("version", "releaseDate"):
        if not isinstance(manifest.get(field), str) or not manifest[field]:
            raise ReleaseIntegrityError(f"Manifest requires a non-empty {field}")
    return manifest


def canonical_archive_path(manifest: dict[str, object]) -> Path:
    return DEPLOYMENT_ROOT / f"prospecting-extension-{manifest['version']}.zip"


def sidecar_path(archive_path: Path) -> Path:
    return archive_path.with_name(f"{archive_path.name}.sha256")


def release_timestamp(manifest: dict[str, object]) -> tuple[int, int, int, int, int, int]:
    try:
        release_date = date.fromisoformat(str(manifest["releaseDate"]))
    except ValueError as exc:
        raise ReleaseIntegrityError("Manifest releaseDate must be ISO YYYY-MM-DD") from exc
    if release_date.year < 1980:
        raise ReleaseIntegrityError("Manifest releaseDate must be 1980 or later for ZIP timestamps")
    return (release_date.year, release_date.month, release_date.day, 0, 0, 0)


def source_entries() -> dict[str, Path]:
    if not MANIFEST_PATH.is_file():
        raise ReleaseIntegrityError(f"Missing package manifest: {MANIFEST_PATH}")
    if not FILES_ROOT.is_dir():
        raise ReleaseIntegrityError(f"Missing package source directory: {FILES_ROOT}")

    entries = {"manifest.json": MANIFEST_PATH}
    for path in sorted(FILES_ROOT.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_file():
            entries[path.relative_to(EXTENSION_ROOT).as_posix()] = path
    return entries


def validate_archive_name(archive_path: Path, manifest: dict[str, object], allow_noncanonical_output: bool) -> None:
    expected = canonical_archive_path(manifest).name
    if not allow_noncanonical_output and archive_path.name != expected:
        raise ReleaseIntegrityError(
            f"Release archive must be named {expected}; use --allow-noncanonical-output only for isolated test output"
        )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_sidecar(archive_path: Path) -> str:
    digest = sha256(archive_path)
    sidecar_path(archive_path).write_text(f"{digest}  {archive_path.name}\n", encoding="ascii", newline="\n")
    return digest


def build(archive_path: Path, *, allow_noncanonical_output: bool = False) -> str:
    manifest = load_manifest()
    validate_archive_name(archive_path, manifest, allow_noncanonical_output)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = release_timestamp(manifest)
    entries = source_entries()

    with zipfile.ZipFile(
        archive_path,
        mode="w",
        compression=ZIP_COMPRESSION,
        compresslevel=ZIP_COMPRESSLEVEL,
        strict_timestamps=True,
    ) as archive:
        for entry_name in sorted(entries):
            info = zipfile.ZipInfo(entry_name, date_time=timestamp)
            info.compress_type = ZIP_COMPRESSION
            info.external_attr = ZIP_FILE_MODE << 16
            info.create_system = 3
            archive.writestr(info, entries[entry_name].read_bytes(), compress_type=ZIP_COMPRESSION, compresslevel=ZIP_COMPRESSLEVEL)
    return write_sidecar(archive_path)


def read_sidecar(archive_path: Path) -> str:
    path = sidecar_path(archive_path)
    if not path.is_file():
        raise ReleaseIntegrityError(f"Missing SHA-256 sidecar: {path}")
    expected = f"{sha256(archive_path)}  {archive_path.name}\n"
    actual = path.read_text(encoding="ascii")
    if actual != expected:
        raise ReleaseIntegrityError(f"SHA-256 sidecar does not match {archive_path.name}")
    return expected.split("  ", 1)[0]


def check(archive_path: Path, *, allow_noncanonical_output: bool = False) -> str:
    manifest = load_manifest()
    validate_archive_name(archive_path, manifest, allow_noncanonical_output)
    if not archive_path.is_file():
        raise ReleaseIntegrityError(f"Missing release archive: {archive_path}")
    expected_entries = source_entries()
    try:
        with zipfile.ZipFile(archive_path) as archive:
            corrupt_entry = archive.testzip()
            if corrupt_entry is not None:
                raise ReleaseIntegrityError(f"Corrupt ZIP member: {corrupt_entry}")
            actual_names = [info.filename for info in archive.infolist() if not info.is_dir()]
            if len(actual_names) != len(set(actual_names)):
                raise ReleaseIntegrityError("Release archive contains duplicate entries")
            actual_set = set(actual_names)
            expected_set = set(expected_entries)
            if actual_set != expected_set:
                missing = sorted(expected_set - actual_set)
                extras = sorted(actual_set - expected_set)
                raise ReleaseIntegrityError(f"Release archive entries differ; missing={missing}, extras={extras}")
            for entry_name, source_path in expected_entries.items():
                if archive.read(entry_name) != source_path.read_bytes():
                    raise ReleaseIntegrityError(f"Release archive bytes differ for {entry_name}")
            if json.loads(archive.read("manifest.json")) != manifest:
                raise ReleaseIntegrityError("Release archive manifest does not match source manifest")
    except zipfile.BadZipFile as exc:
        raise ReleaseIntegrityError(f"Invalid ZIP archive: {exc}") from exc
    return read_sidecar(archive_path)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify an existing package and SHA-256 sidecar")
    parser.add_argument("--output", type=Path, help="archive path; defaults to the canonical deployment artifact")
    parser.add_argument(
        "--allow-noncanonical-output",
        action="store_true",
        help="allow a noncanonical archive filename for an isolated temporary test artifact",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        manifest = load_manifest()
        archive_path = (args.output or canonical_archive_path(manifest)).resolve()
        digest = check(archive_path, allow_noncanonical_output=args.allow_noncanonical_output) if args.check else build(
            archive_path, allow_noncanonical_output=args.allow_noncanonical_output
        )
    except ReleaseIntegrityError as exc:
        print(f"release integrity error: {exc}", file=sys.stderr)
        return 2
    print(f"{archive_path} {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
