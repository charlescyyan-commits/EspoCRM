from __future__ import annotations

from unittest import TestCase
from unittest.mock import patch

from chitu_connector.espocrm_sync.connector_api import (
    ConnectorApiError,
    ProspectingConnectorClient,
)
from chitu_connector.espocrm_sync.mapper import EspoCRMSyncMapper
from chitu_connector.espocrm_sync.real_sync import build_synthetic_source


class _Response:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.body


class ConnectorApiTests(TestCase):
    def setUp(self) -> None:
        self.payload = EspoCRMSyncMapper().build(build_synthetic_source())
        self.client = ProspectingConnectorClient("http://localhost:8080", "test-api-key")

    def test_requires_api_key_and_absolute_http_url(self) -> None:
        with self.assertRaises(ConnectorApiError):
            ProspectingConnectorClient("http://localhost:8080", "")
        with self.assertRaises(ConnectorApiError):
            ProspectingConnectorClient("localhost:8080", "key")

    def test_posts_contract_to_lead_route_with_api_key(self) -> None:
        response = b'{"success":true,"created":true,"updated":false,"external_id":"synthetic_test_dealer_v1","crm_id":"lead-1"}'
        with patch("chitu_connector.espocrm_sync.connector_api.urlopen", return_value=_Response(response)) as urlopen:
            result = self.client.sync_lead(self.payload)

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:8080/api/v1/Prospecting/sync/lead")
        self.assertEqual(request.get_header("X-api-key"), "test-api-key")
        self.assertEqual(result.crm_id, "lead-1")
        self.assertTrue(result.created)

    def test_posts_evidence_and_proposal_routes(self) -> None:
        evidence_response = b'{"success":true,"created":true,"updated":false,"external_id":"synthetic_test_dealer_v1","crm_id":"evidence-1"}'
        proposal_response = b'{"success":true,"created":false,"updated":true,"external_id":"synthetic_test_dealer_v1","crm_id":"lead-1","eligibility":true,"action":"NO_AUTOMATIC_OPPORTUNITY"}'
        with patch("chitu_connector.espocrm_sync.connector_api.urlopen", side_effect=[_Response(evidence_response), _Response(proposal_response)]) as urlopen:
            evidence = self.client.sync_evidence(self.payload)
            proposal = self.client.sync_opportunity_proposal(self.payload)

        self.assertEqual(urlopen.call_args_list[0].args[0].full_url, "http://localhost:8080/api/v1/Prospecting/sync/evidence")
        self.assertEqual(urlopen.call_args_list[1].args[0].full_url, "http://localhost:8080/api/v1/Prospecting/sync/opportunity-proposal")
        self.assertEqual(evidence.crm_id, "evidence-1")
        self.assertTrue(proposal.eligibility)
        self.assertEqual(proposal.action, "NO_AUTOMATIC_OPPORTUNITY")

    def test_rejects_incomplete_response(self) -> None:
        with self.assertRaises(ConnectorApiError):
            self.client._response({"success": True})
