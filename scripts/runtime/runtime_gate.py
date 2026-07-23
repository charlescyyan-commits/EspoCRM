"""Read-only EspoCRM runtime gate for CI and regression use.

The gate deliberately uses GET requests only.  It never rebuilds the extension,
clears cache, migrates a database, or creates/updates/deletes CRM records.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "crm-extension" / "manifest.json"
CONTRACT_PATH = ROOT / "docs" / "sync-contracts" / "ESPOCRM_SYNC_CONTRACT_V1.json"
CONNECTOR_CONTRACT_PATH = ROOT / "chitu-connector" / "chitu_connector" / "espocrm_sync" / "contract.py"
MODULE_ENTITY_DEFS = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "Prospecting"
    / "Resources"
    / "metadata"
    / "entityDefs"
)
LEAD_DEF_PATH = MODULE_ENTITY_DEFS / "Lead.json"
EVIDENCE_DEF_PATH = MODULE_ENTITY_DEFS / "ResearchEvidence.json"

EXIT_PASS = 0
EXIT_FAILURE = 1
EXIT_CONFIGURATION = 2

RUNTIME_FIELDS = {
    "Lead": frozenset({
        "peQualificationStatus", "peResearchStatus", "peSyncStatus", "peCandidateId",
        "peLastSyncAt", "peOpportunityScoreV4", "peScoreTier", "peConfidence",
        "peEvidenceCoverage", "peBestFirstProduct", "peEngineVersion", "peScoreRulesVersion",
        "peResearchSummary", "peKeyEvidence", "peRecommendedApproach",
    }),
    "ResearchEvidence": frozenset({
        "peEvidenceId", "peClaim", "peClaimType", "peEvidenceType", "peSourceUrl",
        "peEvidenceText", "peContentSummary", "peConfidence", "peCapturedAt",
        "peSchemaVersion", "peSnapshotHash", "peCanonicalUrl", "peEvidenceTypeNormalized",
        "peClaimHash",
    }),
}
VERSION_KEYS = ("prospectingExtensionVersion", "chituProspectingExtensionVersion", "extensionVersion")
CONTRACT_TOP_LEVEL = frozenset({
    "contract_version", "identity", "qualification", "company", "source", "research",
    "score", "recommendation", "evidence", "provenance", "sync",
})
CONTRACT_EVIDENCE_FIELDS = frozenset({
    "evidence_id", "claim_type", "claim", "source_url", "evidence_text", "confidence",
    "captured_at", "schema_version",
})


class GateError(RuntimeError):
    """A sanitized operational failure; no credentials are included."""


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: Any


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


Requester = Callable[[str, str, Mapping[str, str], float], HttpResponse]


def _required_text(environment: Mapping[str, str], key: str) -> str:
    value = environment.get(key, "").strip()
    if not value:
        raise GateError(f"{key} is required")
    return value


def _safe_base_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise GateError("ESPOCRM_BASE_URL must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise GateError("ESPOCRM_BASE_URL must not contain credentials, query parameters, or fragments")
    return value.rstrip("/")


def _timeout(environment: Mapping[str, str]) -> float:
    try:
        value = float(environment.get("ESPOCRM_RUNTIME_GATE_TIMEOUT", "10"))
    except ValueError as error:
        raise GateError("ESPOCRM_RUNTIME_GATE_TIMEOUT must be numeric") from error
    if not 1 <= value <= 120:
        raise GateError("ESPOCRM_RUNTIME_GATE_TIMEOUT must be between 1 and 120 seconds")
    return value


def _http_get(method: str, url: str, headers: Mapping[str, str], timeout: float) -> HttpResponse:
    request = Request(url, headers=dict(headers), method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return HttpResponse(response.status, _decode_json(raw))
    except HTTPError as error:
        return HttpResponse(error.code, _decode_json(error.read()))
    except (URLError, OSError, TimeoutError) as error:
        raise GateError(f"GET unavailable: {error.__class__.__name__}") from error


def _decode_json(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GateError("runtime response was not valid JSON") from error


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GateError(f"required workspace metadata is unreadable: {path.name}") from error
    if not isinstance(value, Mapping):
        raise GateError(f"required workspace metadata is not an object: {path.name}")
    return value


def _workspace_contract_checks() -> tuple[list[Check], str, Mapping[str, frozenset[str]]]:
    manifest = _read_json(MANIFEST_PATH)
    contract = _read_json(CONTRACT_PATH)
    lead = _read_json(LEAD_DEF_PATH)
    evidence = _read_json(EVIDENCE_DEF_PATH)
    extension_version = str(manifest.get("version", "")).strip()
    schema_version = str(contract.get("properties", {}).get("contract_version", {}).get("const", "")).strip()
    connector_source = CONNECTOR_CONTRACT_PATH.read_text(encoding="utf-8")
    checks: list[Check] = []
    checks.append(Check(
        "extension.workspace-manifest",
        "PASS" if extension_version else "FAIL",
        "workspace extension version is available" if extension_version else "manifest version is missing",
    ))
    version_pattern = rf'^CONTRACT_VERSION\s*=\s*["\']{re.escape(schema_version)}["\']'
    checks.append(Check(
        "connector.contract-version",
        "PASS" if schema_version and re.search(version_pattern, connector_source, re.MULTILINE) else "FAIL",
        "connector V1 version matches schema" if schema_version and re.search(version_pattern, connector_source, re.MULTILINE) else "connector V1 version does not match schema",
    ))
    schema_required = contract.get("required")
    evidence_required = contract.get("properties", {}).get("evidence", {}).get("items", {}).get("required")
    contract_complete = (
        isinstance(schema_required, list) and CONTRACT_TOP_LEVEL.issubset(schema_required)
        and isinstance(evidence_required, list) and CONTRACT_EVIDENCE_FIELDS.issubset(evidence_required)
    )
    checks.append(Check(
        "connector.contract-schema",
        "PASS" if contract_complete else "FAIL",
        "V1 contract contains required sync and evidence fields" if contract_complete else "V1 contract required fields are incomplete",
    ))
    field_definitions: dict[str, frozenset[str]] = {}
    for entity, definition in (("Lead", lead), ("ResearchEvidence", evidence)):
        fields = definition.get("fields")
        available = frozenset(fields) if isinstance(fields, Mapping) else frozenset()
        field_definitions[entity] = available
        missing = sorted(RUNTIME_FIELDS[entity] - available)
        checks.append(Check(
            f"connector.schema-{entity}",
            "PASS" if not missing else "FAIL",
            "workspace entity definition covers connector fields" if not missing else f"missing workspace fields: {', '.join(missing)}",
        ))
    return checks, extension_version, field_definitions


def _metadata_url(base_url: str, key: str) -> str:
    return f"{base_url}/api/v1/Metadata?key={quote(key, safe='.') }"


def _extension_version(value: Any) -> str | None:
    if not isinstance(value, Mapping):
        return None
    for key in VERSION_KEYS:
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    for nested_key in ("prospecting", "extensions", "custom"):
        nested = value.get(nested_key)
        if isinstance(nested, Mapping):
            version = _extension_version(nested)
            if version:
                return version
    return None


def run_runtime_gate(environment: Mapping[str, str] | None = None, requester: Requester = _http_get) -> dict[str, Any]:
    """Run all checks using only GET requests and return a JSON-safe report."""
    environment = environment if environment is not None else os.environ
    checks, workspace_version, _ = _workspace_contract_checks()
    try:
        base_url = _safe_base_url(_required_text(environment, "ESPOCRM_BASE_URL"))
        api_key = _required_text(environment, "ESPOCRM_API_KEY")
        timeout = _timeout(environment)
    except GateError as error:
        checks.append(Check("connector.config", "FAIL", str(error)))
        return _report(checks, exit_code=EXIT_CONFIGURATION)

    checks.append(Check("connector.config", "PASS", "ESPOCRM_BASE_URL and ESPOCRM_API_KEY are available"))
    headers = {"Accept": "application/json", "X-Api-Key": api_key}
    try:
        reachable = requester("GET", base_url, {"Accept": "application/json"}, timeout)
        checks.append(Check(
            "runtime.reachable", "PASS" if 200 <= reachable.status < 400 else "FAIL",
            f"HTTP {reachable.status}" if 200 <= reachable.status < 400 else f"unexpected HTTP {reachable.status}",
        ))
        app_params = requester("GET", _metadata_url(base_url, "appParams"), headers, timeout)
        if app_params.status != 200:
            checks.append(Check("runtime.api", "FAIL", f"Metadata appParams returned HTTP {app_params.status}"))
            return _report(checks)
        checks.append(Check("runtime.api", "PASS", "authenticated Metadata API is available"))
        runtime_version = _extension_version(app_params.body)
        if runtime_version is None:
            checks.append(Check("extension.version", "RISK", "runtime metadata exposes no extension version"))
        elif runtime_version != workspace_version:
            checks.append(Check("extension.version", "FAIL", "runtime extension version differs from workspace manifest"))
        else:
            checks.append(Check("extension.version", "PASS", "runtime extension version matches workspace manifest"))

        runtime_fields: dict[str, frozenset[str]] = {}
        evidence = requester("GET", _metadata_url(base_url, "entityDefs.ResearchEvidence"), headers, timeout)
        lead_fields = requester("GET", _metadata_url(base_url, "entityDefs.Lead.fields"), headers, timeout)
        lead_links = requester("GET", _metadata_url(base_url, "entityDefs.Lead.links"), headers, timeout)
        response_map = {"ResearchEvidence": evidence, "Lead": lead_fields}
        metadata_problem = False
        for entity, response in response_map.items():
            body = response.body.get("fields") if entity == "ResearchEvidence" and isinstance(response.body, Mapping) else response.body
            fields = frozenset(body) if response.status == 200 and isinstance(body, Mapping) else frozenset()
            runtime_fields[entity] = fields
            missing = sorted(RUNTIME_FIELDS[entity] - fields)
            metadata_problem = metadata_problem or bool(missing)
            checks.append(Check(
                f"extension.metadata-{entity}",
                "PASS" if not missing else "FAIL",
                "required runtime fields are present" if not missing else f"missing runtime fields: {', '.join(missing)}",
            ))
        has_link = lead_links.status == 200 and isinstance(lead_links.body, Mapping) and "researchEvidences" in lead_links.body
        metadata_problem = metadata_problem or not has_link
        checks.append(Check(
            "extension.metadata-link",
            "PASS" if has_link else "FAIL",
            "Lead researchEvidences link is present" if has_link else "Lead researchEvidences link is missing",
        ))
        checks.append(Check(
            "extension.loaded",
            "PASS" if not metadata_problem else "FAIL",
            "runtime metadata confirms the extension is loaded" if not metadata_problem else "runtime extension metadata is incomplete",
        ))
    except (GateError, OSError, TimeoutError) as error:
        checks.append(Check("runtime.reachable", "FAIL", str(error)))
    return _report(checks)


def _report(checks: list[Check], *, exit_code: int | None = None) -> dict[str, Any]:
    statuses = [check.status for check in checks]
    overall = "FAIL" if "FAIL" in statuses else "PASS WITH RISKS" if "RISK" in statuses else "PASS"
    return {
        "schemaVersion": "1.0",
        "readOnly": True,
        "overallStatus": overall,
        "exitCode": exit_code if exit_code is not None else EXIT_FAILURE if overall == "FAIL" else EXIT_PASS,
        "checks": [asdict(check) for check in checks],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only EspoCRM runtime regression gate")
    parser.add_argument("--json", action="store_true", help="emit only the JSON result")
    args = parser.parse_args(argv)
    result = run_runtime_gate()
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        for check in result["checks"]:
            print(f"{check['status']:<15} {check['name']}: {check['detail']}")
        print(f"{result['overallStatus']} (read-only)")
    return int(result["exitCode"])


if __name__ == "__main__":
    sys.exit(main())
