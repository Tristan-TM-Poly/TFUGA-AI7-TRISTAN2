"""Demonstrate a quadrillion-scale R0.5 plan without materializing it."""
from __future__ import annotations

import json

from omega_generator_discovery_t.campaign import CampaignSpec
from omega_generator_discovery_t.frontier_virtual import (
    AdaptiveWaveScheduler,
    BaseCampaignShape,
    BudgetEnvelope,
    MerkleMountainRange,
    ResourceModel,
    VirtualFrontierPlan,
    VirtualFrontierPolicy,
    resolve_frontier_target,
)


def main() -> None:
    shape = BaseCampaignShape.from_campaign_spec(CampaignSpec())
    plan = VirtualFrontierPlan.build(
        shape,
        resolve_frontier_target(profile="quadrillion"),
        VirtualFrontierPolicy(
            target_records_per_partition=2_000_000,
            max_partitions_per_wave=64,
            max_matrix_entries=64,
        ),
    )
    extreme_cursor = max(0, plan.total_partition_count - 4)
    page = plan.partition_page(extreme_cursor, limit=4)

    model = ResourceModel(
        bytes_per_record=512,
        nanoseconds_per_record=20_000,
        cost_microunits_per_record=1,
        records_per_api_call=50_000,
        records_per_file=250_000,
        records_per_commit=5_000_000,
    )
    budget = BudgetEnvelope(
        max_logical_records=25_000_000,
        max_bytes_written=20_000_000_000,
        max_nanoseconds=1_000_000_000_000,
        max_cost_microunits=25_000_000,
        max_api_calls=1_000,
        max_files=1_000,
        max_commits=20,
    )
    wave = AdaptiveWaveScheduler(
        model, max_partitions_per_wave=64
    ).schedule(plan, 0, budget)

    mmr = MerkleMountainRange()
    for partition in wave.partitions:
        mmr.append(partition.to_dict())

    result = {
        "plan": plan.to_dict(),
        "last_partition_page": page,
        "first_budgeted_wave": wave.to_dict(),
        "wave_partition_mmr": mmr.receipt(),
        "oak_boundary": (
            "A quadrillion-scale virtual plan is not a quadrillion emitted, "
            "validated, useful, novel, or empirically proven objects."
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
