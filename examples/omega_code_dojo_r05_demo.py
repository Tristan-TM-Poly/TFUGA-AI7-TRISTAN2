from __future__ import annotations

import json

from omega_code_dojo_t.r05 import run_r05_benchmark


if __name__ == "__main__":
    print(json.dumps(run_r05_benchmark(), indent=2, sort_keys=True))
