"""Offline, deterministic foundation for research of a Master Prospect website.

The module is intentionally isolated from provider adapters, the acquisition
worker/runner, CRM, persistence, browser tooling, and AI.  A caller must inject
the transport; production network execution is not supplied by this phase.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import StrEnum
from html.parser import HTMLParser
import ipaddress
import re
from typing import Any, Callable, Mapping, Protocol

from .master_prospect import MasterProspect
from .normalization import normalize_domain


DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_RESPONSE_BYTES = 512_000
DEFAULT_MAX_REDIRECTS = 4
MAX_TEXT_CHARS = 100_000
MAX_TITLE_CHARS = 512
MAX_META_DESCRIPTION_CHARS = 1_024
MAX_LINKS = 128


class PageType(StrEnum):
    HOME = "HOME"
    ABOUT = "ABOUT"
    CONTACT = "CONTACT"
    PRODUCTS = "PRODUCTS"
    BRANDS = "BRANDS"
    OTHER = "OTHER"


class ResearchStatus(StrEnum):
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    PLANNED = "PLANNED"
    PARTIAL = "PARTIAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FetchStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    NOT_FETCHED = "NOT_FETCHED"


class ResearchErrorCode(StrEnum):
    INVALID_TARGET = "INVALID_TARGET"
    UNSAFE_TARGET = "UNSAFE_TARGET"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    NETWORK_CONNECTION_ERROR = "NETWORK_CONNECTION_ERROR"
    DNS_ERROR = "DNS_ERROR"
    TLS_ERROR = "TLS_ERROR"
    REDIRECT_ERROR = "REDIRECT_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    ACCESS_DENIED = "ACCESS_DENIED"
    NOT_FOUND = "NOT_FOUND"
    SERVER_ERROR = "SERVER_ERROR"
    UNSUPPORTED_CONTENT_TYPE = "UNSUPPORTED_CONTENT_TYPE"
    RESPONSE_TOO_LARGE = "RESPONSE_TOO_LARGE"
    MALFORMED_HTML = "MALFORMED_HTML"
    EMPTY_CONTENT = "EMPTY_CONTENT"
    HTTP_CLIENT_ERROR = "HTTP_CLIENT_ERROR"


@dataclass(frozen=True, slots=True)
class ResearchEligibility:
    eligible: bool
    root_url: str | None
    normalized_domain: str | None
    error: "WebsiteResearchError | None" = None
    reason: str = ""


@dataclass(frozen=True, slots=True)
class WebsiteResearchError:
    code: ResearchErrorCode
    retryable: bool
    safe_message: str


@dataclass(frozen=True, slots=True)
class WebsiteResearchPlanRequest:
    master_id: str
    canonical_name: str | None
    normalized_domain: str | None
    website: str | None
    country: str | None
    city: str | None
    requested_at: str

    @classmethod
    def from_master(cls, master: MasterProspect, requested_at: str) -> "WebsiteResearchPlanRequest":
        return cls(
            master_id=master.master_id,
            canonical_name=master.canonical_name,
            normalized_domain=master.normalized_domain,
            website=master.website,
            country=master.country,
            city=master.city,
            requested_at=requested_at,
        )

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class UrlPlanItem:
    requested_url: str
    page_type: PageType
    planning_rule: str


@dataclass(frozen=True, slots=True)
class WebsiteHttpRequest:
    url: str
    method: str = "GET"
    headers: Mapping[str, str] = field(default_factory=lambda: {"Accept": "text/html,application/xhtml+xml"}, repr=False)
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES
    max_redirects: int = DEFAULT_MAX_REDIRECTS


@dataclass(frozen=True, slots=True)
class WebsiteHttpResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes | str
    final_url: str
    redirect_chain: tuple[str, ...] = ()
    elapsed_ms: int = 0


class WebsiteTransport(Protocol):
    def fetch(self, request: WebsiteHttpRequest) -> WebsiteHttpResponse: ...


class WebsiteTransportFailure(Exception):
    """A fixture-friendly transport failure with a deterministic category."""

    def __init__(self, code: ResearchErrorCode, *, retryable: bool) -> None:
        super().__init__(code.value)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True, slots=True)
class _ParsedUrl:
    scheme: str
    hostname: str
    path: str


_ABSOLUTE_URL = re.compile(
    r"^(?P<scheme>[A-Za-z][A-Za-z0-9+.-]*)://(?P<authority>[^/?#]*)(?P<path>[^?#]*)(?:\?[^#]*)?(?:#.*)?$"
)


@dataclass(frozen=True, slots=True)
class WebsiteResearchPageResult:
    requested_url: str
    final_url: str | None
    page_type: PageType
    status_code: int | None
    content_type: str | None
    title: str | None
    text_content: str | None
    raw_html: str | None
    meta_description: str | None
    links: tuple[str, ...]
    fetch_status: FetchStatus
    error: WebsiteResearchError | None
    redirect_chain: tuple[str, ...]
    fetched_at: str
    classification_reason: str
    sanitization_actions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class WebsiteResearchPipelineTrace:
    planning_rule: str
    selected_url: str
    page_type: PageType
    fetch_outcome: FetchStatus
    classification_reason: str
    sanitization_actions: tuple[str, ...]
    error_classification: ResearchErrorCode | None

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class WebsiteResearchPipelineResult:
    master_id: str
    normalized_domain: str | None
    canonical_name: str | None
    root_url: str | None
    pages: tuple[WebsiteResearchPageResult, ...]
    research_status: ResearchStatus
    successful_page_count: int
    failed_page_count: int
    selected_page_types: tuple[PageType, ...]
    started_at: str
    completed_at: str
    trace: tuple[WebsiteResearchPipelineTrace, ...]

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


class ResearchEligibilityChecker:
    """Validates a Master Prospect target before planning or transport access."""

    def check(self, master: MasterProspect) -> ResearchEligibility:
        candidate = master.website or master.normalized_domain
        if not candidate:
            return _ineligible(ResearchErrorCode.INVALID_TARGET, "Master Prospect has no website or domain.")
        root_url, domain, error = _canonical_root_url(candidate)
        if error:
            return _ineligible(error.code, error.safe_message, error)
        return ResearchEligibility(True, root_url, domain, None, "Valid public HTTP(S) website target.")


class WebsiteUrlPlanner:
    """Produces a bounded, same-domain URL plan in a fixed order."""

    _PATHS: tuple[tuple[PageType, tuple[str, ...]], ...] = (
        (PageType.HOME, ("/",)),
        (PageType.ABOUT, ("/about", "/about-us")),
        (PageType.CONTACT, ("/contact", "/contact-us")),
        (PageType.PRODUCTS, ("/products", "/shop", "/store")),
        (PageType.BRANDS, ("/brands", "/our-brands")),
    )
    MAX_TOTAL_URLS = 10

    def plan(self, root_url: str) -> tuple[UrlPlanItem, ...]:
        root, domain, error = _canonical_root_url(root_url)
        if error or not root or not domain:
            return ()
        items: list[UrlPlanItem] = []
        seen: set[str] = set()
        for page_type, paths in self._PATHS:
            for path in paths:
                url = _normalize_url(f"{root.rstrip('/')}{path}")
                if url in seen or not _same_root_domain(url, domain):
                    continue
                seen.add(url)
                items.append(UrlPlanItem(url, page_type, f"DEFAULT_{page_type.value}_PATH"))
                if len(items) >= self.MAX_TOTAL_URLS:
                    return tuple(items)
        return tuple(items)


class WebsitePageClassifier:
    """Rule-only classifier: explicit URL path, title/headings, plan, then OTHER."""

    def classify(
        self,
        requested_url: str,
        final_url: str,
        title: str | None,
        headings: tuple[str, ...],
        planned_type: PageType,
    ) -> tuple[PageType, str]:
        for value, source in ((final_url, "final URL"), (requested_url, "requested URL")):
            matched = _page_type_from_path(value)
            if matched:
                return matched, f"Explicit {source} path rule: {matched.value}."
        text = " ".join(filter(None, (title, *headings))).casefold()
        for page_type, words in _CLASSIFICATION_WORDS:
            if any(word in text for word in words):
                return page_type, f"Title/heading keyword rule: {page_type.value}."
        if planned_type is not PageType.OTHER:
            return planned_type, f"Planner fallback: {planned_type.value}."
        return PageType.OTHER, "No deterministic URL, title, heading, or planner rule matched."


class HtmlSanitizer:
    """Extracts bounded visible text and minimal metadata using only stdlib HTMLParser."""

    def sanitize(self, raw_html: str) -> "SanitizedHtml":
        parser = _SanitizingParser()
        try:
            parser.feed(raw_html)
            parser.close()
        except (ValueError, AssertionError) as error:
            raise ValueError("HTML parser rejected the response body") from error
        text = _collapse_whitespace(" ".join(parser.visible_text))
        actions = set(parser.actions)
        if text != " ".join(parser.visible_text).strip():
            actions.add("COLLAPSED_WHITESPACE")
        if len(text) > MAX_TEXT_CHARS:
            text = text[:MAX_TEXT_CHARS]
            actions.add("TRUNCATED_TEXT")
        title = _collapse_whitespace(" ".join(parser.title_parts))[:MAX_TITLE_CHARS] or None
        meta_description = _collapse_whitespace(parser.meta_description)[:MAX_META_DESCRIPTION_CHARS] or None
        return SanitizedHtml(
            title=title,
            text_content=text,
            meta_description=meta_description,
            links=tuple(parser.links[:MAX_LINKS]),
            headings=tuple(_collapse_whitespace(value) for value in parser.headings if _collapse_whitespace(value)),
            actions=tuple(sorted(actions)),
        )


@dataclass(frozen=True, slots=True)
class SanitizedHtml:
    title: str | None
    text_content: str
    meta_description: str | None
    links: tuple[str, ...]
    headings: tuple[str, ...]
    actions: tuple[str, ...]


class WebsiteResearchPipeline:
    """Runs eligibility, planning, injected transport, sanitization, and tracing."""

    def __init__(
        self,
        transport: WebsiteTransport,
        *,
        eligibility_checker: ResearchEligibilityChecker | None = None,
        url_planner: WebsiteUrlPlanner | None = None,
        classifier: WebsitePageClassifier | None = None,
        sanitizer: HtmlSanitizer | None = None,
        clock: Callable[[], str] | None = None,
    ) -> None:
        self._transport = transport
        self._eligibility = eligibility_checker or ResearchEligibilityChecker()
        self._planner = url_planner or WebsiteUrlPlanner()
        self._classifier = classifier or WebsitePageClassifier()
        self._sanitizer = sanitizer or HtmlSanitizer()
        self._clock = clock or _utc_timestamp

    def research(self, master: MasterProspect) -> WebsiteResearchPipelineResult:
        started_at = self._clock()
        request = WebsiteResearchPlanRequest.from_master(master, started_at)
        eligibility = self._eligibility.check(master)
        if not eligibility.eligible:
            trace = WebsiteResearchPipelineTrace(
                planning_rule="ELIGIBILITY_REJECTED",
                selected_url=request.website or request.normalized_domain or "",
                page_type=PageType.OTHER,
                fetch_outcome=FetchStatus.NOT_FETCHED,
                classification_reason=eligibility.reason,
                sanitization_actions=(),
                error_classification=eligibility.error.code if eligibility.error else None,
            )
            return WebsiteResearchPipelineResult(
                master_id=request.master_id,
                normalized_domain=request.normalized_domain,
                canonical_name=request.canonical_name,
                root_url=None,
                pages=(),
                research_status=ResearchStatus.NOT_ELIGIBLE,
                successful_page_count=0,
                failed_page_count=0,
                selected_page_types=(),
                started_at=started_at,
                completed_at=self._clock(),
                trace=(trace,),
            )

        plan = self._planner.plan(eligibility.root_url or "")
        pages = tuple(self._fetch(item, eligibility.normalized_domain or "") for item in plan)
        trace = tuple(
            WebsiteResearchPipelineTrace(
                planning_rule=item.planning_rule,
                selected_url=page.requested_url,
                page_type=page.page_type,
                fetch_outcome=page.fetch_status,
                classification_reason=page.classification_reason,
                sanitization_actions=page.sanitization_actions,
                error_classification=page.error.code if page.error else None,
            )
            for item, page in zip(plan, pages, strict=True)
        )
        successes = tuple(page for page in pages if page.fetch_status is FetchStatus.SUCCESS)
        status = _aggregate_status(len(pages), len(successes))
        selected_types = tuple(dict.fromkeys(page.page_type for page in successes))
        return WebsiteResearchPipelineResult(
            master_id=request.master_id,
            normalized_domain=eligibility.normalized_domain,
            canonical_name=request.canonical_name,
            root_url=eligibility.root_url,
            pages=pages,
            research_status=status,
            successful_page_count=len(successes),
            failed_page_count=len(pages) - len(successes),
            selected_page_types=selected_types,
            started_at=started_at,
            completed_at=self._clock(),
            trace=trace,
        )

    def _fetch(self, item: UrlPlanItem, expected_domain: str) -> WebsiteResearchPageResult:
        fetched_at = self._clock()
        request = WebsiteHttpRequest(url=item.requested_url)
        try:
            response = self._transport.fetch(request)
        except WebsiteTransportFailure as error:
            return _failed_page(item, fetched_at, WebsiteResearchError(error.code, error.retryable, "Website transport failed."))
        except TimeoutError:
            return _failed_page(item, fetched_at, WebsiteResearchError(ResearchErrorCode.NETWORK_TIMEOUT, True, "Website request timed out."))
        except OSError:
            return _failed_page(item, fetched_at, WebsiteResearchError(ResearchErrorCode.NETWORK_CONNECTION_ERROR, True, "Website connection failed."))

        redirect_error = _validate_redirect(response, expected_domain, request.max_redirects)
        if redirect_error:
            return _failed_page(item, fetched_at, redirect_error, response=response)
        status_error = _status_error(response.status_code)
        if status_error:
            return _failed_page(item, fetched_at, status_error, response=response)
        content_type = _header(response.headers, "content-type")
        if not _is_html_content_type(content_type):
            return _failed_page(item, fetched_at, WebsiteResearchError(ResearchErrorCode.UNSUPPORTED_CONTENT_TYPE, False, "Response is not HTML."), response=response, content_type=content_type)
        raw_html, body_error = _decode_body(response.body, request.max_response_bytes)
        if body_error:
            return _failed_page(item, fetched_at, body_error, response=response, content_type=content_type)
        try:
            sanitized = self._sanitizer.sanitize(raw_html or "")
        except ValueError:
            return _failed_page(item, fetched_at, WebsiteResearchError(ResearchErrorCode.MALFORMED_HTML, False, "HTML could not be sanitized."), response=response, content_type=content_type)
        if not sanitized.text_content:
            return _failed_page(item, fetched_at, WebsiteResearchError(ResearchErrorCode.EMPTY_CONTENT, False, "HTML has no visible text."), response=response, content_type=content_type, actions=sanitized.actions)
        final_url = _normalize_url(response.final_url)
        page_type, reason = self._classifier.classify(item.requested_url, final_url, sanitized.title, sanitized.headings, item.page_type)
        return WebsiteResearchPageResult(
            requested_url=item.requested_url,
            final_url=final_url,
            page_type=page_type,
            status_code=response.status_code,
            content_type=content_type,
            title=sanitized.title,
            text_content=sanitized.text_content,
            raw_html=raw_html,
            meta_description=sanitized.meta_description,
            links=sanitized.links,
            fetch_status=FetchStatus.SUCCESS,
            error=None,
            redirect_chain=tuple(_normalize_url(url) for url in response.redirect_chain),
            fetched_at=fetched_at,
            classification_reason=reason,
            sanitization_actions=sanitized.actions,
        )


class _SanitizingParser(HTMLParser):
    _IGNORED = {"script", "style", "noscript", "svg", "canvas", "template", "iframe"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.visible_text: list[str] = []
        self.title_parts: list[str] = []
        self.headings: list[str] = []
        self.links: list[str] = []
        self.meta_description = ""
        self.actions: set[str] = set()
        self._suppressed_depth = 0
        self._title_depth = 0
        self._heading_depth = 0
        self._heading_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        name = tag.casefold()
        attributes = {key.casefold(): value or "" for key, value in attrs}
        hidden = "hidden" in attributes or attributes.get("aria-hidden", "").casefold() == "true" or _hidden_style(attributes.get("style", ""))
        if self._suppressed_depth or name in self._IGNORED or hidden:
            self._suppressed_depth += 1
            if name in self._IGNORED:
                self.actions.add(f"REMOVED_{name.upper()}")
            elif hidden:
                self.actions.add("REMOVED_HIDDEN_CONTENT")
            return
        if name == "title":
            self._title_depth += 1
        if name in {"h1", "h2", "h3"}:
            self._heading_depth += 1
        if name == "meta" and attributes.get("name", "").casefold() == "description":
            self.meta_description = attributes.get("content", "")
        if name == "a" and attributes.get("href") and len(self.links) < MAX_LINKS:
            self.links.append(attributes["href"])

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        name = tag.casefold()
        if self._suppressed_depth:
            self._suppressed_depth -= 1
            return
        if name == "title" and self._title_depth:
            self._title_depth -= 1
        if name in {"h1", "h2", "h3"} and self._heading_depth:
            self._heading_depth -= 1
            self.headings.append(" ".join(self._heading_parts))
            self._heading_parts.clear()

    def handle_data(self, data: str) -> None:
        if self._suppressed_depth:
            return
        if data.strip():
            self.visible_text.append(data)
            if self._title_depth:
                self.title_parts.append(data)
            if self._heading_depth:
                self._heading_parts.append(data)


_CLASSIFICATION_WORDS: tuple[tuple[PageType, tuple[str, ...]], ...] = (
    (PageType.CONTACT, ("contact", "get in touch")),
    (PageType.ABOUT, ("about us", "who we are", "our company")),
    (PageType.PRODUCTS, ("products", "catalog", "shop", "store")),
    (PageType.BRANDS, ("brands", "our brands")),
)


def _canonical_root_url(value: str) -> tuple[str | None, str | None, WebsiteResearchError | None]:
    candidate = value.strip()
    if not candidate:
        return None, None, WebsiteResearchError(ResearchErrorCode.INVALID_TARGET, False, "Website target is empty.")
    if "://" not in candidate and re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", candidate):
        return None, None, WebsiteResearchError(ResearchErrorCode.INVALID_TARGET, False, "Website target must be a public HTTP(S) URL.")
    parsed = _parse_url(candidate if "://" in candidate else f"https://{candidate}")
    if not parsed or parsed.scheme not in {"http", "https"}:
        return None, None, WebsiteResearchError(ResearchErrorCode.INVALID_TARGET, False, "Website target must be a public HTTP(S) URL.")
    if _looks_like_file_url(parsed.path):
        return None, None, WebsiteResearchError(ResearchErrorCode.INVALID_TARGET, False, "Website target is an obvious file URL.")
    raw_host = parsed.hostname
    if not _is_public_host(raw_host):
        return None, None, WebsiteResearchError(ResearchErrorCode.UNSAFE_TARGET, False, "Website target is not a public host.")
    domain = normalize_domain(parsed.hostname)
    if not domain:
        return None, None, WebsiteResearchError(ResearchErrorCode.INVALID_TARGET, False, "Website target has an invalid hostname.")
    return f"{parsed.scheme}://{domain}/", domain, None


def _is_public_host(host: str) -> bool:
    if host in {"localhost", "example", "example.com", "example.org", "example.net"} or host.endswith((".localhost", ".local", ".test", ".invalid", ".example.com", ".example.org", ".example.net")):
        return False
    try:
        return ipaddress.ip_address(host).is_global
    except ValueError:
        return True


def _looks_like_file_url(path: str) -> bool:
    return path.casefold().endswith((".pdf", ".zip", ".rar", ".7z", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".mp4", ".mp3", ".doc", ".docx", ".xls", ".xlsx"))


def _normalize_url(value: str) -> str:
    parsed = _parse_url(value)
    if not parsed:
        return value
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.hostname}{path}"


def _same_root_domain(url: str, expected_domain: str) -> bool:
    parsed = _parse_url(url)
    host = normalize_domain(parsed.hostname) if parsed else None
    return bool(host and host == expected_domain)


def _validate_redirect(response: WebsiteHttpResponse, expected_domain: str, max_redirects: int) -> WebsiteResearchError | None:
    if len(response.redirect_chain) > max_redirects:
        return WebsiteResearchError(ResearchErrorCode.REDIRECT_ERROR, False, "Redirect limit exceeded.")
    urls = (*response.redirect_chain, response.final_url)
    if not all(_same_root_domain(url, expected_domain) and _canonical_root_url(url)[2] is None for url in urls):
        return WebsiteResearchError(ResearchErrorCode.REDIRECT_ERROR, False, "Redirect left the approved public root domain.")
    return None


def _status_error(status: int) -> WebsiteResearchError | None:
    if status in {200, 301, 302, 307, 308}:
        return None
    if status == 204:
        return WebsiteResearchError(ResearchErrorCode.EMPTY_CONTENT, False, "Website returned no content.")
    if status == 408:
        return WebsiteResearchError(ResearchErrorCode.NETWORK_TIMEOUT, True, "Website request timed out.")
    if status == 429:
        return WebsiteResearchError(ResearchErrorCode.RATE_LIMITED, True, "Website rate limit reached.")
    if status in {401, 403}:
        return WebsiteResearchError(ResearchErrorCode.ACCESS_DENIED, False, "Website access was denied.")
    if status == 404:
        return WebsiteResearchError(ResearchErrorCode.NOT_FOUND, False, "Website page was not found.")
    if 500 <= status <= 504:
        return WebsiteResearchError(ResearchErrorCode.SERVER_ERROR, True, "Website server failed.")
    if 400 <= status < 500:
        return WebsiteResearchError(ResearchErrorCode.HTTP_CLIENT_ERROR, False, "Website rejected the request.")
    return WebsiteResearchError(ResearchErrorCode.NETWORK_CONNECTION_ERROR, True, "Website returned an unsupported HTTP status.")


def _header(headers: Mapping[str, str], name: str) -> str | None:
    return next((value for key, value in headers.items() if key.casefold() == name), None)


def _is_html_content_type(value: str | None) -> bool:
    return bool(value and value.split(";", 1)[0].strip().casefold() in {"text/html", "application/xhtml+xml"})


def _decode_body(body: bytes | str, limit: int) -> tuple[str | None, WebsiteResearchError | None]:
    if isinstance(body, str):
        encoded = body.encode("utf-8")
        if len(encoded) > limit:
            return None, WebsiteResearchError(ResearchErrorCode.RESPONSE_TOO_LARGE, False, "Website response exceeded the byte limit.")
        return body, None
    if len(body) > limit:
        return None, WebsiteResearchError(ResearchErrorCode.RESPONSE_TOO_LARGE, False, "Website response exceeded the byte limit.")
    try:
        return body.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, WebsiteResearchError(ResearchErrorCode.MALFORMED_HTML, False, "Website response is not valid UTF-8 HTML.")


def _failed_page(
    item: UrlPlanItem,
    fetched_at: str,
    error: WebsiteResearchError,
    *,
    response: WebsiteHttpResponse | None = None,
    content_type: str | None = None,
    actions: tuple[str, ...] = (),
) -> WebsiteResearchPageResult:
    return WebsiteResearchPageResult(
        requested_url=item.requested_url,
        final_url=_normalize_url(response.final_url) if response else None,
        page_type=item.page_type,
        status_code=response.status_code if response else None,
        content_type=content_type,
        title=None,
        text_content=None,
        raw_html=None,
        meta_description=None,
        links=(),
        fetch_status=FetchStatus.FAILED,
        error=error,
        redirect_chain=tuple(_normalize_url(url) for url in response.redirect_chain) if response else (),
        fetched_at=fetched_at,
        classification_reason="Fetch did not produce a usable HTML page.",
        sanitization_actions=actions,
    )


def _aggregate_status(page_count: int, successful_count: int) -> ResearchStatus:
    if page_count == 0 or successful_count == 0:
        return ResearchStatus.FAILED
    if successful_count == page_count:
        return ResearchStatus.COMPLETED
    return ResearchStatus.PARTIAL


def _page_type_from_path(value: str) -> PageType | None:
    parsed = _parse_url(value)
    path = parsed.path.casefold().strip("/") if parsed else ""
    if not path:
        return PageType.HOME
    first = path.split("/", 1)[0]
    if first in {"contact", "contact-us"}:
        return PageType.CONTACT
    if first in {"about", "about-us", "company", "company-profile", "who-we-are"}:
        return PageType.ABOUT
    if first in {"products", "shop", "store", "catalog", "collections"}:
        return PageType.PRODUCTS
    if first in {"brands", "our-brands", "brand"}:
        return PageType.BRANDS
    return None


def _hidden_style(value: str) -> bool:
    compact = re.sub(r"\s+", "", value.casefold())
    return "display:none" in compact or "visibility:hidden" in compact


def _parse_url(value: str) -> _ParsedUrl | None:
    match = _ABSOLUTE_URL.fullmatch(value.strip())
    if not match:
        return None
    scheme = match.group("scheme").casefold()
    authority = match.group("authority")
    if not authority or "@" in authority:
        return None
    if authority.startswith("["):
        closing = authority.find("]")
        if closing < 2 or authority[closing + 1:] not in {""} and not re.fullmatch(r":\d+", authority[closing + 1:]):
            return None
        host = authority[1:closing]
    else:
        if authority.count(":") > 1:
            return None
        host, separator, port = authority.partition(":")
        if separator and (not port or not port.isdecimal()):
            return None
    host = host.casefold().rstrip(".")
    if not host:
        return None
    return _ParsedUrl(scheme, host, match.group("path") or "/")


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def _ineligible(code: ResearchErrorCode, message: str, error: WebsiteResearchError | None = None) -> ResearchEligibility:
    return ResearchEligibility(False, None, None, error or WebsiteResearchError(code, False, message), message)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _serialize(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value):
        return _serialize(asdict(value))
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, Mapping):
        return {key: _serialize(item) for key, item in value.items()}
    return value
