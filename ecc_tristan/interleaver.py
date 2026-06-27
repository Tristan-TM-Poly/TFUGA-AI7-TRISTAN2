"""Interleaving utilities for burst-error mitigation.

Interleavers do not create information. They spread burst errors across multiple
codewords so small component codes can sometimes correct them independently.
"""
from __future__ import annotations

from typing import List, Sequence


def _validate_bits(bits: Sequence[int]) -> List[int]:
    out = [int(x) for x in bits]
    if any(x not in (0, 1) for x in out):
        raise ValueError("bits must be binary")
    return out


def block_interleaver_permutation(length: int, depth: int) -> List[int]:
    """Return source indices read column-wise from a row-wise block.

    Example for ``length=6, depth=2``:

    ```text
    rows = [[0, 1, 2], [3, 4, 5]]
    order = [0, 3, 1, 4, 2, 5]
    ```
    """
    if length < 0:
        raise ValueError("length must be non-negative")
    if depth <= 0:
        raise ValueError("depth must be positive")
    if length == 0:
        return []
    width = (length + depth - 1) // depth
    order: List[int] = []
    for col in range(width):
        for row in range(depth):
            idx = row * width + col
            if idx < length:
                order.append(idx)
    return order


def apply_permutation(values: Sequence[int], order: Sequence[int]) -> List[int]:
    source = _validate_bits(values)
    indices = [int(x) for x in order]
    if sorted(indices) != list(range(len(source))):
        raise ValueError("order must be a full permutation")
    return [source[idx] for idx in indices]


def invert_permutation(order: Sequence[int]) -> List[int]:
    indices = [int(x) for x in order]
    if sorted(indices) != list(range(len(indices))):
        raise ValueError("order must be a full permutation")
    inverse = [0] * len(indices)
    for out_idx, src_idx in enumerate(indices):
        inverse[src_idx] = out_idx
    return inverse


def block_interleave(bits: Sequence[int], depth: int) -> List[int]:
    source = _validate_bits(bits)
    return apply_permutation(source, block_interleaver_permutation(len(source), depth))


def block_deinterleave(bits: Sequence[int], depth: int) -> List[int]:
    source = _validate_bits(bits)
    order = block_interleaver_permutation(len(source), depth)
    inverse = invert_permutation(order)
    return apply_permutation(source, inverse)
