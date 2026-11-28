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

import httpx
from bs4 import BeautifulSoup

from .commercial import name_key
from .merchant_acquisition import AGENT, PublicOnlyTransport, PublicPages
from .merchant_identity import catalog_evidence, discover, identity, unit_of
from .normalize import normalize_address
from .physical_graph import digest

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
    nodes = list(jsonld_nodes(soup))
    key = name_key(case["name"])
    identity_result = identity(soup, nodes, case)
    name_matches = [s for s, _ in identity_result["name_matches"]]
    body_text = " ".join(soup.stripped_strings)
    town = re.search(r"\bStoneham\b", body_text, re.IGNORECASE)
    civic = case["civic"]
    structured = [n.get("address") for n in nodes if isinstance(n.get("address"), dict)]
    local_structured = [
        a
        for a in structured
        if str(a.get("addressLocality", "")).strip().casefold() == "stoneham"
        and a.get("streetAddress")
        and str(a.get("addressRegion", "MA")).casefold() in {"ma", "massachusetts"}
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
    body_matches = []
    body_conflicts = []
    if town:
        for text in soup.stripped_strings:
            # Verify a civic line with a delimiter, and retain only that public line.
            line = re.split(r"\bStoneham\b", text, maxsplit=1, flags=re.IGNORECASE)[
                0
            ].strip(" ,")
            line = line.replace(",", " ")
            if normalize_address(line) == civic and len(line) < 100:
                body_match = line
                body_matches.append(line)
            elif (
                len(line) < 100
                and re.search(r"\bStoneham\b", text, re.IGNORECASE)
                and re.fullmatch(
                    r"\d+[A-Za-z-]*\s+[\w .'-]+\s+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Court|Ct|Way|Square|Sq|Parkway|Pkwy)\.?",
                    line,
                    re.IGNORECASE,
                )
            ):
                body_conflicts.append(line)
    matching_addresses = [a["streetAddress"] for a in exact_structured] + body_matches
    expected_unit = (
        unit_of(str(case["unit"])) or unit_of("unit " + str(case["unit"]))
        if case.get("unit")
        else None
    )
    observed_units = {unit_of(a) for a in matching_addresses}
    unit_conflict = bool(matching_addresses and (observed_units != {expected_unit}))
    verified = bool(
        name_matches
        and not platform(url)
        and (exact_structured or body_match)
        and not structured_conflicts
        and not body_conflicts
        and not unit_conflict
    )
    result = {
        "official_website_verified": verified,
        **identity_result,
        "unit_status": "ambiguous"
        if unit_conflict
        else ("matched" if expected_unit else "not_specified"),
        "abstention_reasons": (
            []
            if verified
            else (["name_evidence_missing"] if not name_matches else [])
            + (["civic_evidence_missing"] if not matching_addresses else [])
            + (
                ["conflicting_civic_evidence"]
                if structured_conflicts or body_conflicts
                else []
            )
            + (["unit_unresolved"] if unit_conflict else [])
            + (["third_party_platform"] if platform(url) else [])
        ),
        "catalog_evidence": catalog_evidence(soup, nodes, url),
        "identity_excerpt": name_matches[0] if verified else None,
        "advertised_civic_excerpt": (
            (exact_structured[0]["streetAddress"] if exact_structured else body_match)
            if verified
            else None
        ),
        "conflicting_structured_addresses": structured_conflicts,
        "conflicting_body_addresses": body_conflicts,
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
    product = bool(result["catalog_evidence"])
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
    fields = {"official_website"} if verified else set()
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


def assess_case(
    case, pages, directory, independent_premises=None, physical=None, *, page_budget=5
):
    started = time.perf_counter()
    bytes_before, requests_before = pages.bytes, pages.requests
    if not 0 <= page_budget <= 5:
        raise ValueError("page_budget must be between zero and five")
    attempts, documents, discovered, visited = [], [], {}, set()
    extraction = None
    candidates = list(
        dict.fromkeys(
            url for raw in case["urls"] if (url := web_url(raw)) and not platform(url)
        )
    )

    def fetch(url, role, discovery=None):
        visited.add(url)
        status, body = pages.page(url)
        attempt = {
            "url": url,
            "final_url": pages.final_url,
            "role": role,
            "status": status,
            "observed_at": datetime.now(UTC).isoformat(),
            "acquisition_event_ids": pages.last_trace,
            "discovery": discovery,
        }
        attempts.append(attempt)
        if status != "ok":
            return
        final_url = pages.final_url
        visited.add(final_url)
        sha = hashlib.sha256(body).hexdigest()
        snapshot = directory / f"{sha}.body"
        if not snapshot.exists():
            snapshot.write_bytes(body)
        attempt.update({"snapshot": snapshot.name, "sha256": sha})
        result = extract_page(body, final_url, case)
        attempt["extraction"] = result
        documents.append((attempt, result))
        soup = BeautifulSoup(body, "html.parser")
        for link in discover(soup, list(jsonld_nodes(soup)), final_url):
            link["source_sha256"] = sha
            discovered.setdefault(link["url"], link)

    for url in candidates[:3]:
        fetch(url, "frozen_lead")
        if any(result["official_website_verified"] for _, result in documents):
            break
    for _ in range(page_budget):
        pending = sorted(
            (link for url, link in discovered.items() if url not in visited),
            key=lambda link: (link["priority"], link["url"]),
        )
        if not pending:
            break
        link = pending[0]
        fetch(link["url"], "relevant_internal_page", link)

    verified_documents = [
        (a, r) for a, r in documents if r["official_website_verified"]
    ]
    if verified_documents:
        anchor, result = verified_documents[0]
        extraction = dict(result)
        extraction["evidence_pages"] = []
        features, ads, catalog = set(), [], []
        conflicts = []
        for attempt, result in documents:
            if domain(attempt["final_url"]) != domain(anchor["final_url"]):
                continue
            if (
                result["conflicting_structured_addresses"]
                or result["conflicting_body_addresses"]
                or result["unit_status"] == "ambiguous"
            ):
                conflicts.append(attempt["sha256"])
                continue
            features.update(result["individual_capabilities"])
            ads.extend(result["advertised_links"])
            # Catalog on an authored internal page inherits only website ownership,
            # never a new civic/occupancy identity or a transaction verification.
            catalog.extend(
                {**e, "source_sha256": attempt["sha256"], "url": attempt["final_url"]}
                for e in result["catalog_evidence"]
            )
            extraction["evidence_pages"].append(
                {
                    "url": attempt["final_url"],
                    "sha256": attempt["sha256"],
                    "snapshot": attempt["snapshot"],
                    "observed_at": attempt["observed_at"],
                    "resolution_method": result["identity_method"]
                    if result["official_website_verified"]
                    else "authored_same_host_link_from_verified_site",
                }
            )
        if conflicts:
            extraction["official_website_verified"] = False
            extraction["abstention_reasons"] = ["cross_page_civic_or_unit_conflict"]
            extraction["conflict_snapshot_hashes"] = conflicts
        if catalog:
            features.add("catalog")
        extraction["individual_capabilities"] = sorted(features)
        extraction["advertised_links"] = ads
        extraction["catalog_evidence"] = catalog
        extraction["identity_source"] = {
            k: anchor[k] for k in ("final_url", "snapshot", "sha256", "observed_at")
        }
    elif documents:
        extraction = documents[-1][1]
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
        "additional_page_budget": page_budget,
        "additional_pages_attempted": sum(
            a["role"] == "relevant_internal_page" for a in attempts
        ),
        "discovered_pages_not_attempted": sum(url not in visited for url in discovered),
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


def run(
    frozen_path,
    hosts_path,
    output,
    *,
    prior_reviews=None,
    physical_path=None,
    page_budget=5,
    max_redirects=5,
):
    if not 0 <= page_budget <= 5 or not 0 <= max_redirects <= 5:
        raise ValueError("page and redirect budgets must be between zero and five")
    started_at = datetime.now(UTC).isoformat()
    started, cpu = time.perf_counter(), time.process_time()
    frozen = json.loads(frozen_path.read_bytes())
    host_list = json.loads(hosts_path.read_bytes())
    if not isinstance(host_list, list) or not all(
        isinstance(h, str) and re.fullmatch(r"[a-z0-9.-]+", h) for h in host_list
    ):
        raise ValueError("Expected a flat lowercase DNS host array")
    hosts = set(host_list)
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
        timeout=10,
        follow_redirects=False,
        headers={"User-Agent": f"{AGENT}/1.0"},
        transport=PublicOnlyTransport(hosts),
        trust_env=False,
    ) as client:
        pages = PublicPages(client, hosts, output, max_redirects=max_redirects)
        reports = {
            key: [
                assess_case(
                    case,
                    pages,
                    output,
                    prior.get(case["id"]),
                    geo.get(case["civic"]),
                    page_budget=page_budget,
                )
                for case in frozen[key]
            ]
            for key in ("cases", "shared_original_companions", "controls")
        }
    cohort = reports["cases"]
    measures = {
        "locations": len(cohort),
        "retrieved_locations": sum(
            any(a["status"] == "ok" for a in r["attempts"]) for r in cohort
        ),
        "additional_pages_attempted": sum(
            r["additional_pages_attempted"] for r in cohort
        ),
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
                "started_at": started_at,
                "finished_at": datetime.now(UTC).isoformat(),
                "acquisition_version": "phase22a-v1",
                "page_budget": page_budget,
                "max_redirects": max_redirects,
                "physical_sha256": digest(physical_path) if physical_path else None,
                "prior_reviews_sha256": digest(prior_reviews)
                if prior_reviews
                else None,
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
    parser.add_argument("--page-budget", type=int, choices=range(6), default=5)
    parser.add_argument("--max-redirects", type=int, choices=range(6), default=5)
    args = parser.parse_args()
    run(
        args.cohort,
        args.allowed_hosts,
        args.output,
        prior_reviews=args.prior_reviews,
        physical_path=args.physical,
        page_budget=args.page_budget,
        max_redirects=args.max_redirects,
    )


if __name__ == "__main__":
    main()
