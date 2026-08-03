from __future__ import annotations

from dataclasses import dataclass

from .arithmetic import factor_out_twos, gcd, jacobi


@dataclass(frozen=True, slots=True)
class ProthProof:
    n: int
    k: int
    exponent: int
    witness: int
    residue: int
    theorem: str = "Proth"

    def to_dict(self) -> dict[str, int | str]:
        return {
            "method": self.theorem,
            "n": self.n,
            "k": self.k,
            "exponent": self.exponent,
            "witness": self.witness,
            "residue": self.residue,
            "criterion": "a^((N-1)/2) mod N == N-1",
        }


def proth_parameters(value: int) -> tuple[int, int] | None:
    if value <= 2 or value % 2 == 0:
        return None
    k, exponent = factor_out_twos(value - 1)
    if k % 2 == 0 or k >= 2**exponent:
        return None
    return k, exponent


def prove_proth(value: int, max_witness: int = 10_000) -> ProthProof | None:
    parameters = proth_parameters(value)
    if parameters is None:
        return None
    k, exponent = parameters
    for witness in range(2, max_witness + 1):
        if gcd(witness, value) != 1:
            continue
        if jacobi(witness, value) != -1:
            continue
        residue = pow(witness, (value - 1) // 2, value)
        if residue == value - 1:
            return ProthProof(value, k, exponent, witness, residue)
    return None


def verify_proth_proof(proof: dict[str, int | str]) -> bool:
    try:
        value = int(proof["n"])
        witness = int(proof["witness"])
        k = int(proof["k"])
        exponent = int(proof["exponent"])
    except (KeyError, TypeError, ValueError):
        return False
    if value != k * (2**exponent) + 1:
        return False
    if k <= 0 or k % 2 == 0 or k >= 2**exponent:
        return False
    return pow(witness, (value - 1) // 2, value) == value - 1
