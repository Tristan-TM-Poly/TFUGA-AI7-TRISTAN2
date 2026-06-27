"""Small binary linear block codes for Ω-ECC-T.

This module adds an actual encodable code object from generator or parity-check
matrices. Decoding is exhaustive maximum-likelihood over all codewords, so it is
excellent for OAK baselines and small tests, not for large production codes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .gf2 import (
    all_binary_vectors,
    hamming_distance,
    hamming_weight,
    mat_vec_mul_mod2,
    nullspace_mod2,
    rank_mod2,
    transpose,
    validate_bits,
    validate_matrix,
    vec_mat_mul_mod2,
)


@dataclass(frozen=True)
class MLDecodeResult:
    message: List[int]
    codeword: List[int]
    distance: int
    syndrome: List[int]
    candidates_checked: int
    status: str


class LinearBlockCode:
    """Binary linear block code over GF(2)."""

    def __init__(
        self,
        generator_matrix: Sequence[Sequence[int]],
        parity_check_matrix: Optional[Sequence[Sequence[int]]] = None,
        name: str = "LinearBlockCode",
    ) -> None:
        self.generator_matrix = validate_matrix(generator_matrix, "generator_matrix")
        self.k = len(self.generator_matrix)
        self.n = len(self.generator_matrix[0])
        if rank_mod2(self.generator_matrix) != self.k:
            raise ValueError("generator_matrix rows must be linearly independent")
        self.parity_check_matrix = (
            validate_matrix(parity_check_matrix, "parity_check_matrix")
            if parity_check_matrix is not None
            else nullspace_mod2(transpose(self.generator_matrix))
        )
        if self.parity_check_matrix and len(self.parity_check_matrix[0]) != self.n:
            raise ValueError("parity_check_matrix width must match code length")
        expected_zero = [0] * len(self.parity_check_matrix)
        for row in self.generator_matrix:
            if self.syndrome(row) != expected_zero:
                raise ValueError("generator rows must satisfy parity checks")
        self.name = name

    @classmethod
    def from_parity_checks(
        cls, parity_checks: Sequence[Sequence[int]], name: str = "LinearBlockCode"
    ) -> "LinearBlockCode":
        H = validate_matrix(parity_checks, "parity_checks")
        generator = nullspace_mod2(H)
        if not generator:
            raise ValueError("parity checks define only the zero codeword")
        return cls(generator, parity_check_matrix=H, name=name)

    @classmethod
    def toy_6_3(cls) -> "LinearBlockCode":
        return cls.from_parity_checks(
            [
                [1, 1, 0, 1, 0, 0],
                [0, 1, 1, 0, 1, 0],
                [1, 0, 1, 0, 0, 1],
            ],
            name="toy_6_3_linear_code",
        )

    def encode(self, message: Sequence[int]) -> List[int]:
        m = validate_bits(message, self.k, "message")
        return vec_mat_mul_mod2(m, self.generator_matrix)

    def syndrome(self, word: Sequence[int]) -> List[int]:
        if not self.parity_check_matrix:
            return []
        w = validate_bits(word, self.n, "word")
        return mat_vec_mul_mod2(self.parity_check_matrix, w)

    def is_codeword(self, word: Sequence[int]) -> bool:
        return not any(self.syndrome(word))

    def enumerate_messages(self) -> List[List[int]]:
        return list(all_binary_vectors(self.k))

    def enumerate_codewords(self) -> List[List[int]]:
        return [self.encode(message) for message in self.enumerate_messages()]

    def minimum_distance(self) -> int:
        nonzero_weights = [
            hamming_weight(codeword)
            for codeword in self.enumerate_codewords()
            if any(codeword)
        ]
        return min(nonzero_weights) if nonzero_weights else 0

    def rate(self) -> float:
        return self.k / self.n

    def nearest_decode(self, received: Sequence[int]) -> MLDecodeResult:
        r = validate_bits(received, self.n, "received")
        best_message: List[int] | None = None
        best_codeword: List[int] | None = None
        best_distance: int | None = None
        ties = 0
        checked = 0
        for message in self.enumerate_messages():
            codeword = self.encode(message)
            distance = hamming_distance(codeword, r)
            checked += 1
            if best_distance is None or distance < best_distance:
                best_message = message
                best_codeword = codeword
                best_distance = distance
                ties = 1
            elif distance == best_distance:
                ties += 1
        assert best_message is not None and best_codeword is not None and best_distance is not None
        status = "nearest_unique" if ties == 1 else "nearest_tie_oak_uncertain"
        return MLDecodeResult(
            message=best_message,
            codeword=best_codeword,
            distance=best_distance,
            syndrome=self.syndrome(r),
            candidates_checked=checked,
            status=status,
        )
