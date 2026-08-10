from __future__ import annotations

import json

from omega_neuro_t.benchmark import run_p1_benchmark


if __name__ == "__main__":
    print(json.dumps(run_p1_benchmark(), indent=2, sort_keys=True))
