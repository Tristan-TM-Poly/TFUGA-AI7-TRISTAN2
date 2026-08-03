from __future__ import annotations

import json

from omega_prime_value_t.r03.benchmark import build_benchmark


if __name__ == "__main__":
    print(json.dumps(build_benchmark(), indent=2, sort_keys=True))
