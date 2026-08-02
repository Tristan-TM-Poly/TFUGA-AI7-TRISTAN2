from __future__ import annotations

import argparse
import json
from typing import Any, Sequence

from .materials import default_material_atlas
from .mission import demo_air_mission
from .models import default_air, demo_rotor
from .multifidelity import (
    ResourceEnvelope,
    merge_shard_reports,
    plan_shards,
    run_multifidelity_campaign,
)
from .r04_oak import (
    permissive_r04_policy,
    relaxed_r04_constraints,
    run_r04_benchmarks,
)
from .system_optimizer import InfiniteSystemFrontier, SystemSearchConstraints


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-propulsion-r04",
        description="Ω-PROPULSION R0.4 adaptive multifidelity campaign engine",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("benchmark")

    plan = sub.add_parser("plan-shards")
    plan.add_argument("--campaign-id", default="omega-propulsion-r04")
    plan.add_argument("--start-index", type=int, default=0)
    plan.add_argument("--count", type=int, required=True)
    plan.add_argument("--shards", type=int, required=True)

    campaign = sub.add_parser("campaign")
    campaign.add_argument("--campaign-id", default="omega-propulsion-r04")
    campaign.add_argument("--start-index", type=int, default=0)
    campaign.add_argument("--count", type=int, default=8)
    campaign.add_argument("--cost-budget", type=float, default=1_000.0)
    campaign.add_argument("--checkpoint-interval", type=int, default=2)
    campaign.add_argument("--shards", type=int, default=1)
    campaign.add_argument("--relaxed", action="store_true")
    campaign.add_argument("--summary-only", action="store_true")
    return parser


def _constraints(relaxed: bool) -> SystemSearchConstraints:
    return relaxed_r04_constraints() if relaxed else SystemSearchConstraints()


def _summary(report: Any) -> dict[str, Any]:
    payload = report.to_dict()
    if "candidates" in payload:
        payload["candidates"] = []
    if "promotions" in payload:
        payload["promotions"] = []
    if "evidence_events" in payload:
        payload["evidence_events"] = []
    if "pareto_front" in payload:
        payload["pareto_front"] = [
            {
                "candidate_id": item["vector"]["candidate_id"],
                "frontier_index": item["vector"]["frontier_index"],
                "objectives": item["objectives"],
                "evidence_hash": item["evidence_hash"],
            }
            for item in payload["pareto_front"]
        ]
    if payload.get("best") is not None:
        payload["best"] = {
            "candidate_id": payload["best"]["vector"]["candidate_id"],
            "frontier_index": payload["best"]["vector"]["frontier_index"],
            "objectives": payload["best"]["objectives"],
            "evidence_hash": payload["best"]["evidence_hash"],
        }
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "benchmark":
        report = run_r04_benchmarks()
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0 if report.passed else 2

    if args.command == "plan-shards":
        manifests = plan_shards(
            campaign_id=args.campaign_id,
            start_index=args.start_index,
            count=args.count,
            shard_count=args.shards,
        )
        print(
            json.dumps(
                {
                    "campaign_id": args.campaign_id,
                    "manifests": [item.to_dict() for item in manifests],
                    "permanent_total_cap": None,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    rotor = demo_rotor()
    medium = default_air()
    mission = demo_air_mission()
    atlas = default_material_atlas()
    frontier = InfiniteSystemFrontier(namespace=f"{args.campaign_id}:frontier")
    policy = permissive_r04_policy() if args.relaxed else None
    constraints = _constraints(args.relaxed)
    manifests = plan_shards(
        campaign_id=args.campaign_id,
        start_index=args.start_index,
        count=args.count,
        shard_count=args.shards,
    )
    reports = []
    for manifest in manifests:
        reports.append(
            run_multifidelity_campaign(
                rotor,
                medium,
                mission,
                campaign_id=args.campaign_id,
                start_index=manifest.start_index,
                count=manifest.count,
                resources=ResourceEnvelope(
                    max_cost_units=args.cost_budget,
                    checkpoint_interval=args.checkpoint_interval,
                    shard_count=args.shards,
                ),
                frontier=frontier,
                atlas=atlas,
                constraints=constraints,
                policy=policy,
            )
        )
    if len(reports) == 1:
        output = _summary(reports[0]) if args.summary_only else reports[0].to_dict()
    else:
        merged = merge_shard_reports(reports, campaign_id=args.campaign_id)
        output = {
            "shards": [
                _summary(report) if args.summary_only else report.to_dict()
                for report in reports
            ],
            "merged": merged.to_dict(),
            "manifests": [item.to_dict() for item in manifests],
            "permanent_total_cap": None,
            "epistemic_status": (
                "computational evidence-depth campaign only; "
                "F2 is not CFD, experiment or certification"
            ),
        }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
