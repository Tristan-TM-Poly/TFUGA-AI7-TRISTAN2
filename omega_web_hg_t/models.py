from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Callable, Iterable, Mapping, Protocol
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler
import xml.etree.ElementTree as ET

EXTRACTOR_VERSION = "omega-web-hg-html/0.1.0"
TRACKING_PARAMETERS = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "source"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stable_id(prefix: str, *parts: str) -> str:
    digest = sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest}"


def canonicalize_url(url: str, *, base_url: str | None = None) -> str:
    absolute = urljoin(base_url, url) if base_url else url
    split = urlsplit(absolute)
    if split.username or split.password:
        raise ValueError("Les identifiants intégrés à l'URL sont interdits.")
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


class SafeRedirectHandler(HTTPRedirectHandler):
    def __init__(self, validator: Callable[[str], bool]) -> None:
        super().__init__()
        self._validator = validator

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        normalized = canonicalize_url(newurl, base_url=req.full_url)
        if not self._validator(normalized):
            raise ValueError(f"Redirection refusée par PolicyGate: {normalized}")
        return super().redirect_request(req, fp, code, msg, headers, normalized)


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
    discovered_urls: dict[str, str] = field(default_factory=dict)

    @property
    def hypergraph(self) -> dict[str, object]:
        nodes: list[dict[str, object]] = []
        for page in self.pages:
            nodes.append({"id": page.page_id, "kind": "page", "label": page.title or page.canonical_url, "properties": asdict(page)})
        for section in self.sections:
            nodes.append({"id": section.section_id, "kind": "section", "label": section.heading, "properties": asdict(section)})
        known_ids = {str(node["id"]) for node in nodes}
        for node_id, url in sorted(self.discovered_urls.items()):
            if node_id not in known_ids:
                nodes.append({"id": node_id, "kind": "page_candidate", "label": url, "properties": {"url": url}})
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
        self._write_jsonl(root / "url-candidates.jsonl", ({"node_id": key, "url": value} for key, value in sorted(self.discovered_urls.items())))
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
                "url-candidates.jsonl",
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
        ET.SubElement(graphml, "key", id="kind", **{"for": "node", "attr.name": "kind", "attr.type": "string"})
        ET.SubElement(graphml, "key", id="label", **{"for": "node", "attr.name": "label", "attr.type": "string"})
        ET.SubElement(graphml, "key", id="relation", **{"for": "edge", "attr.name": "relation", "attr.type": "string"})
        ET.SubElement(graphml, "key", id="evidence_id", **{"for": "edge", "attr.name": "evidence_id", "attr.type": "string"})
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
