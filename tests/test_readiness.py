import hashlib

import httpx
import pytest

pytest.importorskip("shapely")
pytest.importorskip("bs4")

from um_world_model.merchant_readiness import (
    PublicPages,
    extract_page,
    maturity,
    web_url,
)
from um_world_model.overture_https import HTTPSRange


def test_range_receipt_checks_bytes_and_etag():
    url = "https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com/release/2026-11-18.0/theme=places/type=place/test.parquet"

    def handler(request):
        assert request.headers["range"] == "bytes=2-3"
        return httpx.Response(
            206, content=b"ab", headers={"Content-Range": "bytes 2-3/7", "ETag": '"x"'}
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        file = HTTPSRange(client, url, 7)
        file.seek(2)
        assert file.read(2) == b"ab"
        assert file.receipts[0]["sha256"] == hashlib.sha256(b"ab").hexdigest()
        with pytest.raises(ValueError, match="outside"):
            HTTPSRange(client, url.replace("2026-11-18.0", "latest"), 7)


def test_no_network_on_disallowed_hosts_or_unsafe_leads():
    def denied(_request):
        raise AssertionError("No network request expected")

    with httpx.Client(transport=httpx.MockTransport(denied)) as client:
        pages = PublicPages(client, {"allowed.test"})
        assert pages.page("https://blocked.test/") == ("host_not_allowed", None)
    assert (
        web_url("https://example.test/path?session=test") == "https://example.test/path"
    )
    assert not web_url("http://127.0.0.1/")


def test_verified_business_needs_local_identity_and_ads_do_not_raise_maturity():
    body = b"""<title>Example Books</title><p>1 Main Street, Stoneham, MA</p>
    <a href="https://checkout.example.test/">Shop online</a>"""
    case = {"name": "Example Books", "civic": "1 MAIN ST"}
    result = extract_page(body, "https://example.test/", case)
    assert result["official_website_verified"]
    assert result["advertised_links"][0]["kind"] == "ecommerce_link"
    assert (
        maturity(website=True, capabilities=result["individual_capabilities"]) == "L1"
    )
    assert maturity(website=True, capabilities={"third_party_pathway_observed"}) == "L3"
    assert maturity(website=True, capabilities={"first_party_pathway_observed"}) == "L4"
    assert maturity(website=False, capabilities={}) == "Unknown"
    assert (
        maturity(website=False, capabilities={}, confirmed_without_website=True) == "L0"
    )
    assert not extract_page(
        body, "https://example.test/", {**case, "civic": "2 MAIN ST"}
    )["official_website_verified"]
