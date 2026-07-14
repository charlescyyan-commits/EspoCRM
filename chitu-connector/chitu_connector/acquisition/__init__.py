"""Offline, deterministic acquisition worker core.

This package deliberately has no EspoCRM HTTP client and no external search
provider implementation.  A future adapter may implement ``AcquisitionStore``
without changing the worker contract.
"""

from .fake_provider import DeterministicFakeProvider
from .models import (
    ClaimResult,
    JobExecutionResult,
    NormalizedCandidate,
    PersistenceError,
    ProviderError,
    ProviderRateLimitError,
    ProviderResult,
    RawCandidate,
    SearchRequest,
)
from .worker import AcquisitionStore, AcquisitionWorker

__all__ = [
    "AcquisitionStore",
    "AcquisitionWorker",
    "ClaimResult",
    "DeterministicFakeProvider",
    "JobExecutionResult",
    "NormalizedCandidate",
    "PersistenceError",
    "ProviderError",
    "ProviderRateLimitError",
    "ProviderResult",
    "RawCandidate",
    "SearchRequest",
]
