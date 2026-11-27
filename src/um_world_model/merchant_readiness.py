"""Bounded, read-only merchant page retrieval and conservative census assessment."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import resource
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from .commercial import name_key
from .normalize import normalize_address
from .physical_graph import digest

AGENT = "UMWorldModelResearch"
MAX_BODY = 2_000_000
PLATFORMS = {
    "facebook.com",
    "instagram.com",
    "linktr.ee",
    "groupon.com",
    "toasttab.com",
    "yelp.com",
    "bookshop.org",
    "ubereats.com",
    "doordash.com",
}


def web_url(value: str) -> str | None:
    """Use public HTTPS only. Remove credentials, tracking and fragments from leads."""
    try:
        url = urlsplit(value.strip())
        host = url.hostname
        if (
            not host
            or url.scheme not in {"https", "http"}
            or url.username
            or url.password
            or url.port not in {None, 443}
            or "." not in host
        ):
            return None
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return urlunsplit(("https", host, url.path or "/", "", ""))
    except ValueError:
        pass
    return None


def domain(url):
    return urlsplit(url).hostname or ""


def platform(url):
    host = domain(url)
    return any(host == p or host.endswith("." + p) for p in PLATFORMS)


class PublicPages:
    def __init__(self, client: httpx.Client, allowed_hosts: set[str]):
        self.client, self.hosts = client, allowed_hosts
        self.robots = {}
        self.waits = {}
        self.last = {}
        self.bytes = self.requests = 0

    def request(self, url):
        host = domain(url)
        if host not in self.hosts:
            return "host_not_allowed", None
        delay = self.waits.get(host, 0.3)
        time.sleep(max(0, delay - (time.monotonic() - self.last.get(host, 0))))
        self.last[host] = time.monotonic()
        self.requests += 1
        try:
            with self.client.stream("GET", url) as response:
                if response.is_redirect:
                    target = web_url(urljoin(url, response.headers.get("location", "")))
                    return (
                        "redirect_review"
                        if target and (domain(target) in self.hosts)
                        else "redirect_host_not_allowed"
                    ), target
                if response.status_code != 200:
                    return f"http_{response.status_code}", None
                if "html" not in response.headers.get(
                    "content-type", ""
                ).lower() and not url.endswith("/robots.txt"):
                    return "not_html", None
                body = bytearray()
                try:
                    for chunk in response.iter_bytes(chunk_size=16384):
                        if len(body) + len(chunk) > MAX_BODY:
                            return "body_limit", None
                        body.extend(chunk)
                finally:
                    self.bytes += response.num_bytes_downloaded
                return "ok", bytes(body)
        except httpx.ProxyError:
            return "proxy_denied", None
        except httpx.HTTPError:
            return "network_error", None

    def page(self, url):
        host = domain(url)
        if host not in self.hosts:
            return "host_not_allowed", None
        if host not in self.robots:
            code, body = self.request(f"https://{host}/robots.txt")
            self.robots[host] = False
            if code == "http_404" or code == "http_410":
                self.robots[host] = None
            elif code == "ok" and not body.lstrip().startswith(b"<"):
                robot = RobotFileParser()
                robot.parse(body.decode("utf-8", errors="replace").splitlines())
                delay = robot.crawl_delay(AGENT) or robot.crawl_delay("*") or 0
                rate = robot.request_rate(AGENT) or robot.request_rate("*")
                if rate and rate.requests:
                    delay = max(delay, rate.seconds / rate.requests)
                if delay <= 10:
                    self.waits[host] = max(0.3, delay)
                    self.robots[host] = robot
        robot = self.robots[host]
        if robot is False or (robot is not None and not robot.can_fetch(AGENT, url)):
            return "robots_unavailable_or_disallows", None
        return self.request(url)


def jsonld_nodes(soup):
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except ValueError:
            continue
        pending = list(data) if isinstance(data, list) else [data]
        for node in pending:
            if isinstance(node, dict):
                yield node
                if isinstance(node.get("@graph"), list):
                    pending.extend(node["@graph"])


def extract_page(body: bytes, url: str, case: dict) -> dict:
    """Verify exact name evidence. Treat links as advertisements, not tested flows."""
    soup = BeautifulSoup(body, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    headings = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
    nodes = list(jsonld_nodes(soup))
    names = [node["name"] for node in nodes if isinstance(node.get("name"), str)]
    key = name_key(case["name"])
    title_segments = re.split(r"\s+[|–—-]\s+", title)
    name_matches = [
        s for s in names + headings + title_segments if key and name_key(s) == key
    ]
    body_text = " ".join(soup.stripped_strings)
    town = re.search(r"\bStoneham\b", body_text, re.IGNORECASE)
    civic = case["civic"]
    structured = [n.get("address") for n in nodes if isinstance(n.get("address"), dict)]
    local_structured = [
        a
        for a in structured
        if str(a.get("addressLocality", "")).strip().casefold() == "stoneham"
        and a.get("streetAddress")
    ]
    exact_structured = [
        a for a in local_structured if normalize_address(a["streetAddress"]) == civic
    ]
    structured_conflicts = sorted(
        {
            a["streetAddress"]
            for a in local_structured
            if normalize_address(a["streetAddress"]) != civic
        }
    )
    body_match = None
    if town:
        for text in soup.stripped_strings:
            # Verify a civic line with a delimiter, and retain only that public line.
            line = re.split(r",|\bStoneham\b", text, maxsplit=1, flags=re.IGNORECASE)[
                0
            ].strip()
            if normalize_address(line) == civic and len(line) < 100:
                body_match = line
                break
    verified = bool(
        name_matches
        and not platform(url)
        and (exact_structured or body_match)
        and not structured_conflicts
    )
    result = {
        "official_website_verified": verified,
        "identity_excerpt": name_matches[0] if verified else None,
        "advertised_civic_excerpt": (
            (exact_structured[0]["streetAddress"] if exact_structured else body_match)
            if verified
            else None
        ),
        "conflicting_structured_addresses": structured_conflicts if verified else [],
        "hours": [
            n.get("openingHours")
            for n in nodes
            if name_key(str(n.get("name", ""))) == key and n.get("openingHours")
        ]
        if verified
        else [],
        "public_offering_names": [
            n["name"]
            for n in nodes
            if n.get("@type") in ("Product", "Menu") and isinstance(n.get("name"), str)
        ][:5]
        if verified
        else [],
        "individual_capabilities": [],
        "advertised_links": [],
    }
    if not verified:
        return result
    product = any(
        n.get("@type") in ("Product", "Menu") and n.get("name") for n in nodes
    )
    labels = Counter()
    for anchor in soup.select("a[href]"):
        href = (
            web_url(urljoin(url, anchor["href"]))
            if not anchor["href"].startswith("#")
            else None
        )
        if not href:
            continue
        label = anchor.get_text(" ", strip=True).casefold()
        capabilities = {
            "catalog_link": r"\b(menu|catalog|products)\b",
            "ordering_link": r"\b(order|delivery|takeout)\b",
            "booking_link": r"\b(reserve|reservation|book a|appointment)\b",
            "ecommerce_link": r"\b(shop online|checkout|cart|buy)\b",
        }
        for kind, pattern in capabilities.items():
            if re.search(pattern, label) and labels[kind] < 2:
                labels[kind] += 1
                result["advertised_links"].append({"kind": kind, "url": href})
        if re.search(r"(?:^|\.)(facebook\.com|instagram\.com)$", domain(href)):
            labels["social_presence_link"] += 1
        if platform(href) and re.search(r"shop|book|order|delivery|buy", label):
            labels["marketplace_link"] += 1
    fields = {"official_website"}
    if product:
        fields.add("catalog")
    if labels["social_presence_link"]:
        fields.add("social_presence")
    if labels["marketplace_link"]:
        fields.add("marketplace_link")
    # A visible contact form is a capability indicator. Never submit it.
    if any(
        form.select_one("textarea") and form.select_one('button, input[type="submit"]')
        for form in soup.select("form")
    ):
        fields.add("inquiry_form")
    result["individual_capabilities"] = sorted(fields)
    return result


def maturity(*, website, capabilities, confirmed_without_website=False):
    if "first_party_pathway_observed" in capabilities and website:
        return "L4"
    if "third_party_pathway_observed" in capabilities and website:
        return "L3"
    if "catalog" in capabilities and website:
        return "L2"
    if website:
        return "L1"
    return "L0" if confirmed_without_website else "Unknown"


def assess_case(case, pages, directory, independent_premises=None, physical=None):
    started = time.perf_counter()
    bytes_before, requests_before = pages.bytes, pages.requests
    attempts = []
    extraction = None
    candidates = list(
        dict.fromkeys(
            url for raw in case["urls"] if (url := web_url(raw)) and not platform(url)
        )
    )
    for url in candidates[:3]:
        status, body = pages.page(url)
        attempt = {
            "url": url,
            "status": status,
            "observed_at": datetime.now(UTC).isoformat(),
        }
        attempts.append(attempt)
        if status != "ok":
            continue
        sha = hashlib.sha256(body).hexdigest()
        snapshot = directory / f"{sha}.html"
        if not snapshot.exists():
            with snapshot.open("xb") as file:
                file.write(body)
        attempt.update({"snapshot": snapshot.name, "sha256": sha})
        extraction = extract_page(body, url, case)
        if extraction["official_website_verified"]:
            break
    verified = bool(extraction and extraction["official_website_verified"])
    features = extraction["individual_capabilities"] if verified else []
    level = maturity(website=verified, capabilities=features)
    corroborated = bool(
        verified
        and independent_premises
        and not case["observed_flags"]
        and not case["unit"]
        and normalize_address(independent_premises["value"]) == case["civic"]
    )
    linked = []
    if corroborated and physical:
        options = {
            tuple(edge["parcel_ids"])
            for edge in physical
            if edge["status"] == "accepted"
        }
        if len(options) == 1 and all(edge["status"] == "accepted" for edge in physical):
            linked = list(next(iter(options)))
    transaction_advertising = bool(
        verified
        and any(
            item["kind"] in {"ordering_link", "ecommerce_link", "booking_link"}
            for item in extraction["advertised_links"]
        )
    )
    scoped_assessment = bool(verified and not transaction_advertising)
    if verified:
        # Advertised transaction links need a separately reviewed destination.
        if transaction_advertising:
            reason = "transaction_pathway_review"
        elif not corroborated:
            reason = "independent_premises_review"
        elif not linked:
            reason = "physical_link_review"
        else:
            reason = None
    elif not candidates:
        reason = "no_first_party_url_lead"
    elif attempts and all(a["status"] == "host_not_allowed" for a in attempts):
        reason = "merchant_hosts_not_allowlisted"
    elif any(a["status"] == "ok" for a in attempts):
        reason = "merchant_identity_requires_review"
    else:
        reason = "page_access_or_robots_review"
    return {
        "case_id": case["id"],
        "stratum": case.get("stratum", "regression_control"),
        "civic": case["civic"],
        "source_refs": case["source_refs"],
        "flags": case["observed_flags"],
        "level": level,
        "attempts": attempts,
        "extraction": extraction,
        "review_reason": reason,
        "digital_assessment_completed": scoped_assessment,
        "corroborated_advertised_premises": corroborated,
        "independent_premises_evidence": independent_premises if corroborated else None,
        "parcel_ids": linked,
        "seconds": time.perf_counter() - started,
        "requests": pages.requests - requests_before,
        "transfer_bytes": pages.bytes - bytes_before,
    }


def run(frozen_path, hosts_path, output, *, prior_reviews=None, physical_path=None):
    started, cpu = time.perf_counter(), time.process_time()
    frozen = json.loads(frozen_path.read_bytes())
    hosts = set(json.loads(hosts_path.read_bytes()))
    prior = {}
    if prior_reviews:
        reviews = json.loads(prior_reviews.read_bytes())
        for review in reviews:
            for field in review["fields"]:
                if (
                    field["field"] != "premises"
                    or field["lineage"] != "chamber_gift_listing"
                ):
                    continue
                observed_at = datetime.fromisoformat(field["observed_at"])
                if observed_at.tzinfo is None or not (
                    0 <= (datetime.now(UTC) - observed_at).days <= 90
                ):
                    continue
                path = (prior_reviews.parent / field["snapshot"]).resolve()
                if (
                    not path.is_relative_to(prior_reviews.parent.resolve())
                    or digest(path) != field["sha256"]
                ):
                    raise ValueError("Prior Chamber receipt cannot be verified")
                prior[review["business_id"]] = field
    geo = {}
    if physical_path:
        for edge in json.loads(physical_path.read_bytes())["address_parcel_edges"]:
            geo.setdefault(edge["civic"], []).append(edge)
    output.mkdir(parents=True, exist_ok=False)
    with httpx.Client(
        timeout=10, follow_redirects=False, headers={"User-Agent": f"{AGENT}/1.0"}
    ) as client:
        pages = PublicPages(client, hosts)
        reports = {
            key: [
                assess_case(
                    case, pages, output, prior.get(case["id"]), geo.get(case["civic"])
                )
                for case in frozen[key]
            ]
            for key in ("cases", "shared_original_companions", "controls")
        }
    cohort = reports["cases"]
    measures = {
        "locations": len(cohort),
        "verified_websites": sum(r["level"] not in {"L0", "Unknown"} for r in cohort),
        "corroborated": sum(r["corroborated_advertised_premises"] for r in cohort),
        "corroborated_with_parcels": sum(bool(r["parcel_ids"]) for r in cohort),
        "digital_reviews_completed": sum(
            r["digital_assessment_completed"] for r in cohort
        ),
        "autonomous_completions": sum(not r["review_reason"] for r in cohort),
        "review_reasons": dict(Counter(r["review_reason"] for r in cohort)),
        "maturity": dict(Counter(r["level"] for r in cohort)),
        "wall_seconds": time.perf_counter() - started,
        "cpu_seconds": time.process_time() - cpu,
        "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "requests": pages.requests,
        "transfer_bytes": pages.bytes,
    }
    with (output / "audit.json").open("x", encoding="utf-8") as file:
        json.dump(
            {
                "cohort_sha256": digest(frozen_path),
                "host_policy_sha256": digest(hosts_path),
                "metrics": measures,
                **reports,
            },
            file,
            indent=2,
        )
    print(json.dumps(measures, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cohort", "allowed_hosts", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--prior-reviews", type=Path)
    parser.add_argument("--physical", type=Path)
    args = parser.parse_args()
    run(
        args.cohort,
        args.allowed_hosts,
        args.output,
        prior_reviews=args.prior_reviews,
        physical_path=args.physical,
    )


if __name__ == "__main__":
    main()
