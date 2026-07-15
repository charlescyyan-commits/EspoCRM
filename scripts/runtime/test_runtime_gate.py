from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime_gate import HttpResponse, MANIFEST_PATH, RUNTIME_FIELDS, run_runtime_gate  # noqa: E402


def enabled_environment() -> dict[str, str]:
    return {
        "ESPOCRM_BASE_URL": "http://crm.test",
        "ESPOCRM_API_KEY": "not-a-real-secret",
        "ESPOCRM_RUNTIME_GATE_TIMEOUT": "5",
    }


def runtime_metadata() -> dict[str, HttpResponse]:
    workspace_version = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["version"]
    return {
        "http://crm.test": HttpResponse(200, {}),
        "http://crm.test/api/v1/Metadata?key=appParams": HttpResponse(200, {"prospectingExtensionVersion": workspace_version}),
        "http://crm.test/api/v1/Metadata?key=entityDefs.ResearchEvidence": HttpResponse(200, {"fields": {field: {} for field in RUNTIME_FIELDS["ResearchEvidence"]}}),
        "http://crm.test/api/v1/Metadata?key=entityDefs.Lead.fields": HttpResponse(200, {field: {} for field in RUNTIME_FIELDS["Lead"]}),
        "http://crm.test/api/v1/Metadata?key=entityDefs.Lead.links": HttpResponse(200, {"researchEvidences": {}}),
    }


class FakeRequester:
    def __init__(self, responses: Mapping[str, HttpResponse], error: Exception | None = None) -> None:
        self.responses = dict(responses)
        self.error = error
        self.calls: list[tuple[str, str]] = []

    def __call__(self, method: str, url: str, _: Mapping[str, str], __: float) -> HttpResponse:
        self.calls.append((method, url))
        if self.error:
            raise self.error
        return self.responses[url]


class RuntimeGateTests(unittest.TestCase):
    def test_success_case_is_read_only_and_passes(self) -> None:
        requester = FakeRequester(runtime_metadata())
        result = run_runtime_gate(enabled_environment(), requester)
        self.assertEqual(result["overallStatus"], "PASS")
        self.assertTrue(result["readOnly"])
        self.assertEqual({method for method, _ in requester.calls}, {"GET"})

    def test_missing_extension_case_fails_metadata_check(self) -> None:
        responses = runtime_metadata()
        responses["http://crm.test/api/v1/Metadata?key=entityDefs.ResearchEvidence"] = HttpResponse(404, {})
        result = run_runtime_gate(enabled_environment(), FakeRequester(responses))
        checks = {item["name"]: item for item in result["checks"]}
        self.assertEqual(result["overallStatus"], "FAIL")
        self.assertEqual(checks["extension.loaded"]["status"], "FAIL")

    def test_missing_config_case_fails_before_http(self) -> None:
        requester = FakeRequester({})
        result = run_runtime_gate({}, requester)
        self.assertEqual(result["overallStatus"], "FAIL")
        self.assertEqual(requester.calls, [])
        self.assertEqual(next(item for item in result["checks"] if item["name"] == "connector.config")["status"], "FAIL")

    def test_api_unavailable_case_is_reported_without_writes(self) -> None:
        requester = FakeRequester(runtime_metadata(), ConnectionError("offline"))
        result = run_runtime_gate(enabled_environment(), requester)
        self.assertEqual(result["overallStatus"], "FAIL")
        self.assertEqual({method for method, _ in requester.calls}, {"GET"})
        self.assertEqual(next(item for item in result["checks"] if item["name"] == "runtime.reachable")["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
