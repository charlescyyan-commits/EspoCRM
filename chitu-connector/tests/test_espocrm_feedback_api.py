from __future__ import annotations

from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import patch

from chitu_connector.espocrm_sync.feedback_api import (
    FeedbackApiError,
    FeedbackConnectorClient,
    FeedbackSyncPayload,
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


class FeedbackConnectorApiTests(TestCase):
    def setUp(self) -> None:
        self.payload = FeedbackSyncPayload(
            lead_id="crm-lead-1",
            feedback_type="INTERESTED",
            outcome="POSITIVE",
            timestamp=datetime(2026, 7, 12, 9, 0, tzinfo=timezone.utc),
            feedback_id="feedback-ext-1",
            product="Resin Tank",
            stage="Interested",
        )
        self.client = FeedbackConnectorClient("http://localhost:8080", "test-api-key")

    def test_posts_stable_payload_with_api_key(self) -> None:
        response = b'{"success":true,"external_id":"feedback-ext-1","accepted":true,"created":true,"feedback_id":"feedback-1","learning_signal_id":"signal-1"}'
        with patch("chitu_connector.espocrm_sync.feedback_api.urlopen", return_value=_Response(response)) as urlopen:
            result = self.client.sync_feedback(self.payload)

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:8080/api/v1/Prospecting/feedback/sync")
        self.assertEqual(request.get_header("X-api-key"), "test-api-key")
        self.assertTrue(result.accepted)
        self.assertTrue(result.created)
        self.assertEqual(result.learning_signal_id, "signal-1")

    def test_rejects_invalid_payload_and_response(self) -> None:
        with self.assertRaises(FeedbackApiError):
            FeedbackSyncPayload("lead", "UNKNOWN", "POSITIVE", datetime.now(timezone.utc))
        with self.assertRaises(FeedbackApiError):
            FeedbackSyncPayload("lead", "WON", "POSITIVE", datetime(2026, 7, 12, 9, 0))
        with self.assertRaises(FeedbackApiError):
            self.client._response({"success": True})
