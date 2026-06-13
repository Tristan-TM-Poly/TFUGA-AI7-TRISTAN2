"""Demo for the finite prime tensor packet.

Run from the repository root:

    python examples/prime_tensor_demo.py

This prints a compact JSON packet containing primes, primorial digits,
residues, gap tensors, modular gap tensors, OAK status, and motif hyperedges.
"""

from __future__ import annotations

import json

from sage_tristan.prime_tensors import finite_prime_tensor_packet


def main() -> int:
    packet = finite_prime_tensor_packet(count=12, max_jump=2)
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
