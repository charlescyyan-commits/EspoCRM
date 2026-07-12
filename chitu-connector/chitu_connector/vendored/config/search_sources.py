"""Search-source configuration is deliberately separate from planning logic."""

from __future__ import annotations

from enum import StrEnum


class SearchSource(StrEnum):
    GOOGLE_SEARCH = "GOOGLE_SEARCH"
    GOOGLE_MAPS = "GOOGLE_MAPS"
    INDUSTRY_DIRECTORY = "INDUSTRY_DIRECTORY"
    CUSTOM_IMPORT = "CUSTOM_IMPORT"


DEFAULT_SOURCES: tuple[SearchSource, ...] = (
    SearchSource.GOOGLE_SEARCH,
    SearchSource.GOOGLE_MAPS,
    SearchSource.INDUSTRY_DIRECTORY,
    SearchSource.CUSTOM_IMPORT,
)

SOURCE_RATIONALES: dict[SearchSource, str] = {
    SearchSource.GOOGLE_SEARCH: "Broad, deterministic query discovery plan only.",
    SearchSource.GOOGLE_MAPS: "Local business discovery plan only; no maps request is made.",
    SearchSource.INDUSTRY_DIRECTORY: "Industry-directory discovery plan only.",
    SearchSource.CUSTOM_IMPORT: "Reserved for a future user-provided local import.",
}
