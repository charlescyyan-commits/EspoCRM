"""Narrow HTTP transport seam for the Brevo transactional-email API."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class BrevoHttpResponse:
    status_code: int
    body: Mapping[str, object] | None


class BrevoHttpClient(Protocol):
    """Transport seam. Tests inject a mock; adapters do not use HTTP directly."""

    def post_json(
        self,
        path: str,
        *,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> BrevoHttpResponse: ...


class BrevoTransportError(RuntimeError):
    """Sanitized transport failure; never embeds a response body or credentials."""


class UrllibBrevoHttpClient:
    """Explicit transport implementation for a future, opt-in runtime caller."""

    base_url = "https://api.brevo.com/v3"

    def post_json(
        self,
        path: str,
        *,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> BrevoHttpResponse:
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:  # nosec B310 - explicit opt-in transport seam
                return BrevoHttpResponse(response.status, _json_mapping(response.read()))
        except HTTPError as error:
            return BrevoHttpResponse(error.code, _json_mapping(error.read()))
        except (TimeoutError, URLError) as error:
            raise BrevoTransportError(error.__class__.__name__) from error


def _json_mapping(value: bytes) -> Mapping[str, object] | None:
    try:
        parsed = json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None
