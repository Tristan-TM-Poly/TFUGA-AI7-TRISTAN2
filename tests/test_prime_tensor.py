from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PRIME_TENSOR = ROOT / "experiments" / "prime_tensor"
if str(PRIME_TENSOR) not in sys.path:
    sys.path.insert(0, str(PRIME_TENSOR))

from prime_tensor import (
    first_primes,
    gap_tensor_rows,
    oak_report,
    prime_tensor,
    reconstruct_from_signature,
)


def test_prime_tensor_reconstructs_primes_in_crt_scope():
    signatures = prime_tensor(16)

    for signature in signatures:
        reconstructed = reconstruct_from_signature(signature)
        if signature.index_1based >= 4:
            assert reconstructed == signature.prime
            assert 0 < signature.prime < signature.primorial_modulus


def test_first_primes_are_deterministic():
    assert first_primes(12) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]


def test_gap_tensor_residue_consistency():
    primes = first_primes(10)
    rows = gap_tensor_rows(primes, max_step=2)

    assert rows
    for row in rows:
        assert row["gap"] == row["future_prime"] - row["prime"]
        assert row["residues"] == [row["gap"] % modulus for modulus in row["moduli"]]


def test_oak_report_keeps_prime_tensor_guardrails():
    report = oak_report(16)

    assert report["status"] == "PROVED_LOCAL"
    assert report["failures"] == []
    guardrails = "\n".join(report["guardrails"])
    assert "No claim is made about Riemann" in guardrails
    assert "Statistical usefulness requires" in guardrails
