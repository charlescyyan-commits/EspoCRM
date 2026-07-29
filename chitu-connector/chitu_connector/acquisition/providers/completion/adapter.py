"""Provider-agnostic CompletionProvider bridge with injected transport only."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Mapping

from ...models import ProviderError, ProviderRateLimitError
from ..base import HttpRequest, HttpResponse, HttpTransport
from ..capabilities import Capability, CapabilityDeclaration
from ..cost import CostEnvelope
from ..taxonomy import classify_provider_error
from .base import CompletionCapability, CompletionRequest, CompletionResult


_SYSTEM_PROMPTS = {
    CompletionCapability.RESEARCH_EVIDENCE: (
        "Summarize and structure the provided evidence. Do not fabricate facts; "
        "state uncertainty when the evidence is insufficient."
    ),
    CompletionCapability.QUALIFICATION_INSIGHT: (
        "Provide contextual intelligence for operator review only. State uncertainty "
        "clearly and do not make final decisions."
    ),
    CompletionCapability.DRAFT_ASSISTANCE: (
        "Generate proposed text for operator review. The operator decides whether "
        "to use the output; do not initiate any external action."
    ),
    CompletionCapability.REPLY_ASSISTANCE: (
        "Provide advisory classification, sentiment, and suggested categorization "
        "for operator review. Do not alter any record state."
    ),
}


@dataclass(frozen=True, slots=True)
class CompletionConfig:
    """Resolved bridge configuration; the API key is never repr-visible."""

    api_key: str = field(repr=False)
    base_url: str
    default_model: str
    default_max_tokens: int = 4096
    default_temperature: float = 0.7


class CompletionBridgeProvider:
    """Provider-agnostic, operator-attributed completion capability bridge."""

    name = "COMPLETION_BRIDGE"

    def __init__(self, config: CompletionConfig, *, transport: HttpTransport) -> None:
        self._config = config
        self._transport = transport

    @property
    def capabilities(self) -> CapabilityDeclaration:
        return CapabilityDeclaration(Capability.COMPLETION, supports_json_mode=True)

    def complete(self, request: CompletionRequest) -> CompletionResult:
        _validate(request)
        http_request = self._build_request(request)
        started_at = time.monotonic()
        response = self._send(http_request)
        latency_ms = max(1, int((time.monotonic() - started_at) * 1000))
        payload = _decode_mapping(response)
        return self._normalize(payload, response.headers, request, latency_ms)

    def _build_request(self, request: CompletionRequest) -> HttpRequest:
        messages = [
            {"role": "system", "content": self._system_prompt(request)},
            {"role": "user", "content": request.prompt},
        ]
        body = {
            "model": request.model or self._config.default_model,
            "messages": messages,
            "max_tokens": request.max_tokens or self._config.default_max_tokens,
            "temperature": request.temperature if request.temperature is not None else self._config.default_temperature,
            "metadata": {"initiating_user": request.initiating_user},
        }
        return HttpRequest(
            method="POST",
            url=f"{self._config.base_url.rstrip('/')}/chat/completions",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._config.api_key}",
                "Idempotency-Key": request.idempotency_key,
            },
            body=json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        )

    def _system_prompt(self, request: CompletionRequest) -> str:
        context = "{}"
        if request.context is not None:
            try:
                context = json.dumps(request.context, separators=(",", ":"), sort_keys=True)
            except (TypeError, ValueError) as error:
                raise _provider_error("COMPLETION_INVALID_CONTEXT", "Completion context must be structured JSON", 400) from error
        return f"{_SYSTEM_PROMPTS[request.capability]}\nOperator purpose: {request.purpose}\nStructured context: {context}"

    def _send(self, request: HttpRequest) -> HttpResponse:
        try:
            response = self._transport.send(request)
        except TimeoutError as error:
            raise _provider_error("COMPLETION_TIMEOUT", "Completion bridge timed out", 0) from error
        except OSError as error:
            raise _provider_error("COMPLETION_TRANSPORT_ERROR", "Completion bridge transport failed", 0) from error
        if response.status_code >= 400:
            raise _http_error(response)
        return response

    def _normalize(
        self,
        payload: Mapping[str, Any],
        headers: Mapping[str, str],
        request: CompletionRequest,
        latency_ms: int,
    ) -> CompletionResult:
        choice = _first_choice(payload)
        message = choice.get("message")
        content = message.get("content") if isinstance(message, Mapping) else choice.get("content")
        if not isinstance(content, str):
            raise _provider_error("COMPLETION_MALFORMED_RESPONSE", "Completion bridge returned invalid content", 400)

        model = payload.get("model") if isinstance(payload.get("model"), str) else request.model or self._config.default_model
        if not model:
            raise _provider_error("COMPLETION_MALFORMED_RESPONSE", "Completion bridge returned no model", 400)
        usage = payload.get("usage") if isinstance(payload.get("usage"), Mapping) else {}
        provider_request_id = _header(headers, "x-request-id") or _stable_identifier("request", request.idempotency_key)
        return CompletionResult(
            completion_id=_stable_identifier("completion", request.idempotency_key),
            capability=request.capability,
            content=content,
            finish_reason=_normalize_finish_reason(choice.get("finish_reason")),
            model=model,
            cost=CostEnvelope(
                tokens_in=_non_negative_int(usage.get("prompt_tokens")),
                tokens_out=_non_negative_int(usage.get("completion_tokens")),
                model=model,
                latency_ms=latency_ms,
                provider_request_id=provider_request_id,
                currency="USD",
                amount=0.0,
            ),
            prompt_template_version=request.prompt_template_version,
        )


def _validate(request: CompletionRequest) -> None:
    if not isinstance(request.capability, CompletionCapability):
        raise _provider_error("COMPLETION_INVALID_CAPABILITY", "Completion capability is not authorized", 400)
    if not request.initiating_user.strip():
        raise _provider_error("COMPLETION_MISSING_INITIATING_USER", "Completion requires an initiating user", 400)
    if not request.purpose.strip() or not request.prompt.strip():
        raise _provider_error("COMPLETION_INVALID_REQUEST", "Completion purpose and prompt are required", 400)


def _decode_mapping(response: HttpResponse) -> Mapping[str, Any]:
    if isinstance(response.body, Mapping):
        return response.body
    try:
        payload = json.loads(response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body)
    except (UnicodeDecodeError, TypeError, json.JSONDecodeError) as error:
        raise _provider_error("COMPLETION_MALFORMED_RESPONSE", "Completion bridge returned malformed JSON", 400) from error
    if not isinstance(payload, Mapping):
        raise _provider_error("COMPLETION_MALFORMED_RESPONSE", "Completion bridge returned an invalid response", 400)
    return payload


def _first_choice(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], Mapping):
        raise _provider_error("COMPLETION_MALFORMED_RESPONSE", "Completion bridge returned no completion choice", 400)
    return choices[0]


def _normalize_finish_reason(value: object) -> str:
    normalized = value.casefold() if isinstance(value, str) else ""
    return {
        "stop": "STOP",
        "length": "LENGTH",
        "content_filter": "CONTENT_FILTER",
        "tool_calls": "STOP",
    }.get(normalized, "STOP")


def _non_negative_int(value: object) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


def _stable_identifier(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def _header(headers: Mapping[str, str], name: str) -> str | None:
    for key, value in headers.items():
        if key.casefold() == name and isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _http_error(response: HttpResponse) -> ProviderError:
    if _is_content_filter(response):
        return _provider_error(
            "COMPLETION_CONTENT_FILTER",
            "Completion content policy rejected the request; operator revision is required",
            response.status_code,
        )
    if response.status_code == 429:
        return _rate_limit_error(
            "COMPLETION_RATE_LIMITED",
            "Completion bridge rate limit reached",
            _parse_retry_after(response.headers),
        )
    if response.status_code >= 500:
        return _provider_error("COMPLETION_UPSTREAM_ERROR", "Completion bridge service failed", response.status_code)
    if response.status_code in {401, 403}:
        return _provider_error("COMPLETION_AUTH_FAILED", "Completion bridge authentication failed", response.status_code)
    if response.status_code == 402:
        return _provider_error("COMPLETION_QUOTA_EXHAUSTED", "Completion bridge quota exhausted", response.status_code)
    return _provider_error(f"COMPLETION_HTTP_{response.status_code}", "Completion bridge rejected the request", response.status_code)


def _is_content_filter(response: HttpResponse) -> bool:
    if response.status_code != 400:
        return False
    body = _body_string(response).casefold()
    return any(marker in body for marker in ("content_filter", "content filter", "content_policy", "safety", "moderation", "inappropriate"))


def _body_string(response: HttpResponse) -> str:
    if isinstance(response.body, Mapping):
        return json.dumps(response.body, separators=(",", ":"), sort_keys=True)
    if isinstance(response.body, bytes):
        return response.body.decode("utf-8", errors="replace")
    return response.body


def _provider_error(code: str, safe_message: str, status_code: int) -> ProviderError:
    classified = classify_provider_error(status_code, code)
    error = ProviderError(code, safe_message, retryable=classified.retryable)
    error.error_class = classified.error_class
    return error


def _rate_limit_error(code: str, safe_message: str, retry_after: int | None) -> ProviderRateLimitError:
    classified = classify_provider_error(429, code, retry_after=retry_after)
    error = ProviderRateLimitError(code, safe_message, retryable=classified.retryable, retry_after=classified.retry_after)
    error.error_class = classified.error_class
    return error


def _parse_retry_after(headers: Mapping[str, str]) -> int | None:
    for key in ("retry-after", "Retry-After"):
        value = headers.get(key)
        if value is None:
            continue
        try:
            seconds = int(value)
        except (TypeError, ValueError):
            continue
        if seconds >= 0:
            return seconds
    return None
