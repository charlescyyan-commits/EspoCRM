"""Pure input/output contracts for official-brand qualification."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IdentitySignals:
    url: str
    redirect_target: str | None = None
    organization_name: str | None = None
    page_title: str | None = None
    copyright_text: str | None = None


@dataclass(frozen=True, slots=True)
class BrandFilterDecision:
    excluded: bool
    reason_code: str | None
    matched_brand_id: str | None
    audit_record: dict[str, object]
