from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping
import re

from .github_memory import (
    CapabilityRequest,
    GitHubMemoryIndex,
    PRMemory,
    ReuseBeforeCreateGate,
    _stable_digest,
    _tokens,
)
from .github_memory_evolution import (
    LLMTFederationCompiler,
    LLMTIdentity,
    ResidualCodeCompiler,
)

INTELLIGENCE_SCHEMA_VERSION = "1.2.0"

LENS_KINDS = {
    "global",
    "repository",
    "pr",
    "module",
    "theory",
    "system",
    "application",
    "creation",
}

_LINEAGE_PATTERNS = (
    ("reconstructs", re.compile(r"(?im)^\s*(?:reconstructs?|reconstructed[_ -]from)\s*:\s*(.+)$")),
    ("stacked_on", re.compile(r"(?im)^\s*(?:stacked[_ -]on|stacked on)\s*:\s*(.+)$")),
    ("converges", re.compile(r"(?im)^\s*(?:converges?|convergence[_ -]of)\s*:\s*(.+)$")),
    ("source_pr", re.compile(r"(?im)^\s*(?:source[_ -]pr|source pr)\s*:\s*(.+)$")),
)

_FAILURE_RE = re.compile(
    r"(?i)(?:\bM[-−]\b|\bfail(?:ed|ure|ing)?\b|\berror\b|\bblocked\b|"
    r"\bcancel(?:led|ed)\b|\bregression\b|\bbroken\b|\bdebt\b|\bbehind\b)"
)
_CONCEPT_RE = re.compile(r"(?:Ω|OMEGA)[-A-Za-z0-9_∞²³]+")


def _dedupe(items: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(item) for item in items if str(item)))


def _qualified_pr_refs(text: str, default_repository: str) -> tuple[str, ...]:
    refs: list[str] = []
    occupied: set[str] = set()
    for match in re.finditer(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(\d+)", text):
        refs.append(f"pr:{match.group(1)}#{int(match.group(2))}")
        occupied.add(match.group(0))
    scrubbed = text
    for token in occupied:
        scrubbed = scrubbed.replace(token, "")
    for number in re.findall(r"(?:PR[- ]?|#)(\d+)", scrubbed, flags=re.IGNORECASE):
        refs.append(f"pr:{default_repository}#{int(number)}")
    return _dedupe(refs)


@dataclass(frozen=True)
class HistoryCoverageReceipt:
    repository_count: int
    pr_count: int
    open_count: int
    draft_count: int
    merged_count: int
    closed_not_merged_count: int
    exact_state_partition: bool
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema"] = f"omega-github-history-coverage/v{INTELLIGENCE_SCHEMA_VERSION}"
        payload["fingerprint"] = _stable_digest(payload)
        return payload


@dataclass(frozen=True)
class LineageSignal:
    source_ref: str
    target_ref: str
    relation: str
    axis: str
    evidence: str
    confidence: float
    review_required: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PRGenome:
    ref: str
    repository: str
    number: int
    lifecycle: str
    epistemic_memory: str
    head_sha: str | None
    named_concepts: tuple[str, ...]
    intent_tokens: tuple[str, ...]
    changed_files: tuple[str, ...]
    asset_ids: tuple[str, ...]
    symbol_assets: tuple[str, ...]
    failure_memory: tuple[str, ...]
    lineage_refs: tuple[str, ...]
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema"] = f"omega-pr-genome/v{INTELLIGENCE_SCHEMA_VERSION}"
        payload["fingerprint"] = _stable_digest(payload)
        return payload


class HistoryArchaeologist:
    """Read-only archaeological view over all indexed PR lifecycle states."""

    @staticmethod
    def coverage(indexes: Mapping[str, GitHubMemoryIndex]) -> HistoryCoverageReceipt:
        prs = [pr for index in indexes.values() for pr in index.prs.values()]
        open_count = sum(pr.lifecycle == "OPEN" for pr in prs)
        draft_count = sum(pr.lifecycle == "DRAFT" for pr in prs)
        merged_count = sum(pr.lifecycle == "MERGED" for pr in prs)
        closed_count = sum(pr.lifecycle == "CLOSED" for pr in prs)
        exact = len(prs) == open_count + draft_count + merged_count + closed_count
        return HistoryCoverageReceipt(
            repository_count=len(indexes),
            pr_count=len(prs),
            open_count=open_count,
            draft_count=draft_count,
            merged_count=merged_count,
            closed_not_merged_count=closed_count,
            exact_state_partition=exact,
            boundary=(
                "GitHub lifecycle partitions history; lifecycle is not evidence quality. "
                "MERGED != M+, CLOSED != M-, and NOT_MERGED != useless."
            ),
        )

    @staticmethod
    def lineage(indexes: Mapping[str, GitHubMemoryIndex]) -> tuple[LineageSignal, ...]:
        signals: list[LineageSignal] = []
        seen: set[tuple[str, str, str, str]] = set()

        for repository, index in sorted(indexes.items()):
            for edge in index.graph.edges:
                key = (edge.source, edge.target, edge.relation, "declared")
                if key in seen:
                    continue
                seen.add(key)
                signals.append(
                    LineageSignal(
                        source_ref=edge.source,
                        target_ref=edge.target,
                        relation=edge.relation,
                        axis="declared",
                        evidence=edge.evidence,
                        confidence=edge.confidence,
                        review_required=False,
                    )
                )

            for pr in sorted(index.prs.values(), key=lambda item: item.number):
                for relation, pattern in _LINEAGE_PATTERNS:
                    for match in pattern.finditer(pr.body):
                        for target in _qualified_pr_refs(match.group(1), repository):
                            key = (pr.ref, target, relation, "historical")
                            if key in seen:
                                continue
                            seen.add(key)
                            signals.append(
                                LineageSignal(
                                    source_ref=pr.ref,
                                    target_ref=target,
                                    relation=relation,
                                    axis="historical",
                                    evidence=match.group(0).strip(),
                                    confidence=1.0,
                                    review_required=False,
                                )
                            )

        signals.sort(key=lambda row: (row.source_ref, row.target_ref, row.relation, row.axis))
        return tuple(signals)


class PRGenomeCompiler:
    """Compiles PR-level reusable memory from the canonical GitHubMemoryIndex."""

    @staticmethod
    def compile(index: GitHubMemoryIndex, pr: PRMemory, lineage: Iterable[LineageSignal] = ()) -> PRGenome:
        assets = sorted(
            (asset for asset in index.assets.values() if asset.source_ref == pr.ref),
            key=lambda asset: asset.asset_id,
        )
        symbols = tuple(
            asset.asset_id
            for asset in assets
            if "symbol" in asset.source_kind.lower() or asset.asset_id.startswith("symbol:")
        )
        failure_memory = tuple(
            line.strip()
            for line in pr.body.splitlines()
            if line.strip() and _FAILURE_RE.search(line)
        )
        concepts = tuple(sorted(set(_CONCEPT_RE.findall(f"{pr.title}\n{pr.body}"))))
        neighbors: list[str] = []
        for signal in lineage:
            if signal.source_ref == pr.ref:
                neighbors.append(signal.target_ref)
            elif signal.target_ref == pr.ref:
                neighbors.append(signal.source_ref)
        return PRGenome(
            ref=pr.ref,
            repository=pr.repository,
            number=pr.number,
            lifecycle=pr.lifecycle,
            epistemic_memory=pr.epistemic_memory,
            head_sha=pr.head_sha,
            named_concepts=concepts,
            intent_tokens=pr.keywords,
            changed_files=pr.files,
            asset_ids=tuple(asset.asset_id for asset in assets),
            symbol_assets=symbols,
            failure_memory=_dedupe(failure_memory),
            lineage_refs=_dedupe(neighbors),
            boundary=(
                "PRGenome is an indexed reuse lead. Names, files, symbols, lifecycle and lineage "
                "do not prove semantic equivalence, correctness, novelty, or fitness."
            ),
        )

    def compile_all(self, indexes: Mapping[str, GitHubMemoryIndex]) -> dict[str, PRGenome]:
        lineage = HistoryArchaeologist.lineage(indexes)
        genomes: dict[str, PRGenome] = {}
        for index in indexes.values():
            for pr in index.prs.values():
                genomes[pr.ref] = self.compile(index, pr, lineage)
        return genomes


@dataclass(frozen=True)
class ReuseCoalition:
    request_id: str
    selected_capabilities: tuple[str, ...]
    source_refs: tuple[str, ...]
    inspected_pr_candidates: tuple[str, ...]
    requested_outputs: tuple[str, ...]
    contract_covered_outputs: tuple[str, ...]
    residual_outputs: tuple[str, ...]
    reuse_coverage_ratio: float
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema"] = f"omega-minimal-reuse-coalition/v{INTELLIGENCE_SCHEMA_VERSION}"
        payload["fingerprint"] = _stable_digest(payload)
        return payload


class MinimalReuseCoalitionCompiler:
    """Greedy contract-level coalition. Historical similarity remains inspection-only evidence."""

    @staticmethod
    def _utility(obs: Any) -> float:
        cap = obs.capability
        return (
            float(cap.quality)
            + float(cap.verifiability)
            + float(cap.reuse)
            + float(cap.information_gain)
            - float(cap.risk)
            - float(cap.cost)
        )

    def compile(
        self,
        indexes: Mapping[str, GitHubMemoryIndex],
        request: CapabilityRequest,
        *,
        max_pr_candidates: int = 12,
    ) -> ReuseCoalition:
        residual = set(request.produces)
        selected: list[tuple[str, Any]] = []

        candidates: list[tuple[float, str, Any]] = []
        for repository, index in indexes.items():
            for capability_id, obs in index.capabilities.items():
                gain = len(residual & set(obs.capability.produces)) if residual else 0
                if residual and gain == 0:
                    continue
                candidates.append((self._utility(obs), repository, obs))
        candidates.sort(key=lambda row: (-row[0], row[1], row[2].capability_id))

        if residual:
            while residual:
                best = None
                best_gain: set[str] = set()
                for score, repository, obs in candidates:
                    if any(existing[1] is obs for existing in selected):
                        continue
                    gain = residual & set(obs.capability.produces)
                    if not gain:
                        continue
                    candidate = (len(gain), score, repository, obs.capability_id)
                    if best is None or candidate > best[0]:
                        best = (candidate, repository, obs)
                        best_gain = gain
                if best is None:
                    break
                _, repository, obs = best
                selected.append((repository, obs))
                residual -= best_gain

        pr_rows: list[dict[str, Any]] = []
        for repository, index in indexes.items():
            for row in index.search_prs(request, top_k=max_pr_candidates):
                record = dict(row)
                record["repository"] = repository
                pr_rows.append(record)
        pr_rows.sort(key=lambda row: (-float(row.get("score", 0.0)), row["repository"], -int(row.get("number", 0))))

        selected_capabilities = tuple(
            f"{repository}:{obs.capability_id}" for repository, obs in selected
        )
        sources = _dedupe(obs.source_ref for _, obs in selected)
        covered = tuple(sorted(set(request.produces) - residual))
        requested = tuple(request.produces)
        coverage = (len(covered) / len(requested)) if requested else 0.0

        return ReuseCoalition(
            request_id=request.request_id,
            selected_capabilities=selected_capabilities,
            source_refs=sources,
            inspected_pr_candidates=_dedupe(str(row["ref"]) for row in pr_rows[:max_pr_candidates]),
            requested_outputs=requested,
            contract_covered_outputs=covered,
            residual_outputs=tuple(sorted(residual)),
            reuse_coverage_ratio=round(coverage, 6),
            boundary=(
                "Coalition coverage is explicit Capability contract output coverage only. "
                "Historical PR ranking is an inspection queue, not semantic equivalence. "
                "Exact implementation/tests must be inspected before transplant or reuse."
            ),
        )


@dataclass(frozen=True)
class MemoryLens:
    lens_id: str
    kind: str
    selector: str

    def __post_init__(self) -> None:
        if self.kind not in LENS_KINDS:
            raise ValueError(f"unsupported lens kind: {self.kind}")


class MemoryLensCompiler:
    """Many LLMT views, one canonical memory substrate."""

    def compile(
        self,
        indexes: Mapping[str, GitHubMemoryIndex],
        request: CapabilityRequest,
        lenses: Iterable[MemoryLens],
        *,
        max_items: int = 6,
    ) -> dict[str, Any]:
        packets: list[dict[str, Any]] = []
        all_candidates: list[dict[str, Any]] = []

        for repository, index in sorted(indexes.items()):
            context = ReuseBeforeCreateGate(index).compile_context(request, max_items=max_items)
            for row in context["decision"]["historical_candidates"]:
                item = dict(row)
                item["repository"] = repository
                all_candidates.append(item)

        all_candidates.sort(
            key=lambda row: (
                -float(row.get("score", 0.0)),
                str(row.get("repository", "")),
                str(row.get("source_ref") or row.get("ref") or ""),
            )
        )

        for lens in lenses:
            selector_tokens = set(_tokens(lens.selector))
            selected = []
            for row in all_candidates:
                haystack = _tokens(
                    (
                        str(row.get("repository", "")),
                        str(row.get("label", "")),
                        str(row.get("title", "")),
                        str(row.get("source_ref", "")),
                        str(row.get("ref", "")),
                    )
                )
                if lens.kind == "global" or not selector_tokens or selector_tokens & set(haystack):
                    selected.append(row)
                if len(selected) >= max_items:
                    break
            if not selected:
                selected = all_candidates[:max_items]
            packets.append(
                {
                    "lens_id": lens.lens_id,
                    "kind": lens.kind,
                    "selector": lens.selector,
                    "authority": "read|draft",
                    "historical_candidates": selected,
                    "boundary": (
                        "LLMT lens is a bounded view over one canonical memory substrate; "
                        "lens/model multiplicity is not independent evidence."
                    ),
                }
            )

        payload = {
            "schema": f"omega-github-memory-lenses/v{INTELLIGENCE_SCHEMA_VERSION}",
            "packets": packets,
            "packet_count": len(packets),
            "canonical_memory": "external GitHubMemoryIndex set",
            "authority_ceiling": "draft",
        }
        payload["fingerprint"] = _stable_digest(payload)
        return payload


class CumulativeIntelligenceCompiler:
    """R0.8→R1.2: history atlas + genomes + reuse coalition + LLMT context capsule."""

    def compile(
        self,
        indexes: Mapping[str, GitHubMemoryIndex],
        request: CapabilityRequest,
        *,
        max_items: int = 8,
    ) -> dict[str, Any]:
        if not indexes:
            raise ValueError("at least one repository memory index is required")

        coverage = HistoryArchaeologist.coverage(indexes)
        lineage = HistoryArchaeologist.lineage(indexes)
        genomes = PRGenomeCompiler().compile_all(indexes)
        coalition = MinimalReuseCoalitionCompiler().compile(
            indexes, request, max_pr_candidates=max_items * 2
        )

        relevant_refs = coalition.inspected_pr_candidates[: max_items * 2]
        relevant_genomes = [
            genomes[ref].to_dict() for ref in relevant_refs if ref in genomes
        ]
        negative_hits = [
            {
                "ref": genome["ref"],
                "failure_memory": genome["failure_memory"],
            }
            for genome in relevant_genomes
            if genome["failure_memory"]
        ]

        residual_by_repo: list[dict[str, Any]] = []
        federation_by_repo: list[dict[str, Any]] = []
        for repository, index in sorted(indexes.items()):
            residual = ResidualCodeCompiler(index).compile(request).to_dict()
            residual_by_repo.append({"repository": repository, "residual": residual})
            identities = (
                LLMTIdentity(f"{repository}:global", "global", "*", "draft", None),
            )
            federation = LLMTFederationCompiler(index).compile(
                request, identities, max_items=max_items
            )
            federation_by_repo.append({"repository": repository, "federation": federation})

        lenses = (
            MemoryLens("global", "global", "*"),
            MemoryLens("repo", "repository", " ".join(sorted(indexes))),
            MemoryLens("theory", "theory", request.description),
            MemoryLens("system", "system", request.description),
            MemoryLens("application", "application", request.description),
            MemoryLens("creation", "creation", request.description),
        )
        lens_packets = MemoryLensCompiler().compile(
            indexes, request, lenses, max_items=max_items
        )

        lineage_rows = [
            signal.to_dict()
            for signal in lineage
            if signal.source_ref in relevant_refs or signal.target_ref in relevant_refs
        ][: max_items * 4]

        payload: dict[str, Any] = {
            "schema": f"omega-github-cumulative-intelligence/v{INTELLIGENCE_SCHEMA_VERSION}",
            "request": {
                "request_id": request.request_id,
                "description": request.description,
                "domains": list(request.domains),
                "consumes": list(request.consumes),
                "produces": list(request.produces),
            },
            "history_coverage": coverage.to_dict(),
            "minimal_reuse_coalition": coalition.to_dict(),
            "relevant_pr_genomes": relevant_genomes,
            "lineage_neighborhood": lineage_rows,
            "negative_memory_hits": negative_hits,
            "repository_residual_courts": residual_by_repo,
            "llmt_federation": federation_by_repo,
            "memory_lenses": lens_packets,
            "generation_constitution": {
                "search_all_history_before_create": True,
                "reuse_before_create": True,
                "compose_before_duplicate": True,
                "extend_before_fork": True,
                "inspect_before_assume": True,
                "preserve_provenance": True,
                "consult_negative_memory": True,
                "create_only_residual": True,
                "test_transplant": True,
                "record_outcome": True,
                "feed_result_back_to_memory": True,
                "write_authority_granted": False,
            },
            "oak_boundaries": [
                "MERGED != M+",
                "CLOSED != M-",
                "NOT_MERGED != useless",
                "PR similarity != semantic equivalence",
                "AST symbol existence != reusable behavior",
                "lineage signal != causal proof",
                "contract coverage != implementation compatibility",
                "LLMT packet count != independent evidence",
                "generation allowed != GitHub write authority",
                "historical utility != current validity",
            ],
        }
        payload["fingerprint"] = _stable_digest(payload)
        return payload
