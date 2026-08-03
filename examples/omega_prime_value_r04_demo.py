from __future__ import annotations

import json

from omega_prime_value_t.r04.benchmark import deterministic_benchmark


if __name__ == "__main__":
    print(json.dumps(deterministic_benchmark(), indent=2, sort_keys=True))
