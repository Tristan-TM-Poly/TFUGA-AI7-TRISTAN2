from __future__ import annotations

import json

from omega_generator_discovery_t.campaign import CampaignSpec
from omega_generator_discovery_t.campaign_scale import (
    ScalePlanner,
    ValidationPolicy,
    resolve_target_records,
    validate_epoch_range,
)


def main() -> int:
    spec = CampaignSpec()
    target = resolve_target_records(spec, profile="hundred-million")
    plan = ScalePlanner(spec).plan(target)
    validation = validate_epoch_range(
        spec,
        0,
        start=0,
        stop=128,
        policy=ValidationPolicy(sample_ppm=1_000_000),
    )
    print(
        json.dumps(
            {
                "scale_plan": plan.to_dict(include_partitions=False),
                "validation_probe": validation.to_dict(),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
