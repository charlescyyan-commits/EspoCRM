from __future__ import annotations

from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import patch

from chitu_connector.espocrm_sync.feedback_signal_export import (
    FeedbackSignalExportClient,
    FeedbackSignalExportError,
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


class FeedbackSignalExportTests(TestCase):
    def setUp(self) -> None:
        self.client = FeedbackSignalExportClient("http://localhost:8080", "test-api-key")

    def test_exports_learning_signals_for_lead(self) -> None:
        body = (
            b'{"list":[{"id":"sig-1","leadId":"lead-1","signalType":"EMAIL_INTERESTED",'
            b'"actualOutcome":"POSITIVE","product":"LCD","campaign":"Camp A",'
            b'"salesFeedbackId":"fb-1","createdAt":"2026-07-12T10:00:00+00:00"}],"total":1}'
        )
        with patch("chitu_connector.espocrm_sync.feedback_signal_export.urlopen", return_value=_Response(body)) as urlopen:
            rows = self.client.export_for_lead("lead-1")

        request = urlopen.call_args.args[0]
        self.assertIn("/api/v1/LearningSignal?", request.full_url)
        self.assertEqual(request.get_header("X-api-key"), "test-api-key")
        self.assertEqual(len(rows), 1)
        payload = rows[0].to_dict()
        self.assertEqual(payload["lead_id"], "lead-1")
        self.assertEqual(payload["feedback_type"], "EMAIL_INTERESTED")
        self.assertEqual(payload["outcome"], "POSITIVE")
        self.assertEqual(payload["campaign"], "Camp A")
        self.assertIn("timestamp", payload)

    def test_requires_api_key_and_valid_response(self) -> None:
        with self.assertRaises(FeedbackSignalExportError):
            FeedbackSignalExportClient("http://localhost:8080", "")
        with self.assertRaises(FeedbackSignalExportError):
            self.client._map_signal({"leadId": "x"})
