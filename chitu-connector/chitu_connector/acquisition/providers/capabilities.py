"""Provider capability declarations shared by C20 capability ports.

This module is intentionally declarative.  It performs no provider I/O and
does not resolve credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Capability(Enum):
    """The bounded capability families authorized for Phase3C20 WP2."""

    SEARCH = "search"
    ENRICHMENT = "enrichment"
    COMPLETION = "completion"


@dataclass(frozen=True, slots=True)
class CapabilityDeclaration:
    """Static capabilities advertised by a provider implementation."""

    capability: Capability
    supports_streaming: bool = False
    supports_json_mode: bool = False
    max_context_tokens: int | None = None
    supports_vision: bool = False
