"""Plan the default 1,179,648-record Ω generator campaign."""
from __future__ import annotations

import json

from omega_generator_discovery_t.campaign import CampaignSpec, partition_campaign


spec = CampaignSpec()
partitions = partition_campaign(spec, 64)
print(
    json.dumps(
        {
            **spec.manifest(),
            "partition_count": len(partitions),
            "first_partition": partitions[0].to_dict(),
            "last_partition": partitions[-1].to_dict(),
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
)
