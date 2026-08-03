from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import ipaddress
import json
from pathlib import Path
import re
import socket
import time
from typing import Callable, Iterable, Mapping, Protocol
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, build_opener
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

EXTRACTOR_VERSION = "omega-web-hg-html/0.1.0"
TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stable_id(prefix: str, *parts: str) -> str:
    digest = sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest}"


def canonicalize_url(url: str, *, base_url: str | None = None) -> str:
    absolute = urljoin(base_url, url) if base_url else url
    split = urlsplit(absolute)
    scheme = split.scheme.lower()
    hostname = (split.hostname or "").lower().rstrip(".")
    if not scheme or not hostname:
        raise ValueError(f"URL absolue HTTP(S) requise: {url!r}")

    port = split.port
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        port = None
    netloc = hostname if port is None else f"{hostname}:{port}"

    path = re.sub(r"/{2,}", "/", split.path or "/")
    query_items = []
    for key, value in parse_qsl(split.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in TRACKING_PARAMETERS:
            continue
        query_items.append((key, value))
    query_items.sort()
    return urlunsplit((scheme, netloc, path, urlencode(query_items, doseq=True), ""))


@dataclass(frozen=True)
class CrawlConfig:
    seed_url: str
    allowed_domains: tuple[str, ...] = ()
    include_subdomains: bool = False
    user_agent: str = "OmegaWebHG/0.1 (+https://github.com/Tristan-TM-Poly)"
    page_budget: int | None = 100
    max_response_bytes: int = 5_000_000
    delay_seconds: float = 1.0
    timeout_seconds: float = 20.0
    store_raw: bool = True
    block_private_networks: bool = True

    def normalized_domains(self) -> tuple[str, ...]:
        if self.allowed_domains:
            return tuple(sorted({domain.lower().rstrip(".") for domain in self.allowed_domains}))
        host = (urlsplit(self.seed_url).hostname or "").lower().rstrip(".")
        if not host:
            raise ValueError("seed_url doit contenir un domaine")
        return (host,)


@dataclass(frozen=True)
class PolicyDecision:
    url: str
    allowed: bool
    code: str
    reason: str
    checked_at: str


@dataclass(frozen=True)
class FetchResponse:
    requested_url: str
    final_url: str
    status: int
    headers: Mapping[str, str]
    body: bytes
    fetched_at: str


class Fetcher(Protocol):
    def fetch(self, url: str, *, headers: Mapping[str, str] | None = None) -> FetchResponse:
        ...


class PolicyGate:
    def __init__(
        self,
        config: CrawlConfig,
        *,
        resolver: Callable[[str], Iterable[str]] | None = None,
        robots_loader: Callable[[str], str | None] | None = None,
    ) -> None:
        self.config = config
        self.allowed_domains = config.normalized_domains()
        self._resolver = resolver or self._default_resolver
        self._robots_loader = robots_loader or self._default_robots_loader
        self._robots: dict[str, RobotFileParser | None] = {}

    @staticmethod
    def _default_resolver(hostname: str) -> Iterable[str]:
        return sorted({row[4][0] for row in socket.getaddrinfo(hostname, None)})

    def _default_robots_loader(self, robots_url: str) -> str | None:
        request = Request(robots_url, headers={"User-Agent": self.config.user_agent, "Accept": "text/plain,*/*;q=0.1"})
        try:
            with build_opener().open(request, timeout=self.config.timeout_seconds) as response:
                payload = response.read(1_000_000)
                return payload.decode("utf-8", errors="replace")
        except OSError:
            return None

    def _domain_allowed(self, host: str) -> bool:
        for domain in self.allowed_domains:
            if host == domain:
                return True
            if self.config.include_subdomains and host.endswith("." + domain):
                return True
        return False

    def _public_addresses_only(self, host: str) -> bool:
        try:
            addresses = list(self._resolver(host))
        except OSError:
            return False
        if not addresses:
            return False
        for raw in addresses:
            address = ipaddress.ip_address(raw)
            if not address.is_global:
                return False
        return True

    def _robots_for(self, url: str) -> RobotFileParser | None:
        split = urlsplit(url)
        origin = f"{split.scheme}://{split.netloc}"
        if origin in self._robots:
            return self._robots[origin]
        robots_url = origin + "/robots.txt"
        payload = self._robots_loader(robots_url)
        if payload is None:
            self._robots[origin] = None
            return None
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(payload.splitlines())
        self._robots[origin] = parser
        return parser

    def decide(self, url: str, *, check_robots: bool = True) -> PolicyDecision:
        checked_at = utc_now()
        try:
            normalized = canonicalize_url(url)
        except (ValueError, UnicodeError) as exc:
            return PolicyDecision(url, False, "INVALID_URL", str(exc), checked_at)

        split = urlsplit(normalized)
        host = split.hostname or ""
        if split.scheme not in {"http", "https"}:
            return PolicyDecision(normalized, False, "SCHEME_DENIED", "Seuls HTTP et HTTPS sont autorisés.", checked_at)
        if split.username or split.password:
            return PolicyDecision(normalized, False, "CREDENTIALS_DENIED", "Les identifiants intégrés à l'URL sont interdits.", checked_at)
        if not self._domain_allowed(host):
            return PolicyDecision(normalized, False, "OUT_OF_SCOPE", "Domaine hors de la portée autorisée.", checked_at)
        if self.config.block_private_networks and not self._public_addresses_only(host):
            return PolicyDecision(normalized, False, "NON_PUBLIC_NETWORK", "Adresse privée, locale, réservée ou non résolue.", checked_at)
        if check_robots:
            robots = self._robots_for(normalized)
            if robots is not None and not robots.can_fetch(self.config.user_agent, normalized):
                return PolicyDecision(normalized, False, "ROBOTS_DENIED", "Accès refusé par robots.txt.", checked_at)
        return PolicyDecision(normalized, True, "ALLOW", "Portée, réseau et robots acceptés.", checked_at)


class PoliteHTTPFetcher:
    def __init__(self, config: CrawlConfig) -> None:
        self.config = config
        self._last_request: dict[str, float] = {}
        self._opener = build_opener()

    def _throttle(self, host: str) -> None:
        previous = self._last_request.get(host)
        if previous is not None:
            remaining = self.config.delay_seconds - (time.monotonic() - previous)
            if remaining > 0:
                time.sleep(remaining)
        self._last_request[host] = time.monotonic()

    def fetch(self, url: str, *, headers: Mapping[str, str] | None = None) -> FetchResponse:
        host = urlsplit(url).hostname or ""
        self._throttle(host)
        request_headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.5,*/*;q=0.1",
        }
        if headers:
            request_headers.update(headers)
        request = Request(url, headers=request_headers)
        with self._opener.open(request, timeout=self.config.timeout_seconds) as response:
            body = response.read(self.config.max_response_bytes + 1)
            if len(body) > self.config.max_response_bytes:
                raise ValueError(f"Réponse supérieure à {self.config.max_response_bytes} octets")
            response_headers = {key.lower(): value for key, value in response.headers.items()}
            return FetchResponse(
                requested_url=url,
                final_url=canonicalize_url(response.geturl()),
                status=int(getattr(response, "status", response.getcode())),
                headers=response_headers,
                body=body,
                fetched_at=utc_now(),
            )


@dataclass(frozen=True)
class SectionRecord:
    section_id: str
    page_id: str
    index: int
    level: int
    heading: str
    text: str
    locator: str


@dataclass(frozen=True)
class PageRecord:
    page_id: str
    requested_url: str
    final_url: str
    canonical_url: str
    title: str
    language: str | None
    evidence_id: str
    content_sha256: str
    fetched_at: str
    status: int
    content_type: str
    byte_length: int


@dataclass(frozen=True)
class EdgeRecord:
    edge_id: str
    relation: str
    source_id: str
    target_id: str
    evidence_id: str


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    requested_url: str
    final_url: str
    fetched_at: str
    http_status: int
    content_type: str
    content_sha256: str
    byte_length: int
    headers: Mapping[str, str]
    extractor: str
    policy_code: str
    raw_blob: str | None


@dataclass
class ParsedHTML:
    title: str = ""
    canonical_url: str | None = None
    language: str | None = None
    links: list[str] = field(default_factory=list)
    sections: list[tuple[int, str, str]] = field(default_factory=list)


class SemanticHTMLParser(HTMLParser):
    _TEXT_TAGS = {"p", "li", "blockquote", "pre", "td", "th", "dt", "dd"}
    _IGNORE_TAGS = {"script", "style", "noscript", "svg", "canvas", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.result = ParsedHTML()
        self._ignored_depth = 0
        self._title_depth = 0
        self._heading_level: int | None = None
        self._heading_chunks: list[str] = []
        self._text_depth = 0
        self._text_chunks: list[str] = []
        self._current_level = 0
        self._current_heading = "Document"
        self._current_chunks: list[str] = []

    @staticmethod
    def _clean(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr = {key.lower(): value for key, value in attrs}
        if tag in self._IGNORE_TAGS:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if tag == "html":
            self.result.language = attr.get("lang")
        elif tag == "title":
            self._title_depth += 1
        elif tag == "link" and (attr.get("rel") or "").lower() == "canonical" and attr.get("href"):
            self.result.canonical_url = attr["href"]
        elif tag == "a" and attr.get("href"):
            self.result.links.append(attr["href"])
        elif re.fullmatch(r"h[1-6]", tag):
            self._flush_section()
            self._heading_level = int(tag[1])
            self._heading_chunks = []
        elif tag in self._TEXT_TAGS:
            self._text_depth += 1
            if self._text_depth == 1:
                self._text_chunks = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self._IGNORE_TAGS:
            if self._ignored_depth:
                self._ignored_depth -= 1
            return
        if self._ignored_depth:
            return
        if tag == "title" and self._title_depth:
            self._title_depth -= 1
        elif re.fullmatch(r"h[1-6]", tag) and self._heading_level is not None:
            heading = self._clean(" ".join(self._heading_chunks)) or "Section sans titre"
            self._current_level = self._heading_level
            self._current_heading = heading
            self._heading_level = None
            self._heading_chunks = []
        elif tag in self._TEXT_TAGS and self._text_depth:
            self._text_depth -= 1
            if self._text_depth == 0:
                text = self._clean(" ".join(self._text_chunks))
                if text:
                    self._current_chunks.append(text)
                self._text_chunks = []

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        if self._title_depth:
            self.result.title += data
        if self._heading_level is not None:
            self._heading_chunks.append(data)
        if self._text_depth:
            self._text_chunks.append(data)

    def _flush_section(self) -> None:
        text = self._clean("\n".join(self._current_chunks))
        if text:
            self.result.sections.append((self._current_level, self._current_heading, text))
        self._current_chunks = []

    def finish(self) -> ParsedHTML:
        self._flush_section()
        self.result.title = self._clean(self.result.title)
        return self.result


def parse_html(body: bytes, *, content_type: str = "text/html") -> ParsedHTML:
    charset_match = re.search(r"charset=([\w.-]+)", content_type, flags=re.I)
    charset = charset_match.group(1) if charset_match else "utf-8"
    try:
        text = body.decode(charset, errors="replace")
    except LookupError:
        text = body.decode("utf-8", errors="replace")
    parser = SemanticHTMLParser()
    parser.feed(text)
    parser.close()
    return parser.finish()


@dataclass
class CrawlResult:
    config: CrawlConfig
    pages: list[PageRecord] = field(default_factory=list)
    sections: list[SectionRecord] = field(default_factory=list)
    edges: list[EdgeRecord] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    decisions: list[PolicyDecision] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    raw_blobs: dict[str, bytes] = field(default_factory=dict)

    @property
    def hypergraph(self) -> dict[str, object]:
        nodes: list[dict[str, object]] = []
        for page in self.pages:
            nodes.append({"id": page.page_id, "kind": "page", "label": page.title or page.canonical_url, "properties": asdict(page)})
        for section in self.sections:
            nodes.append({"id": section.section_id, "kind": "section", "label": section.heading, "properties": asdict(section)})
        hyperedges = [asdict(edge) for edge in self.edges]
        return {"schema": "omega-web-hg/0.1", "nodes": nodes, "hyperedges": hyperedges}

    def oak_report(self) -> dict[str, object]:
        allowed = sum(1 for item in self.decisions if item.allowed)
        denied = len(self.decisions) - allowed
        evidence_ids = {item.evidence_id for item in self.evidence}
        orphan_pages = [page.page_id for page in self.pages if page.evidence_id not in evidence_ids]
        section_page_ids = {item.page_id for item in self.sections}
        page_ids = {item.page_id for item in self.pages}
        orphan_sections = sorted(section_page_ids - page_ids)
        raw_expected = sum(1 for item in self.evidence if item.raw_blob)
        raw_present = sum(1 for item in self.evidence if item.raw_blob and item.raw_blob in self.raw_blobs)
        status = "PASS_R0_1" if not orphan_pages and not orphan_sections and not self.errors else "PASS_WITH_ERRORS_R0_1"
        return {
            "status": status,
            "scope": list(self.config.normalized_domains()),
            "pages": len(self.pages),
            "sections": len(self.sections),
            "edges": len(self.edges),
            "evidence_records": len(self.evidence),
            "policy_allowed": allowed,
            "policy_denied": denied,
            "errors": self.errors,
            "orphan_pages": orphan_pages,
            "orphan_sections": orphan_sections,
            "raw_blobs_expected": raw_expected,
            "raw_blobs_present": raw_present,
            "boundary": "Structural capture and provenance audit only; extracted content is not factual certification or legal permission to republish.",
        }

    @staticmethod
    def _write_jsonl(path: Path, records: Iterable[object]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for record in records:
                payload = asdict(record) if hasattr(record, "__dataclass_fields__") else record
                handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def write(self, output_dir: str | Path) -> Path:
        root = Path(output_dir)
        root.mkdir(parents=True, exist_ok=True)
        self._write_jsonl(root / "pages.jsonl", self.pages)
        self._write_jsonl(root / "sections.jsonl", self.sections)
        self._write_jsonl(root / "edges.jsonl", self.edges)
        self._write_jsonl(root / "evidence.jsonl", self.evidence)
        self._write_jsonl(root / "policy-decisions.jsonl", self.decisions)
        (root / "hypergraph.json").write_text(json.dumps(self.hypergraph, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        (root / "oak-report.json").write_text(json.dumps(self.oak_report(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        manifest = {
            "schema": "omega-web-hg-manifest/0.1",
            "created_at": utc_now(),
            "seed_url": canonicalize_url(self.config.seed_url),
            "allowed_domains": list(self.config.normalized_domains()),
            "page_budget": self.config.page_budget,
            "extractor": EXTRACTOR_VERSION,
            "outputs": [
                "pages.jsonl",
                "sections.jsonl",
                "edges.jsonl",
                "evidence.jsonl",
                "policy-decisions.jsonl",
                "hypergraph.json",
                "hypergraph.graphml",
                "oak-report.json",
            ],
        }
        (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        (root / "hypergraph.graphml").write_text(self.to_graphml(), encoding="utf-8")
        for relative, payload in self.raw_blobs.items():
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
        return root

    def to_graphml(self) -> str:
        graphml = ET.Element("graphml", xmlns="http://graphml.graphdrawing.org/xmlns")
        graph = ET.SubElement(graphml, "graph", edgedefault="directed", id="omega-web-hg")
        for node in self.hypergraph["nodes"]:  # type: ignore[index]
            element = ET.SubElement(graph, "node", id=str(node["id"]))
            ET.SubElement(element, "data", key="kind").text = str(node["kind"])
            ET.SubElement(element, "data", key="label").text = str(node["label"])
        for edge in self.edges:
            element = ET.SubElement(graph, "edge", id=edge.edge_id, source=edge.source_id, target=edge.target_id)
            ET.SubElement(element, "data", key="relation").text = edge.relation
            ET.SubElement(element, "data", key="evidence_id").text = edge.evidence_id
        return ET.tostring(graphml, encoding="unicode")


class WebHypergraphCrawler:
    def __init__(
        self,
        config: CrawlConfig,
        *,
        policy: PolicyGate | None = None,
        fetcher: Fetcher | None = None,
    ) -> None:
        self.config = config
        self.policy = policy or PolicyGate(config)
        self.fetcher = fetcher or PoliteHTTPFetcher(config)

    def crawl(self) -> CrawlResult:
        result = CrawlResult(config=self.config)
        seed = canonicalize_url(self.config.seed_url)
        frontier: deque[str] = deque([seed])
        queued = {seed}
        visited: set[str] = set()

        while frontier:
            if self.config.page_budget is not None and len(result.pages) >= self.config.page_budget:
                break
            candidate = frontier.popleft()
            if candidate in visited:
                continue
            visited.add(candidate)

            decision = self.policy.decide(candidate)
            result.decisions.append(decision)
            if not decision.allowed:
                continue

            try:
                response = self.fetcher.fetch(candidate)
                final_decision = self.policy.decide(response.final_url, check_robots=False)
                if not final_decision.allowed:
                    result.decisions.append(final_decision)
                    continue
                content_type = response.headers.get("content-type", "application/octet-stream")
                if "html" not in content_type.lower():
                    result.errors.append({"url": candidate, "code": "UNSUPPORTED_CONTENT", "message": content_type})
                    continue
                parsed = parse_html(response.body, content_type=content_type)
            except (OSError, ValueError, UnicodeError) as exc:
                result.errors.append({"url": candidate, "code": type(exc).__name__, "message": str(exc)})
                continue

            body_hash = sha256(response.body).hexdigest()
            canonical = canonicalize_url(parsed.canonical_url, base_url=response.final_url) if parsed.canonical_url else response.final_url
            page_id = stable_id("page", canonical)
            evidence_id = stable_id("evidence", response.final_url, body_hash, response.fetched_at)
            raw_blob = f"raw/{body_hash[:2]}/{body_hash}.html" if self.config.store_raw else None
            if raw_blob:
                result.raw_blobs[raw_blob] = response.body

            page = PageRecord(
                page_id=page_id,
                requested_url=response.requested_url,
                final_url=response.final_url,
                canonical_url=canonical,
                title=parsed.title,
                language=parsed.language,
                evidence_id=evidence_id,
                content_sha256=body_hash,
                fetched_at=response.fetched_at,
                status=response.status,
                content_type=content_type,
                byte_length=len(response.body),
            )
            result.pages.append(page)
            result.evidence.append(
                EvidenceRecord(
                    evidence_id=evidence_id,
                    requested_url=response.requested_url,
                    final_url=response.final_url,
                    fetched_at=response.fetched_at,
                    http_status=response.status,
                    content_type=content_type,
                    content_sha256=body_hash,
                    byte_length=len(response.body),
                    headers={key: value for key, value in response.headers.items() if key in {"etag", "last-modified", "content-type", "content-language", "cache-control"}},
                    extractor=EXTRACTOR_VERSION,
                    policy_code=decision.code,
                    raw_blob=raw_blob,
                )
            )

            for index, (level, heading, text) in enumerate(parsed.sections):
                section_id = stable_id("section", page_id, str(index), heading, text)
                section = SectionRecord(
                    section_id=section_id,
                    page_id=page_id,
                    index=index,
                    level=level,
                    heading=heading,
                    text=text,
                    locator=f"section:{index}",
                )
                result.sections.append(section)
                result.edges.append(
                    EdgeRecord(
                        edge_id=stable_id("edge", page_id, section_id, "PAGE_CONTAINS_SECTION"),
                        relation="PAGE_CONTAINS_SECTION",
                        source_id=page_id,
                        target_id=section_id,
                        evidence_id=evidence_id,
                    )
                )

            for raw_link in parsed.links:
                try:
                    link = canonicalize_url(raw_link, base_url=response.final_url)
                except (ValueError, UnicodeError):
                    continue
                target_id = stable_id("page", link)
                result.edges.append(
                    EdgeRecord(
                        edge_id=stable_id("edge", page_id, target_id, "PAGE_LINKS_TO_PAGE"),
                        relation="PAGE_LINKS_TO_PAGE",
                        source_id=page_id,
                        target_id=target_id,
                        evidence_id=evidence_id,
                    )
                )
                if link not in queued:
                    queued.add(link)
                    frontier.append(link)

        return result
