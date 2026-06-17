"""Run the Omega-FFWT-HAC-CVCD MVP benchmark.

Usage:
    python examples/omega_ffwt_demo.py
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sage_tristan.omega_ffwt import run_minimal_benchmark


if __name__ == "__main__":
    result = run_minimal_benchmark(length=64, seed=7)
    print(json.dumps(result, indent=2, sort_keys=True))
