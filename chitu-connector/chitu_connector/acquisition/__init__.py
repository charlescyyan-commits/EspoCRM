"""Offline, deterministic acquisition worker core.

This package deliberately has no EspoCRM HTTP client and no external search
provider implementation.  A future adapter may implement ``AcquisitionStore``
without changing the worker contract.
"""

from .fake_provider import DeterministicFakeProvider
from .models import (
    JobExecutionResult,
    NormalizedCandidate,
    ProviderError,
    ProviderResult,
    RawCandidate,
    SearchRequest,
)
from .worker import AcquisitionStore, AcquisitionWorker

__all__ = [
    "AcquisitionStore",
    "AcquisitionWorker",
    "DeterministicFakeProvider",
    "JobExecutionResult",
    "NormalizedCandidate",
    "ProviderError",
    "ProviderResult",
    "RawCandidate",
    "SearchRequest",
]
