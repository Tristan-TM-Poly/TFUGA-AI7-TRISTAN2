"""Demo for the finite prime tensor packet.

Run from the repository root:

    python examples/prime_tensor_demo.py

This prints a compact JSON packet containing primes, primorial digits,
residues, gap tensors, modular gap tensors, OAK status, and motif hyperedges.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sage_tristan.prime_tensors import finite_prime_tensor_packet


def main() -> int:
    packet = finite_prime_tensor_packet(count=12, max_jump=2)
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
