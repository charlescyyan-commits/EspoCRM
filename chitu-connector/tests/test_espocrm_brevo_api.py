from __future__ import annotations

from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import patch

from chitu_connector.espocrm_sync.brevo_api import (
    BrevoApiError,
    BrevoConnectorClient,
    BrevoEmailEventPayload,
)


class _Response:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.body


class BrevoConnectorApiTests(TestCase):
    def setUp(self) -> None:
        self.payload = BrevoEmailEventPayload(
            lead_id="crm-lead-1",
            message_id="brevo-msg-1",
            event_type="email_delivered",
            timestamp=datetime(2026, 7, 12, 10, 0, tzinfo=timezone.utc),
            campaign="Campaign A",
        )
        self.client = BrevoConnectorClient("http://localhost:8080", "test-api-key")

    def test_normalizes_brevo_event_and_posts_with_api_key(self) -> None:
        response = (
            b'{"success":true,"accepted":true,"created":true,"duplicate":false,'
            b'"external_message_id":"brevo-msg-1","event_type":"DELIVERED",'
            b'"email_event_id":"evt-1","lead_id":"crm-lead-1"}'
        )
        with patch("chitu_connector.espocrm_sync.brevo_api.urlopen", return_value=_Response(response)) as urlopen:
            result = self.client.sync_email_event(self.payload)

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:8080/api/v1/Prospecting/brevo/email-event")
        self.assertEqual(request.get_header("X-api-key"), "test-api-key")
        self.assertEqual(self.payload.event_type, "DELIVERED")
        self.assertTrue(result.created)
        self.assertFalse(result.duplicate)
        self.assertEqual(result.event_type, "DELIVERED")

    def test_rejects_invalid_payload_and_response(self) -> None:
        with self.assertRaises(BrevoApiError):
            BrevoEmailEventPayload("lead", "msg", "unknown_event", datetime.now(timezone.utc))
        with self.assertRaises(BrevoApiError):
            BrevoEmailEventPayload("lead", "msg", "SENT", datetime(2026, 7, 12, 10, 0))
        with self.assertRaises(BrevoApiError):
            self.client._response({"success": True})
