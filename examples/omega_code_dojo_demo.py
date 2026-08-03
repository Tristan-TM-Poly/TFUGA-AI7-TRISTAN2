from __future__ import annotations

import json

from omega_code_dojo_t import run_oak_benchmark


if __name__ == "__main__":
    print(json.dumps(run_oak_benchmark(), indent=2, sort_keys=True))
