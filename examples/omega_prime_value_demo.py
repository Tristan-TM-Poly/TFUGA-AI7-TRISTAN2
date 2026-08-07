from __future__ import annotations

import json

from omega_prime_value_t.campaign import PrimeCampaign, SearchPolicy


if __name__ == "__main__":
    report = PrimeCampaign(
        SearchPolicy(exponent=23, k_min=1, k_max=255, max_results=5)
    ).run()
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
