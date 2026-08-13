"""Fanout-first exact inspection overlays for the per-PR LLMT portfolio.

The module consumes the canonical PR-LLMT portfolio and reuses #447 progressive
GitHub hydration. It deduplicates candidate PRs across all open target PRs,
prioritizes candidates that can inform the most packets, and emits read-only
inspection evidence. Operational budgets are explicit parameters, never hard
architecture ceilings. Checkpoints are keyed by exact (PR ref, head SHA), so a
moved head automatically becomes pending again.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
import argparse
import json
import os

from .github_memory import GitHubMemoryIndex, GitHubPRSource, _stable_digest
from .github_memory_zoom import ProgressiveGitHubRetriever

INSPECTION_SCHEMA_VERSION = "0.1.0"
CHECKPOINT_SCHEMA_VERSION = "0.1.0"


def _pr_number(ref: str) -> int:
    try:
        return int(ref.rsplit("#", 1)[1])
    except (IndexError, ValueError):
        return -1


@dataclass(frozen=True)
class InspectionCandidate:
    ref: str
    head_sha: str | None
    fanout: int
    affected_targets: tuple[str, ...]
    evidence_axes: tuple[str, ...]
    best_historical_rank: int | None
    historical_rank_mass: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _checkpoint_heads(checkpoint: Mapping[str, Any] | None) -> dict[str, str]:
    if checkpoint is None:
        return {}
    if checkpoint.get("schema") != f"omega-pr-llmt-inspection-checkpoint/v{CHECKPOINT_SCHEMA_VERSION}":
        raise ValueError(f"unsupported checkpoint schema: {checkpoint.get('schema')}")
    return {
        str(ref): str(sha)
        for ref, sha in dict(checkpoint.get("completed_heads", {})).items()
        if str(ref) and str(sha)
    }


def compile_inspection_checkpoint(overlay: Mapping[str, Any]) -> dict[str, Any]:
    """Compress successful exact-head inspections into a resumable checkpoint."""
    if overlay.get("schema") != f"omega-pr-llmt-inspection-overlay/v{INSPECTION_SCHEMA_VERSION}":
        raise ValueError(f"unsupported inspection overlay schema: {overlay.get('schema')}")
    completed: dict[str, str] = {}
    for row in overlay.get("overlays", []):
        if row.get("inspection_state") != "HYDRATED_STATIC_AST":
            continue
        ref = str(row.get("ref", ""))
        head_sha = str(row.get("head_sha", ""))
        if ref and head_sha:
            completed[ref] = head_sha
    payload: dict[str, Any] = {
        "schema": f"omega-pr-llmt-inspection-checkpoint/v{CHECKPOINT_SCHEMA_VERSION}",
        "portfolio_fingerprint": overlay.get("portfolio_fingerprint"),
        "completed_ref_count": len(completed),
        "completed_heads": dict(sorted(completed.items())),
        "boundary": (
            "A checkpoint suppresses re-inspection only while the candidate PR head SHA is unchanged. "
            "Head movement invalidates freshness automatically; checkpoint presence is not correctness or compatibility proof."
        ),
    }
    payload["fingerprint"] = _stable_digest(payload)
    return payload


def compile_inspection_plan(
    portfolio: Mapping[str, Any],
    *,
    max_candidates: int | None = None,
    checkpoint: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Deduplicate candidate PRs and prioritize high-fanout exact inspection."""
    if max_candidates is not None and max_candidates < 0:
        raise ValueError("max_candidates must be non-negative or omitted")
    if portfolio.get("schema") != "omega-pr-llmt-portfolio/v0.1.0":
        raise ValueError(f"unsupported portfolio schema: {portfolio.get('schema')}")
    completed_heads = _checkpoint_heads(checkpoint)

    target_sets: dict[str, set[str]] = {}
    axes: dict[str, set[str]] = {}
    ranks: dict[str, list[int]] = {}
    head_shas: dict[str, str | None] = {}
    target_head_shas = {
        str(packet["target"]["ref"]): packet["target"].get("head_sha")
        for packet in portfolio.get("packets", [])
    }

    for packet in portfolio.get("packets", []):
        target_ref = str(packet["target"]["ref"])
        for candidate in packet["historical_retrieval"]["candidates"]:
            ref = str(candidate["ref"])
            target_sets.setdefault(ref, set()).add(target_ref)
            axes.setdefault(ref, set()).add("historical_retrieval")
            ranks.setdefault(ref, []).append(int(candidate["rank"]))
            candidate_sha = candidate.get("head_sha")
            if ref not in head_shas or head_shas[ref] is None:
                head_shas[ref] = str(candidate_sha) if candidate_sha else None
        for descendant in packet.get("known_later_descendants", []):
            ref = str(descendant["source_ref"])
            target_sets.setdefault(ref, set()).add(target_ref)
            axes.setdefault(ref, set()).add("known_later_descendant")
            if ref not in head_shas or head_shas[ref] is None:
                target_sha = target_head_shas.get(ref)
                head_shas[ref] = str(target_sha) if target_sha else None

    candidates: list[InspectionCandidate] = []
    for ref, targets in target_sets.items():
        observed_ranks = ranks.get(ref, [])
        candidates.append(
            InspectionCandidate(
                ref=ref,
                head_sha=head_shas.get(ref),
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
    current_completed = [
        candidate
        for candidate in candidates
        if candidate.head_sha and completed_heads.get(candidate.ref) == candidate.head_sha
    ]
    pending = [candidate for candidate in candidates if candidate not in current_completed]
    selected = pending if max_candidates is None else pending[:max_candidates]
    stale_checkpoint_refs = sorted(
        ref
        for ref, old_sha in completed_heads.items()
        if ref in head_shas and head_shas.get(ref) and head_shas.get(ref) != old_sha
    )
    unverifiable_checkpoint_refs = sorted(
        ref for ref in completed_heads if ref in head_shas and not head_shas.get(ref)
    )
    selected_targets = {
        target
        for candidate in selected
        for target in candidate.affected_targets
    }
    completed_targets = {
        target
        for candidate in current_completed
        for target in candidate.affected_targets
    }
    total_targets = {
        str(packet["target"]["ref"])
        for packet in portfolio.get("packets", [])
    }
    payload: dict[str, Any] = {
        "schema": f"omega-pr-llmt-inspection-plan/v{INSPECTION_SCHEMA_VERSION}",
        "portfolio_fingerprint": portfolio.get("fingerprint"),
        "checkpoint_fingerprint": checkpoint.get("fingerprint") if checkpoint else None,
        "operational_budget": {
            "max_candidates": max_candidates,
            "architecture_hard_cap": False,
            "boundary": (
                "max_candidates is an execution/API budget for this run, not a system ceiling; "
                "increase, shard or resume in later runs without changing the model."
            ),
        },
        "planned_unique_ref_count": len(candidates),
        "completed_current_ref_count": len(current_completed),
        "pending_ref_count": len(pending),
        "selected_ref_count": len(selected),
        "backlog_ref_count": len(pending) - len(selected),
        "stale_checkpoint_ref_count": len(stale_checkpoint_refs),
        "stale_checkpoint_refs": stale_checkpoint_refs,
        "unverifiable_checkpoint_ref_count": len(unverifiable_checkpoint_refs),
        "unverifiable_checkpoint_refs": unverifiable_checkpoint_refs,
        "completed_current_refs": [candidate.ref for candidate in current_completed],
        "completed_packet_coverage_count": len(completed_targets),
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


def _merge_overlays(
    prior_overlay: Mapping[str, Any] | None,
    current_overlays: Iterable[Mapping[str, Any]],
    *,
    portfolio_fingerprint: Any,
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    if prior_overlay is not None:
        if prior_overlay.get("schema") != f"omega-pr-llmt-inspection-overlay/v{INSPECTION_SCHEMA_VERSION}":
            raise ValueError(f"unsupported prior overlay schema: {prior_overlay.get('schema')}")
        if prior_overlay.get("portfolio_fingerprint") != portfolio_fingerprint:
            raise ValueError("prior overlay portfolio fingerprint mismatch")
        for row in prior_overlay.get("overlays", []):
            ref = str(row.get("ref", ""))
            if ref:
                merged[ref] = dict(row)
    for row in current_overlays:
        ref = str(row.get("ref", ""))
        if ref:
            merged[ref] = dict(row)
    return [merged[ref] for ref in sorted(merged, key=lambda item: (_pr_number(item), item))]


def inspect_portfolio(
    index: GitHubMemoryIndex,
    portfolio: Mapping[str, Any],
    source: GitHubPRSource,
    *,
    max_candidates: int | None = None,
    max_files_per_pr: int = 4,
    extract_symbols: bool = True,
    checkpoint: Mapping[str, Any] | None = None,
    prior_overlay: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Execute one bounded exact-source inspection pass over a portfolio."""
    plan = compile_inspection_plan(
        portfolio,
        max_candidates=max_candidates,
        checkpoint=checkpoint,
    )
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

    wave_overlays: list[dict[str, Any]] = []
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
        wave_overlays.append(
            {
                "ref": ref,
                "fanout": candidate["fanout"],
                "affected_targets": candidate["affected_targets"],
                "evidence_axes": candidate["evidence_axes"],
                "best_historical_rank": candidate["best_historical_rank"],
                "head_sha": pr.head_sha if pr else candidate.get("head_sha"),
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

    cumulative_overlays = _merge_overlays(
        prior_overlay,
        wave_overlays,
        portfolio_fingerprint=portfolio.get("fingerprint"),
    )
    inspected_targets = {
        target
        for row in cumulative_overlays
        if row.get("inspection_state") == "HYDRATED_STATIC_AST"
        for target in row.get("affected_targets", [])
    }
    cumulative_hydrated = sum(
        row.get("inspection_state") == "HYDRATED_STATIC_AST"
        for row in cumulative_overlays
    )
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
        "cumulative_overlay_count": len(cumulative_overlays),
        "cumulative_hydrated_ref_count": cumulative_hydrated,
        "packet_coverage_after_successful_hydration": len(inspected_targets),
        "overlays": cumulative_overlays,
        "wave_overlays": wave_overlays,
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
            "CHECKPOINT_MATCH != CORRECTNESS_PROOF",
            "INSPECTION_OVERLAY != GITHUB_WRITE_AUTHORITY",
        ],
    }
    payload["fingerprint"] = _stable_digest(payload)
    checkpoint_payload = compile_inspection_checkpoint(payload)
    return plan, payload, checkpoint_payload


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
    plan_cmd.add_argument("--checkpoint")
    plan_cmd.add_argument("--output")

    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("index")
    inspect_cmd.add_argument("portfolio")
    inspect_cmd.add_argument("--max-candidates", type=int)
    inspect_cmd.add_argument("--max-files-per-pr", type=int, default=4)
    inspect_cmd.add_argument("--without-symbols", action="store_true")
    inspect_cmd.add_argument("--checkpoint")
    inspect_cmd.add_argument("--prior-overlay")
    inspect_cmd.add_argument("--token-env", default="GITHUB_TOKEN")
    inspect_cmd.add_argument("--output-index")
    inspect_cmd.add_argument("--output-plan")
    inspect_cmd.add_argument("--output-overlay")
    inspect_cmd.add_argument("--output-checkpoint")

    args = parser.parse_args(argv)
    if args.command == "plan":
        portfolio = _load(args.portfolio)
        checkpoint = _load(args.checkpoint) if args.checkpoint else None
        plan = compile_inspection_plan(
            portfolio,
            max_candidates=args.max_candidates,
            checkpoint=checkpoint,
        )
        _write(args.output, plan)
        return 0

    index = GitHubMemoryIndex.from_dict(_load(args.index))
    portfolio = _load(args.portfolio)
    checkpoint = _load(args.checkpoint) if args.checkpoint else None
    prior_overlay = _load(args.prior_overlay) if args.prior_overlay else None
    source = GitHubPRSource(token=os.getenv(args.token_env) if args.token_env else None)
    plan, overlay, checkpoint_payload = inspect_portfolio(
        index,
        portfolio,
        source,
        max_candidates=args.max_candidates,
        max_files_per_pr=args.max_files_per_pr,
        extract_symbols=not args.without_symbols,
        checkpoint=checkpoint,
        prior_overlay=prior_overlay,
    )
    _write(args.output_index, index.to_dict())
    _write(args.output_plan, plan)
    _write(args.output_overlay, overlay)
    _write(args.output_checkpoint, checkpoint_payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
