"""Bounded public HTTPS acquisition, with private request and robots evidence."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit

import httpx

AGENT = "UMWorldModelResearch"
MAX_BODY = 2_000_000
MAX_ROBOTS = 256_000
# GET endpoints can mutate state too. Never follow transactional/action URLs.
ACTION = re.compile(
    r"(?:^|[/_.-])(checkout|cart|add-to-cart|buy-now|logout|login|sign-in|account|payment|purchase|subscribe|submit|confirm|delete|remove|cancel|pay)(?:$|[/_.-])",
    re.IGNORECASE,
)


def safe_url(value: str) -> str | None:
    """Strict policy for redirects/discovery; never upgrade or rewrite their query."""
    try:
        p = urlsplit(value)
        host = p.hostname or ""
        if (
            p.scheme != "https"
            or p.username
            or p.password
            or p.port not in {None, 443}
            or not re.fullmatch(r"[a-z0-9.-]+", host)
            or "." not in host
            or p.query
            or any(ord(c) < 32 for c in value)
            or "\\" in value
        ):
            return None
        try:
            ipaddress.ip_address(host)
            return None
        except ValueError:
            pass
        if ACTION.search(unquote(p.path)):
            return None
        return urlunsplit(("https", host, p.path or "/", "", ""))
    except ValueError:
        return None


class PublicOnlyTransport(httpx.BaseTransport):
    """Pin each request to a checked public IP; retain hostname for Host and TLS.

    No environment proxies, DNS rebinding window, TLS disabling or cross-host
    keepalive reuse. All DNS answers must be public, including IPv4-mapped IPv6.
    """

    def __init__(self, hosts, *, resolver=socket.getaddrinfo, transport=None):
        self.hosts = set(hosts)
        self.resolve = resolver
        self.inner = transport or httpx.HTTPTransport(
            verify=True,
            trust_env=False,
            retries=0,
            limits=httpx.Limits(max_keepalive_connections=0),
        )

    def handle_request(self, request):
        host = request.url.host
        if not safe_url(str(request.url)) or host not in self.hosts:
            raise httpx.ConnectError("destination_policy_denied", request=request)
        try:
            answers = self.resolve(host, 443, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise httpx.ConnectError("dns_resolution_failed", request=request) from exc
        ips = sorted({answer[4][0] for answer in answers})
        addresses = [ipaddress.ip_address(ip) for ip in ips]
        if not ips or any(
            not ip.is_global
            or ip.is_multicast
            or ip.is_reserved
            or getattr(ip, "is_site_local", False)
            for ip in addresses
        ):
            raise httpx.ConnectError("private_network_destination", request=request)
        # HTTPcore's documented request extension supplies TLS SNI/verification name.
        # The URL's IP is the actual connection target; it is never DNS-resolved again.
        pinned = httpx.Request(
            request.method,
            request.url.copy_with(host=ips[0]),
            headers={**dict(request.headers), "host": host, "connection": "close"},
            stream=request.stream,
            extensions={**request.extensions, "sni_hostname": host},
        )
        response = self.inner.handle_request(pinned)
        response.extensions["validated_public_ips"] = ips
        return response

    def close(self):
        self.inner.close()


def octets(value):
    # RFC 9309: decode unreserved percent encodings; keep reserved octets encoded.
    value = re.sub(
        r"%([0-9a-fA-F]{2})",
        lambda m: (
            chr(int(m[1], 16))
            if chr(int(m[1], 16))
            in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
            else "%" + m[1].upper()
        ),
        value,
    )
    return quote(value, safe="/%*:$?&=+;,@!~'()-._")


class RobotsRules:
    """Conservative robots groups, longest-match rules, and pacing directives."""

    def __init__(self, body):
        text = body.decode("utf-8-sig", errors="strict")
        if text.lstrip().startswith(("<", "{", "[")) or "\x00" in text:
            raise ValueError("unsupported_content")
        groups, agents, rules, pacing = [], [], [], []
        seen_directive = False
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if ":" not in line:
                raise ValueError("unsupported_syntax")
            key, value = (part.strip() for part in line.split(":", 1))
            key = key.lower()
            if key == "user-agent":
                if seen_directive:
                    groups.append((agents, rules, pacing))
                    agents, rules, pacing, seen_directive = [], [], [], False
                if not value:
                    raise ValueError("empty_agent")
                agents.append(value.lower())
            elif key in {"allow", "disallow", "crawl-delay", "request-rate"}:
                if not agents:
                    raise ValueError("rule_without_agent")
                seen_directive = True
                if key in {"allow", "disallow"}:
                    if value and not value.startswith(("/", "*")):
                        raise ValueError("unsupported_path")
                    if value:
                        rules.append((key == "allow", octets(value)))
                else:
                    try:
                        if key == "request-rate":
                            n, seconds = value.split("/")
                            delay = float(seconds) / int(n)
                        else:
                            delay = float(value)
                        if not 0 <= delay < float("inf"):
                            raise ValueError()
                    except (ValueError, ZeroDivisionError):
                        raise ValueError("unsupported_pacing") from None
                    pacing.append(delay)
            elif key != "sitemap":
                # Unknown access extensions cannot safely be interpreted as permission.
                raise ValueError("unsupported_directive")
        if agents:
            groups.append((agents, rules, pacing))
        matches = [
            (
                max(
                    (len(a) for a in names if a != "*" and a in AGENT.lower()),
                    default=0,
                ),
                rs,
                ps,
                "*" in names,
            )
            for names, rs, ps in groups
        ]
        best = max((m[0] for m in matches), default=0)
        selected = [
            (rs, ps)
            for score, rs, ps, wildcard in matches
            if (score == best if best else wildcard)
        ]
        self.rules = [r for rs, _ in selected for r in rs]
        self.delay = max([0.3] + [p for _, ps in selected for p in ps])
        self.group_count = len(selected)

    def allowed(self, url):
        p = urlsplit(url)
        path = octets(p.path + ("?" + p.query if p.query else ""))
        matches = []
        for allow, pattern in self.rules:
            end = pattern.endswith("$")
            pattern = pattern[:-1] if end else pattern
            regex = (
                "^"
                + ".*".join(re.escape(s) for s in pattern.split("*"))
                + ("$" if end else "")
            )
            if re.search(regex, path):
                matches.append((len(pattern.replace("*", "").encode()), allow))
        return max(matches, default=(0, True))[1]


class PublicPages:
    def __init__(
        self,
        client,
        allowed_hosts,
        evidence_dir: Path | None = None,
        *,
        max_redirects=5,
    ):
        if not 0 <= max_redirects <= 5:
            raise ValueError("max_redirects must be between zero and five")
        self.client, self.hosts = client, set(allowed_hosts)
        self.directory = evidence_dir
        self.max_redirects = max_redirects
        self.robots, self.waits, self.last = {}, {}, {}
        self.bytes = self.requests = 0
        self.events = []
        self.final_url = None
        self.last_trace = []

    def record(self, **record):
        record = {
            "id": len(self.events),
            "observed_at": datetime.now(UTC).isoformat(),
            **record,
        }
        self.events.append(record)
        if self.directory:
            with (self.directory / "acquisition.jsonl").open(
                "a", encoding="utf-8"
            ) as f:
                f.write(json.dumps(record) + "\n")
        return record

    def policy(self, url):
        if not safe_url(url):
            return "unsafe_destination"
        if urlsplit(url).hostname not in self.hosts:
            return "host_not_allowed"
        return None

    def request(self, url, *, kind="page"):
        denied = self.policy(url)
        if denied:
            self.record(kind=kind, url=url, status=denied)
            return denied, None, None
        host = urlsplit(url).hostname
        time.sleep(
            max(
                0,
                self.waits.get(host, 0.3) - (time.monotonic() - self.last.get(host, 0)),
            )
        )
        self.requests += 1
        record = {
            "kind": kind,
            "url": url,
            "source_id": "merchant_web" if kind == "page" else "merchant_robots",
            "source_record_id": None,
            "source_vintage": None,
            "resolution_method": "bounded_https_get",
        }
        try:
            with self.client.stream("GET", url, follow_redirects=False) as response:
                record.update(
                    http_status=response.status_code,
                    content_type=response.headers.get("content-type", ""),
                    source_vintage=response.headers.get("last-modified"),
                    etag=response.headers.get("etag"),
                    resolved_ips=response.extensions.get("validated_public_ips"),
                )
                body = bytearray()
                limit = MAX_ROBOTS if kind == "robots" else MAX_BODY
                truncated = False
                try:
                    for chunk in response.iter_bytes(chunk_size=16384):
                        if len(body) + len(chunk) > limit:
                            body.extend(chunk[: limit - len(body)])
                            truncated = True
                            break
                        body.extend(chunk)
                finally:
                    self.bytes += response.num_bytes_downloaded
                body = bytes(body)
                sha = hashlib.sha256(body).hexdigest()
                record.update(
                    sha256=sha,
                    snapshot=sha + ".body",
                    truncated=truncated,
                    decoded_bytes=len(body),
                    transfer_bytes=response.num_bytes_downloaded,
                )
                if self.directory:
                    path = self.directory / record["snapshot"]
                    if not path.exists():
                        path.write_bytes(body)
                target = None
                if response.is_redirect:
                    target = urljoin(url, response.headers.get("location", ""))
                    status = (
                        "redirect"
                        if response.headers.get("location")
                        else "redirect_missing_location"
                    )
                    record["redirect_to"] = target
                elif response.status_code != 200:
                    status = f"http_{response.status_code}"
                elif truncated:
                    status = "body_limit"
                elif kind == "page" and "html" not in record["content_type"].lower():
                    status = "not_html"
                else:
                    status = "ok"
                self.record(**record, status=status)
                return status, body, target
        except httpx.HTTPError as exc:
            detail = str(exc)
            if "private_network_destination" in detail:
                status = "private_network_destination"
            elif "dns_resolution_failed" in detail:
                status = "dns_error"
            elif "CERTIFICATE_VERIFY_FAILED" in detail:
                status = "tls_error"
            elif isinstance(exc, httpx.TimeoutException):
                status = "network_timeout"
            elif isinstance(exc, httpx.ProxyError):
                status = "proxy_denied"
            else:
                status = "network_error"
            self.record(
                **record, status=status, error_type=type(exc).__name__, error=detail
            )
            return status, None, None
        finally:
            self.last[host] = time.monotonic()

    def chain(self, url, *, kind):
        seen = set()
        for hop in range(self.max_redirects + 1):
            denied = self.policy(url)
            if denied:
                status = ("redirect_" if hop else "") + denied
                self.record(kind=kind, url=url, status=status)
                return status, None, url
            if url in seen:
                self.record(kind=kind, url=url, status="redirect_loop")
                return "redirect_loop", None, url
            seen.add(url)
            if kind == "page":
                decision = self.permitted(url)
                if decision != "allowed":
                    return decision, None, url
            status, body, target = self.request(url, kind=kind)
            if status != "redirect":
                return status, body, url
            if hop == self.max_redirects:
                self.record(kind=kind, url=url, status="redirect_limit")
                return "redirect_limit", None, url
            # Validate the destination without normalizing away unsafe query/scheme.
            url = target
        raise AssertionError("unreachable")

    def permitted(self, url):
        host = urlsplit(url).hostname
        if host not in self.robots:
            start = len(self.events)
            status, body, final = self.chain(
                f"https://{host}/robots.txt", kind="robots"
            )
            robot, decision = None, "robots_" + status
            if status in {"http_404", "http_410"}:
                decision = "allowed"
            elif status == "ok":
                try:
                    robot = RobotsRules(body)
                    decision = "allowed" if robot.delay <= 10 else "robots_pacing_limit"
                    self.waits[host] = robot.delay
                except (UnicodeError, ValueError) as exc:
                    decision = "robots_unsupported_content"
                    self.record(
                        kind="robots_parser",
                        url=final,
                        status=decision,
                        reason=str(exc),
                    )
            self.robots[host] = (robot, decision, list(range(start, len(self.events))))
        robot, decision, evidence = self.robots[host]
        if decision == "allowed" and robot and not robot.allowed(url):
            decision = "robots_explicit_disallow"
        self.record(
            kind="robots_decision",
            url=url,
            status=decision,
            evidence_event_ids=evidence,
            parser="deterministic_robots_v1",
            applicable_rules=robot.rules if robot else None,
            crawl_delay=robot.delay if robot else None,
        )
        return decision

    def page(self, url):
        start = len(self.events)
        status, body, self.final_url = self.chain(url, kind="page")
        self.last_trace = list(range(start, len(self.events)))
        return status, body
