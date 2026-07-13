"""The small interface implemented by deterministic and future providers."""

from __future__ import annotations

from typing import Protocol

from .models import ProviderResult, SearchRequest


class SearchProvider(Protocol):
    @property
    def name(self) -> str: ...

    def search(self, request: SearchRequest) -> ProviderResult: ...
