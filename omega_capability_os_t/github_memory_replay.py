"""Ω GitHub Decision Replay / Reuse Bench R0.8.

R0.8 evaluates whether cumulative GitHub memory can recover declared prior work
and reduce the *capability-token residual* versus a CREATE-first baseline.

The benchmark deliberately separates three things:
1. controlled capability-policy fixtures;
2. historical lineage retrieval using target PR title only as the query;
3. OAK leakage checks.

It does not claim LOC, time, defect, causal, or monetary savings from proxy
metrics alone.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping
import argparse
import json
from pathlib import Path

from .core import Capability
from .github_memory import (
    CapabilityObservation,
    CapabilityRequest,
    GitHubMemoryIndex,
    PRMemory,
    ReuseBeforeCreateGate,
    extract_explicit_relations,
    _stable_digest,
    _tokens,
)

REPLAY_SCHEMA_VERSION = "0.8.0"
ANCESTOR_RELATIONS = {"uses", "extends", "derived_from", "supersedes", "replaces"}


@dataclass(frozen=True)
class PolicyReplayReceipt:
    request_id: str
    reuse_action: str
    requested_outputs: tuple[str, ...]
    create_first_new_outputs: tuple[str, ...]
    reuse_first_residual_outputs: tuple[str, ...]
    output_tokens_avoided: int
    output_token_avoidance_fraction: float
    generation_allowed: bool
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema"] = f"omega-github-policy-replay/v{REPLAY_SCHEMA_VERSION}"
        payload["fingerprint"] = _stable_digest(payload)
        return payload


def compare_create_first_vs_reuse(
    index: GitHubMemoryIndex,
    request: CapabilityRequest,
) -> PolicyReplayReceipt:
    """Compare a CREATE-first token baseline with the current reuse gate.

    The baseline assumes every requested output would be implemented anew.
    The result is a capability-token proxy only; it is not LOC/time saved.
    """
    decision = ReuseBeforeCreateGate(index).decide(request)
    requested = tuple(sorted(set(request.produces)))
    residual = tuple(sorted(set(decision.residual_outputs)))
    avoided = max(0, len(requested) - len(residual))
    fraction = avoided / len(requested) if requested else 0.0
    generation_allowed = decision.action in {"CREATE", "EXTEND"} and bool(residual or decision.action == "CREATE")
    return PolicyReplayReceipt(
        request_id=request.request_id,
        reuse_action=decision.action,
        requested_outputs=requested,
        create_first_new_outputs=requested,
        reuse_first_residual_outputs=residual,
        output_tokens_avoided=avoided,
        output_token_avoidance_fraction=round(fraction, 6),
        generation_allowed=generation_allowed,
        boundary=(
            "Capability-token avoidance is a controlled architecture proxy only. "
            "It is not measured LOC, engineering time, defects avoided, maintenance savings, "
            "causal benefit, or permission to write."
        ),
    )


@dataclass(frozen=True)
class HistoricalReplayCase:
    target_ref: str
    target_number: int
    query_mode: str
    prior_pr_count: int
    gold_lineage_refs: tuple[str, ...]
    retrieved_refs: tuple[str, ...]
    hits: tuple[str, ...]
    recall_at_k: float
    candidate_fraction: float
    target_leaked: bool
    future_leakage_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "gold_lineage_refs",
            "retrieved_refs",
            "hits",
            "future_leakage_refs",
        ):
            payload[key] = list(payload[key])
        return payload


def _gold_ancestor_refs(target: PRMemory) -> tuple[str, ...]:
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


def _prefix_index(index: GitHubMemoryIndex, target: PRMemory) -> GitHubMemoryIndex:
    prefix = GitHubMemoryIndex()
    for pr in index.prs.values():
        if pr.repository == target.repository and pr.number < target.number:
            prefix.add_pr(pr)
    return prefix


def replay_historical_lineage(
    index: GitHubMemoryIndex,
    *,
    top_k: int = 8,
    max_targets: int | None = None,
) -> dict[str, Any]:
    """Replay historical retrieval without exposing target/future PRs to the retriever.

    Target title is used as the query. The current target body is used only as
    post-hoc gold lineage labels. This is a retrieval benchmark, not a
    reconstruction of the exact historical model context.
    """
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    targets = sorted(index.prs.values(), key=lambda pr: (pr.repository, pr.number))
    cases: list[HistoricalReplayCase] = []
    skipped_no_lineage = 0

    for target in targets:
        gold = _gold_ancestor_refs(target)
        if not gold:
            skipped_no_lineage += 1
            continue
        prefix = _prefix_index(index, target)
        if not prefix.prs:
            continue

        request = CapabilityRequest(
            request_id=f"replay:{target.ref}",
            description=target.title,
            domains=("github", "software"),
            consumes=(),
            produces=(),
        )
        ranked = prefix.search_prs(request, top_k=top_k)
        retrieved = tuple(str(row["ref"]) for row in ranked)
        retrieved_set = set(retrieved)
        hits = tuple(ref for ref in gold if ref in retrieved_set)
        future = tuple(
            ref for ref in retrieved
            if int(ref.rsplit("#", 1)[1]) >= target.number
        )
        candidate_fraction = min(1.0, len(retrieved) / len(prefix.prs)) if prefix.prs else 0.0
        cases.append(
            HistoricalReplayCase(
                target_ref=target.ref,
                target_number=target.number,
                query_mode="title_only",
                prior_pr_count=len(prefix.prs),
                gold_lineage_refs=gold,
                retrieved_refs=retrieved,
                hits=hits,
                recall_at_k=round(len(hits) / len(gold), 6),
                candidate_fraction=round(candidate_fraction, 6),
                target_leaked=target.ref in retrieved,
                future_leakage_refs=future,
            )
        )
        if max_targets is not None and len(cases) >= max_targets:
            break

    total_gold = sum(len(case.gold_lineage_refs) for case in cases)
    total_hits = sum(len(case.hits) for case in cases)
    macro_recall = (
        sum(case.recall_at_k for case in cases) / len(cases)
        if cases else 0.0
    )
    payload: dict[str, Any] = {
        "schema": f"omega-github-historical-lineage-replay/v{REPLAY_SCHEMA_VERSION}",
        "top_k": top_k,
        "eligible_target_count": len(cases),
        "skipped_no_lineage_count": skipped_no_lineage,
        "gold_lineage_ref_count": total_gold,
        "hit_count": total_hits,
        "micro_recall_at_k": round(total_hits / total_gold, 6) if total_gold else 0.0,
        "macro_recall_at_k": round(macro_recall, 6),
        "mean_candidate_fraction": round(
            sum(case.candidate_fraction for case in cases) / len(cases), 6
        ) if cases else 0.0,
        "target_leakage_count": sum(case.target_leaked for case in cases),
        "future_leakage_count": sum(len(case.future_leakage_refs) for case in cases),
        "cases": [case.to_dict() for case in cases],
        "contamination": {
            "query_uses_target_title_only": True,
            "target_body_used_as_gold_only": True,
            "target_pr_hidden_from_retrieval": True,
            "future_prs_hidden_from_retrieval": True,
            "pretraining_exposure": "unknown",
            "historical_metadata_fidelity": "current_snapshot_proxy",
        },
        "boundary": (
            "Explicit PR lineage is an incomplete post-hoc gold set. Recall measures recovery of declared ancestors only; "
            "it does not measure all useful reuse. PR-number ordering is a creation-order proxy, current metadata is not an "
            "exact historical snapshot, and title-only replay is not causal evidence of engineering savings."
        ),
    }
    payload["fingerprint"] = _stable_digest(payload)
    return payload


def _fixture_cap(capability_id: str, produces: tuple[str, ...]) -> CapabilityObservation:
    cap = Capability(
        capability_id=capability_id,
        domains=("github", "memory"),
        consumes=("repository",),
        produces=produces,
        authority="read",
        quality=0.95,
        information_gain=0.90,
        verifiability=0.95,
        reuse=0.95,
        cost=0.10,
        latency=0.10,
        risk=0.05,
    )
    return CapabilityObservation(
        capability=cap,
        source_ref=f"fixture:{capability_id}",
        keywords=_tokens((capability_id, *cap.domains, *cap.consumes, *cap.produces)),
    )


def deterministic_policy_fixtures() -> tuple[dict[str, Any], ...]:
    request = CapabilityRequest(
        request_id="fixture-request",
        description="GitHub memory index and capability graph",
        domains=("github", "memory"),
        consumes=("repository",),
        produces=("pr_index", "capability_graph"),
    )

    full = GitHubMemoryIndex()
    full.capabilities["fixture.full"] = _fixture_cap(
        "fixture.full", ("pr_index", "capability_graph")
    )
    partial = GitHubMemoryIndex()
    partial.capabilities["fixture.partial"] = _fixture_cap(
        "fixture.partial", ("pr_index",)
    )
    empty = GitHubMemoryIndex()

    scenarios = (
        ("full_reuse", full, "REUSE", 1.0),
        ("partial_extend", partial, "EXTEND", 0.5),
        ("no_prior_create", empty, "CREATE", 0.0),
    )
    rows: list[dict[str, Any]] = []
    for case_id, fixture_index, expected_action, expected_avoidance in scenarios:
        receipt = compare_create_first_vs_reuse(fixture_index, request).to_dict()
        passed = (
            receipt["reuse_action"] == expected_action
            and receipt["output_token_avoidance_fraction"] == expected_avoidance
        )
        rows.append(
            {
                "case_id": case_id,
                "expected_action": expected_action,
                "expected_output_token_avoidance_fraction": expected_avoidance,
                "observed": receipt,
                "passed": passed,
            }
        )
    return tuple(rows)


def compile_reuse_bench_court(
    index: GitHubMemoryIndex | None = None,
    *,
    top_k: int = 8,
    max_targets: int | None = None,
) -> dict[str, Any]:
    synthetic = deterministic_policy_fixtures()
    historical = replay_historical_lineage(
        index or GitHubMemoryIndex(),
        top_k=top_k,
        max_targets=max_targets,
    )
    synthetic_pass = all(row["passed"] for row in synthetic)
    leakage_free = (
        historical["target_leakage_count"] == 0
        and historical["future_leakage_count"] == 0
    )
    payload: dict[str, Any] = {
        "schema": f"omega-github-reuse-bench-court/v{REPLAY_SCHEMA_VERSION}",
        "synthetic_policy_cases": list(synthetic),
        "historical_lineage": historical,
        "oak": {
            "status": "PASS" if synthetic_pass and leakage_free else "FAIL",
            "synthetic_policy_pass": synthetic_pass,
            "historical_temporal_leakage_free": leakage_free,
            "boundaries": [
                "OUTPUT_TOKEN_AVOIDANCE != LOC_OR_TIME_SAVED",
                "LINEAGE_RECALL != ALL_REUSE_RECALL",
                "CURRENT_PR_METADATA != EXACT_HISTORICAL_CONTEXT",
                "REPLAY_ADVANTAGE != CAUSAL_ENGINEERING_ADVANTAGE",
                "BENCHMARK_PASS != EXTERNAL_WORLD_TRUTH",
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
    parser = argparse.ArgumentParser(prog="omega-github-reuse-bench")
    sub = parser.add_subparsers(dest="command", required=True)

    policy = sub.add_parser("policy")
    policy.add_argument("index")
    policy.add_argument("request")
    policy.add_argument("--output")

    historical = sub.add_parser("historical")
    historical.add_argument("index")
    historical.add_argument("--top-k", type=int, default=8)
    historical.add_argument("--max-targets", type=int)
    historical.add_argument("--output")

    court = sub.add_parser("court")
    court.add_argument("index")
    court.add_argument("--top-k", type=int, default=8)
    court.add_argument("--max-targets", type=int)
    court.add_argument("--output")

    args = parser.parse_args(argv)
    index = GitHubMemoryIndex.from_dict(_load(args.index))

    if args.command == "policy":
        request = CapabilityRequest.from_dict(_load(args.request))
        payload = compare_create_first_vs_reuse(index, request).to_dict()
    elif args.command == "historical":
        payload = replay_historical_lineage(
            index, top_k=args.top_k, max_targets=args.max_targets
        )
    else:
        payload = compile_reuse_bench_court(
            index, top_k=args.top_k, max_targets=args.max_targets
        )

    _write(args.output, payload)
    return 0 if payload.get("oak", {}).get("status", "PASS") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
