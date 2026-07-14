from __future__ import annotations

from unittest import TestCase

from chitu_connector.acquisition.master_prospect import MasterProspect
from chitu_connector.acquisition.website_research import (
    FetchStatus,
    HtmlSanitizer,
    PageType,
    ResearchEligibilityChecker,
    ResearchErrorCode,
    ResearchStatus,
    WebsiteHttpResponse,
    WebsitePageClassifier,
    WebsiteResearchPipeline,
    WebsiteTransportFailure,
    WebsiteUrlPlanner,
)


TIME = "2026-07-13T00:00:00Z"
DOMAIN = "acme-vendor.com"
ROOT = f"https://{DOMAIN}/"
HTML = "<html><head><title>Acme Products</title><meta name='description' content='Public catalog'></head><body><h1>Acme Products</h1><p>Visible &amp; useful text.</p></body></html>"


def master(*, website: str | None = ROOT, domain: str | None = DOMAIN) -> MasterProspect:
    return MasterProspect(
        master_id="mp_fixture_acme",
        normalized_domain=domain,
        canonical_name="acme",
        website=website,
        country="US",
        city="Austin",
        source_count=1,
        provider_list=("APIFY",),
        matched_raw_records=(),
        provider_metadata=(),
        discovery_history=(),
        merge_traces=(),
        created_at=TIME,
        updated_at=TIME,
    )


def response(
    url: str,
    *,
    status: int = 200,
    body: bytes | str = HTML,
    content_type: str = "text/html; charset=utf-8",
    final_url: str | None = None,
    redirects: tuple[str, ...] = (),
    headers: dict[str, str] | None = None,
) -> WebsiteHttpResponse:
    merged_headers = {"Content-Type": content_type}
    if headers:
        merged_headers.update(headers)
    return WebsiteHttpResponse(status, merged_headers, body, final_url or url, redirects, 4)


class FakeTransport:
    def __init__(self, fixtures: dict[str, WebsiteHttpResponse | Exception] | None = None, *, default: WebsiteHttpResponse | Exception | None = None) -> None:
        self.fixtures = fixtures or {}
        self.default = default
        self.requests = []

    def fetch(self, request):
        self.requests.append(request)
        fixture = self.fixtures.get(request.url, self.default)
        if fixture is None:
            fixture = response(request.url, status=404, body="", final_url=request.url)
        if isinstance(fixture, Exception):
            raise fixture
        return fixture


def pipeline(transport: FakeTransport) -> WebsiteResearchPipeline:
    return WebsiteResearchPipeline(transport, clock=lambda: TIME)


def page_for(result, url: str):
    return next(page for page in result.pages if page.requested_url == url)


class EligibilityTests(TestCase):
    def test_allows_http_https_and_domain_only_public_targets(self) -> None:
        checker = ResearchEligibilityChecker()
        self.assertEqual(checker.check(master(website="http://ACME-vendor.com/catalog")).root_url, "http://acme-vendor.com/")
        self.assertEqual(checker.check(master(website="https://acme-vendor.com/")).root_url, ROOT)
        self.assertEqual(checker.check(master(website=None, domain=DOMAIN)).root_url, ROOT)

    def test_rejects_empty_unsafe_and_non_http_targets(self) -> None:
        checker = ResearchEligibilityChecker()
        cases = (
            master(website=None, domain=None),
            master(website="http://localhost/"),
            master(website="http://127.0.0.1/"),
            master(website="http://10.0.0.8/"),
            master(website="http://[::1]/"),
            master(website="file:///etc/passwd"),
            master(website="javascript:alert(1)"),
            master(website="https://acme-vendor.com/catalog.pdf"),
        )
        for candidate in cases:
            with self.subTest(target=candidate.website or candidate.normalized_domain):
                result = checker.check(candidate)
                self.assertFalse(result.eligible)
                self.assertIn(result.error.code, {ResearchErrorCode.INVALID_TARGET, ResearchErrorCode.UNSAFE_TARGET})


class UrlPlanningTests(TestCase):
    def test_plan_is_stable_deduplicated_bounded_and_same_domain(self) -> None:
        plan = WebsiteUrlPlanner().plan("https://WWW.acme-vendor.com/catalog?q=1#fragment")
        self.assertEqual(len(plan), 10)
        self.assertEqual([item.page_type for item in plan], [
            PageType.HOME, PageType.ABOUT, PageType.ABOUT, PageType.CONTACT,
            PageType.CONTACT, PageType.PRODUCTS, PageType.PRODUCTS,
            PageType.PRODUCTS, PageType.BRANDS, PageType.BRANDS,
        ])
        self.assertEqual(plan[0].requested_url, ROOT)
        self.assertEqual(len({item.requested_url for item in plan}), len(plan))
        self.assertTrue(all(item.requested_url.startswith(ROOT) for item in plan))
        self.assertTrue(all("?" not in item.requested_url and "#" not in item.requested_url for item in plan))


class SanitizationAndClassificationTests(TestCase):
    def test_sanitizer_removes_non_visible_elements_and_extracts_safe_content(self) -> None:
        raw = """<html><head><title> Acme &amp; Co </title><meta name='description' content='  Public  details '><style>bad</style><script>secret()</script></head><body><h1>Products</h1><p> Visible &amp; useful </p><div hidden>hidden</div><iframe>iframe</iframe><a href='/contact'> Contact </a></body></html>"""
        sanitized = HtmlSanitizer().sanitize(raw)
        self.assertEqual(sanitized.title, "Acme & Co")
        self.assertEqual(sanitized.meta_description, "Public details")
        self.assertEqual(sanitized.text_content, "Acme & Co Products Visible & useful Contact")
        self.assertEqual(sanitized.links, ("/contact",))
        self.assertIn("REMOVED_SCRIPT", sanitized.actions)
        self.assertIn("REMOVED_STYLE", sanitized.actions)
        self.assertIn("REMOVED_HIDDEN_CONTENT", sanitized.actions)
        self.assertIn("REMOVED_IFRAME", sanitized.actions)

    def test_url_path_rule_wins_when_title_conflicts(self) -> None:
        page_type, reason = WebsitePageClassifier().classify(
            f"{ROOT}contact-us", f"{ROOT}contact-us", "Products", (), PageType.PRODUCTS
        )
        self.assertEqual(page_type, PageType.CONTACT)
        self.assertIn("Explicit", reason)

    def test_classifier_covers_home_about_contact_products_brands_and_other(self) -> None:
        classifier = WebsitePageClassifier()
        cases = (
            (ROOT, PageType.HOME),
            (f"{ROOT}about/company", PageType.ABOUT),
            (f"{ROOT}contact", PageType.CONTACT),
            (f"{ROOT}collections", PageType.PRODUCTS),
            (f"{ROOT}our-brands", PageType.BRANDS),
            (f"{ROOT}news", PageType.OTHER),
        )
        for url, expected in cases:
            with self.subTest(url=url):
                actual, _ = classifier.classify(url, url, None, (), PageType.OTHER)
                self.assertEqual(actual, expected)


class FetchPolicyTests(TestCase):
    def test_safe_redirect_is_processed_and_malicious_redirect_is_blocked(self) -> None:
        for status in (301, 302):
            with self.subTest(status=status):
                safe_transport = FakeTransport({ROOT: response(ROOT, status=status, final_url=f"https://www.{DOMAIN}/", redirects=(ROOT,))})
                safe_result = pipeline(safe_transport).research(master())
                self.assertEqual(page_for(safe_result, ROOT).fetch_status, FetchStatus.SUCCESS)

        unsafe_transport = FakeTransport({ROOT: response(ROOT, status=302, final_url="http://127.0.0.1/", redirects=(ROOT,))})
        unsafe_result = pipeline(unsafe_transport).research(master())
        page = page_for(unsafe_result, ROOT)
        self.assertEqual(page.error.code, ResearchErrorCode.REDIRECT_ERROR)
        self.assertFalse(page.error.retryable)

        cross_domain = FakeTransport({ROOT: response(ROOT, status=302, final_url="https://evil-vendor.com/", redirects=(ROOT,))})
        self.assertEqual(page_for(pipeline(cross_domain).research(master()), ROOT).error.code, ResearchErrorCode.REDIRECT_ERROR)

    def test_redirect_limit_and_supported_redirect_statuses_are_handled(self) -> None:
        too_many = FakeTransport({ROOT: response(ROOT, status=302, redirects=(ROOT, ROOT, ROOT, ROOT, ROOT))})
        self.assertEqual(page_for(pipeline(too_many).research(master()), ROOT).error.code, ResearchErrorCode.REDIRECT_ERROR)
        for status in (307, 308):
            with self.subTest(status=status):
                result = pipeline(FakeTransport({ROOT: response(ROOT, status=status)})).research(master())
                self.assertEqual(page_for(result, ROOT).fetch_status, FetchStatus.SUCCESS)

    def test_http_error_classes_are_deterministic(self) -> None:
        cases = (
            (204, ResearchErrorCode.EMPTY_CONTENT, False),
            (400, ResearchErrorCode.HTTP_CLIENT_ERROR, False),
            (401, ResearchErrorCode.ACCESS_DENIED, False),
            (403, ResearchErrorCode.ACCESS_DENIED, False),
            (408, ResearchErrorCode.NETWORK_TIMEOUT, True),
            (404, ResearchErrorCode.NOT_FOUND, False),
            (429, ResearchErrorCode.RATE_LIMITED, True),
            (500, ResearchErrorCode.SERVER_ERROR, True),
            (502, ResearchErrorCode.SERVER_ERROR, True),
            (503, ResearchErrorCode.SERVER_ERROR, True),
            (504, ResearchErrorCode.SERVER_ERROR, True),
        )
        for status, code, retryable in cases:
            with self.subTest(status=status):
                result = pipeline(FakeTransport({ROOT: response(ROOT, status=status, body="")})).research(master())
                error = page_for(result, ROOT).error
                self.assertEqual(error.code, code)
                self.assertEqual(error.retryable, retryable)

    def test_timeout_size_content_type_empty_and_malformed_body_are_classified(self) -> None:
        cases = (
            (TimeoutError(), ResearchErrorCode.NETWORK_TIMEOUT),
            (response(ROOT, body="x" * 600_000), ResearchErrorCode.RESPONSE_TOO_LARGE),
            (response(ROOT, content_type="application/pdf"), ResearchErrorCode.UNSUPPORTED_CONTENT_TYPE),
            (response(ROOT, content_type="image/png"), ResearchErrorCode.UNSUPPORTED_CONTENT_TYPE),
            (response(ROOT, body="<html><body><script>only</script></body></html>"), ResearchErrorCode.EMPTY_CONTENT),
            (response(ROOT, body=b"\xff\xfe"), ResearchErrorCode.MALFORMED_HTML),
        )
        for fixture, expected in cases:
            with self.subTest(expected=expected):
                result = pipeline(FakeTransport({ROOT: fixture})).research(master())
                self.assertEqual(page_for(result, ROOT).error.code, expected)

    def test_transport_failure_categories_do_not_expose_headers_or_messages(self) -> None:
        for code in (ResearchErrorCode.DNS_ERROR, ResearchErrorCode.TLS_ERROR, ResearchErrorCode.NETWORK_CONNECTION_ERROR):
            with self.subTest(code=code):
                transport = FakeTransport({ROOT: WebsiteTransportFailure(code, retryable=True)})
                result = pipeline(transport).research(master())
                self.assertEqual(page_for(result, ROOT).error.code, code)

        response_with_secret = response(ROOT, headers={"Authorization": "Bearer secret", "X-API-Key": "secret"})
        output = pipeline(FakeTransport({ROOT: response_with_secret})).research(master()).to_dict()
        self.assertNotIn("secret", str(output))
        self.assertNotIn("Authorization", str(output))


class PipelineTests(TestCase):
    def test_completed_result_has_deterministic_order_complete_trace_and_no_master_mutation(self) -> None:
        transport = FakeTransport(default=response(ROOT))
        input_master = master()
        result = pipeline(transport).research(input_master)

        self.assertEqual(result.research_status, ResearchStatus.COMPLETED)
        self.assertEqual(result.successful_page_count, 10)
        self.assertEqual(result.failed_page_count, 0)
        self.assertEqual(len(result.trace), 10)
        self.assertEqual([request.url for request in transport.requests], [page.requested_url for page in result.pages])
        self.assertEqual(input_master, master())
        self.assertEqual(result.to_dict()["research_status"], "COMPLETED")

    def test_partial_failed_and_not_eligible_results_have_clear_statuses(self) -> None:
        partial = pipeline(FakeTransport({ROOT: response(ROOT)})).research(master())
        self.assertEqual(partial.research_status, ResearchStatus.PARTIAL)
        self.assertEqual(partial.successful_page_count, 1)
        self.assertEqual(partial.failed_page_count, 9)

        failed = pipeline(FakeTransport(default=response(ROOT, status=500, body=""))).research(master())
        self.assertEqual(failed.research_status, ResearchStatus.FAILED)
        self.assertEqual(failed.successful_page_count, 0)
        self.assertEqual(failed.failed_page_count, 10)

        transport = FakeTransport(default=response(ROOT))
        not_eligible = pipeline(transport).research(master(website="http://localhost/", domain="localhost"))
        self.assertEqual(not_eligible.research_status, ResearchStatus.NOT_ELIGIBLE)
        self.assertEqual(len(transport.requests), 0)
        self.assertEqual(not_eligible.trace[0].error_classification, ResearchErrorCode.UNSAFE_TARGET)
