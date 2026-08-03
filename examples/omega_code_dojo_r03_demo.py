from __future__ import annotations

import json

from omega_code_dojo_t.r03.benchmark import run_r03_benchmark


if __name__ == "__main__":
    print(json.dumps(run_r03_benchmark(), indent=2, sort_keys=True))
