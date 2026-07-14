"""Transport-neutral interfaces for external acquisition providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from ..models import ProviderResult, SearchRequest


@dataclass(frozen=True, slots=True)
class HttpRequest:
    method: str
    url: str
    headers: Mapping[str, str] = field(repr=False)
    body: bytes | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status_code: int
    body: bytes | str | Mapping[str, Any]
    headers: Mapping[str, str] = field(default_factory=dict, repr=False)


class HttpTransport(Protocol):
    def send(self, request: HttpRequest) -> HttpResponse: ...


class ProviderAdapter(Protocol):
    @property
    def name(self) -> str: ...

    def search(self, request: SearchRequest) -> ProviderResult: ...
