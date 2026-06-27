"""Small, auditable Hamming(7,4) code for Ω-ECC-T MVP."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


def _bits4(data: Sequence[int]) -> List[int]:
    out = [int(b) for b in data]
    if len(out) != 4 or any(b not in (0, 1) for b in out):
        raise ValueError("Hamming(7,4) expects exactly four 0/1 data bits")
    return out


def _bits7(codeword: Sequence[int]) -> List[int]:
    out = [int(b) for b in codeword]
    if len(out) != 7 or any(b not in (0, 1) for b in out):
        raise ValueError("Hamming(7,4) expects exactly seven 0/1 code bits")
    return out


# Positions are 1-indexed in the comments: p1 p2 d1 p4 d2 d3 d4.
def encode(data_bits: Sequence[int]) -> List[int]:
    """Encode four bits into a Hamming(7,4) codeword."""
    d1, d2, d3, d4 = _bits4(data_bits)
    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p4 = d2 ^ d3 ^ d4
    return [p1, p2, d1, p4, d2, d3, d4]


def syndrome(codeword: Sequence[int]) -> Tuple[int, int, int]:
    """Return the three Hamming parity checks as (s1, s2, s4)."""
    c = _bits7(codeword)
    s1 = c[0] ^ c[2] ^ c[4] ^ c[6]
    s2 = c[1] ^ c[2] ^ c[5] ^ c[6]
    s4 = c[3] ^ c[4] ^ c[5] ^ c[6]
    return (s1, s2, s4)


def syndrome_index(s: Tuple[int, int, int]) -> int:
    """Return the 1-indexed bit position indicated by the syndrome, or 0."""
    s1, s2, s4 = s
    return s1 + 2 * s2 + 4 * s4


@dataclass(frozen=True)
class DecodeResult:
    data_bits: List[int]
    corrected_codeword: List[int]
    syndrome: Tuple[int, int, int]
    corrected_position: int
    status: str
    oak_trust: float

    @property
    def corrected(self) -> bool:
        return self.corrected_position != 0


def decode(received: Sequence[int]) -> DecodeResult:
    """Decode and correct up to one bit error.

    OAK-safe limit: Hamming(7,4) corrects one bit. Two or more errors may be
    miscorrected, so the result includes a trust flag rather than a proof.
    """
    c = _bits7(received)
    s = syndrome(c)
    pos = syndrome_index(s)
    corrected = list(c)
    status = "clean"
    trust = 1.0
    if pos:
        corrected[pos - 1] ^= 1
        status = "corrected_single_bit_candidate"
        trust = 0.90
    if syndrome(corrected) != (0, 0, 0):
        status = "uncorrectable_residual_syndrome"
        trust = 0.0
    data = [corrected[2], corrected[4], corrected[5], corrected[6]]
    return DecodeResult(data, corrected, s, pos, status, trust)


def all_codewords() -> Dict[Tuple[int, int, int, int], List[int]]:
    """Enumerate the 16 codewords, useful for exhaustive OAK checks."""
    return {
        (a, b, c, d): encode([a, b, c, d])
        for a in (0, 1)
        for b in (0, 1)
        for c in (0, 1)
        for d in (0, 1)
    }
