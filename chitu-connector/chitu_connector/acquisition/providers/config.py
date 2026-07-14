"""Explicit, environment-backed configuration for provider adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from os import environ
from typing import Mapping
from urllib.parse import urlparse


class ProviderConfigurationError(ValueError):
    """Configuration is missing or unsafe for an adapter invocation."""


@dataclass(frozen=True, slots=True)
class ApifyConfig:
    api_token: str = field(repr=False)
    base_url: str = "https://api.apify.com"
    actor_id: str = "apify/google-search-scraper"
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        token = self.api_token.strip()
        if not token:
            raise ProviderConfigurationError("APIFY_API_TOKEN is required")
        object.__setattr__(self, "api_token", token)

        parsed = urlparse(self.base_url.rstrip("/"))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.query or parsed.fragment:
            raise ProviderConfigurationError("APIFY_API_BASE_URL must be an absolute HTTP(S) URL")
        if not self.actor_id.strip():
            raise ProviderConfigurationError("APIFY_ACTOR_ID is required")
        if self.timeout_seconds <= 0:
            raise ProviderConfigurationError("APIFY_TIMEOUT_SECONDS must be positive")

    @classmethod
    def from_env(cls, values: Mapping[str, str] | None = None) -> "ApifyConfig":
        source = environ if values is None else values
        token = source.get("APIFY_API_TOKEN", "")
        base_url = source.get("APIFY_API_BASE_URL", "https://api.apify.com")
        actor_id = source.get("APIFY_ACTOR_ID", "apify/google-search-scraper")
        raw_timeout = source.get("APIFY_TIMEOUT_SECONDS", "30")
        try:
            timeout = float(raw_timeout)
        except (TypeError, ValueError) as error:
            raise ProviderConfigurationError("APIFY_TIMEOUT_SECONDS must be numeric") from error
        return cls(token, base_url=base_url, actor_id=actor_id, timeout_seconds=timeout)


@dataclass(frozen=True, slots=True)
class SerperConfig:
    api_key: str = field(repr=False)
    base_url: str = "https://google.serper.dev"
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        key = self.api_key.strip()
        if not key:
            raise ProviderConfigurationError("SERPER_API_KEY is required")
        object.__setattr__(self, "api_key", key)

        parsed = urlparse(self.base_url.rstrip("/"))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.query or parsed.fragment:
            raise ProviderConfigurationError("SERPER_BASE_URL must be an absolute HTTP(S) URL")
        if self.timeout_seconds <= 0:
            raise ProviderConfigurationError("SERPER_TIMEOUT_SECONDS must be positive")

    @classmethod
    def from_env(cls, values: Mapping[str, str] | None = None) -> "SerperConfig":
        source = environ if values is None else values
        key = source.get("SERPER_API_KEY", "")
        base_url = source.get("SERPER_BASE_URL", "https://google.serper.dev")
        raw_timeout = source.get("SERPER_TIMEOUT_SECONDS", "30")
        try:
            timeout = float(raw_timeout)
        except (TypeError, ValueError) as error:
            raise ProviderConfigurationError("SERPER_TIMEOUT_SECONDS must be numeric") from error
        return cls(key, base_url=base_url, timeout_seconds=timeout)
