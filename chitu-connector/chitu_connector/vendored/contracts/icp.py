"""Input contract for deterministic ICP planning."""

from __future__ import annotations

from dataclasses import dataclass, field
@dataclass(frozen=True, slots=True)
class ICPInput:
    """User-controlled ICP inputs; no external lookup is performed."""

    product: str
    target_countries: tuple[str, ...]
    customer_types: tuple[str, ...] = ()
    target_brands: tuple[str, ...] = ()
    company_size_min: int | None = None
    company_size_max: int | None = None
    include_terms: tuple[str, ...] = ()
    exclude_terms: tuple[str, ...] = ()
    languages: tuple[str, ...] = ("en",)
    source_preferences: tuple[str, ...] = ()
    expected_count: int = 100
    manual_keywords: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.product.strip():
            raise ValueError("product is required")
        if not self.target_countries:
            raise ValueError("at least one target country is required")
        if not self.languages:
            raise ValueError("at least one language is required")
        if self.expected_count <= 0:
            raise ValueError("expected_count must be positive")
        if self.company_size_min is not None and self.company_size_min < 0:
            raise ValueError("company_size_min cannot be negative")
        if (
            self.company_size_min is not None
            and self.company_size_max is not None
            and self.company_size_min > self.company_size_max
        ):
            raise ValueError("company_size_min cannot exceed company_size_max")
