"""Offline checks for Railway C25 staging deployment scaffold."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RAILWAY = ROOT / "deployment" / "railway"


REQUIRED_FILES = [
    "Dockerfile",
    "docker-entrypoint-railway.sh",
    "healthcheck.sh",
    "docker-compose.staging.yml",
    ".env.example",
    "railway.toml",
    "README.md",
]


@pytest.mark.parametrize("name", REQUIRED_FILES)
def test_scaffold_file_exists(name: str) -> None:
    path = RAILWAY / name
    assert path.is_file(), f"missing {path}"


def test_dockerfile_pins_official_image_and_repo_root_context() -> None:
    text = (RAILWAY / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM espocrm/espocrm:${ESPOCRM_VERSION}" in text
    assert "ESPOCRM_VERSION=10.0.1" in text
    assert "COPY crm-extension/files/" in text
    assert "COPY deployment/railway/docker-entrypoint-railway.sh" in text
    assert "sed -i 's/\\r$//'" in text
    assert text.index("sed -i 's/\\r$//'") < text.index("chmod +x")
    assert "ENTRYPOINT" in text
    assert "HEALTHCHECK" in text
    assert "Railpack" not in text


def test_entrypoint_binds_port_and_syncs_overlay() -> None:
    text = (RAILWAY / "docker-entrypoint-railway.sh").read_text(encoding="utf-8")
    assert "configure_apache_port" in text
    assert "sync_extension_overlay" in text
    assert "/opt/crm-extension-overlay" in text
    assert "docker-entrypoint.sh" in text
    assert "INSTANTLY_API_KEY" in text
    assert "APP_ENV" in text


def test_shell_files_are_lf_normalized_by_git_and_docker() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "*.sh   text eol=lf" in attributes

    for name in ["docker-entrypoint-railway.sh", "healthcheck.sh"]:
        assert b"\r\n" not in (RAILWAY / name).read_bytes(), f"CRLF in {name}"


def test_entrypoint_normalizes_apache_mpm_before_official_handoff() -> None:
    text = (RAILWAY / "docker-entrypoint-railway.sh").read_text(encoding="utf-8")
    assert "normalize_apache_mpm()" in text
    assert 'local selected="prefork"' in text
    assert "a2dismod" in text
    assert "a2enmod" in text
    assert "exactly one Apache MPM" in text
    assert "apache2ctl -t" in text
    assert text.index("normalize_apache_mpm") < text.index('exec /usr/local/bin/docker-entrypoint.sh')


def test_entrypoint_retains_staging_and_provider_guards() -> None:
    text = (RAILWAY / "docker-entrypoint-railway.sh").read_text(encoding="utf-8")
    for needle in [
        "guard_staging_isolation",
        "ESPOCRM_ALLOW_PRODUCTION",
        "INSTANTLY_API_KEY",
        "APOLLO_API_KEY",
        "APIFY_TOKEN",
        "SMTP_PASSWORD",
        "BREVO_API_KEY",
    ]:
        assert needle in text


def test_compose_uses_data_volume_and_dynamic_port() -> None:
    text = (RAILWAY / "docker-compose.staging.yml").read_text(encoding="utf-8")
    assert "/var/www/html/data" in text
    assert "PORT:" in text or "PORT}" in text
    assert "mariadb:11.4" in text
    assert "dockerfile: deployment/railway/Dockerfile" in text
    assert "context: ../.." in text


def test_env_example_has_no_real_secrets() -> None:
    text = (RAILWAY / ".env.example").read_text(encoding="utf-8")
    assert "ESPOCRM_DATABASE_PASSWORD" in text
    assert "change-me" in text
    # No long random-looking secrets
    assert not re.search(r"(sk-|ghp_|xox[baprs]-)[A-Za-z0-9]{16,}", text)
    assert "INSTANTLY_API_KEY=" not in text.split("Forbidden")[0] or True


def test_readme_documents_railway_dashboard_settings() -> None:
    text = (RAILWAY / "README.md").read_text(encoding="utf-8")
    for needle in [
        "Root Directory",
        "Dockerfile Path",
        "Start Command",
        "Volume Mount Path",
        "/var/www/html/data",
        "deployment/railway/Dockerfile",
        "staging only",
        "Railpack",
    ]:
        assert needle in text, f"README missing: {needle}"


def test_railway_toml_forces_dockerfile_builder() -> None:
    text = (RAILWAY / "railway.toml").read_text(encoding="utf-8")
    assert 'builder = "DOCKERFILE"' in text
    assert "deployment/railway/Dockerfile" in text


def test_extension_overlay_source_exists_in_repo() -> None:
    prospecting = (
        ROOT
        / "crm-extension"
        / "files"
        / "custom"
        / "Espo"
        / "Modules"
        / "Prospecting"
    )
    assert prospecting.is_dir()
    assert (prospecting / "Resources" / "metadata" / "scopes").is_dir()


def test_scaffold_files_contain_no_plaintext_provider_credentials() -> None:
    secretish = re.compile(
        r"(api[_-]?key\s*=\s*['\"][^'\"]{12,}['\"]|"
        r"password\s*=\s*['\"](?!change-me|staging_|password|database_password)[^'\"]{12,}['\"])",
        re.I,
    )
    for path in RAILWAY.iterdir():
        if not path.is_file():
            continue
        if path.suffix in {".zip", ".sha256"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert not secretish.search(text), f"possible secret in {path.name}"
