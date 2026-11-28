import hashlib
import json

import httpx
import pytest

from um_world_model.merchant_acquisition import (
    PublicOnlyTransport,
    PublicPages,
    RobotsRules,
)
from um_world_model.merchant_readiness import assess_case, extract_page


@pytest.fixture(autouse=True)
def no_wait(monkeypatch):
    monkeypatch.setattr(
        "um_world_model.merchant_acquisition.time.sleep", lambda _: None
    )


def response(body="", status=200, **headers):
    return httpx.Response(
        status, text=body, headers={"content-type": "text/html", **headers}
    )


def pages_for(handler, tmp_path, hosts=("a.test", "b.test"), **kwargs):
    return PublicPages(
        httpx.Client(transport=httpx.MockTransport(handler)),
        set(hosts),
        tmp_path,
        **kwargs,
    )


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.169.254",
        "::1",
        "fd00::1",
        "100.64.0.1",
        "::ffff:127.0.0.1",
        "ff0e::1",
        "fec0::1",
    ],
)
def test_transport_rejects_nonpublic_dns_even_if_allowlisted(ip):
    def forbidden(_):
        pytest.fail("Private IP must not reach the HTTP transport")

    transport = PublicOnlyTransport(
        {"a.test"},
        resolver=lambda *a, **k: [(None, None, None, None, (ip, 443))],
        transport=httpx.MockTransport(forbidden),
    )
    with pytest.raises(httpx.ConnectError, match="private_network_destination"):
        transport.handle_request(httpx.Request("GET", "https://a.test/"))


def test_public_ip_is_pinned_without_losing_tls_hostname_and_rebinding_is_denied():
    calls = []
    ips = iter(["93.184.216.34", "127.0.0.1"])

    def handler(req):
        calls.append(req)
        assert req.url.host == "93.184.216.34"
        assert req.headers["host"] == "a.test"
        assert req.extensions["sni_hostname"] == "a.test"
        assert req.headers["connection"] == "close"
        return response("ok")

    transport = PublicOnlyTransport(
        {"a.test"},
        resolver=lambda *a, **k: [(None, None, None, None, (next(ips), 443))],
        transport=httpx.MockTransport(handler),
    )
    transport.handle_request(httpx.Request("GET", "https://a.test/"))
    with pytest.raises(httpx.ConnectError, match="private_network"):
        transport.handle_request(httpx.Request("GET", "https://a.test/next"))
    assert len(calls) == 1


def test_mixed_public_private_answers_are_rejected():
    transport = PublicOnlyTransport(
        {"a.test"},
        resolver=lambda *a, **k: [
            (None, None, None, None, (ip, 443)) for ip in ["93.184.216.34", "10.0.0.1"]
        ],
        transport=httpx.MockTransport(lambda _: pytest.fail("No network")),
    )
    with pytest.raises(httpx.ConnectError, match="private_network"):
        transport.handle_request(httpx.Request("GET", "https://a.test/"))


def test_redirected_page_checks_destination_robots_and_retains_evidence(tmp_path):
    calls = []

    def handler(req):
        calls.append(str(req.url))
        if req.url.path == "/robots.txt":
            return response(
                "User-agent: *\nDisallow: /secret"
                if req.url.host == "b.test"
                else "User-agent: *\nAllow: /"
            )
        return response("", 302, location="https://b.test/secret")

    pages = pages_for(handler, tmp_path)
    assert pages.page("https://a.test/")[0] == "robots_explicit_disallow"
    assert "https://b.test/secret" not in calls
    assert len(calls) == 3
    for event in pages.events:
        if event.get("snapshot"):
            assert (
                hashlib.sha256((tmp_path / event["snapshot"]).read_bytes()).hexdigest()
                == event["sha256"]
            )
    assert pages.events[-1]["evidence_event_ids"]


def test_same_host_redirect_rechecks_path_rules(tmp_path):
    def handler(req):
        if req.url.path == "/robots.txt":
            return response("User-agent: *\nDisallow: /private")
        assert req.url.path == "/"
        return response("", 301, location="/private")

    assert (
        pages_for(handler, tmp_path).page("https://a.test/")[0]
        == "robots_explicit_disallow"
    )


@pytest.mark.parametrize(
    "target,status",
    [
        ("http://a.test/", "redirect_unsafe_destination"),
        ("https://outside.test/", "redirect_host_not_allowed"),
        ("https://127.0.0.1/", "redirect_unsafe_destination"),
        ("https://a.test/?add-to-cart=1", "redirect_unsafe_destination"),
        ("https://a.test/checkout", "redirect_unsafe_destination"),
        ("https://user:pass@a.test/", "redirect_unsafe_destination"),
    ],
)
def test_redirect_restrictions_before_network(tmp_path, target, status):
    def handler(req):
        if req.url.path == "/robots.txt":
            return response("", 404)
        assert str(req.url) == "https://a.test/"
        return response("", 301, location=target)

    assert pages_for(handler, tmp_path).page("https://a.test/")[0] == status


def test_robots_redirect_loop_and_budget(tmp_path):
    def loop(req):
        return response("", 301, location="/robots.txt")

    pages = pages_for(loop, tmp_path)
    assert pages.page("https://a.test/")[0] == "robots_redirect_loop"
    assert pages.requests == 1

    def endless(req):
        return response("", 301, location=req.url.path + "x")

    pages = pages_for(endless, tmp_path, max_redirects=2)
    assert pages.page("https://a.test/")[0] == "robots_redirect_limit"
    assert pages.requests == 3


def test_robots_redirects_and_404_policy(tmp_path):
    def handler(req):
        if req.url.host == "a.test" and req.url.path == "/robots.txt":
            return response("", 301, location="https://b.test/robots.txt")
        if req.url.path == "/robots.txt":
            return response("", 404)
        return response("<title>OK</title>")

    pages = pages_for(handler, tmp_path)
    assert pages.page("https://a.test/")[0] == "ok"
    assert pages.requests == 3
    assert any(e.get("http_status") == 404 and e.get("snapshot") for e in pages.events)


@pytest.mark.parametrize(
    "body,status",
    [
        ("<html>no robots here</html>", "robots_unsupported_content"),
        ("User-agent: *\nDisallow: /", "robots_explicit_disallow"),
        ("User-agent: *\nCrawl-delay: 11", "robots_pacing_limit"),
        ("User-agent: *\nCrawl-delay: invalid", "robots_unsupported_content"),
        ("User-agent: *\nUnknown: /", "robots_unsupported_content"),
    ],
)
def test_robots_diagnostics(tmp_path, body, status):
    assert (
        pages_for(lambda _: response(body), tmp_path).page("https://a.test/")[0]
        == status
    )


def test_robots_transport_error_is_not_crawl_denial(tmp_path):
    def fail(req):
        raise httpx.ConnectError("dns_resolution_failed", request=req)

    pages = pages_for(fail, tmp_path)
    assert pages.page("https://a.test/")[0] == "robots_dns_error"
    assert pages.events[0]["error_type"] == "ConnectError"


def test_robots_longest_match_specific_groups_wildcards_and_fractional_delay():
    rules = RobotsRules(
        b"User-agent: *\nDisallow: /\nUser-agent: UMWorldModelResearch\nDisallow: /shop*\nAllow: /shop/public\nCrawl-delay: 0.5\n"
    )
    assert rules.allowed("https://a.test/about")
    assert not rules.allowed("https://a.test/shop/private")
    assert rules.allowed("https://a.test/shop/public")
    assert rules.delay == 0.5
    assert not RobotsRules(b"User-agent: *\nDisallow: /ab$").allowed(
        "https://a.test/%61b"
    )
    assert RobotsRules(b"User-agent: *\nDisallow: /ab$").allowed("https://a.test/abc")


CASE = {
    "id": "synthetic",
    "name": "Example Books",
    "civic": "1 MAIN ST",
    "unit": None,
    "urls": ["https://a.test/"],
    "source_refs": ["fixture"],
    "observed_flags": [],
}
HTML = "<title>Example Books</title><p>1 Main Street, Stoneham, MA</p>"


def test_relevant_page_budget_priority_and_no_transaction_or_external_requests(
    tmp_path,
):
    paths = []

    def handler(req):
        paths.append(req.url.path)
        if req.url.path == "/robots.txt":
            return response("User-agent: *\nAllow: /")
        if req.url.path == "/":
            return response(
                HTML
                + "".join(
                    f'<a href="/{label}">{label}</a>'
                    for label in [
                        "ordering",
                        "booking",
                        "products",
                        "shop",
                        "menu",
                        "locations",
                        "contact",
                        "about",
                        "checkout",
                    ]
                )
                + '<a href="https://outside.test/shop">Shop</a>'
            )
        return response("<title>Page</title>")

    result = assess_case(CASE, pages_for(handler, tmp_path), tmp_path)
    assert paths == [
        "/robots.txt",
        "/",
        "/about",
        "/contact",
        "/locations",
        "/menu",
        "/shop",
    ]
    assert result["additional_pages_attempted"] == 5
    assert result["discovered_pages_not_attempted"] == 3
    assert result["level"] == "L1"
    assert result["review_reason"] == "transaction_pathway_review"


def test_patinas_catalog_is_discovered_without_transaction(tmp_path):
    case = {**CASE, "name": "Patina'd", "civic": "379 MAIN ST"}

    def handler(req):
        if req.url.path == "/robots.txt":
            return response("", 404)
        if req.url.path == "/":
            return response(
                "<title>Patina'd</title><p>379 Main St, Stoneham, MA</p><a href='/shop'>Shop</a>"
            )
        assert req.url.path == "/shop"
        return response(
            "".join(
                f'<div class="product-list-item"><h2>Example item {i}</h2><span>$12.00</span></div>'
                for i in range(2)
            )
        )

    result = assess_case(case, pages_for(handler, tmp_path), tmp_path)
    assert result["level"] == "L2"
    assert len(result["extraction"]["catalog_evidence"]) == 2
    assert all(e["source_sha256"] for e in result["extraction"]["catalog_evidence"])


def test_gaetano_expansion_requires_title_logo_and_exact_civic():
    case = {"name": "Gaetano's", "civic": "271 MAIN ST"}
    body = b"<title>Gaetano's Restaurant - Stoneham, MA</title><img alt=\"Gaetano's Restaurant logo top\"><p>271 Main Street, Stoneham, MA</p>"
    r = extract_page(body, "https://a.test/", case)
    assert (
        r["official_website_verified"]
        and r["identity_method"] == "descriptor_expansion_title_logo"
    )
    assert not extract_page(
        body.replace(b"logo top", b"food"), "https://a.test/", case
    )["official_website_verified"]
    assert not extract_page(body, "https://a.test/", {**case, "civic": "272 MAIN ST"})[
        "official_website_verified"
    ]
    assert not extract_page(
        body.replace(b"Restaurant", b"Market"), "https://a.test/", case
    )["official_website_verified"]


def test_structured_alias_requires_business_node_and_same_civic():
    node = {
        "@type": "LocalBusiness",
        "name": "Example Books and Gifts",
        "alternateName": "Example Books",
        "address": {
            "streetAddress": "1 Main St",
            "addressLocality": "Stoneham",
            "addressRegion": "MA",
        },
    }

    def extract(n):
        return extract_page(
            (
                '<script type="application/ld+json">' + json.dumps(n) + "</script>"
            ).encode(),
            "https://a.test/",
            CASE,
        )

    assert extract(node)["official_website_verified"]
    assert not extract({**node, "@type": "Product"})["official_website_verified"]
    assert not extract({**node, "alternateName": "Example Book"})[
        "official_website_verified"
    ]
    assert not extract(
        {**node, "address": {**node["address"], "streetAddress": "2 Main St"}}
    )["official_website_verified"]


def test_unit_verification_is_not_erased_by_civic_normalization():
    body = (HTML.replace("1 Main Street,", "1 Main Street, Suite 2,")).encode()
    assert not extract_page(body, "https://a.test/", CASE)["official_website_verified"]
    assert extract_page(body, "https://a.test/", {**CASE, "unit": "2"})[
        "official_website_verified"
    ]
    assert not extract_page(body, "https://a.test/", {**CASE, "unit": "3"})[
        "official_website_verified"
    ]
    assert not extract_page(HTML.encode(), "https://a.test/", {**CASE, "unit": "2"})[
        "official_website_verified"
    ]


def test_cross_page_conflict_cannot_be_cherry_picked(tmp_path):
    def handler(req):
        if req.url.path == "/robots.txt":
            return response("", 404)
        if req.url.path == "/":
            return response(HTML + '<a href="/contact">Contact</a>')
        return response(
            '<script type="application/ld+json">'
            + json.dumps(
                {
                    "@type": "LocalBusiness",
                    "name": "Example Books",
                    "address": {
                        "streetAddress": "2 Main St",
                        "addressLocality": "Stoneham",
                    },
                }
            )
            + "</script>"
        )

    result = assess_case(CASE, pages_for(handler, tmp_path), tmp_path)
    assert result["level"] == "Unknown"
    assert result["extraction"]["abstention_reasons"] == [
        "cross_page_civic_or_unit_conflict"
    ]


def test_book_oasis_remains_exact_positive_control():
    body = b"<title>The Book Oasis</title><p>311 Main St, Stoneham, MA</p>"
    result = extract_page(
        body, "https://a.test/", {"name": "The Book Oasis", "civic": "311 MAIN ST"}
    )
    assert (
        result["official_website_verified"]
        and result["identity_method"] == "exact_name"
    )


def test_sponsor_logo_alone_is_not_site_identity():
    body = b'<title>Different Business</title><img alt="Example Books logo"><p>1 Main St, Stoneham, MA</p>'
    assert not extract_page(body, "https://a.test/", CASE)["official_website_verified"]


def test_explicit_unit_label_in_frozen_case_is_preserved():
    body = b"<title>Example Books</title><p>1 Main St, Suite 2, Stoneham, MA</p>"
    assert extract_page(body, "https://a.test/", {**CASE, "unit": "Suite 2"})[
        "official_website_verified"
    ]


def test_body_contact_conflict_cannot_be_cherry_picked(tmp_path):
    def handler(req):
        if req.url.path == "/robots.txt":
            return response("", 404)
        if req.url.path == "/":
            return response(HTML + '<a href="/contact">Contact</a>')
        return response("<p>2 Main St, Stoneham, MA</p>")

    result = assess_case(CASE, pages_for(handler, tmp_path), tmp_path)
    assert result["level"] == "Unknown"


def test_mixed_unit_evidence_remains_ambiguous():
    body = b"<title>Example Books</title><p>1 Main St, Suite 2, Stoneham, MA</p><p>1 Main St, Stoneham, MA</p>"
    assert not extract_page(body, "https://a.test/", CASE)["official_website_verified"]


def test_oversize_robots_prefix_is_hashed_but_not_parsed(tmp_path, monkeypatch):
    monkeypatch.setattr("um_world_model.merchant_acquisition.MAX_ROBOTS", 10)
    pages = pages_for(lambda _: response("User-agent: *\nDisallow: /"), tmp_path)
    assert pages.page("https://a.test/")[0] == "robots_body_limit"
    event = pages.events[0]
    assert event["truncated"] and event["decoded_bytes"] == 10
    assert (tmp_path / event["snapshot"]).read_bytes() == b"User-agent"
