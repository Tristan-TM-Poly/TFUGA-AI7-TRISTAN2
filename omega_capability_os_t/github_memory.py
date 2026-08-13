from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import re

from .core import Capability, load_registry

MEMORY_SCHEMA_VERSION = "0.1.0"
RELATIONS = {
    "uses",
    "implements",
    "extends",
    "duplicates",
    "replaces",
    "supersedes",
    "conflicts",
    "generalizes",
    "specializes",
    "derived_from",
    "tests",
    "failed_because",
    "candidate_similarity",
}
DECISIONS = {"REUSE", "COMPOSE", "EXTEND", "INSPECT", "CREATE"}

_STOPWORDS = {
    "a", "an", "and", "as", "at", "be", "by", "de", "des", "du", "en", "et", "for",
    "from", "in", "la", "le", "les", "of", "on", "or", "pour", "the", "to", "un", "une",
    "with", "t", "omega", "feat", "fix", "docs", "test", "tests", "py", "md", "json",
}


def _tokens(value: str | Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, str):
        raw = value
    else:
        raw = " ".join(str(item) for item in value)
    parts = re.findall(r"[A-Za-z0-9]+", raw.lower().replace("_", " ").replace("-", " "))
    return tuple(sorted({part for part in parts if len(part) > 1 and part not in _STOPWORDS}))


def _jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    a, b = set(left), set(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _coverage(required: Iterable[str], produced: Iterable[str]) -> float:
    req = set(required)
    if not req:
        return 0.0
    return len(req & set(produced)) / len(req)


def _stable_digest(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CapabilityRequest:
    request_id: str
    description: str
    domains: tuple[str, ...] = ()
    consumes: tuple[str, ...] = ()
    produces: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CapabilityRequest":
        return cls(
            request_id=str(payload.get("request_id") or payload.get("id") or "request"),
            description=str(payload.get("description", "")),
            domains=tuple(map(str, payload.get("domains", []))),
            consumes=tuple(map(str, payload.get("consumes", []))),
            produces=tuple(map(str, payload.get("produces", []))),
        )

    @property
    def keywords(self) -> tuple[str, ...]:
        return _tokens((self.description, *self.domains, *self.consumes, *self.produces))


@dataclass(frozen=True)
class PRMemory:
    repository: str
    number: int
    state: str
    title: str
    body: str = ""
    head_sha: str | None = None
    head_ref: str | None = None
    base_ref: str | None = None
    draft: bool = False
    merged: bool = False
    files: tuple[str, ...] = ()
    updated_at: str | None = None
    url: str | None = None

    @property
    def ref(self) -> str:
        return f"pr:{self.repository}#{self.number}"

    @property
    def lifecycle(self) -> str:
        if self.merged:
            return "MERGED"
        if self.state.lower() == "open":
            return "DRAFT" if self.draft else "OPEN"
        return "CLOSED"

    @property
    def epistemic_memory(self) -> str:
        # Lifecycle is not evidence quality. M+ requires an explicit outcome receipt elsewhere.
        return "M?"

    @property
    def keywords(self) -> tuple[str, ...]:
        return _tokens((self.title, self.body, *self.files))

    @classmethod
    def from_github(cls, repository: str, payload: Mapping[str, Any], files: Iterable[str] = ()) -> "PRMemory":
        head = payload.get("head") if isinstance(payload.get("head"), Mapping) else {}
        base = payload.get("base") if isinstance(payload.get("base"), Mapping) else {}
        number = payload.get("number") or payload.get("pr_number")
        if number is None:
            raise ValueError("pull request payload is missing number")
        merged = bool(payload.get("merged") or payload.get("merged_at"))
        return cls(
            repository=repository,
            number=int(number),
            state=str(payload.get("state", "unknown")),
            title=str(payload.get("title", "")),
            body=str(payload.get("body") or ""),
            head_sha=str(payload.get("head_sha") or head.get("sha") or "") or None,
            head_ref=str(payload.get("head_ref") or head.get("ref") or "") or None,
            base_ref=str(payload.get("base") if isinstance(payload.get("base"), str) else base.get("ref") or "") or None,
            draft=bool(payload.get("draft", False)),
            merged=merged,
            files=tuple(sorted(set(map(str, files)))),
            updated_at=str(payload.get("updated_at") or "") or None,
            url=str(payload.get("html_url") or payload.get("url") or payload.get("display_url") or "") or None,
        )


@dataclass(frozen=True)
class AssetObservation:
    asset_id: str
    source_ref: str
    source_kind: str
    label: str
    keywords: tuple[str, ...]
    confidence: float
    boundary: str


@dataclass(frozen=True)
class CapabilityObservation:
    capability: Capability
    source_ref: str
    source_kind: str = "explicit_registry"
    keywords: tuple[str, ...] = ()
    confidence: float = 1.0

    @property
    def capability_id(self) -> str:
        return self.capability.capability_id


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    relation: str
    evidence: str
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if self.relation not in RELATIONS:
            raise ValueError(f"unsupported relation: {self.relation}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be inside [0, 1]")


class CapabilityGraph:
    """Typed relation graph. Semantic similarity is always kept separate from explicit lineage."""

    def __init__(self, edges: Iterable[GraphEdge] = ()) -> None:
        self._edges: list[GraphEdge] = []
        for edge in edges:
            self.add(edge)

    @property
    def edges(self) -> tuple[GraphEdge, ...]:
        return tuple(self._edges)

    def add(self, edge: GraphEdge) -> None:
        if edge not in self._edges:
            self._edges.append(edge)

    def related(self, node: str, relations: Iterable[str] | None = None) -> tuple[GraphEdge, ...]:
        allowed = set(relations or RELATIONS)
        return tuple(
            edge for edge in self._edges
            if edge.relation in allowed and (edge.source == node or edge.target == node)
        )

    def supersession_chain(self, node: str) -> tuple[str, ...]:
        chain = [node]
        seen = {node}
        current = node
        while True:
            candidates = [
                edge.target for edge in self._edges
                if edge.source == current and edge.relation in {"supersedes", "replaces"}
            ]
            if not candidates:
                return tuple(chain)
            nxt = sorted(candidates)[0]
            if nxt in seen:
                raise ValueError(f"supersession cycle detected at {nxt}")
            chain.append(nxt)
            seen.add(nxt)
            current = nxt


_EXPLICIT_RELATION_PATTERNS = {
    "uses": re.compile(r"(?im)^\s*(?:uses|reuses)\s*:\s*(.+)$"),
    "extends": re.compile(r"(?im)^\s*extends\s*:\s*(.+)$"),
    "supersedes": re.compile(r"(?im)^\s*supersedes\s*:\s*(.+)$"),
    "replaces": re.compile(r"(?im)^\s*replaces\s*:\s*(.+)$"),
    "conflicts": re.compile(r"(?im)^\s*conflicts\s*:\s*(.+)$"),
    "derived_from": re.compile(r"(?im)^\s*(?:derived[_ -]from|inherits[_ -]from)\s*:\s*(.+)$"),
}


def extract_explicit_relations(pr: PRMemory) -> tuple[GraphEdge, ...]:
    edges: list[GraphEdge] = []
    for relation, pattern in _EXPLICIT_RELATION_PATTERNS.items():
        for match in pattern.finditer(pr.body):
            refs = re.findall(r"(?:PR[- ]?|#)(\d+)", match.group(1), flags=re.IGNORECASE)
            for number in refs:
                target = f"pr:{pr.repository}#{int(number)}"
                edges.append(GraphEdge(pr.ref, target, relation, evidence=match.group(0).strip()))
    return tuple(edges)


@dataclass
class GitHubMemoryIndex:
    capabilities: dict[str, CapabilityObservation] = field(default_factory=dict)
    prs: dict[str, PRMemory] = field(default_factory=dict)
    assets: dict[str, AssetObservation] = field(default_factory=dict)
    graph: CapabilityGraph = field(default_factory=CapabilityGraph)
    atlas_receipts: list[dict[str, Any]] = field(default_factory=list)

    def add_pr(self, pr: PRMemory) -> None:
        self.prs[pr.ref] = pr
        for edge in extract_explicit_relations(pr):
            self.graph.add(edge)
        for path in pr.files:
            if not path.endswith((".py", ".rs", ".go", ".ts", ".tsx", ".js", ".java", ".cpp", ".c", ".h", ".md", ".json", ".yml", ".yaml")):
                continue
            asset_id = f"asset:{pr.ref}:{path}"
            self.assets[asset_id] = AssetObservation(
                asset_id=asset_id,
                source_ref=pr.ref,
                source_kind="pr_changed_file",
                label=path,
                keywords=_tokens((path, pr.title, pr.body)),
                confidence=0.55,
                boundary="changed-file candidate != reusable semantic capability; inspect exact implementation before reuse",
            )

    def ingest_pull_requests(self, repository: str, payloads: Iterable[Mapping[str, Any]]) -> None:
        for item in payloads:
            files = item.get("files", ())
            if files and isinstance(next(iter(files), None), Mapping):
                files = [str(row.get("filename", "")) for row in files if row.get("filename")]
            self.add_pr(PRMemory.from_github(repository, item, files=files))

    def ingest_capability_registry(self, payload: Mapping[str, Any], source_ref: str) -> None:
        for cap in load_registry(dict(payload)):
            obs = CapabilityObservation(
                capability=cap,
                source_ref=source_ref,
                source_kind="explicit_registry",
                keywords=_tokens((cap.capability_id, *cap.domains, *cap.consumes, *cap.produces)),
                confidence=1.0,
            )
            self.capabilities[cap.capability_id] = obs
            self.graph.add(GraphEdge(source_ref, f"cap:{cap.capability_id}", "implements", evidence="explicit Capability OS registry"))

    def ingest_master_atlas(self, payload: Mapping[str, Any], source_ref: str = "omega-master-doc-atlas") -> None:
        receipt = {
            "source_ref": source_ref,
            "atlas_fingerprint": payload.get("atlas_fingerprint"),
            "repository_count": payload.get("repository_count"),
            "truth_boundary": payload.get("truth_boundary"),
        }
        self.atlas_receipts.append(receipt)
        for idx, item in enumerate(payload.get("shared_component_candidates", [])):
            name = str(item.get("normalized_name", f"candidate-{idx}"))
            asset_id = f"atlas:{source_ref}:{idx}:{name}"
            members = item.get("members", [])
            member_text = [str(member.get("repository", "")) for member in members if isinstance(member, Mapping)]
            self.assets[asset_id] = AssetObservation(
                asset_id=asset_id,
                source_ref=source_ref,
                source_kind="atlas_structural_candidate",
                label=name,
                keywords=_tokens((name, *member_text)),
                confidence=0.35,
                boundary="atlas structural/name candidate != semantic equivalence or automatic supersession",
            )

    def search_assets(self, request: CapabilityRequest, top_k: int = 12) -> list[dict[str, Any]]:
        rows = []
        query = request.keywords
        for asset in self.assets.values():
            score = round(_jaccard(query, asset.keywords) * asset.confidence, 6)
            if score <= 0:
                continue
            rows.append({
                "asset_id": asset.asset_id,
                "source_ref": asset.source_ref,
                "source_kind": asset.source_kind,
                "label": asset.label,
                "score": score,
                "boundary": asset.boundary,
            })
        rows.sort(key=lambda row: (-row["score"], row["asset_id"]))
        return rows[:top_k]

    def search_prs(self, request: CapabilityRequest, top_k: int = 12) -> list[dict[str, Any]]:
        rows = []
        for pr in self.prs.values():
            score = round(_jaccard(request.keywords, pr.keywords), 6)
            if score <= 0:
                continue
            rows.append({
                "ref": pr.ref,
                "number": pr.number,
                "title": pr.title,
                "lifecycle": pr.lifecycle,
                "epistemic_memory": pr.epistemic_memory,
                "head_sha": pr.head_sha,
                "score": score,
                "boundary": "PR similarity/lifecycle != correctness, semantic equivalence, or M+ evidence",
            })
        rows.sort(key=lambda row: (-row["score"], -row["number"]))
        return rows[:top_k]

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema": f"omega-github-memory-index/v{MEMORY_SCHEMA_VERSION}",
            "capabilities": [
                {
                    "capability": {
                        "id": obs.capability.capability_id,
                        "domains": list(obs.capability.domains),
                        "consumes": list(obs.capability.consumes),
                        "produces": list(obs.capability.produces),
                        "authority": obs.capability.authority,
                        "quality": obs.capability.quality,
                        "information_gain": obs.capability.information_gain,
                        "verifiability": obs.capability.verifiability,
                        "reuse": obs.capability.reuse,
                        "cost": obs.capability.cost,
                        "latency": obs.capability.latency,
                        "risk": obs.capability.risk,
                        "alternatives": list(obs.capability.alternatives),
                        "failure_modes": list(obs.capability.failure_modes),
                    },
                    "source_ref": obs.source_ref,
                    "source_kind": obs.source_kind,
                    "keywords": list(obs.keywords),
                    "confidence": obs.confidence,
                }
                for obs in sorted(self.capabilities.values(), key=lambda x: x.capability_id)
            ],
            "prs": [asdict(pr) for pr in sorted(self.prs.values(), key=lambda x: (x.repository, x.number))],
            "assets": [asdict(asset) for asset in sorted(self.assets.values(), key=lambda x: x.asset_id)],
            "edges": [asdict(edge) for edge in self.graph.edges],
            "atlas_receipts": list(self.atlas_receipts),
            "oak_boundaries": [
                "PR_MERGED != M_PLUS",
                "PR_SIMILARITY != SEMANTIC_EQUIVALENCE",
                "CHANGED_FILE != REUSABLE_CAPABILITY",
                "ATLAS_NAME_MATCH != SHARED_IMPLEMENTATION",
                "CANDIDATE_REUSE != VERIFIED_REUSE",
            ],
        }
        payload["fingerprint"] = _stable_digest(payload)
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GitHubMemoryIndex":
        index = cls()
        for row in payload.get("prs", []):
            mutable = dict(row)
            mutable["files"] = tuple(mutable.get("files", []))
            index.add_pr(PRMemory(**mutable))
        for row in payload.get("assets", []):
            mutable = dict(row)
            mutable["keywords"] = tuple(mutable.get("keywords", []))
            asset = AssetObservation(**mutable)
            index.assets[asset.asset_id] = asset
        for row in payload.get("capabilities", []):
            cap = Capability.from_dict(dict(row["capability"]))
            obs = CapabilityObservation(
                capability=cap,
                source_ref=str(row["source_ref"]),
                source_kind=str(row.get("source_kind", "explicit_registry")),
                keywords=tuple(map(str, row.get("keywords", []))),
                confidence=float(row.get("confidence", 1.0)),
            )
            index.capabilities[cap.capability_id] = obs
        index.graph = CapabilityGraph(GraphEdge(**dict(row)) for row in payload.get("edges", []))
        index.atlas_receipts = [dict(row) for row in payload.get("atlas_receipts", [])]
        return index


@dataclass(frozen=True)
class ReuseDecision:
    request_id: str
    action: str
    coverage: float
    residual_outputs: tuple[str, ...]
    selected_capabilities: tuple[str, ...]
    capability_candidates: tuple[dict[str, Any], ...]
    historical_candidates: tuple[dict[str, Any], ...]
    creation_allowed: bool
    oak_boundary: str

    def __post_init__(self) -> None:
        if self.action not in DECISIONS:
            raise ValueError(f"unsupported decision: {self.action}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReuseBeforeCreateGate:
    """Fail-closed reuse gate: formal capability coverage first, historical leads second, creation last."""

    def __init__(self, index: GitHubMemoryIndex, inspect_threshold: float = 0.12) -> None:
        self.index = index
        self.inspect_threshold = inspect_threshold

    def _rank_capabilities(self, request: CapabilityRequest) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        req_domains = set(request.domains)
        req_inputs = set(request.consumes)
        for obs in self.index.capabilities.values():
            cap = obs.capability
            output_cov = _coverage(request.produces, cap.produces)
            input_score = _jaccard(req_inputs, cap.consumes)
            domain_score = _jaccard(req_domains, cap.domains)
            lexical = _jaccard(request.keywords, obs.keywords)
            score = (
                0.45 * output_cov
                + 0.10 * input_score
                + 0.10 * domain_score
                + 0.15 * lexical
                + 0.10 * cap.reuse
                + 0.05 * cap.quality
                + 0.05 * cap.verifiability
                - 0.05 * cap.risk
                - 0.03 * cap.cost
            ) * obs.confidence
            rows.append({
                "capability_id": cap.capability_id,
                "source_ref": obs.source_ref,
                "score": round(max(0.0, score), 6),
                "output_coverage": round(output_cov, 6),
                "produces": list(cap.produces),
                "consumes": list(cap.consumes),
                "authority": cap.authority,
            })
        rows.sort(key=lambda row: (-row["score"], -row["output_coverage"], row["capability_id"]))
        return rows

    def decide(self, request: CapabilityRequest) -> ReuseDecision:
        ranked = self._rank_capabilities(request)
        historical = self.index.search_assets(request, top_k=12) + self.index.search_prs(request, top_k=12)
        historical.sort(key=lambda row: (-float(row.get("score", 0.0)), str(row.get("asset_id") or row.get("ref"))))
        historical = historical[:12]

        required = set(request.produces)
        selected: list[str] = []
        covered: set[str] = set()
        for row in ranked:
            newly = required & set(row["produces"]) - covered
            if not newly:
                continue
            selected.append(row["capability_id"])
            covered.update(newly)
            if covered >= required:
                break

        coverage = 1.0 if not required and ranked and ranked[0]["score"] >= 0.55 else (
            len(covered) / len(required) if required else 0.0
        )
        residual = tuple(sorted(required - covered))
        top = ranked[0] if ranked else None
        one_cap_full = bool(top and (not required or top["output_coverage"] >= 0.999) and top["score"] >= 0.55)

        if one_cap_full:
            action = "REUSE"
            selected = [top["capability_id"]]
        elif required and coverage >= 0.999 and len(selected) > 1:
            action = "COMPOSE"
        elif top and top["output_coverage"] >= 0.40 and top["score"] >= 0.30:
            action = "EXTEND"
            selected = [top["capability_id"]]
            covered = required & set(top["produces"])
            residual = tuple(sorted(required - covered))
            coverage = len(covered) / len(required) if required else 0.0
        elif historical and float(historical[0].get("score", 0.0)) >= self.inspect_threshold:
            action = "INSPECT"
            selected = []
            coverage = 0.0
            residual = tuple(sorted(required))
        else:
            action = "CREATE"
            selected = []
            coverage = 0.0
            residual = tuple(sorted(required))

        return ReuseDecision(
            request_id=request.request_id,
            action=action,
            coverage=round(coverage, 6),
            residual_outputs=residual,
            selected_capabilities=tuple(selected),
            capability_candidates=tuple(ranked[:12]),
            historical_candidates=tuple(historical),
            creation_allowed=action == "CREATE",
            oak_boundary=(
                "Gate output is an architecture/retrieval recommendation, not proof of semantic equivalence or correctness. "
                "INSPECT requires exact source inspection; REUSE/COMPOSE/EXTEND still require tests and OAK evidence."
            ),
        )

    def compile_context(self, request: CapabilityRequest, max_items: int = 8) -> dict[str, Any]:
        decision = self.decide(request)
        cap_rows = list(decision.capability_candidates[:max_items])
        historical = list(decision.historical_candidates[:max_items])
        source_refs = {row["source_ref"] for row in cap_rows if row.get("source_ref")}
        source_refs.update(str(row.get("source_ref") or row.get("ref")) for row in historical)
        relations = [
            asdict(edge) for edge in self.index.graph.edges
            if edge.source in source_refs or edge.target in source_refs
        ][: max_items * 2]
        packet = {
            "schema": "omega-github-llmt-context/v1",
            "request": asdict(request),
            "decision": decision.to_dict(),
            "relations": relations,
            "instructions": [
                "inspect exact candidate implementation before modifying or creating code",
                "prefer reuse/composition/extension over new modules when OAK evidence supports it",
                "generate only residual capability that existing verified components do not cover",
                "preserve provenance and supersession history",
                "never promote PR lifecycle, lexical similarity, atlas overlap, or consensus to semantic truth",
            ],
        }
        packet["fingerprint"] = _stable_digest(packet)
        return packet


class GitHubPRSource:
    """Read-only GitHub REST snapshotter. Transport injection keeps CI deterministic and network-free."""

    def __init__(
        self,
        token: str | None = None,
        api_base: str = "https://api.github.com",
        transport: Callable[[str], Any] | None = None,
    ) -> None:
        self.token = token
        self.api_base = api_base.rstrip("/")
        self.transport = transport or self._http_get

    def _http_get(self, url: str) -> Any:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub read failed HTTP {exc.code}: {body[:300]}") from exc

    def _pages(self, path: str, max_items: int | None = None) -> list[Mapping[str, Any]]:
        rows: list[Mapping[str, Any]] = []
        page = 1
        while True:
            separator = "&" if "?" in path else "?"
            url = f"{self.api_base}{path}{separator}{urlencode({'per_page': 100, 'page': page})}"
            payload = self.transport(url)
            if not isinstance(payload, list):
                raise TypeError(f"expected GitHub list response for {path}")
            rows.extend(item for item in payload if isinstance(item, Mapping))
            if max_items is not None and len(rows) >= max_items:
                return rows[:max_items]
            if len(payload) < 100:
                return rows
            page += 1

    def snapshot(self, repository: str, include_files: bool = True, max_prs: int | None = None) -> list[dict[str, Any]]:
        owner, name = repository.split("/", 1)
        pulls = self._pages(f"/repos/{owner}/{name}/pulls?state=all", max_items=max_prs)
        output: list[dict[str, Any]] = []
        for pr in pulls:
            row = dict(pr)
            if include_files:
                number = int(row["number"])
                files = self._pages(f"/repos/{owner}/{name}/pulls/{number}/files")
                row["files"] = [str(item.get("filename")) for item in files if item.get("filename")]
            output.append(row)
        return output


def build_live_index(
    repository: str,
    *,
    token: str | None = None,
    capability_registry: Mapping[str, Any] | None = None,
    include_files: bool = True,
    max_prs: int | None = None,
    source: GitHubPRSource | None = None,
) -> GitHubMemoryIndex:
    source = source or GitHubPRSource(token=token)
    index = GitHubMemoryIndex()
    index.ingest_pull_requests(repository, source.snapshot(repository, include_files=include_files, max_prs=max_prs))
    if capability_registry is not None:
        index.ingest_capability_registry(capability_registry, source_ref=f"registry:{repository}")
    return index
