from __future__ import annotations

import os
from unittest import TestCase
from unittest.mock import patch

from chitu_connector.espocrm_sync.mapper import EspoCRMSyncMapper
from chitu_connector.espocrm_sync.real_client import (
    EnvironmentSafetyError,
    LOCAL_TEST_URL,
    LocalEspoCRMClient,
    SYNTHETIC_MARKER,
    _LEAD_FIELDS,
    _RESEARCH_EVIDENCE_FIELDS,
)
from chitu_connector.espocrm_sync.real_sync import build_synthetic_source


class StubClient(LocalEspoCRMClient):
    def __init__(self, metadata: dict[str, object]) -> None:
        super().__init__(LOCAL_TEST_URL, "test-user", "test-password")
        self.metadata = metadata
        self.calls: list[tuple[str, str]] = []

    def _request(self, method, path, body=None, query=None, headers=None):
        self.calls.append((method, path))
        if path == "App/user":
            return {"token": "test-token"}
        if path == "Metadata":
            return self.metadata[query["key"]]
        return {}


def metadata() -> dict[str, object]:
    return {
        "entityDefs.Lead.fields": {field: {} for field in _LEAD_FIELDS},
        "entityDefs.ResearchEvidence": {"fields": {field: {} for field in _RESEARCH_EVIDENCE_FIELDS}},
        "entityDefs.Lead.links": {"researchEvidences": {}},
    }


class LocalClientSafetyTests(TestCase):
    def test_remote_target_is_rejected(self) -> None:
        with self.assertRaises(EnvironmentSafetyError):
            LocalEspoCRMClient("https://crm.example", "user", "password")

    def test_environment_requires_explicit_test_flag(self) -> None:
        with patch.dict(os.environ, {"ESPOCRM_TEST_ENV": "", "ESPOCRM_ADMIN_USERNAME": "user", "ESPOCRM_ADMIN_PASSWORD": "password"}, clear=False):
            with self.assertRaises(EnvironmentSafetyError):
                LocalEspoCRMClient.from_environment()

    def test_environment_reads_only_local_test_variables(self) -> None:
        with patch.dict(os.environ, {"ESPOCRM_TEST_ENV": "true", "ESPOCRM_TEST_URL": LOCAL_TEST_URL, "ESPOCRM_ADMIN_USERNAME": "user", "ESPOCRM_ADMIN_PASSWORD": "password"}, clear=False):
            client = LocalEspoCRMClient.from_environment()
        self.assertEqual(client.base_url, LOCAL_TEST_URL)

    def test_environment_accepts_local_test_api_key(self) -> None:
        with patch.dict(os.environ, {"ESPOCRM_TEST_ENV": "true", "ESPOCRM_TEST_URL": LOCAL_TEST_URL, "ESPOCRM_TEST_API_KEY": "test-key"}, clear=True):
            client = LocalEspoCRMClient.from_environment()
        self.assertEqual(client.api_key, "test-key")

    def test_authentication_uses_app_user_token(self) -> None:
        client = StubClient(metadata())
        client.authenticate()
        self.assertIn(("GET", "App/user"), client.calls)

    def test_preflight_requires_extension_metadata(self) -> None:
        client = StubClient(metadata())
        client.authenticate()
        client.preflight()
        self.assertIn(("GET", "Metadata"), client.calls)
        incomplete = StubClient({"entityDefs.Lead.fields": {}, "entityDefs.ResearchEvidence": {"fields": {}}, "entityDefs.Lead.links": {}})
        incomplete.authenticate()
        with self.assertRaises(EnvironmentSafetyError):
            incomplete.preflight()

    def test_lead_payload_is_synthetic_and_field_limited(self) -> None:
        payload = EspoCRMSyncMapper().build(build_synthetic_source())
        body = LocalEspoCRMClient(LOCAL_TEST_URL, "user", "password")._lead_body(payload)
        self.assertEqual(set(body), _LEAD_FIELDS | {"lastName"})
        self.assertEqual(body["lastName"], body["name"])
        self.assertIn(SYNTHETIC_MARKER, body["description"])
        self.assertIn("is_test=true", body["description"])
        self.assertIn("data_type=synthetic", body["description"])

    def test_evidence_payload_is_field_limited(self) -> None:
        payload = EspoCRMSyncMapper().build(build_synthetic_source())
        body = LocalEspoCRMClient(LOCAL_TEST_URL, "user", "password")._evidence_body(payload.to_dict()["evidence"][0], payload)
        self.assertEqual(set(body), _RESEARCH_EVIDENCE_FIELDS)

    def test_absolute_api_path_is_rejected_before_request(self) -> None:
        client = LocalEspoCRMClient(LOCAL_TEST_URL, "user", "password")
        with self.assertRaises(EnvironmentSafetyError):
            client._request("GET", "https://example.com/api/v1/Lead")

    def test_lifecycle_helpers_reject_non_crm_entities(self) -> None:
        client = LocalEspoCRMClient(LOCAL_TEST_URL, "user", "password")
        with self.assertRaises(EnvironmentSafetyError):
            client.search_records("Role", "name", "test", "id")
