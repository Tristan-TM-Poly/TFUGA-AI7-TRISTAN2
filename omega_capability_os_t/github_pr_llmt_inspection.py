"""Fanout-first exact inspection overlays for the per-PR LLMT portfolio.

The module consumes the canonical PR-LLMT portfolio and reuses #447 progressive
GitHub hydration. It deduplicates candidate PRs across all open target PRs,
prioritizes candidates that can inform the most packets, and emits read-only
inspection evidence. Operational budgets are explicit parameters, never hard
architecture ceilings.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping
import argparse
import json
import os

from .github_memory import GitHubMemoryIndex, GitHubPRSource, _stable_digest
from .github_memory_zoom import ProgressiveGitHubRetriever

INSPECTION_SCHEMA_VERSION = "0.1.0"


def _pr_number(ref: str) -> int:
    try:
        return int(ref.rsplit("#", 1)[1])
    except (IndexError, ValueError):
        return -1


@dataclass(frozen=True)
class InspectionCandidate:
    ref: str
    fanout: int
    affected_targets: tuple[str, ...]
    evidence_axes: tuple[str, ...]
    best_historical_rank: int | None
    historical_rank_mass: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compile_inspection_plan(
    portfolio: Mapping[str, Any],
    *,
    max_candidates: int | None = None,
) -> dict[str, Any]:
    """Deduplicate candidate PRs and prioritize high-fanout exact inspection."""
    if max_candidates is not None and max_candidates < 0:
        raise ValueError("max_candidates must be non-negative or omitted")
    if portfolio.get("schema") != "omega-pr-llmt-portfolio/v0.1.0":
        raise ValueError(f"unsupported portfolio schema: {portfolio.get('schema')}")

    target_sets: dict[str, set[str]] = {}
    axes: dict[str, set[str]] = {}
    ranks: dict[str, list[int]] = {}

    for packet in portfolio.get("packets", []):
        target_ref = str(packet["target"]["ref"])
        for candidate in packet["historical_retrieval"]["candidates"]:
            ref = str(candidate["ref"])
            target_sets.setdefault(ref, set()).add(target_ref)
            axes.setdefault(ref, set()).add("historical_retrieval")
            ranks.setdefault(ref, []).append(int(candidate["rank"]))
        for descendant in packet.get("known_later_descendants", []):
            ref = str(descendant["source_ref"])
            target_sets.setdefault(ref, set()).add(target_ref)
            axes.setdefault(ref, set()).add("known_later_descendant")

    candidates: list[InspectionCandidate] = []
    for ref, targets in target_sets.items():
        observed_ranks = ranks.get(ref, [])
        candidates.append(
            InspectionCandidate(
                ref=ref,
                fanout=len(targets),
                affected_targets=tuple(sorted(targets, key=lambda item: (_pr_number(item), item))),
                evidence_axes=tuple(sorted(axes.get(ref, set()))),
                best_historical_rank=min(observed_ranks) if observed_ranks else None,
                historical_rank_mass=round(
                    sum(1.0 / rank for rank in observed_ranks if rank > 0), 6
                ),
            )
        )

    candidates.sort(
        key=lambda row: (
            -row.fanout,
            -row.historical_rank_mass,
            row.best_historical_rank if row.best_historical_rank is not None else 10**9,
            -_pr_number(row.ref),
            row.ref,
        )
    )
    selected = candidates if max_candidates is None else candidates[:max_candidates]
    selected_targets = {
        target
        for candidate in selected
        for target in candidate.affected_targets
    }
    total_targets = {
        str(packet["target"]["ref"])
        for packet in portfolio.get("packets", [])
    }
    payload: dict[str, Any] = {
        "schema": f"omega-pr-llmt-inspection-plan/v{INSPECTION_SCHEMA_VERSION}",
        "portfolio_fingerprint": portfolio.get("fingerprint"),
        "operational_budget": {
            "max_candidates": max_candidates,
            "architecture_hard_cap": False,
            "boundary": (
                "max_candidates is an execution/API budget for this run, not a system ceiling; "
                "increase, shard or resume in later runs without changing the model."
            ),
        },
        "planned_unique_ref_count": len(candidates),
        "selected_ref_count": len(selected),
        "backlog_ref_count": len(candidates) - len(selected),
        "selected_packet_coverage_count": len(selected_targets),
        "total_packet_count": len(total_targets),
        "selected_packet_coverage_fraction": round(
            len(selected_targets) / len(total_targets), 6
        ) if total_targets else 0.0,
        "selected_pair_count": sum(candidate.fanout for candidate in selected),
        "candidates": [candidate.to_dict() for candidate in candidates],
        "selected_refs": [candidate.ref for candidate in selected],
        "authority": {
            "read": True,
            "write_authority_granted": False,
            "merge_authority_granted": False,
        },
        "boundary": (
            "Fanout prioritizes reusable inspection effort, not semantic relevance. "
            "Every selected PR still requires exact source/test evidence before reuse."
        ),
    }
    payload["fingerprint"] = _stable_digest(payload)
    return payload


def inspect_portfolio(
    index: GitHubMemoryIndex,
    portfolio: Mapping[str, Any],
    source: GitHubPRSource,
    *,
    max_candidates: int | None = None,
    max_files_per_pr: int = 4,
    extract_symbols: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Execute one bounded exact-source inspection pass over a portfolio."""
    plan = compile_inspection_plan(portfolio, max_candidates=max_candidates)
    retriever = ProgressiveGitHubRetriever(source)
    receipt = retriever.hydrate_refs(
        index,
        plan["selected_refs"],
        request_id=f"pr-llmt-inspection:{portfolio.get('fingerprint', 'unknown')}",
        max_files_per_pr=max_files_per_pr,
        extract_symbols=extract_symbols,
    )

    candidate_by_ref = {row["ref"]: row for row in plan["candidates"]}
    errors_by_ref: dict[str, list[dict[str, str]]] = {}
    for error in receipt.errors:
        errors_by_ref.setdefault(str(error.get("ref", "")), []).append(dict(error))

    overlays: list[dict[str, Any]] = []
    for ref in plan["selected_refs"]:
        pr = index.prs.get(ref)
        assets = sorted(
            (
                asset
                for asset in index.assets.values()
                if asset.source_ref == ref and asset.source_kind == "pr_head_python_ast_symbol"
            ),
            key=lambda asset: asset.asset_id,
        )
        candidate = candidate_by_ref[ref]
        overlays.append(
            {
                "ref": ref,
                "fanout": candidate["fanout"],
                "affected_targets": candidate["affected_targets"],
                "evidence_axes": candidate["evidence_axes"],
                "best_historical_rank": candidate["best_historical_rank"],
                "head_sha": pr.head_sha if pr else None,
                "lifecycle": pr.lifecycle if pr else None,
                "title": pr.title if pr else None,
                "changed_files": list(pr.files) if pr else [],
                "symbol_assets": [asset.asset_id for asset in assets],
                "errors": errors_by_ref.get(ref, []),
                "inspection_state": (
                    "HYDRATED_STATIC_AST"
                    if ref in receipt.hydrated_prs and not errors_by_ref.get(ref)
                    else "PARTIAL_OR_ERROR"
                ),
            }
        )

    inspected_targets = {
        target
        for overlay in overlays
        if overlay["inspection_state"] == "HYDRATED_STATIC_AST"
        for target in overlay["affected_targets"]
    }
    payload: dict[str, Any] = {
        "schema": f"omega-pr-llmt-inspection-overlay/v{INSPECTION_SCHEMA_VERSION}",
        "portfolio_fingerprint": portfolio.get("fingerprint"),
        "plan_fingerprint": plan["fingerprint"],
        "progressive_retrieval": receipt.to_dict(),
        "selected_ref_count": plan["selected_ref_count"],
        "hydrated_ref_count": len(receipt.hydrated_prs),
        "changed_file_count": receipt.changed_file_count,
        "symbol_count": receipt.symbol_count,
        "error_count": len(receipt.errors),
        "packet_coverage_after_successful_hydration": len(inspected_targets),
        "overlays": overlays,
        "authority": {
            "read": True,
            "write_authority_granted": False,
            "merge_authority_granted": False,
        },
        "oak_boundaries": [
            "FANOUT != SEMANTIC_RELEVANCE",
            "HYDRATED_HEAD != CORRECT_IMPLEMENTATION",
            "CHANGED_FILE != REUSABLE_BEHAVIOR",
            "AST_SYMBOL != BEHAVIORAL_EQUIVALENCE",
            "STATIC_INSPECTION != TEST_EXECUTION",
            "INSPECTION_OVERLAY != GITHUB_WRITE_AUTHORITY",
        ],
    }
    payload["fingerprint"] = _stable_digest(payload)
    return plan, payload


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
    parser = argparse.ArgumentParser(prog="omega-pr-llmt-inspection")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_cmd = sub.add_parser("plan")
    plan_cmd.add_argument("portfolio")
    plan_cmd.add_argument("--max-candidates", type=int)
    plan_cmd.add_argument("--output")

    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("index")
    inspect_cmd.add_argument("portfolio")
    inspect_cmd.add_argument("--max-candidates", type=int)
    inspect_cmd.add_argument("--max-files-per-pr", type=int, default=4)
    inspect_cmd.add_argument("--without-symbols", action="store_true")
    inspect_cmd.add_argument("--token-env", default="GITHUB_TOKEN")
    inspect_cmd.add_argument("--output-index")
    inspect_cmd.add_argument("--output-plan")
    inspect_cmd.add_argument("--output-overlay")

    args = parser.parse_args(argv)
    if args.command == "plan":
        portfolio = _load(args.portfolio)
        plan = compile_inspection_plan(portfolio, max_candidates=args.max_candidates)
        _write(args.output, plan)
        return 0

    index = GitHubMemoryIndex.from_dict(_load(args.index))
    portfolio = _load(args.portfolio)
    source = GitHubPRSource(token=os.getenv(args.token_env) if args.token_env else None)
    plan, overlay = inspect_portfolio(
        index,
        portfolio,
        source,
        max_candidates=args.max_candidates,
        max_files_per_pr=args.max_files_per_pr,
        extract_symbols=not args.without_symbols,
    )
    _write(args.output_index, index.to_dict())
    _write(args.output_plan, plan)
    _write(args.output_overlay, overlay)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
