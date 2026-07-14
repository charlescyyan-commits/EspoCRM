"""Safety-first stdlib runtime REST harness for local EspoCRM tests."""
from __future__ import annotations

import json
import os
import re
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


EXIT_PASS = 0
EXIT_TEST_FAILURE = 1
EXIT_CONFIGURATION = 2
EXIT_MISSING_DEPENDENCY = 3
EXIT_CLEANUP_INCOMPLETE = 4
EXIT_SAFETY_BLOCKED = 5
DEFAULT_ALLOWED_HOSTS = {"localhost", "127.0.0.1", "::1"}
PRODUCTION_HOST_TOKENS = ("prod", "production", "railway", "render", "heroku", "azurewebsites")
MARKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{3,40}$")
RUN_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{3,40}_\d{8}T\d{6}Z_[0-9A-F]{8}$")


class RuntimeHarnessError(RuntimeError):
    exit_code = EXIT_TEST_FAILURE


class RuntimeConfigurationError(RuntimeHarnessError):
    exit_code = EXIT_CONFIGURATION


class RuntimeDependencyError(RuntimeHarnessError):
    exit_code = EXIT_MISSING_DEPENDENCY


class RuntimeSafetyError(RuntimeHarnessError):
    exit_code = EXIT_SAFETY_BLOCKED


class RuntimeCleanupError(RuntimeHarnessError):
    exit_code = EXIT_CLEANUP_INCOMPLETE


@dataclass(frozen=True)
class RuntimeConfig:
    base_url: str
    api_key: str
    prefix: str
    timeout: float
    allowed_hosts: frozenset[str]

    @classmethod
    def from_environment(cls, env: Mapping[str, str] | None = None) -> "RuntimeConfig":
        env = env if env is not None else os.environ
        if env.get("ESPOCRM_RUNTIME_TEST_ENABLED", "") != "true":
            raise RuntimeSafetyError("Runtime tests are disabled; set ESPOCRM_RUNTIME_TEST_ENABLED=true explicitly.")
        base_url = env.get("ESPOCRM_BASE_URL", "").strip()
        api_key = env.get("ESPOCRM_API_KEY", "").strip()
        if not base_url:
            raise RuntimeDependencyError("ESPOCRM_BASE_URL is required.")
        if not api_key:
            raise RuntimeDependencyError("ESPOCRM_API_KEY is required.")
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise RuntimeConfigurationError("ESPOCRM_BASE_URL must be an absolute HTTP(S) URL.")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise RuntimeSafetyError("ESPOCRM_BASE_URL must not contain credentials, query parameters, or fragments.")
        host = parsed.hostname.lower()
        configured_hosts = {item.strip().lower() for item in env.get("ESPOCRM_RUNTIME_ALLOWED_HOSTS", "").split(",") if item.strip()}
        allowed_hosts = frozenset(DEFAULT_ALLOWED_HOSTS | configured_hosts)
        if host not in allowed_hosts:
            raise RuntimeSafetyError("Runtime target host is not local or explicitly allowlisted.")
        if any(token in host for token in PRODUCTION_HOST_TOKENS):
            raise RuntimeSafetyError("Runtime target resembles a production environment.")
        prefix = env.get("ESPOCRM_RUNTIME_TEST_PREFIX", "CHITU_RT").strip()
        if not MARKER_PATTERN.fullmatch(prefix):
            raise RuntimeConfigurationError("ESPOCRM_RUNTIME_TEST_PREFIX has an unsafe format.")
        try:
            timeout = float(env.get("ESPOCRM_RUNTIME_TEST_TIMEOUT", "20"))
        except ValueError as error:
            raise RuntimeConfigurationError("ESPOCRM_RUNTIME_TEST_TIMEOUT must be numeric.") from error
        if not 1 <= timeout <= 120:
            raise RuntimeConfigurationError("ESPOCRM_RUNTIME_TEST_TIMEOUT must be between 1 and 120 seconds.")
        return cls(base_url.rstrip("/"), api_key, prefix, timeout, allowed_hosts)


def new_run_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{secrets.token_hex(4).upper()}"


def validate_run_id(run_id: str) -> str:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise RuntimeConfigurationError("Runtime run ID has an unsafe format.")
    return run_id


@dataclass
class ApiResponse:
    status: int
    body: Any


class RuntimeRestClient:
    """Small REST client that never includes credentials in error text."""

    def __init__(self, config: RuntimeConfig, opener: Callable[..., Any] = urlopen) -> None:
        self.config = config
        self._opener = opener

    def request(self, method: str, path: str, payload: Mapping[str, Any] | None = None, query: Mapping[str, Any] | None = None, *, api_key: str | None = None) -> ApiResponse:
        url = f"{self.config.base_url}/{path.lstrip('/')}"
        if query:
            url = f"{url}?{urlencode(query)}"
        headers = {"Accept": "application/json", "X-Api-Key": api_key if api_key is not None else self.config.api_key}
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with self._opener(request, timeout=self.config.timeout) as response:
                return ApiResponse(response.status, self._decode_json(response.read()))
        except HTTPError as error:
            return ApiResponse(error.code, self._decode_json(error.read()))
        except (URLError, TimeoutError, OSError) as error:
            raise RuntimeHarnessError(f"{method} {self._safe_path(path)} failed: {error.__class__.__name__}.") from error

    @staticmethod
    def _decode_json(raw: bytes) -> Any:
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeHarnessError("REST response was not valid JSON.") from error

    @staticmethod
    def _safe_path(path: str) -> str:
        return path.split("?", 1)[0]


@dataclass
class Fixture:
    runId: str
    entity: str
    recordId: str
    marker: str
    createdBySuite: str
    cleanupRequired: bool = True
    cleanupResult: str = "PENDING"
    cleanupError: str | None = None


class FixtureRegistry:
    def __init__(self, path: Path, run_id: str) -> None:
        self.path = path
        self.run_id = run_id
        self.fixtures: list[Fixture] = []

    @classmethod
    def create(cls, results_root: Path, run_id: str) -> "FixtureRegistry":
        validate_run_id(run_id)
        registry = cls(results_root / f"runtime-fixtures-{run_id}.json", run_id)
        registry._persist()
        return registry

    @classmethod
    def load(cls, path: Path, run_id: str) -> "FixtureRegistry":
        validate_run_id(run_id)
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("runId") != run_id:
            raise RuntimeSafetyError("Registry run ID does not match the requested cleanup run.")
        registry = cls(path, run_id)
        registry.fixtures = [Fixture(**item) for item in raw.get("fixtures", [])]
        if any(item.runId != run_id or item.marker != run_id for item in registry.fixtures):
            raise RuntimeSafetyError("Registry contains a fixture outside the requested run marker.")
        return registry

    def register(self, entity: str, record_id: str, marker: str, suite: str) -> Fixture:
        if not record_id or marker != self.run_id:
            raise RuntimeSafetyError("Fixture registration requires the current run marker and a record ID.")
        fixture = Fixture(self.run_id, entity, record_id, marker, suite)
        self.fixtures.append(fixture)
        self._persist()
        return fixture

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schemaVersion": "1.0", "runId": self.run_id, "fixtures": [asdict(item) for item in self.fixtures]}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def record_has_marker(body: Any, marker: str) -> bool:
    if not isinstance(body, Mapping):
        return False
    return any(marker in str(body.get(field, "")) for field in ("name", "description", "peEvidenceId", "peCandidateId"))


class CleanupEngine:
    ORDER = {"ResearchEvidence": 0, "ProspectPool": 1, "SearchJob": 2, "SearchStrategy": 3, "Lead": 4}

    def __init__(self, client: RuntimeRestClient, registry: FixtureRegistry) -> None:
        self.client = client
        self.registry = registry

    def preview(self) -> list[dict[str, str]]:
        return [{"entity": item.entity, "recordId": item.recordId, "marker": item.marker} for item in sorted(self.registry.fixtures, key=lambda item: self.ORDER.get(item.entity, 99)) if item.cleanupRequired]

    def cleanup(self) -> list[Fixture]:
        for fixture in sorted(self.registry.fixtures, key=lambda item: self.ORDER.get(item.entity, 99)):
            if not fixture.cleanupRequired or fixture.cleanupResult == "CLEANED":
                continue
            try:
                current = self.client.request("GET", f"{fixture.entity}/{fixture.recordId}")
                if current.status == 404:
                    fixture.cleanupResult = "CLEANED"
                elif current.status != 200 or not record_has_marker(current.body, fixture.marker):
                    raise RuntimeSafetyError("Fixture marker verification failed; refusing deletion.")
                else:
                    deleted = self.client.request("DELETE", f"{fixture.entity}/{fixture.recordId}")
                    if deleted.status not in {200, 204}:
                        raise RuntimeCleanupError(f"Delete returned HTTP {deleted.status}.")
                    verified = self.client.request("GET", f"{fixture.entity}/{fixture.recordId}")
                    if verified.status != 404:
                        raise RuntimeCleanupError("Deleted fixture did not return 404 on verification.")
                    fixture.cleanupResult = "CLEANED"
            except RuntimeHarnessError as error:
                fixture.cleanupResult = "FAILED"
                fixture.cleanupError = str(error)
            finally:
                self.registry._persist()
        return self.registry.fixtures

    def residue_audit(self) -> list[Fixture]:
        residue: list[Fixture] = []
        for fixture in self.registry.fixtures:
            response = self.client.request("GET", f"{fixture.entity}/{fixture.recordId}")
            if response.status != 404:
                residue.append(fixture)
        return residue


def expect_status(label: str, response: ApiResponse, statuses: set[int]) -> Any:
    if response.status not in statuses:
        raise RuntimeHarnessError(f"{label}: expected HTTP {sorted(statuses)}, received {response.status}.")
    return response.body


def require_record_id(label: str, body: Any) -> str:
    if not isinstance(body, Mapping) or not body.get("id"):
        raise RuntimeHarnessError(f"{label}: response did not contain a record ID.")
    return str(body["id"])


def run_smoke(client: RuntimeRestClient, registry: FixtureRegistry, marker: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    expect_status("authentication", client.request("GET", "App/user"), {200})
    results.append({"name": "environment", "status": "PASS"})
    lead = expect_status("lead create", client.request("POST", "Lead", {"lastName": f"{marker} Lead", "description": marker}), {200, 201})
    lead_id = require_record_id("lead create", lead)
    registry.register("Lead", lead_id, marker, "smoke")
    expect_status("lead read", client.request("GET", f"Lead/{lead_id}"), {200})
    expect_status("lead update", client.request("PUT", f"Lead/{lead_id}", {"description": f"{marker} updated"}), {200})
    persisted = expect_status("lead reread", client.request("GET", f"Lead/{lead_id}"), {200})
    if not isinstance(persisted, Mapping) or persisted.get("description") != f"{marker} updated":
        raise RuntimeHarnessError("Lead update did not persist the marker value.")
    results.append({"name": "lead", "status": "PASS"})
    evidence = expect_status("evidence create", client.request("POST", "ResearchEvidence", {"name": f"{marker} Evidence", "peEvidenceId": marker, "peClaim": "Synthetic runtime fixture", "peSourceUrl": "https://example.invalid/runtime", "leadId": lead_id}), {200, 201})
    evidence_id = require_record_id("evidence create", evidence)
    registry.register("ResearchEvidence", evidence_id, marker, "smoke")
    evidence_read = expect_status("evidence read", client.request("GET", f"ResearchEvidence/{evidence_id}"), {200})
    if not isinstance(evidence_read, Mapping) or evidence_read.get("leadId") != lead_id:
        raise RuntimeHarnessError("ResearchEvidence was not linked to the runtime Lead fixture.")
    results.append({"name": "researchEvidence", "status": "PASS"})
    return results


def run_with_cleanup(client: RuntimeRestClient, registry: FixtureRegistry, action: Callable[[], list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[Fixture]]:
    """Run a write-capable child action and always try registry-only cleanup."""
    child_error: Exception | None = None
    results: list[dict[str, Any]] = []
    try:
        results = action()
    except Exception as error:
        child_error = error
    cleanup = CleanupEngine(client, registry).cleanup()
    try:
        residue = CleanupEngine(client, registry).residue_audit()
    except RuntimeHarnessError as error:
        raise RuntimeCleanupError("Residue audit could not complete safely.") from error
    if any(item.cleanupResult != "CLEANED" for item in cleanup) or residue:
        raise RuntimeCleanupError("Runtime fixture cleanup left unresolved records.")
    if child_error:
        if isinstance(child_error, RuntimeHarnessError):
            raise child_error
        raise RuntimeHarnessError("Runtime child action failed.") from child_error
    return results, cleanup


def run_acl(client: RuntimeRestClient, marker: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    unauthenticated = client.request("GET", "App/user", api_key="")
    expect_status("unauthenticated request", unauthenticated, {401, 403})
    invalid = client.request("GET", "App/user", api_key=f"invalid-{marker}")
    expect_status("invalid credential", invalid, {401, 403})
    results.append({"name": "authentication-denial", "status": "PASS"})
    results.append({"name": "insufficient-write-role", "status": "SKIPPED", "reason": "No dedicated denied-write credential configured."})
    return results
