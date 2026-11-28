"""Evidence-bound name variants, unit checks, and bounded internal link selection."""

import re
from urllib.parse import urljoin, urlsplit

from .commercial import name_key
from .merchant_acquisition import safe_url
from .normalize import normalize_address

DESCRIPTORS = (
    "restaurant",
    "italian restaurant",
    "bar and grill",
    "inc",
    "llc",
    "ltd",
    "incorporated",
)
BUSINESS_TYPES = {
    "Organization",
    "LocalBusiness",
    "Restaurant",
    "Store",
    "BookStore",
    "FoodEstablishment",
    "ProfessionalService",
    "MedicalBusiness",
    "Dentist",
    "BeautySalon",
    "NailSalon",
    "HealthAndBeautyBusiness",
    "DryCleaningOrLaundry",
    "SportsActivityLocation",
}
UNIT = re.compile(
    r"(?:\b(?:suite|ste|unit|apt|apartment)\.?\s*|#\s*)([a-z0-9-]+)\b", re.IGNORECASE
)
PRIORITIES = [
    r"\babout\b",
    r"\bcontact\b",
    r"\blocations?\b",
    r"\bmenus?\b",
    r"\bshop\b",
    r"\bproducts?\b",
    r"\bservices?\b",
    r"\b(bookings?|reservations?|appointments?)\b",
    r"\b(order|ordering|takeout)\b",
]


def organization(node):
    types = node.get("@type", [])
    types = [types] if isinstance(types, str) else types
    return isinstance(types, list) and bool(
        BUSINESS_TYPES.intersection(str(t) for t in types)
    )


def unit_of(value):
    match = UNIT.search(value or "")
    return match[1].upper() if match else None


def identity(soup, nodes, case):
    expected = name_key(case["name"])
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    candidates = [(text, "title") for text in re.split(r"\s+[|–—-]\s+", title)]
    candidates += [(h.get_text(" ", strip=True), "heading") for h in soup.select("h1")]
    for node in nodes:
        if organization(node):
            candidates += [
                (node[k], "structured_name")
                for k in ("name", "legalName")
                if isinstance(node.get(k), str)
            ]
    for img in soup.select("img[alt]"):
        alt = img.get("alt", "")
        if re.search(r"\blogo\b", alt, re.IGNORECASE):
            candidates.append(
                (re.split(r"\s+logo\b", alt, flags=re.IGNORECASE)[0], "logo")
            )
    exact = [
        (s, origin)
        for s, origin in candidates
        if expected and name_key(s) == expected and origin != "logo"
    ]
    matches, method = exact, "exact_name" if exact else None
    alias_nodes = []
    if not matches:
        for node in nodes:
            alt = node.get("alternateName", [])
            alt = [alt] if isinstance(alt, str) else alt
            address = node.get("address", {})
            if (
                organization(node)
                and isinstance(alt, list)
                and isinstance(node.get("name"), str)
                and expected in [name_key(x) for x in alt if isinstance(x, str)]
                and isinstance(address, dict)
                and str(address.get("addressLocality", "")).casefold() == "stoneham"
                and normalize_address(address.get("streetAddress")) == case["civic"]
            ):
                alias_nodes.append(node)
                matches.append((node["name"], "structured_alternate_name"))
                method = "explicit_structured_alias_with_civic"
    if not matches and len(expected.replace(" ", "")) >= 5:
        expanded = [
            (s, origin)
            for s, origin in candidates
            if any(name_key(s) == expected + " " + suffix for suffix in DESCRIPTORS)
        ]
        # A title and logo must independently display the SAME expansion, not merely
        # share tokens. No edit-distance or arbitrary prefix acceptance is used.
        for text, _ in expanded:
            origins = {
                origin for s, origin in expanded if name_key(s) == name_key(text)
            }
            if "logo" in origins and origins.intersection(
                {"title", "heading", "structured_name"}
            ):
                matches = [
                    (s, origin)
                    for s, origin in expanded
                    if name_key(s) == name_key(text)
                ]
                method = "descriptor_expansion_title_logo"
                break
    return {
        "name_matches": matches,
        "identity_method": method,
        "name_candidates": candidates,
        "alias_evidence": [
            {
                "name": n["name"],
                "alternateName": n["alternateName"],
                "address": n["address"],
            }
            for n in alias_nodes
        ],
    }


def discover(soup, nodes, base_url):
    """Only authored internal links/metadata; no guessed paths or sitemap crawl."""
    raw = [
        (a.get("href", ""), a.get_text(" ", strip=True)) for a in soup.select("a[href]")
    ]
    for node in nodes:
        for key, label in [
            ("hasMenu", "menu"),
            ("menu", "menu"),
            ("hasOfferCatalog", "products"),
        ]:
            values = node.get(key, [])
            values = values if isinstance(values, list) else [values]
            for value in values:
                if isinstance(value, dict):
                    value = value.get("url", "")
                if isinstance(value, str):
                    raw.append((value, label))
    candidates = {}
    for href, label in raw:
        if not href or href.startswith("#"):
            continue
        url = safe_url(urljoin(base_url, href))
        if not url or urlsplit(url).hostname != urlsplit(base_url).hostname:
            continue
        subject = label + " " + re.sub(r"[-_/]", " ", urlsplit(url).path)
        priority = next(
            (
                i
                for i, pattern in enumerate(PRIORITIES)
                if re.search(pattern, subject, re.IGNORECASE)
            ),
            None,
        )
        if priority is not None:
            item = {
                "url": url,
                "label": label[:160],
                "priority": priority,
                "discovered_on": base_url,
            }
            if url not in candidates or priority < candidates[url]["priority"]:
                candidates[url] = item
    return sorted(candidates.values(), key=lambda x: (x["priority"], x["url"]))[:200]


def catalog_evidence(soup, nodes, url):
    evidence = []
    for n in nodes:
        if n.get("@type") in ("Product", "Menu") and isinstance(n.get("name"), str):
            evidence.append(
                {"method": "structured_product_or_menu", "excerpt": n["name"][:160]}
            )
    if evidence:
        return evidence[:5]
    if not re.search(r"menu|shop|product|catalog", urlsplit(url).path, re.IGNORECASE):
        return []
    # Repeated named, priced product/menu cards; a price somewhere on the page
    # alone is not a catalog. Ignore global wrappers and unnamed cart controls.
    found = set()
    for card in soup.select(
        '[class*="product"], [class*="Product"], [class*="menu-item"], [itemtype$="Product"]'
    ):
        classes = " ".join(card.get("class", []))
        if not re.search(
            r"item|card|list-item", classes, re.IGNORECASE
        ) and not card.get("itemtype"):
            continue
        name = card.select_one(
            'h1, h2, h3, h4, [class*="title"], [class*="Title"], [class*="name"], [itemprop="name"]'
        )
        text = card.get_text(" ", strip=True)
        price = re.search(r"\$\s*\d+(?:[.,]\d{2})?", text)
        if name and price and len(text) <= 1800:
            label = name.get_text(" ", strip=True)
            if label and label not in found:
                found.add(label)
                evidence.append(
                    {
                        "method": "visible_named_priced_card",
                        "excerpt": label[:120] + " " + price[0],
                    }
                )
    return evidence[:5] if len(evidence) >= 2 else []
