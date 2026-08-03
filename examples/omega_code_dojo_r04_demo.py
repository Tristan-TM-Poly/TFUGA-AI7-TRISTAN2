from __future__ import annotations

import json

from omega_code_dojo_t.r04.benchmark import run_r04_benchmark


if __name__ == "__main__":
    print(json.dumps(run_r04_benchmark(4096), indent=2, sort_keys=True))
