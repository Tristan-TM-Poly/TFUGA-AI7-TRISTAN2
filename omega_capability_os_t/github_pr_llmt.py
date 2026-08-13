"""Read-only per-PR LLMT work packets over cumulative GitHub memory.

This module does not create a second GitHub memory substrate. It projects the
canonical GitHubMemoryIndex / Cumulative Intelligence state into one bounded
packet per currently open PR. Historical ancestry ranking reuses the frozen
retrieval policy; explicit later descendants remain a separate evidence axis.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
import argparse
import json

from .github_cumulative_intelligence import (
    HistoryArchaeologist,
    LineageSignal,
    PRGenome,
    PRGenomeCompiler,
)
from .github_memory import GitHubMemoryIndex, PRMemory, _stable_digest
from .github_retrieval_arena import _prefix_index, _rankings

PR_LLMT_SCHEMA_VERSION = "0.1.0"
RANKER_VERSION = "frozen-v0.1"
RANKING_STRATEGY = "hybrid_rrf"


@dataclass(frozen=True)
class PRCandidate:
    ref: str
    rank: int
    number: int
    lifecycle: str
    title: str
    head_sha: str | None
    base_ref: str | None
    failure_memory: tuple[str, ...]
    exact_inspection_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PRLineageEvidence:
    source_ref: str
    target_ref: str
    relation: str
    axis: str
    evidence: str
    confidence: float
    review_required: bool

    @classmethod
    def from_signal(cls, signal: LineageSignal) -> "PRLineageEvidence":
        return cls(
            source_ref=signal.source_ref,
            target_ref=signal.target_ref,
            relation=signal.relation,
            axis=signal.axis,
            evidence=signal.evidence,
            confidence=signal.confidence,
            review_required=signal.review_required,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _pr_number(ref: str) -> int:
    try:
        return int(ref.rsplit("#", 1)[1])
    except (IndexError, ValueError):
        return -1


def rank_prior_candidates(
    index: GitHubMemoryIndex,
    target: PRMemory,
    *,
    top_k: int = 8,
) -> tuple[str, ...]:
    """Rank strict historical candidates without using target body/base as query input."""
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    prefix = _prefix_index(index, target)
    if not prefix.prs:
        return ()
    rankings = _rankings(
        prefix,
        query_title=target.title,
        target_number=target.number,
    )
    return tuple(rankings[RANKING_STRATEGY][:top_k])


def _lineage_for_target(
    target: PRMemory,
    lineage: Iterable[LineageSignal],
) -> tuple[tuple[PRLineageEvidence, ...], tuple[PRLineageEvidence, ...]]:
    ancestors: list[PRLineageEvidence] = []
    descendants: list[PRLineageEvidence] = []
    for signal in lineage:
        if signal.source_ref == target.ref and _pr_number(signal.target_ref) < target.number:
            ancestors.append(PRLineageEvidence.from_signal(signal))
        elif signal.target_ref == target.ref and _pr_number(signal.source_ref) > target.number:
            descendants.append(PRLineageEvidence.from_signal(signal))
    ancestors.sort(key=lambda row: (row.target_ref, row.relation, row.axis))
    descendants.sort(key=lambda row: (row.source_ref, row.relation, row.axis))
    return tuple(ancestors), tuple(descendants)


def compile_pr_work_packet(
    index: GitHubMemoryIndex,
    target: PRMemory,
    *,
    lineage: Iterable[LineageSignal] | None = None,
    genomes: Mapping[str, PRGenome] | None = None,
    top_k: int = 8,
) -> dict[str, Any]:
    if target.lifecycle not in {"OPEN", "DRAFT"}:
        raise ValueError(f"PR work packet requires OPEN/DRAFT target, got {target.lifecycle}")

    lineage_rows = tuple(lineage) if lineage is not None else HistoryArchaeologist.lineage({target.repository: index})
    genome_map = dict(genomes) if genomes is not None else PRGenomeCompiler().compile_all({target.repository: index})
    target_genome = genome_map[target.ref]
    ranked_refs = rank_prior_candidates(index, target, top_k=top_k)

    candidates: list[PRCandidate] = []
    for rank, ref in enumerate(ranked_refs, start=1):
        pr = index.prs.get(ref)
        if pr is None:
            continue
        genome = genome_map.get(ref)
        candidates.append(
            PRCandidate(
                ref=ref,
                rank=rank,
                number=pr.number,
                lifecycle=pr.lifecycle,
                title=pr.title,
                head_sha=pr.head_sha,
                base_ref=pr.base_ref,
                failure_memory=genome.failure_memory if genome else (),
            )
        )

    ancestors, descendants = _lineage_for_target(target, lineage_rows)
    payload: dict[str, Any] = {
        "schema": f"omega-pr-llmt-work-packet/v{PR_LLMT_SCHEMA_VERSION}",
        "target": {
            "ref": target.ref,
            "repository": target.repository,
            "number": target.number,
            "lifecycle": target.lifecycle,
            "title": target.title,
            "head_sha": target.head_sha,
            "head_ref": target.head_ref,
            "base_ref": target.base_ref,
            "updated_at": target.updated_at,
            "changed_files_known": len(target.files),
            "named_concepts": list(target_genome.named_concepts),
            "failure_memory": list(target_genome.failure_memory),
        },
        "historical_retrieval": {
            "strategy": RANKING_STRATEGY,
            "ranker_version": RANKER_VERSION,
            "status": "PROBATIONARY_CROSS_REPO_RETROSPECTIVE_REPLICATION",
            "query_surface": "target_title_only",
            "strict_prior_prs_only": True,
            "candidates": [candidate.to_dict() for candidate in candidates],
            "boundary": (
                "Validated historical ranking is an inspection queue for prior PRs only. "
                "Rank does not prove semantic equivalence or implementation compatibility."
            ),
        },
        "declared_prior_lineage": [row.to_dict() for row in ancestors],
        "known_later_descendants": [row.to_dict() for row in descendants],
        "inspection_contract": {
            "progressive_zoom_required": True,
            "inspect_exact_head_sha": True,
            "inspect_changed_files": True,
            "inspect_static_symbols": True,
            "inspect_tests_and_ci": True,
            "consult_negative_memory": True,
            "reuse_before_create": True,
            "create_only_residual": True,
            "write_authority_granted": False,
            "merge_authority_granted": False,
        },
        "required_outputs_after_inspection": [
            "intent_summary",
            "reuse_plan",
            "problem_findings",
            "solution_candidates",
            "optimization_candidates",
            "tests_to_run",
            "oak_decision",
            "residual_change_plan",
        ],
        "oak_boundaries": [
            "RANKED_CANDIDATE != REUSABLE_IMPLEMENTATION",
            "DECLARED_LINEAGE != CAUSAL_DEPENDENCY_PROOF",
            "LATER_DESCENDANT != AUTOMATIC_SUPERSESSION",
            "AST_SYMBOL != BEHAVIORAL_EQUIVALENCE",
            "CI_GREEN != EXTERNAL_TRUTH",
            "PACKET_GENERATION != GITHUB_WRITE_AUTHORITY",
        ],
    }
    payload["fingerprint"] = _stable_digest(payload)
    return payload


def compile_pr_llmt_portfolio(
    index: GitHubMemoryIndex,
    *,
    top_k: int = 8,
) -> dict[str, Any]:
    """Compile one bounded packet for every currently OPEN/DRAFT PR in the index."""
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    repositories = sorted({pr.repository for pr in index.prs.values()})
    if len(repositories) > 1:
        raise ValueError("portfolio expects a repository-scoped GitHubMemoryIndex")
    repository = repositories[0] if repositories else ""
    lineage = HistoryArchaeologist.lineage({repository: index}) if repository else ()
    genomes = PRGenomeCompiler().compile_all({repository: index}) if repository else {}
    targets = sorted(
        (pr for pr in index.prs.values() if pr.lifecycle in {"OPEN", "DRAFT"}),
        key=lambda pr: pr.number,
        reverse=True,
    )

    packets = [
        compile_pr_work_packet(
            index,
            target,
            lineage=lineage,
            genomes=genomes,
            top_k=top_k,
        )
        for target in targets
    ]
    inspection_pairs = sum(
        len(packet["historical_retrieval"]["candidates"])
        + len(packet["known_later_descendants"])
        for packet in packets
    )
    unique_refs = sorted(
        {
            candidate["ref"]
            for packet in packets
            for candidate in packet["historical_retrieval"]["candidates"]
        }
        | {
            row["source_ref"]
            for packet in packets
            for row in packet["known_later_descendants"]
        }
    )

    payload: dict[str, Any] = {
        "schema": f"omega-pr-llmt-portfolio/v{PR_LLMT_SCHEMA_VERSION}",
        "repository": repository,
        "ranker_version": RANKER_VERSION,
        "ranking_strategy": RANKING_STRATEGY,
        "open_or_draft_pr_count": len(targets),
        "packet_count": len(packets),
        "top_k_per_target": top_k,
        "inspection_pair_count": inspection_pairs,
        "unique_candidate_ref_count": len(unique_refs),
        "unique_candidate_refs": unique_refs,
        "packets": packets,
        "governing_invariants": [
            "SEARCH_ALL_HISTORY_BEFORE_CREATE",
            "REUSE_BEFORE_CREATE",
            "COMPOSE_BEFORE_DUPLICATE",
            "EXTEND_BEFORE_FORK",
            "INSPECT_BEFORE_ASSUME",
            "CONSULT_M_MINUS",
            "CREATE_ONLY_THE_RESIDUAL",
            "TEST_THE_TRANSPLANT",
            "RECORD_THE_OUTCOME",
        ],
        "authority": {
            "read": True,
            "draft_analysis": True,
            "write_authority_granted": False,
            "merge_authority_granted": False,
        },
        "boundary": (
            "The portfolio packetizes all open PRs but does not claim they are ready, correct, "
            "mergeable, mutually compatible, or authorized for mutation. Exact inspection and current CI remain required."
        ),
    }
    payload["fingerprint"] = _stable_digest(payload)
    return payload


def _load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: str | None, payload: Mapping[str, Any]) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-pr-llmt")
    sub = parser.add_subparsers(dest="command", required=True)

    portfolio = sub.add_parser("portfolio")
    portfolio.add_argument("index")
    portfolio.add_argument("--top-k", type=int, default=8)
    portfolio.add_argument("--output")

    packet = sub.add_parser("packet")
    packet.add_argument("index")
    packet.add_argument("target_ref")
    packet.add_argument("--top-k", type=int, default=8)
    packet.add_argument("--output")

    args = parser.parse_args(argv)
    index = GitHubMemoryIndex.from_dict(_load(args.index))
    if args.command == "portfolio":
        payload = compile_pr_llmt_portfolio(index, top_k=args.top_k)
    else:
        target = index.prs.get(args.target_ref)
        if target is None:
            raise KeyError(f"unknown target PR ref: {args.target_ref}")
        payload = compile_pr_work_packet(index, target, top_k=args.top_k)
    _write(args.output, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
