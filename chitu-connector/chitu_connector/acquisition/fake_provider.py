"""Network-free provider used only for deterministic worker verification."""

from __future__ import annotations

from .models import ProviderError, ProviderResult, RawCandidate, SearchRequest


class DeterministicFakeProvider:
    """Produces fixed data from explicit test modes, never time/random/network data."""

    name = "DETERMINISTIC_FAKE"

    def search(self, request: SearchRequest) -> ProviderResult:
        mode = request.keyword.strip().casefold()
        if mode == "fake:empty":
            return ProviderResult(self.name, ())
        if mode == "fake:retryable-error":
            raise ProviderError("FAKE_TRANSIENT", "Deterministic temporary provider failure", retryable=True)
        if mode == "fake:non-retryable-error":
            raise ProviderError("FAKE_INVALID_REQUEST", "Deterministic invalid provider request", retryable=False)

        country = request.country or "US"
        candidates = (
            RawCandidate(
                provider_candidate_id="fake-alpha-001",
                company_name=" Alpha 3D Distribution ",
                domain="HTTPS://www.alpha-3d.example/catalog?source=fake#top",
                source_url="https://provider.invalid/results/alpha-3d?candidate=001",
                country=country,
                raw_payload={"id": "fake-alpha-001", "rank": 1, "fixture": "default"},
            ),
            RawCandidate(
                provider_candidate_id="fake-beta-002",
                company_name="Beta Distributor",
                domain="beta-distributor.example.",
                source_url="https://provider.invalid/results/beta-distributor?candidate=002",
                country=country,
                raw_payload={"id": "fake-beta-002", "rank": 2, "fixture": "default"},
            ),
            RawCandidate(
                provider_candidate_id="fake-alpha-duplicate-003",
                company_name="Alpha 3D Distribution duplicate",
                domain="http://alpha-3d.example/another/path?duplicate=true",
                source_url="https://provider.invalid/results/alpha-3d?candidate=003",
                country=country,
                raw_payload={"id": "fake-alpha-duplicate-003", "rank": 3, "fixture": "duplicate"},
            ),
        )
        return ProviderResult(self.name, candidates[: request.result_limit])
