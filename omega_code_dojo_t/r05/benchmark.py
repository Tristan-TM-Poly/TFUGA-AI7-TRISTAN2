from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .engine import MultiJudgeEngine, MultiJudgePolicy, fixture_references
from .policy import (
    AccessRequest,
    ContaminationError,
    Decision,
    Normalizer,
    PLATFORMS,
    PlatformMode,
    PolicyGate,
    ProblemRef,
)


def run_r05_benchmark() -> dict[str, object]:
    base = fixture_references(64)
    blocked = tuple(
        ProblemRef(
            platform.platform_id,
            "blocked-fixture",
            f"Blocked fixture for {platform.display_name}",
            ("general_problem_solving",),
            0.99,
            platform.blocked_content[0],
            f"{platform.platform_id}:blocked-fixture",
            metadata={"expected_decision": "block"},
        )
        for platform in PLATFORMS
    )
    references = base + base[:8] + blocked
    policy = MultiJudgePolicy(
        reference_budget=len(base) + len(blocked),
        shadow_budget=256,
        max_attempts=2,
        permanent_total_cap=None,
    )
    first = MultiJudgeEngine().run(references, policy)
    second = MultiJudgeEngine().run(references, policy)
    gate = PolicyGate()

    contamination_blocked = False
    try:
        Normalizer().normalize(
            (
                {
                    "platform_id": "codeforces",
                    "external_id": "contaminated",
                    "title": "contaminated",
                    "tags": ["graph"],
                    "difficulty": 0.5,
                    "statement": "must not enter metadata pipeline",
                },
            )
        )
    except ContaminationError:
        contamination_blocked = True

    invariants = {
        "nine_platforms_registered": len(PLATFORMS) == 9,
        "logical_reference_space_is_1236950581248": first["logical_reference_space"] == 1_236_950_581_248,
        "duplicate_references_are_deduplicated": first["discovered_references"] > first["normalized_references"],
        "all_platforms_represented": len(first["platform_metrics"]) == 9,
        "shadow_budget_materialized": first["materialized_shadow_problems"] == 256,
        "all_shadow_fixtures_solved": first["shadow_solve_rate"] == 1.0,
        "blocked_references_detected": first["blocked_references"] == 9,
        "dmoj_training_blocked_without_permission": gate.evaluate(AccessRequest("dmoj", PlatformMode.TRAIN, "problem_metadata", automated=True)).decision is Decision.BLOCK,
        "codeforces_metadata_discovery_allowed": gate.evaluate(AccessRequest("codeforces", PlatformMode.DISCOVER, "problem_metadata", automated=True)).decision is Decision.ALLOW,
        "automated_submission_not_allowed": gate.evaluate(AccessRequest("codewars", PlatformMode.SUBMIT, "user_owned_solution", automated=True, user_owned=True, license_id="MIT")).decision is not Decision.ALLOW,
        "forbidden_payload_fields_rejected": contamination_blocked,
        "deterministic_receipt": first == second,
        "receipt_hash_valid": first["receipt_sha256"] == _receipt_hash(first),
        "external_problem_solution_not_claimed": first["claims"]["external_problem_solution_claimed"] is False,
        "no_automated_external_submission_claim": first["claims"]["automated_external_submission_claimed"] is False,
        "no_permanent_cap": first["permanent_total_cap"] is None,
    }
    certified = all(invariants.values())
    return {
        "status": "CERTIFIED_MULTI_JUDGE_SHADOW_FIXTURES_R0_5" if certified else "OAK_INVARIANT_FAILURE_R0_5",
        "system": "omega-multi-judge-dojo-t-infinity",
        "version": "R0.5",
        "platform_catalog": [item.to_dict() for item in PLATFORMS],
        "logical_reference_space": first["logical_reference_space"],
        "discovered_references": first["discovered_references"],
        "normalized_references": first["normalized_references"],
        "selected_references": first["selected_references"],
        "materialized_shadow_problems": first["materialized_shadow_problems"],
        "solved_shadow_problems": first["solved_shadow_problems"],
        "shadow_solve_rate": first["shadow_solve_rate"],
        "blocked_references": first["blocked_references"],
        "total_cost_units": first["total_cost_units"],
        "permanent_total_cap": first["permanent_total_cap"],
        "deterministic": first == second,
        "receipt_sha256": first["receipt_sha256"],
        "invariants": invariants,
        "claims": first["claims"],
        "receipt": first,
    }


def _receipt_hash(receipt: dict[str, object]) -> str:
    from .policy import sha256_hex
    payload = dict(receipt)
    payload.pop("receipt_sha256", None)
    return sha256_hex(payload)


def _write(payload: object, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-code-dojo-r05",
        description="OAK-safe multi-platform metadata and shadow-resolution factory.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    registry = sub.add_parser("registry")
    registry.add_argument("--output")

    plan = sub.add_parser("plan")
    plan.add_argument("--per-platform", type=int, default=16)
    plan.add_argument("--limit", type=int, default=32)
    plan.add_argument("--output")

    benchmark = sub.add_parser("benchmark")
    benchmark.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "registry":
        _write({"system": "omega-multi-judge-dojo-t-infinity", "version": "R0.5", "platforms": [item.to_dict() for item in PLATFORMS]}, args.output)
        return 0
    if args.command == "plan":
        engine = MultiJudgeEngine()
        refs = fixture_references(args.per_platform)
        normalized = engine.normalizer.normalize(refs)
        selections = engine.planner.select(normalized, args.limit)
        _write({"system": "omega-multi-judge-dojo-t-infinity", "version": "R0.5", "selections": [item.to_dict() for item in selections]}, args.output)
        return 0

    payload = run_r05_benchmark()
    _write(payload, args.output)
    return 0 if payload["status"] == "CERTIFIED_MULTI_JUDGE_SHADOW_FIXTURES_R0_5" else 1
