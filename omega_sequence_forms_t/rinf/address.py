"""Logical research-space addressing and deterministic traversal."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import islice
import math
from typing import Iterable, Iterator, Sequence

from .models import CellAddress


DEFAULT_AXIS_SIZES: tuple[int, int, int, int, int] = (256, 512, 128, 64, 32)
AXIS_NAMES: tuple[str, ...] = ("family", "transformation", "validator", "regime", "domain")


@dataclass(frozen=True)
class CellSpace:
    family_count: int = DEFAULT_AXIS_SIZES[0]
    transformation_count: int = DEFAULT_AXIS_SIZES[1]
    validator_count: int = DEFAULT_AXIS_SIZES[2]
    regime_count: int = DEFAULT_AXIS_SIZES[3]
    domain_count: int = DEFAULT_AXIS_SIZES[4]

    def __post_init__(self) -> None:
        if any(value <= 0 for value in self.shape):
            raise ValueError("all cell-space dimensions must be positive")

    @property
    def shape(self) -> tuple[int, int, int, int, int]:
        return (
            self.family_count,
            self.transformation_count,
            self.validator_count,
            self.regime_count,
            self.domain_count,
        )

    @property
    def logical_cells(self) -> int:
        return math.prod(self.shape)

    def contains(self, address: CellAddress) -> bool:
        return all(
            0 <= value < size
            for value, size in zip(address.as_mapping().values(), self.shape)
        )

    def flatten(self, address: CellAddress) -> int:
        if not self.contains(address):
            raise IndexError(f"address outside cell space: {address.render()}")
        result = 0
        for value, size in zip(address.as_mapping().values(), self.shape):
            result = result * size + value
        return result

    def unflatten(self, index: int) -> CellAddress:
        if not 0 <= index < self.logical_cells:
            raise IndexError(f"flat cell index outside [0,{self.logical_cells})")
        values = [0] * len(self.shape)
        remaining = index
        for position in range(len(self.shape) - 1, -1, -1):
            size = self.shape[position]
            values[position] = remaining % size
            remaining //= size
        return CellAddress(*values)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": "omega-sequence-forms-cell-space/1",
            "axes": dict(zip(AXIS_NAMES, self.shape)),
            "logical_cells": self.logical_cells,
            "permanent_total_cap": None,
        }


class FeistelPermutation:
    """Cycle-walk permutation for deterministic pseudo-random cell traversal.

    It avoids allocating a list proportional to the 34-billion-cell logical
    space.  The permutation is deterministic for a seed and supports random
    access to any traversal position.
    """

    def __init__(self, size: int, seed: int, rounds: int = 6) -> None:
        if size <= 0:
            raise ValueError("size must be positive")
        if rounds < 2:
            raise ValueError("at least two Feistel rounds are required")
        self.size = size
        self.seed = seed
        self.rounds = rounds
        bits = max(2, (size - 1).bit_length())
        if bits % 2:
            bits += 1
        self.bits = bits
        self.half_bits = bits // 2
        self.mask = (1 << self.half_bits) - 1
        self.domain_size = 1 << bits

    def _round(self, right: int, round_index: int) -> int:
        payload = f"{self.seed}:{round_index}:{right}".encode("ascii")
        digest = sha256(payload).digest()
        return int.from_bytes(digest[:8], "big") & self.mask

    def _permute_domain(self, value: int) -> int:
        left = (value >> self.half_bits) & self.mask
        right = value & self.mask
        for round_index in range(self.rounds):
            left, right = right, left ^ self._round(right, round_index)
        return ((left & self.mask) << self.half_bits) | (right & self.mask)

    def permute(self, value: int) -> int:
        if not 0 <= value < self.size:
            raise IndexError("permutation input outside logical range")
        candidate = value
        while True:
            candidate = self._permute_domain(candidate)
            if candidate < self.size:
                return candidate


@dataclass(frozen=True)
class TraversalSlice:
    start: int = 0
    stop: int | None = None
    stride: int = 1

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError("start must be non-negative")
        if self.stop is not None and self.stop < self.start:
            raise ValueError("stop must not precede start")
        if self.stride <= 0:
            raise ValueError("stride must be positive")


def iter_addresses(
    *,
    space: CellSpace | None = None,
    seed: int = 0,
    traversal: TraversalSlice | None = None,
) -> Iterator[CellAddress]:
    space = space or CellSpace()
    traversal = traversal or TraversalSlice()
    permutation = FeistelPermutation(space.logical_cells, seed)
    stop = space.logical_cells if traversal.stop is None else min(traversal.stop, space.logical_cells)
    for position in range(traversal.start, stop, traversal.stride):
        yield space.unflatten(permutation.permute(position))


def sample_addresses(count: int, *, seed: int = 0, space: CellSpace | None = None) -> tuple[CellAddress, ...]:
    if count < 0:
        raise ValueError("count must be non-negative")
    space = space or CellSpace()
    return tuple(islice(iter_addresses(space=space, seed=seed), min(count, space.logical_cells)))


def shard_for(address: CellAddress, shard_count: int, *, space: CellSpace | None = None) -> int:
    if shard_count <= 0:
        raise ValueError("shard_count must be positive")
    space = space or CellSpace()
    flat = space.flatten(address)
    digest = sha256(str(flat).encode("ascii")).digest()
    return int.from_bytes(digest[:8], "big") % shard_count


def partition_addresses(
    addresses: Iterable[CellAddress],
    shard_count: int,
    *,
    space: CellSpace | None = None,
) -> tuple[list[CellAddress], ...]:
    shards = tuple([] for _ in range(shard_count))
    for address in addresses:
        shards[shard_for(address, shard_count, space=space)].append(address)
    return shards


def cell_space_receipt(space: CellSpace | None = None) -> dict[str, object]:
    space = space or CellSpace()
    payload = space.canonical_payload()
    payload.update(
        {
            "default_expected_cells": 34_359_738_368,
            "matches_default": space.logical_cells == 34_359_738_368,
            "address_roundtrip_samples": [
                {
                    "flat": index,
                    "address": space.unflatten(index).render(),
                    "roundtrip": space.flatten(space.unflatten(index)),
                }
                for index in sorted({0, 1, space.logical_cells // 2, space.logical_cells - 1})
            ],
        }
    )
    return payload
