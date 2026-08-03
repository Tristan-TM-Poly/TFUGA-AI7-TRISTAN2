from __future__ import annotations

import json

from omega_code_dojo_t.r02.benchmark import run_r02_benchmark


if __name__ == "__main__":
    print(json.dumps(run_r02_benchmark(16), indent=2, sort_keys=True))
