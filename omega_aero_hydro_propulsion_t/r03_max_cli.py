from __future__ import annotations

import argparse
import json
from typing import Any, Sequence

from .materials import default_material_atlas
from .mission import demo_air_mission
from .models import default_air, demo_rotor
from .r03_max_oak import run_r03_max_benchmarks
from .system_optimizer import InfiniteSystemFrontier, SystemSearchConstraints, evaluate_system_candidate, run_system_campaign


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-propulsion-r03-max",
        description="Ω-PROPULSION R0.3 Max unbounded deterministic system-search frontier",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("benchmark")

    candidate = sub.add_parser("candidate")
    candidate.add_argument("--index", type=int, default=0)
    candidate.add_argument("--observer-distance", type=float, default=10.0)

    campaign = sub.add_parser("campaign")
    campaign.add_argument("--start-index", type=int, default=0)
    campaign.add_argument("--count", type=int, default=8)
    campaign.add_argument("--checkpoint-interval", type=int, default=4)
    campaign.add_argument("--previous-digest", default="0" * 64)
    campaign.add_argument("--observer-distance", type=float, default=10.0)
    campaign.add_argument("--summary-only", action="store_true")
    campaign.add_argument("--relaxed", action="store_true")
    return parser


def _relaxed_constraints() -> SystemSearchConstraints:
    return SystemSearchConstraints(
        maximum_rotor_mass_kg=None,
        minimum_structural_safety_factor=0.05,
        maximum_overall_spl_db=None,
        minimum_robust_feasible_probability=0.0,
        minimum_safe_continuation_fraction=0.0,
        maximum_expected_shaft_energy_j=None,
        maximum_tip_mach=2.0,
    )


def _campaign_summary(payload: dict[str, Any]) -> dict[str, Any]:
    best = payload["best"]
    return {
        "start_index": payload["start_index"],
        "requested_count": payload["requested_count"],
        "evaluated_count": payload["evaluated_count"],
        "feasible_count": payload["feasible_count"],
        "next_index": payload["next_index"],
        "best_candidate_id": None if best is None else best["vector"]["candidate_id"],
        "best_objectives": None if best is None else best["objectives"],
        "pareto_candidate_ids": [item["vector"]["candidate_id"] for item in payload["pareto_front"]],
        "checkpoints": payload["checkpoints"],
        "final_chain_digest": payload["final_chain_digest"],
        "frontier": payload["frontier"],
        "constraints": payload["constraints"],
        "permanent_total_cap": payload["permanent_total_cap"],
        "physics_certified": payload["physics_certified"],
        "certification_notice": payload["certification_notice"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "benchmark":
        report = run_r03_max_benchmarks()
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0 if report.passed else 2

    rotor = demo_rotor()
    medium = default_air()
    mission = demo_air_mission()
    atlas = default_material_atlas()
    frontier = InfiniteSystemFrontier()
    constraints = _relaxed_constraints() if getattr(args, "relaxed", False) else SystemSearchConstraints()

    if args.command == "candidate":
        vector = frontier.vector_at(args.index, atlas)
        result = evaluate_system_candidate(
            rotor,
            medium,
            mission,
            vector,
            atlas=atlas,
            constraints=constraints,
            observer_distance_m=args.observer_distance,
        )
        print(json.dumps({
            "candidate": result.to_dict(),
            "frontier": frontier.to_dict(),
            "material_record": atlas.get_record(vector.material_name).to_dict(),
            "epistemic_status": "system-search screening only; not flight, marine, structural, acoustic, reliability or regulatory certification",
        }, indent=2, sort_keys=True))
        return 0

    report = run_system_campaign(
        rotor,
        medium,
        mission,
        start_index=args.start_index,
        count=args.count,
        frontier=frontier,
        atlas=atlas,
        constraints=constraints,
        observer_distance_m=args.observer_distance,
        checkpoint_interval=args.checkpoint_interval,
        previous_chain_digest=args.previous_digest,
    )
    payload = report.to_dict()
    if args.summary_only:
        payload = _campaign_summary(payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report.best is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
