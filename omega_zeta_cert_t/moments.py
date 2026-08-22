from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable, Sequence

from .model import MomentTensorSpec, MomentWordMode


def rotate_word(word: tuple[int, ...], shift: int) -> tuple[int, ...]:
    if not word:
        return word
    shift %= len(word)
    return word[shift:] + word[:shift]


def canonical_cyclic_word(word: Sequence[int]) -> tuple[int, ...]:
    item = tuple(int(x) for x in word)
    if not item:
        raise ValueError("word must be non-empty")
    return min(rotate_word(item, shift) for shift in range(len(item)))


def cyclic_word_representatives(alphabet_size: int, word_length: int) -> tuple[tuple[int, ...], ...]:
    if alphabet_size < 1 or word_length < 1:
        raise ValueError("alphabet_size and word_length must be positive")
    representatives = {
        canonical_cyclic_word(word)
        for word in product(range(alphabet_size), repeat=word_length)
    }
    return tuple(sorted(representatives))


def moment_coordinate_labels(spec: MomentTensorSpec) -> tuple[str, ...]:
    """Materialize deterministic labels for modest research specifications.

    The count can be computed without materializing all words. This function is
    intended for bounded audit fixtures and fails explicitly if the requested
    representation would create more than one million labels.
    """
    spec.validate()
    total = spec.observable_count
    if total > 1_000_000:
        raise ValueError("label materialization exceeds bounded audit-fixture budget")

    labels: list[str] = []
    for order in range(1, spec.max_order + 1):
        mode = spec.word_mode
        if not spec.include_cross_moments or mode is MomentWordMode.DIAGONAL:
            labels.extend(f"M{order}[{i}]" for i in range(spec.window_count))
        elif mode is MomentWordMode.SYMMETRIC:
            for word in _nondecreasing_words(spec.window_count, order):
                labels.append(_label(order, word, "sym"))
        elif mode is MomentWordMode.CYCLIC:
            for word in cyclic_word_representatives(spec.window_count, order):
                labels.append(_label(order, word, "cyc"))
        elif mode is MomentWordMode.FULL:
            for word in product(range(spec.window_count), repeat=order):
                labels.append(_label(order, word, "full"))
        else:
            raise AssertionError(f"unsupported word mode {mode}")
    return tuple(labels)


def _nondecreasing_words(alphabet_size: int, word_length: int) -> Iterable[tuple[int, ...]]:
    def rec(prefix: tuple[int, ...], minimum: int) -> Iterable[tuple[int, ...]]:
        if len(prefix) == word_length:
            yield prefix
            return
        for value in range(minimum, alphabet_size):
            yield from rec(prefix + (value,), value)
    return rec((), 0)


def _label(order: int, word: Sequence[int], kind: str) -> str:
    return f"M{order}:{kind}[" + ",".join(map(str, word)) + "]"


Matrix = tuple[tuple[int, ...], ...]


def matmul(a: Matrix, b: Matrix) -> Matrix:
    if not a or not b or len(a[0]) != len(b):
        raise ValueError("incompatible matrices")
    rows = len(a)
    cols = len(b[0])
    inner = len(b)
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(inner)) for j in range(cols))
        for i in range(rows)
    )


def matrix_trace(a: Matrix) -> int:
    if not a or any(len(row) != len(a) for row in a):
        raise ValueError("trace requires a square matrix")
    return sum(a[i][i] for i in range(len(a)))


@dataclass(frozen=True)
class TraceWordCountermodel:
    tr_abc: int
    tr_bca: int
    tr_cab: int
    tr_acb: int
    cyclic_invariance_holds: bool
    arbitrary_permutation_invariance_fails: bool
    proof_claimed: bool = False

    def to_dict(self) -> dict:
        return {
            "tr_abc": self.tr_abc,
            "tr_bca": self.tr_bca,
            "tr_cab": self.tr_cab,
            "tr_acb": self.tr_acb,
            "cyclic_invariance_holds": self.cyclic_invariance_holds,
            "arbitrary_permutation_invariance_fails": self.arbitrary_permutation_invariance_fails,
            "proof_claimed": self.proof_claimed,
        }


def noncommutative_trace_countermodel() -> TraceWordCountermodel:
    """Exact 2x2 countermodel to unjustified full symmetrization.

    A=E12, B=E21, C=E11 gives
      tr(ABC)=tr(BCA)=tr(CAB)=1,
      tr(ACB)=0.
    Thus cyclic trace invariance survives while arbitrary permutation
    invariance fails.
    """
    a: Matrix = ((0, 1), (0, 0))
    b: Matrix = ((0, 0), (1, 0))
    c: Matrix = ((1, 0), (0, 0))

    def tr3(x: Matrix, y: Matrix, z: Matrix) -> int:
        return matrix_trace(matmul(matmul(x, y), z))

    tr_abc = tr3(a, b, c)
    tr_bca = tr3(b, c, a)
    tr_cab = tr3(c, a, b)
    tr_acb = tr3(a, c, b)
    return TraceWordCountermodel(
        tr_abc=tr_abc,
        tr_bca=tr_bca,
        tr_cab=tr_cab,
        tr_acb=tr_acb,
        cyclic_invariance_holds=(tr_abc == tr_bca == tr_cab),
        arbitrary_permutation_invariance_fails=(tr_acb != tr_abc),
    )
