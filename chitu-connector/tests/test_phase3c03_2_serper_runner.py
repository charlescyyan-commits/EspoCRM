from __future__ import annotations

import json
import os
from io import StringIO
from unittest import TestCase

from chitu_connector.acquisition.models import ProviderResult, RawCandidate, SearchRequest
from chitu_connector.acquisition.providers import SerperConfig, SerperSearchProvider
from chitu_connector.acquisition.runner import main


def _runner_environ() -> dict[str, str]:
    """Minimal required env for runner config loading."""
    return {
        "ESPOCRM_BASE_URL": "https://fixture.espo.invalid",
        "ESPOCRM_API_KEY": "fixture-espo-api-key",
    }


class _FakeProviderDouble:
    """Deterministic stub that records calls for factory-resolution tests."""

    name = "FAKE_DOUBLE"

    def __init__(self) -> None:
        self.calls: list[SearchRequest] = []

    def search(self, request: SearchRequest) -> ProviderResult:
        self.calls.append(request)
        return ProviderResult(self.name, ())


class _SerperProviderDouble:
    """Deterministic stub that records calls for serper factory-resolution tests."""

    name = "SERPER_DOUBLE"

    def __init__(self) -> None:
        self.calls: list[SearchRequest] = []

    def search(self, request: SearchRequest) -> ProviderResult:
        self.calls.append(request)
        return ProviderResult(self.name, ())


class _FakeRepository:
    """Minimal repository stub for runner tests."""

    def __init__(self, job_found: bool = True, status: str = "QUEUED") -> None:
        self._job_found = job_found
        self._status = status

    def fetch_search_job(self, job_id: str) -> dict | None:
        if not self._job_found:
            return None
        return {"id": job_id, "status": self._status}

    def claim_search_job(self, *args, **kwargs):  # noqa: ANN
        from chitu_connector.acquisition.models import ClaimResult
        return ClaimResult(True, {"id": kwargs.get("job_id", "x"), "status": "RUNNING"}, "QUEUED", "RUNNING")

    def update_search_job(self, *args, **kwargs):  # noqa: ANN
        pass

    def has_prospect(self, *args, **kwargs):  # noqa: ANN
        return False

    def create_prospect(self, *args, **kwargs):  # noqa: ANN
        pass


class RunnerFactoryResolutionTests(TestCase):
    # ------------------------------------------------------------------
    # Provider acceptance
    # ------------------------------------------------------------------

    def test_runner_accepts_fake_provider(self) -> None:
        """Existing --provider fake must still be accepted."""
        provider = _FakeProviderDouble()
        repository_factory = lambda cfg: _FakeRepository()  # noqa: E731

        exit_code = main(
            ["run-job", "--job-id", "job-001", "--provider", "fake"],
            repository_factory=repository_factory,
            provider_factory=lambda: provider,
            environ=_runner_environ(),
            stdout=StringIO(),
            stderr=StringIO(),
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(provider.calls[0].job_id, "job-001")

    def test_runner_accepts_serper_provider_via_factory_override(self) -> None:
        """--provider serper with an explicit factory override must route correctly."""
        provider = _SerperProviderDouble()
        repository_factory = lambda cfg: _FakeRepository()  # noqa: E731

        exit_code = main(
            ["run-job", "--job-id", "job-serper-001", "--provider", "serper"],
            repository_factory=repository_factory,
            provider_factory=lambda: provider,
            environ=_runner_environ(),
            stdout=StringIO(),
            stderr=StringIO(),
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(provider.calls[0].job_id, "job-serper-001")

    def test_runner_rejects_unknown_provider(self) -> None:
        """Unknown provider must produce an INVALID_ARGUMENT error."""
        buf = StringIO()
        exit_code = main(
            ["run-job", "--job-id", "job-001", "--provider", "bogus"],
            environ=_runner_environ(),
            stdout=buf,
            stderr=StringIO(),
        )
        self.assertEqual(exit_code, 2)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["errorCode"], "INVALID_ARGUMENT")

    # ------------------------------------------------------------------
    # Provider name property
    # ------------------------------------------------------------------

    def test_serper_search_provider_has_correct_name(self) -> None:
        config = SerperConfig("test-key")
        # Use a no-op transport — we only check the name property here.
        provider = SerperSearchProvider(config, transport=_NoOpTransport())
        self.assertEqual(provider.name, "SERPER")

    # ------------------------------------------------------------------
    # Factory override precedence
    # ------------------------------------------------------------------

    def test_factory_override_supersedes_provider_flag(self) -> None:
        """When provider_factory is explicitly set, it must be used regardless of --provider."""
        provider = _FakeProviderDouble()
        repository_factory = lambda cfg: _FakeRepository()  # noqa: E731

        exit_code = main(
            ["run-job", "--job-id", "job-001", "--provider", "serper"],
            repository_factory=repository_factory,
            provider_factory=lambda: provider,
            environ=_runner_environ(),
            stdout=StringIO(),
            stderr=StringIO(),
        )

        self.assertEqual(exit_code, 0)
        # The fake double was used despite --provider serper
        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(provider.name, "FAKE_DOUBLE")


class _NoOpTransport:
    """Transport that must never be called; used only for name-property checks."""

    def send(self, request):  # noqa: ANN
        raise AssertionError("Transport must not be called for name-property checks")
