from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Iterable, Mapping
import xml.etree.ElementTree as ET

from omega_web_hg_t.models import CrawlConfig, CrawlResult, stable_id, utc_now

R02_SCHEMA = "omega-web-hg/0.2"
R02_EXTRACTOR = "omega-web-hg-multiformat/0.2.0"


def config_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class R02Config:
    seed_url: str
    allowed_domains: tuple[str, ...] = ()
    include_subdomains: bool = False
    user_agent: str = "OmegaWebHG/0.2 (+https://github.com/Tristan-TM-Poly)"
    resource_budget: int | None = 1_000
    max_depth: int | None = 12
    max_frontier: int | None = 100_000
    max_response_bytes: int = 10_000_000
    delay_seconds: float = 1.0
    timeout_seconds: float = 20.0
    store_raw: bool = True
    store_warc: bool = True
    discover_standard_endpoints: bool = True
    discover_sitemaps: bool = True
    discover_feeds: bool = True
    respect_meta_robots: bool = True
    block_private_networks: bool = True
    max_retries: int = 2
    lease_seconds: int = 300

    def base(self) -> CrawlConfig:
        return CrawlConfig(
            seed_url=self.seed_url,
            allowed_domains=self.allowed_domains,
            include_subdomains=self.include_subdomains,
            user_agent=self.user_agent,
            page_budget=self.resource_budget,
            max_response_bytes=self.max_response_bytes,
            delay_seconds=self.delay_seconds,
            timeout_seconds=self.timeout_seconds,
            store_raw=self.store_raw,
            block_private_networks=self.block_private_networks,
        )

    def as_manifest(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FrontierItem:
    url: str
    depth: int
    priority: float
    discovered_from: str | None
    mechanism: str
    attempts: int


@dataclass(frozen=True)
class DiscoveryRecord:
    discovery_id: str
    source_url: str | None
    target_url: str
    mechanism: str
    depth: int
    discovered_at: str
    queued: bool
    note: str = ""


@dataclass(frozen=True)
class DocumentMetadataRecord:
    metadata_id: str
    page_id: str
    url: str
    robots_directives: tuple[str, ...]
    feed_urls: tuple[str, ...]
    sitemap_urls: tuple[str, ...]
    license_urls: tuple[str, ...]
    jsonld_sha256: tuple[str, ...]
    noarchive: bool
    nofollow: bool


@dataclass(frozen=True)
class VersionRecord:
    version_id: str
    run_id: str
    url: str
    canonical_url: str
    fetched_at: str
    http_status: int
    content_type: str
    content_sha256: str
    byte_length: int
    evidence_id: str
    etag: str | None
    last_modified: str | None
    title: str
    section_digest: str
    raw_blob: str | None
    warc_record_id: str | None


@dataclass(frozen=True)
class ChangeRecord:
    change_id: str
    run_id: str
    url: str
    change_type: str
    detected_at: str
    previous_version_id: str | None
    current_version_id: str | None
    previous_sha256: str | None
    current_sha256: str | None
    details: Mapping[str, object] = field(default_factory=dict)


@dataclass
class RunBundle:
    run_id: str
    config: R02Config
    crawl: CrawlResult
    discoveries: list[DiscoveryRecord] = field(default_factory=list)
    metadata: list[DocumentMetadataRecord] = field(default_factory=list)
    versions: list[VersionRecord] = field(default_factory=list)
    changes: list[ChangeRecord] = field(default_factory=list)
    started_at: str = field(default_factory=utc_now)
    finished_at: str | None = None
    frontier_remaining: int = 0
    resumed: bool = False
    state_snapshot: str | None = None
    warc_file: str | None = None

    @staticmethod
    def _write_jsonl(path: Path, records: Iterable[object]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for record in records:
                payload = asdict(record) if hasattr(record, "__dataclass_fields__") else record
                handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    @property
    def hypergraph_v2(self) -> dict[str, object]:
        nodes: dict[str, dict[str, object]] = {}
        edges: dict[str, dict[str, object]] = {}

        def add_node(node_id: str, kind: str, label: str, properties: Mapping[str, object] | None = None) -> None:
            nodes.setdefault(node_id, {"id": node_id, "kind": kind, "label": label, "properties": dict(properties or {})})

        def add_edge(relation: str, source_id: str, target_id: str, evidence_id: str | None = None) -> None:
            edge_id = stable_id("edge", relation, source_id, target_id, evidence_id or "")
            edges.setdefault(edge_id, {"edge_id": edge_id, "relation": relation, "source_id": source_id, "target_id": target_id, "evidence_id": evidence_id})

        add_node(self.run_id, "crawl_run", self.run_id, {"started_at": self.started_at, "finished_at": self.finished_at})
        for node in self.crawl.hypergraph["nodes"]:  # type: ignore[index]
            add_node(str(node["id"]), str(node["kind"]), str(node["label"]), node.get("properties", {}))
        for edge in self.crawl.hypergraph["hyperedges"]:  # type: ignore[index]
            edges[str(edge["edge_id"])] = dict(edge)
        for evidence in self.crawl.evidence:
            add_node(evidence.evidence_id, "evidence", evidence.final_url, asdict(evidence))
        for version in self.versions:
            page_id = stable_id("page", version.canonical_url)
            add_node(page_id, "page_candidate", version.canonical_url, {"url": version.canonical_url})
            add_node(version.version_id, "page_version", f"{version.canonical_url} @ {version.fetched_at}", asdict(version))
            add_edge("PAGE_HAS_VERSION", page_id, version.version_id, version.evidence_id)
            add_edge("VERSION_DERIVED_FROM_EVIDENCE", version.version_id, version.evidence_id, version.evidence_id)
            add_edge("RUN_CAPTURED_VERSION", self.run_id, version.version_id, version.evidence_id)
        for metadata in self.metadata:
            add_node(metadata.metadata_id, "document_metadata", metadata.url, asdict(metadata))
            add_edge("PAGE_HAS_METADATA", metadata.page_id, metadata.metadata_id)
        for change in self.changes:
            add_node(change.change_id, "change", f"{change.change_type}: {change.url}", asdict(change))
            add_edge("RUN_DETECTED_CHANGE", self.run_id, change.change_id)
            if change.previous_version_id:
                add_node(change.previous_version_id, "page_version", change.previous_version_id)
                add_edge("CHANGE_PREVIOUS_VERSION", change.change_id, change.previous_version_id)
            if change.current_version_id:
                add_node(change.current_version_id, "page_version", change.current_version_id)
                add_edge("CHANGE_CURRENT_VERSION", change.change_id, change.current_version_id)
        for discovery in self.discoveries:
            target_id = stable_id("page", discovery.target_url)
            add_node(target_id, "page_candidate", discovery.target_url, {"url": discovery.target_url})
            source_id = self.run_id if discovery.source_url is None else stable_id("page", discovery.source_url)
            if discovery.source_url is not None:
                add_node(source_id, "page_candidate", discovery.source_url, {"url": discovery.source_url})
            add_edge(f"DISCOVERED_BY_{discovery.mechanism.upper()}", source_id, target_id)
        for decision in self.crawl.decisions:
            decision_id = stable_id("policy", decision.url, decision.code, decision.checked_at)
            add_node(decision_id, "policy_decision", f"{decision.code}: {decision.url}", asdict(decision))
            target_id = stable_id("page", decision.url)
            add_node(target_id, "page_candidate", decision.url, {"url": decision.url})
            add_edge("RUN_MADE_POLICY_DECISION", self.run_id, decision_id)
            add_edge("POLICY_DECISION_GOVERNS_URL", decision_id, target_id)
        return {"schema": R02_SCHEMA, "nodes": sorted(nodes.values(), key=lambda item: str(item["id"])), "hyperedges": sorted(edges.values(), key=lambda item: str(item["edge_id"]))}

    @property
    def provenance_jsonld(self) -> dict[str, object]:
        graph: list[dict[str, object]] = [{"@id": f"urn:omega:{self.run_id}", "@type": "prov:Activity", "schema:name": self.run_id, "prov:startedAtTime": self.started_at, "prov:endedAtTime": self.finished_at}]
        for page in self.crawl.pages:
            graph.append({"@id": f"urn:omega:{page.page_id}", "@type": "prov:Entity", "schema:name": page.title or page.canonical_url, "schema:url": page.canonical_url, "omega:contentSha256": page.content_sha256})
        for evidence in self.crawl.evidence:
            graph.append({"@id": f"urn:omega:{evidence.evidence_id}", "@type": "prov:Entity", "schema:url": evidence.final_url, "omega:contentSha256": evidence.content_sha256, "omega:httpStatus": evidence.http_status})
        for version in self.versions:
            graph.append({"@id": f"urn:omega:{version.version_id}", "@type": "prov:Entity", "prov:specializationOf": {"@id": f"urn:omega:{stable_id('page', version.canonical_url)}"}, "prov:wasDerivedFrom": {"@id": f"urn:omega:{version.evidence_id}"}, "prov:wasGeneratedBy": {"@id": f"urn:omega:{self.run_id}"}, "prov:generatedAtTime": version.fetched_at, "omega:contentSha256": version.content_sha256})
        return {"@context": {"prov": "http://www.w3.org/ns/prov#", "schema": "https://schema.org/", "omega": "urn:omega:web-hg:"}, "@graph": graph}

    def to_graphml_v2(self) -> str:
        graphml = ET.Element("graphml", xmlns="http://graphml.graphdrawing.org/xmlns")
        ET.SubElement(graphml, "key", id="kind", **{"for": "node", "attr.name": "kind", "attr.type": "string"})
        ET.SubElement(graphml, "key", id="label", **{"for": "node", "attr.name": "label", "attr.type": "string"})
        ET.SubElement(graphml, "key", id="relation", **{"for": "edge", "attr.name": "relation", "attr.type": "string"})
        ET.SubElement(graphml, "key", id="evidence_id", **{"for": "edge", "attr.name": "evidence_id", "attr.type": "string"})
        graph = ET.SubElement(graphml, "graph", edgedefault="directed", id="omega-web-hg-r02")
        for node in self.hypergraph_v2["nodes"]:  # type: ignore[index]
            element = ET.SubElement(graph, "node", id=str(node["id"]))
            ET.SubElement(element, "data", key="kind").text = str(node["kind"])
            ET.SubElement(element, "data", key="label").text = str(node["label"])
        for edge in self.hypergraph_v2["hyperedges"]:  # type: ignore[index]
            element = ET.SubElement(graph, "edge", id=str(edge["edge_id"]), source=str(edge["source_id"]), target=str(edge["target_id"]))
            ET.SubElement(element, "data", key="relation").text = str(edge["relation"])
            if edge.get("evidence_id"):
                ET.SubElement(element, "data", key="evidence_id").text = str(edge["evidence_id"])
        return ET.tostring(graphml, encoding="unicode")

    def oak_report(self) -> dict[str, object]:
        page_ids = {item.page_id for item in self.crawl.pages}
        evidence_ids = {item.evidence_id for item in self.crawl.evidence}
        node_ids = page_ids | {item.section_id for item in self.crawl.sections} | set(self.crawl.discovered_urls)
        orphan_edges = [item.edge_id for item in self.crawl.edges if item.source_id not in node_ids or item.target_id not in node_ids]
        graph_v2 = self.hypergraph_v2
        graph_v2_node_ids = {str(item["id"]) for item in graph_v2["nodes"]}  # type: ignore[index]
        orphan_edges_v2 = [str(item["edge_id"]) for item in graph_v2["hyperedges"] if str(item["source_id"]) not in graph_v2_node_ids or str(item["target_id"]) not in graph_v2_node_ids]  # type: ignore[index]
        orphan_evidence = [item.evidence_id for item in self.crawl.pages if item.evidence_id not in evidence_ids]
        duplicate_versions = len(self.versions) - len({item.version_id for item in self.versions})
        status = "PASS_R0_2"
        if orphan_edges or orphan_edges_v2 or orphan_evidence or duplicate_versions or self.crawl.errors:
            status = "PASS_WITH_FINDINGS_R0_2"
        return {"schema": "omega-web-hg-oak/0.2", "status": status, "run_id": self.run_id, "pages": len(self.crawl.pages), "sections": len(self.crawl.sections), "edges": len(self.crawl.edges), "evidence_records": len(self.crawl.evidence), "discoveries": len(self.discoveries), "versions": len(self.versions), "changes": len(self.changes), "frontier_remaining": self.frontier_remaining, "resumed": self.resumed, "orphan_edges": orphan_edges, "orphan_edges_v2": orphan_edges_v2, "orphan_evidence": orphan_evidence, "duplicate_versions": duplicate_versions, "errors": self.crawl.errors, "boundaries": ["Structural capture and provenance are not factual certification.", "robots.txt and meta robots are technical gates, not legal authorization.", "WARC capture is not permission to republish copyrighted or personal data.", "DNS checks reduce SSRF risk but do not certify resistance to every DNS rebinding scenario."]}

    def write(self, root: str | Path) -> Path:
        destination = Path(root)
        destination.mkdir(parents=True, exist_ok=True)
        self.crawl.write(destination)
        self._write_jsonl(destination / "discoveries.jsonl", self.discoveries)
        self._write_jsonl(destination / "document-metadata.jsonl", self.metadata)
        self._write_jsonl(destination / "versions.jsonl", self.versions)
        self._write_jsonl(destination / "changes.jsonl", self.changes)
        (destination / "hypergraph-v2.json").write_text(json.dumps(self.hypergraph_v2, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        (destination / "hypergraph-v2.graphml").write_text(self.to_graphml_v2(), encoding="utf-8")
        (destination / "provenance.jsonld").write_text(json.dumps(self.provenance_jsonld, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        report = self.oak_report()
        (destination / "oak-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        manifest = {"schema": "omega-web-hg-manifest/0.2", "run_id": self.run_id, "started_at": self.started_at, "finished_at": self.finished_at or utc_now(), "config": self.config.as_manifest(), "config_sha256": config_digest(self.config.as_manifest()), "resumed": self.resumed, "frontier_remaining": self.frontier_remaining, "state_snapshot": self.state_snapshot, "warc_file": self.warc_file, "outputs": sorted(path.name for path in destination.iterdir() if path.is_file())}
        (destination / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return destination
