from __future__ import annotations

from unittest import TestCase

from chitu_connector.acquisition.evidence_extraction import WebsiteResearchEvidenceExtractor
from chitu_connector.acquisition.website_research import (
    FetchStatus,
    PageType,
    ResearchStatus,
    WebsiteResearchPageResult,
    WebsiteResearchPipelineResult,
)


TIME = "2026-07-13T00:00:00Z"


def page(
    *,
    requested_url: str = "https://acme.example/",
    final_url: str | None = "https://acme.example/",
    title: str | None = "Acme Products",
    meta_description: str | None = "Industrial products for distributors.",
    text_content: str | None = "Acme sells industrial products. Contact our team for details.",
    fetch_status: FetchStatus = FetchStatus.SUCCESS,
) -> WebsiteResearchPageResult:
    return WebsiteResearchPageResult(
        requested_url=requested_url,
        final_url=final_url,
        page_type=PageType.HOME,
        status_code=200,
        content_type="text/html",
        title=title,
        text_content=text_content,
        raw_html=None,
        meta_description=meta_description,
        links=(),
        fetch_status=fetch_status,
        error=None,
        redirect_chain=(),
        fetched_at=TIME,
        classification_reason="Fixture page.",
        sanitization_actions=(),
    )


def pipeline_result(*pages: WebsiteResearchPageResult) -> dict[str, object]:
    return WebsiteResearchPipelineResult(
        master_id="mp-acme",
        normalized_domain="acme.example",
        canonical_name="Acme",
        root_url="https://acme.example/",
        pages=pages,
        research_status=ResearchStatus.COMPLETED,
        successful_page_count=len(pages),
        failed_page_count=0,
        selected_page_types=(PageType.HOME,),
        started_at=TIME,
        completed_at=TIME,
        trace=(),
    ).to_dict()


class WebsiteResearchEvidenceExtractorTests(TestCase):
    def setUp(self) -> None:
        self.extractor = WebsiteResearchEvidenceExtractor()

    def test_extracts_factual_observations_from_a_normal_page(self) -> None:
        items = self.extractor.extract(pipeline_result(page()))

        self.assertEqual([item.claim_type for item in items], ["page_title", "meta_description", "visible_text"])
        self.assertEqual([item.evidence_type for item in items], ["title", "meta_description", "visible_text"])
        self.assertEqual([item.confidence for item in items], [0.95, 0.90, 0.85])
        self.assertTrue(all(item.source_url == "https://acme.example/" for item in items))
        self.assertEqual(items[-1].claim, "Acme sells industrial products.")
        self.assertEqual(items[-1].evidence_text, "Acme sells industrial products. Contact our team for details.")
        self.assertEqual(items[0].captured_at.isoformat(), "2026-07-13T00:00:00+00:00")
        self.assertTrue(all(item.evidence_id.startswith("ev_") for item in items))

    def test_extracts_multiple_pages_in_input_order(self) -> None:
        home = page(requested_url="https://acme.example/", final_url="https://acme.example/", title="Acme Home", meta_description=None, text_content="Home observation.")
        contact = page(requested_url="https://acme.example/contact", final_url="https://acme.example/contact", title="Contact Acme", meta_description=None, text_content="Call Acme sales.")

        items = self.extractor.extract(pipeline_result(home, contact))

        self.assertEqual([item.source_url for item in items], ["https://acme.example/", "https://acme.example/", "https://acme.example/contact", "https://acme.example/contact"])
        self.assertEqual([item.claim_type for item in items], ["page_title", "visible_text", "page_title", "visible_text"])

    def test_skips_empty_content_and_unsuccessful_pages(self) -> None:
        empty = page(title="", meta_description="  ", text_content="\n\t")
        failed = page(title="Ignored", fetch_status=FetchStatus.FAILED)

        self.assertEqual(self.extractor.extract(pipeline_result(empty, failed)), [])

    def test_skips_page_when_no_valid_source_url_is_available(self) -> None:
        invalid_source = page(requested_url="", final_url=None)

        self.assertEqual(self.extractor.extract(pipeline_result(invalid_source)), [])

    def test_bounds_visible_text_to_the_existing_compact_evidence_limit(self) -> None:
        long_text = "A" * 1_200

        items = self.extractor.extract(pipeline_result(page(title=None, meta_description=None, text_content=long_text)))

        self.assertEqual(len(items), 1)
        self.assertEqual(len(items[0].evidence_text), 1_000)
        self.assertEqual(len(items[0].claim), 500)

    def test_rejects_malformed_input_without_side_effects(self) -> None:
        self.assertEqual(self.extractor.extract({}), [])
        self.assertEqual(self.extractor.extract({"pages": "not-a-list"}), [])
        self.assertEqual(self.extractor.extract({"pages": [None, {"fetch_status": "SUCCESS"}]}), [])

    def test_deduplicates_identical_source_backed_evidence_deterministically(self) -> None:
        first = page(requested_url="https://acme.example/", final_url="https://acme.example/", title="Acme", meta_description=None, text_content="Acme products.")
        duplicate = page(requested_url="https://acme.example/home", final_url="https://acme.example/", title="Acme", meta_description=None, text_content="Acme products.")

        first_run = self.extractor.extract(pipeline_result(first, duplicate))
        second_run = self.extractor.extract(pipeline_result(first, duplicate))

        self.assertEqual(len(first_run), 2)
        self.assertEqual([item.to_dict() for item in first_run], [item.to_dict() for item in second_run])
        self.assertEqual([item.evidence_text for item in first_run], ["Acme", "Acme products."])


if __name__ == "__main__":
    import unittest

    unittest.main()
