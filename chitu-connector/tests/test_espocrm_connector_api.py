from __future__ import annotations

from dataclasses import replace
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

    def test_sync_source_runs_contract_gate_and_all_routes_in_order(self) -> None:
        lead_response = b'{"success":true,"created":true,"updated":false,"external_id":"synthetic_test_dealer_v1","crm_id":"lead-1"}'
        evidence_response = b'{"success":true,"created":true,"updated":false,"external_id":"synthetic_test_dealer_v1","crm_id":"evidence-1"}'
        proposal_response = b'{"success":true,"created":false,"updated":true,"external_id":"synthetic_test_dealer_v1","crm_id":"lead-1","eligibility":true,"action":"NO_AUTOMATIC_OPPORTUNITY"}'
        with patch(
            "chitu_connector.espocrm_sync.connector_api.urlopen",
            side_effect=[_Response(lead_response), _Response(evidence_response), _Response(proposal_response)],
        ) as urlopen:
            result = self.client.sync_source(build_synthetic_source())

        self.assertTrue(result.success)
        self.assertTrue(result.validation.completed)
        self.assertTrue(result.gate.completed)
        self.assertEqual(
            [call.args[0].full_url for call in urlopen.call_args_list],
            [
                "http://localhost:8080/api/v1/Prospecting/sync/lead",
                "http://localhost:8080/api/v1/Prospecting/sync/evidence",
                "http://localhost:8080/api/v1/Prospecting/sync/opportunity-proposal",
            ],
        )

    def test_sync_source_rejects_invalid_contract_without_writes(self) -> None:
        source = build_synthetic_source()
        source.score["score_tier"] = ""
        with patch("chitu_connector.espocrm_sync.connector_api.urlopen") as urlopen:
            result = self.client.sync_source(source)

        self.assertFalse(result.success)
        self.assertFalse(result.validation.completed)
        self.assertEqual(result.validation.reason, "INVALID_FIELD:score.score_tier")
        urlopen.assert_not_called()

    def test_sync_source_gate_rejections_do_not_write(self) -> None:
        cases = (
            ("invalid-tier", lambda source: source.score.__setitem__("score_tier", "D"), "INVALID_SCORE_TIER"),
            ("empty-product", lambda source: source.score.__setitem__("best_first_product", ""), "MISSING_BEST_FIRST_PRODUCT"),
            ("empty-evidence", lambda source: replace(source, research=replace(source.research, evidence_items=())), "MISSING_EVIDENCE"),
            ("low-coverage", lambda source: source.score.__setitem__("evidence_coverage", 0.49), "INSUFFICIENT_EVIDENCE_COVERAGE"),
            ("low-confidence", lambda source: source.score.__setitem__("aggregate_confidence", 0.59), "INSUFFICIENT_CONFIDENCE"),
            ("invalid-v1", lambda source: setattr(source.candidate, "company_name", ""), "INVALID_FIELD:company.name"),
        )
        for name, mutate, reason in cases:
            with self.subTest(name=name):
                source = build_synthetic_source()
                source = mutate(source) or source
                with patch("chitu_connector.espocrm_sync.connector_api.urlopen") as urlopen:
                    result = self.client.sync_source(source)

                self.assertFalse(result.success)
                self.assertEqual(result.validation.reason or result.gate.reason, reason)
                urlopen.assert_not_called()

    def test_sync_source_stops_after_lead_failure(self) -> None:
        with patch(
            "chitu_connector.espocrm_sync.connector_api.urlopen",
            side_effect=ConnectorApiError("lead route failed"),
        ) as urlopen:
            with self.assertRaisesRegex(ConnectorApiError, "lead route failed"):
                self.client.sync_source(build_synthetic_source())

        self.assertEqual(urlopen.call_count, 1)

    def test_sync_source_stops_when_lead_response_reports_failure(self) -> None:
        failed_response = b'{"success":false,"created":false,"updated":false,"external_id":"synthetic_test_dealer_v1","crm_id":"lead-1"}'
        with patch(
            "chitu_connector.espocrm_sync.connector_api.urlopen",
            return_value=_Response(failed_response),
        ) as urlopen:
            result = self.client.sync_source(build_synthetic_source())

        self.assertFalse(result.success)
        self.assertTrue(result.lead.completed)
        self.assertFalse(result.lead.response.success)
        self.assertFalse(result.evidence.completed)
        self.assertEqual(urlopen.call_count, 1)

    def test_sync_source_stops_after_evidence_failure(self) -> None:
        lead_response = b'{"success":true,"created":true,"updated":false,"external_id":"synthetic_test_dealer_v1","crm_id":"lead-1"}'
        with patch(
            "chitu_connector.espocrm_sync.connector_api.urlopen",
            side_effect=[_Response(lead_response), ConnectorApiError("evidence route failed")],
        ) as urlopen:
            with self.assertRaisesRegex(ConnectorApiError, "evidence route failed"):
                self.client.sync_source(build_synthetic_source())

        self.assertEqual(urlopen.call_count, 2)

    def test_sync_source_stops_after_proposal_failure(self) -> None:
        lead_response = b'{"success":true,"created":true,"updated":false,"external_id":"synthetic_test_dealer_v1","crm_id":"lead-1"}'
        evidence_response = b'{"success":true,"created":true,"updated":false,"external_id":"synthetic_test_dealer_v1","crm_id":"evidence-1"}'
        with patch(
            "chitu_connector.espocrm_sync.connector_api.urlopen",
            side_effect=[_Response(lead_response), _Response(evidence_response), ConnectorApiError("proposal route failed")],
        ) as urlopen:
            with self.assertRaisesRegex(ConnectorApiError, "proposal route failed"):
                self.client.sync_source(build_synthetic_source())

        self.assertEqual(urlopen.call_count, 3)

    def test_rejects_incomplete_response(self) -> None:
        with self.assertRaises(ConnectorApiError):
            self.client._response({"success": True})
