"""Small Omega Math Tristan lab demo.

Run with:

    python examples/omega_math_lab_demo.py

The demo avoids external dependencies and prints compact summaries.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sage_tristan.algebra_defect_lab import complex_numbers_as_real_algebra
from sage_tristan.hgfm_core import build_claim_test_graph
from sage_tristan.negative_memory import default_negative_memory_bank
from sage_tristan.prime_tensors import first_primes, residue_signature_by_index, summarize_prime_sample
from sage_tristan.omega_math_tristan import BayesTristanVector, action_score


def main() -> None:
    primes = first_primes(12)
    report = summarize_prime_sample(primes)
    print("PrimeTensor report:", report)
    print("Residue signature for p_8:", residue_signature_by_index(primes, 7))

    algebra = complex_numbers_as_real_algebra()
    x = (1.0, 2.0)
    y = (3.0, -1.0)
    print("Complex algebra defects:", algebra.defect_summary(x, y))

    graph = build_claim_test_graph("claim:ffwt-hac", "test:baseline", "result:pending", passed=True)
    print("HGFM centrality:", graph.centrality_proxy())
    print("HGFM fertility density:", graph.fertility_density())

    bank = default_negative_memory_bank()
    claim_text = "This experiment proves the method improves performance."
    print("Negative memory score:", bank.risk_score(claim_text))
    print("Replacement rules:", bank.replacement_rules_for(claim_text))

    vector = BayesTristanVector(
        probability=0.52,
        utility=0.90,
        fertility=0.95,
        testability=0.86,
        compressibility=0.72,
        risk=0.28,
        oak_maturity=0.30,
    )
    print("Bayes-Tristan action score:", round(action_score(vector), 4))


if __name__ == "__main__":
    main()
