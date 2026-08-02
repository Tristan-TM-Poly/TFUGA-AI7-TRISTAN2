from __future__ import annotations

import json

from omega_aero_hydro_propulsion_t.materials import default_material_atlas
from omega_aero_hydro_propulsion_t.mission import demo_air_mission
from omega_aero_hydro_propulsion_t.models import default_air, demo_rotor
from omega_aero_hydro_propulsion_t.multifidelity import (
    ResourceEnvelope,
    merge_shard_reports,
    plan_shards,
    run_multifidelity_campaign,
)
from omega_aero_hydro_propulsion_t.r04_oak import (
    permissive_r04_policy,
    relaxed_r04_constraints,
)
from omega_aero_hydro_propulsion_t.system_optimizer import InfiniteSystemFrontier


def main() -> None:
    campaign_id = "omega-propulsion-r04-example"
    rotor = demo_rotor()
    medium = default_air()
    mission = demo_air_mission()
    atlas = default_material_atlas()
    frontier = InfiniteSystemFrontier(namespace=f"{campaign_id}:frontier")
    manifests = plan_shards(
        campaign_id=campaign_id,
        start_index=0,
        count=6,
        shard_count=2,
    )
    reports = [
        run_multifidelity_campaign(
            rotor,
            medium,
            mission,
            campaign_id=campaign_id,
            start_index=manifest.start_index,
            count=manifest.count,
            resources=ResourceEnvelope(
                max_cost_units=1_000.0,
                checkpoint_interval=1,
                shard_count=2,
            ),
            frontier=frontier,
            atlas=atlas,
            constraints=relaxed_r04_constraints(),
            policy=permissive_r04_policy(),
        )
        for manifest in manifests
    ]
    merged = merge_shard_reports(reports, campaign_id=campaign_id)
    print(
        json.dumps(
            {
                "manifests": [item.to_dict() for item in manifests],
                "shards": [
                    {
                        "start_index": report.start_index,
                        "next_index": report.next_index,
                        "f0_count": report.f0_count,
                        "f1_count": report.f1_count,
                        "f2_count": report.f2_count,
                        "chain": report.final_chain_digest,
                    }
                    for report in reports
                ],
                "merged": merged.to_dict(),
                "epistemic_status": (
                    "computational evidence-depth demonstration only; "
                    "not CFD, experiment or certification"
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
