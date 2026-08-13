"""Leakage-controlled historical PR retrieval arena.

The arena compares bounded retrieval strategies on the same historical targets.
Target bodies and stack base refs are used only after ranking to derive explicit
or structural lineage gold labels. Retrievers receive the target title and a
strict lower-numbered PR prefix only.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping
import argparse
import json
from pathlib import Path

from .github_cumulative_intelligence import HistoryArchaeologist, PRGenomeCompiler
from .github_memory import (
    CapabilityRequest,
    GitHubMemoryIndex,
    PRMemory,
    _jaccard,
    _stable_digest,
    _tokens,
    extract_explicit_relations,
)
from .github_memory_replay import ANCESTOR_RELATIONS

ARENA_SCHEMA_VERSION = "0.2.0"
STRATEGIES = (
    "lexical_jaccard",
    "recency",
    "graph_centrality",
    "hybrid_rrf",
)
DEFAULT_BRANCH_NAMES = {"main", "master", "develop", "development", "trunk"}


def _declared_gold_refs(target: PRMemory) -> tuple[str, ...]:
    refs: set[str] = set()
    for edge in extract_explicit_relations(target):
        if edge.relation not in ANCESTOR_RELATIONS:
            continue
        try:
            number = int(edge.target.rsplit("#", 1)[1])
        except (IndexError, ValueError):
            continue
        if number < target.number:
            refs.add(edge.target)
    return tuple(sorted(refs))


def _structural_stack_refs(
    index: GitHubMemoryIndex,
    target: PRMemory,
) -> tuple[tuple[str, ...], bool]:
    """Return a unique non-default branch parent, if current PR metadata exposes one.

    The structural label is deliberately conservative: default-like base branches
    are excluded, only lower-numbered PRs in the same repository are eligible,
    and ambiguous reused head refs are rejected instead of guessed.
    """
    base_ref = (target.base_ref or "").strip()
    if not base_ref or base_ref.lower() in DEFAULT_BRANCH_NAMES:
        return (), False
    matches = sorted(
        {
            pr.ref
            for pr in index.prs.values()
            if pr.repository == target.repository
            and pr.number < target.number
            and (pr.head_ref or "").strip() == base_ref
        }
    )
    if len(matches) == 1:
        return (matches[0],), False
    return (), len(matches) > 1


def _gold_ancestor_refs(
    index: GitHubMemoryIndex,
    target: PRMemory,
) -> tuple[tuple[str, ...], dict[str, list[str]], bool]:
    declared = _declared_gold_refs(target)
    structural, ambiguous = _structural_stack_refs(index, target)
    sources: dict[str, list[str]] = {}
    for ref in declared:
        sources.setdefault(ref, []).append("declared_body_lineage")
    for ref in structural:
        sources.setdefault(ref, []).append("stack_base_ref")
    refs = tuple(sorted(sources))
    return refs, sources, ambiguous


def _prefix_index(index: GitHubMemoryIndex, target: PRMemory) -> GitHubMemoryIndex:
    prefix = GitHubMemoryIndex()
    for pr in index.prs.values():
        if pr.repository == target.repository and pr.number < target.number:
            prefix.add_pr(pr)
    return prefix


def _rank_from_scores(
    prefix: GitHubMemoryIndex,
    scores: Mapping[str, float],
) -> list[str]:
    return [
        pr.ref
        for pr in sorted(
            prefix.prs.values(),
            key=lambda pr: (-float(scores.get(pr.ref, 0.0)), -pr.number, pr.ref),
        )
    ]


def _rankings(
    prefix: GitHubMemoryIndex,
    *,
    query_title: str,
    target_number: int,
) -> dict[str, list[str]]:
    if not prefix.prs:
        return {strategy: [] for strategy in STRATEGIES}

    request = CapabilityRequest(
        request_id=f"retrieval-arena:{target_number}",
        description=query_title,
        domains=("github", "software"),
        consumes=(),
        produces=(),
    )
    lexical_rows = prefix.search_prs(request, top_k=max(1, len(prefix.prs)))
    lexical = [str(row["ref"]) for row in lexical_rows]

    repository = next(iter(prefix.prs.values())).repository
    lineage = HistoryArchaeologist.lineage({repository: prefix})
    genomes = PRGenomeCompiler().compile_all({repository: prefix})

    centrality: dict[str, int] = {ref: 0 for ref in prefix.prs}
    for signal in lineage:
        if signal.source_ref in centrality:
            centrality[signal.source_ref] += 1
        if signal.target_ref in centrality:
            centrality[signal.target_ref] += 1
    max_centrality = max(centrality.values(), default=0)

    query_tokens = _tokens(query_title)
    genome_scores: dict[str, float] = {}
    recency_scores: dict[str, float] = {}
    centrality_scores: dict[str, float] = {}
    denominator = max(1, target_number - 1)

    for ref, pr in prefix.prs.items():
        genome = genomes[ref]
        intent_overlap = _jaccard(query_tokens, genome.intent_tokens)
        file_overlap = _jaccard(query_tokens, _tokens(genome.changed_files))
        lineage_density = min(1.0, len(genome.lineage_refs) / 5.0)
        recency = min(1.0, pr.number / denominator)
        hub = (centrality[ref] / max_centrality) if max_centrality else 0.0
        # Frozen v0.1 scoring weights. v0.2 changes evaluation labels/cohorts only.
        genome_scores[ref] = (
            0.50 * intent_overlap
            + 0.15 * file_overlap
            + 0.10 * lineage_density
            + 0.15 * recency
            + 0.10 * hub
        )
        recency_scores[ref] = recency
        centrality_scores[ref] = hub

    recency = _rank_from_scores(prefix, recency_scores)
    graph_centrality = _rank_from_scores(prefix, centrality_scores)
    genome_ranking = _rank_from_scores(prefix, genome_scores)

    lexical_complete = lexical + [ref for ref in recency if ref not in lexical]
    component_rankings = (lexical_complete, genome_ranking, recency, graph_centrality)
    rrf_scores: dict[str, float] = {ref: 0.0 for ref in prefix.prs}
    for ranking in component_rankings:
        for rank, ref in enumerate(ranking, start=1):
            rrf_scores[ref] += 1.0 / (20.0 + rank)
    hybrid_rrf = _rank_from_scores(prefix, rrf_scores)

    return {
        "lexical_jaccard": lexical,
        "recency": recency,
        "graph_centrality": graph_centrality,
        "hybrid_rrf": hybrid_rrf,
    }


def _reciprocal_rank(retrieved: Iterable[str], gold: set[str]) -> float:
    for rank, ref in enumerate(retrieved, start=1):
        if ref in gold:
            return 1.0 / rank
    return 0.0


def _aggregate_metrics(cases: list[dict[str, Any]]) -> dict[str, Any]:
    total_gold = sum(len(case["gold_lineage_refs"]) for case in cases)
    metrics: dict[str, Any] = {}
    for strategy in STRATEGIES:
        total_hits = sum(len(case["strategies"][strategy]["hits"]) for case in cases)
        macro = (
            sum(case["strategies"][strategy]["recall_at_k"] for case in cases) / len(cases)
            if cases else 0.0
        )
        mrr = (
            sum(case["strategies"][strategy]["reciprocal_rank"] for case in cases) / len(cases)
            if cases else 0.0
        )
        candidate_fraction = (
            sum(case["strategies"][strategy]["candidate_fraction"] for case in cases) / len(cases)
            if cases else 0.0
        )
        metrics[strategy] = {
            "hit_count": total_hits,
            "micro_recall_at_k": round(total_hits / total_gold, 6) if total_gold else 0.0,
            "macro_recall_at_k": round(macro, 6),
            "mrr": round(mrr, 6),
            "mean_candidate_fraction": round(candidate_fraction, 6),
            "target_leakage_count": sum(
                bool(case["strategies"][strategy]["target_leaked"]) for case in cases
            ),
            "future_leakage_count": sum(
                len(case["strategies"][strategy]["future_leakage_refs"]) for case in cases
            ),
        }
    return {
        "eligible_target_count": len(cases),
        "gold_lineage_ref_count": total_gold,
        "strategies": metrics,
    }


def _winner(metrics: Mapping[str, Mapping[str, Any]]) -> str:
    return sorted(
        STRATEGIES,
        key=lambda name: (
            -float(metrics[name]["micro_recall_at_k"]),
            -float(metrics[name]["mrr"]),
            float(metrics[name]["mean_candidate_fraction"]),
            name,
        ),
    )[0]


def compile_retrieval_arena(
    index: GitHubMemoryIndex,
    *,
    top_k: int = 8,
    max_targets: int | None = None,
) -> dict[str, Any]:
    """Evaluate frozen retrieval policies under one temporal/contamination contract."""
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    targets = sorted(index.prs.values(), key=lambda pr: (pr.repository, pr.number))
    cases: list[dict[str, Any]] = []
    skipped_no_lineage = 0
    ambiguous_stack_gold_count = 0

    for target in targets:
        gold, gold_sources, ambiguous = _gold_ancestor_refs(index, target)
        ambiguous_stack_gold_count += int(ambiguous)
        if not gold:
            skipped_no_lineage += 1
            continue
        prefix = _prefix_index(index, target)
        if not prefix.prs:
            continue

        strategy_rankings = _rankings(
            prefix,
            query_title=target.title,
            target_number=target.number,
        )
        rows: dict[str, Any] = {}
        gold_set = set(gold)
        for strategy in STRATEGIES:
            retrieved = list(strategy_rankings[strategy][:top_k])
            retrieved_set = set(retrieved)
            hits = [ref for ref in gold if ref in retrieved_set]
            future = [
                ref for ref in retrieved
                if int(ref.rsplit("#", 1)[1]) >= target.number
            ]
            rows[strategy] = {
                "retrieved_refs": retrieved,
                "hits": hits,
                "recall_at_k": round(len(hits) / len(gold), 6),
                "reciprocal_rank": round(_reciprocal_rank(retrieved, gold_set), 6),
                "candidate_fraction": round(
                    min(1.0, len(retrieved) / len(prefix.prs)), 6
                ) if prefix.prs else 0.0,
                "target_leaked": target.ref in retrieved,
                "future_leakage_refs": future,
            }

        cases.append(
            {
                "target_ref": target.ref,
                "target_number": target.number,
                "query_mode": "title_only",
                "prior_pr_count": len(prefix.prs),
                "gold_lineage_refs": list(gold),
                "gold_sources": gold_sources,
                "strategies": rows,
            }
        )
        if max_targets is not None and len(cases) >= max_targets:
            break

    aggregate = _aggregate_metrics(cases)
    metrics = aggregate["strategies"]
    winner = _winner(metrics)
    baseline = metrics["lexical_jaccard"]
    best = metrics[winner]
    leakage_free = all(
        row["target_leakage_count"] == 0 and row["future_leakage_count"] == 0
        for row in metrics.values()
    )
    non_regressive = best["micro_recall_at_k"] >= baseline["micro_recall_at_k"]

    source_counts = {"declared_body_lineage": 0, "stack_base_ref": 0}
    for case in cases:
        for sources in case["gold_sources"].values():
            for source in sources:
                source_counts[source] = source_counts.get(source, 0) + 1

    cut = max(1, int(len(cases) * 0.60)) if cases else 0
    early_cases = cases[:cut]
    late_cases = cases[cut:]
    early = _aggregate_metrics(early_cases)
    late = _aggregate_metrics(late_cases)

    payload: dict[str, Any] = {
        "schema": f"omega-pr-retrieval-arena/v{ARENA_SCHEMA_VERSION}",
        "ranker_version": "frozen-v0.1",
        "top_k": top_k,
        "eligible_target_count": aggregate["eligible_target_count"],
        "skipped_no_lineage_count": skipped_no_lineage,
        "gold_lineage_ref_count": aggregate["gold_lineage_ref_count"],
        "gold_source_counts": source_counts,
        "ambiguous_stack_gold_count": ambiguous_stack_gold_count,
        "strategies": metrics,
        "winner": winner,
        "improved_over_baseline": (
            best["micro_recall_at_k"] > baseline["micro_recall_at_k"]
            or (
                best["micro_recall_at_k"] == baseline["micro_recall_at_k"]
                and best["mrr"] > baseline["mrr"]
            )
        ),
        "temporal_evaluation": {
            "method": "ordered 60/40 retrospective split; frozen ranker, no cohort-specific reweighting",
            "early": early,
            "late_holdout_proxy": late,
            "boundary": (
                "The late cohort is a retrospective holdout proxy, not a pristine prospective test. "
                "No ranking weights are fit or changed inside this court."
            ),
        },
        "cases": cases,
        "contamination": {
            "query_uses_target_title_only": True,
            "target_body_used_as_gold_only": True,
            "target_base_ref_used_as_gold_only": True,
            "target_pr_hidden_from_retrieval": True,
            "future_prs_hidden_from_retrieval": True,
            "rankers_use_prior_pr_metadata_only": True,
            "default_branch_stack_labels_excluded": True,
            "ambiguous_stack_labels_rejected": True,
            "pretraining_exposure": "unknown",
            "historical_metadata_fidelity": "current_snapshot_proxy",
        },
        "oak": {
            "status": "PASS" if leakage_free and non_regressive else "FAIL",
            "temporal_leakage_free": leakage_free,
            "best_not_worse_than_baseline": non_regressive,
            "ranker_frozen_during_v0_2_evaluation": True,
            "boundaries": [
                "ARENA_WINNER != GENERALIZATION",
                "RETROSPECTIVE_HOLDOUT != PROSPECTIVE_VALIDATION",
                "SAME_REPOSITORY_HISTORY != EXTERNAL_REPLICATION",
                "LINEAGE_RECALL != ALL_USEFUL_REUSE",
                "STACK_BASE_REF != SEMANTIC_DEPENDENCY_PROOF",
                "RECENCY_OR_CENTRALITY != CAUSAL_RELEVANCE",
                "PR_GENOME_SIMILARITY != IMPLEMENTATION_COMPATIBILITY",
                "CI_PASS != ENGINEERING_SAVINGS",
            ],
        },
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
    parser = argparse.ArgumentParser(prog="omega-pr-retrieval-arena")
    sub = parser.add_subparsers(dest="command", required=True)
    court = sub.add_parser("court")
    court.add_argument("index")
    court.add_argument("--top-k", type=int, default=8)
    court.add_argument("--max-targets", type=int)
    court.add_argument("--output")
    args = parser.parse_args(argv)

    index = GitHubMemoryIndex.from_dict(_load(args.index))
    payload = compile_retrieval_arena(
        index,
        top_k=args.top_k,
        max_targets=args.max_targets,
    )
    _write(args.output, payload)
    return 0 if payload["oak"]["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
