"""Reversible mixed-radix frontier for identity candidates."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import gcd
from typing import Iterator

from .catalog import SCHEMAS
from .models import IdentityAddress

DIMENSIONS = tuple(range(2, 18))
SCALAR_SYSTEMS = ("real", "complex")
MATRIX_FAMILIES = (
    "dense", "diagonal", "symmetric", "hermitian", "orthogonal", "unitary",
    "projection", "involution", "singular", "ill_conditioned", "nilpotent",
    "jordan", "commuting", "noncommuting",
)
MUTATION_POLICIES = (
    "none", "drop_one", "drop_all", "strengthen_normal", "strengthen_invertible",
    "strengthen_hermitian", "swap_adjoint_transpose", "reverse_operands",
)
TRIAL_PROFILES = ("smoke", "standard", "deep", "adversarial", "sparse", "spectral")


@dataclass(frozen=True)
class FrontierManifest:
    schemas: int
    dimensions: int
    scalar_systems: int
    matrix_families: int
    mutation_policies: int
    trial_profiles: int
    logical_candidates: int
    permanent_total_cap: None = None
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


class IdentityFrontierCodec:
    """Bijective finite-address codec with O(1)-memory deterministic traversal."""

    def __init__(self) -> None:
        self.schema_ids = tuple(schema.schema_id for schema in SCHEMAS)
        self.axes = (
            self.schema_ids,
            DIMENSIONS,
            SCALAR_SYSTEMS,
            MATRIX_FAMILIES,
            MUTATION_POLICIES,
            TRIAL_PROFILES,
        )
        self.radices = tuple(len(axis) for axis in self.axes)
        size = 1
        for radix in self.radices:
            size *= radix
        self.size = size

    def decode(self, index: int) -> IdentityAddress:
        if index < 0 or index >= self.size:
            raise IndexError(f"identity frontier index must be in [0, {self.size})")
        coordinates = [0] * len(self.radices)
        value = index
        for position in range(len(self.radices) - 1, -1, -1):
            value, coordinates[position] = divmod(value, self.radices[position])
        return IdentityAddress(
            schema_id=self.schema_ids[coordinates[0]],
            dimension=DIMENSIONS[coordinates[1]],
            scalar_system=SCALAR_SYSTEMS[coordinates[2]],
            matrix_family=MATRIX_FAMILIES[coordinates[3]],
            mutation_policy=MUTATION_POLICIES[coordinates[4]],
            trial_profile=TRIAL_PROFILES[coordinates[5]],
        )

    def encode(self, address: IdentityAddress) -> int:
        values = (
            address.schema_id, address.dimension, address.scalar_system,
            address.matrix_family, address.mutation_policy, address.trial_profile,
        )
        coordinate_indices: list[int] = []
        for axis, value in zip(self.axes, values):
            try:
                coordinate_indices.append(axis.index(value))
            except ValueError as exc:
                raise ValueError(f"unknown identity-frontier coordinate {value!r}") from exc
        index = 0
        for coordinate, radix in zip(coordinate_indices, self.radices):
            index = index * radix + coordinate
        return index

    def _walk(self, seed: int) -> tuple[int, int]:
        start = int.from_bytes(sha256(f"identity-start:{seed}".encode()).digest()[:8], "big")
        step = int.from_bytes(sha256(f"identity-step:{seed}".encode()).digest()[:8], "big")
        start %= self.size
        step = max(step % self.size, 1)
        while gcd(step, self.size) != 1:
            step += 1
            if step >= self.size:
                step = 1
        return start, step

    def iter_indices(self, count: int, *, seed: int = 0, start_offset: int = 0) -> Iterator[int]:
        if count < 0 or start_offset < 0:
            raise ValueError("count and start_offset must be nonnegative")
        if count + start_offset > self.size:
            raise ValueError("requested window exceeds logical frontier")
        start, step = self._walk(seed)
        for offset in range(start_offset, start_offset + count):
            yield (start + step * offset) % self.size

    def iter_addresses(self, count: int, *, seed: int = 0, start_offset: int = 0) -> Iterator[IdentityAddress]:
        for index in self.iter_indices(count, seed=seed, start_offset=start_offset):
            yield self.decode(index)

    def manifest(self) -> FrontierManifest:
        return FrontierManifest(
            schemas=len(self.schema_ids),
            dimensions=len(DIMENSIONS),
            scalar_systems=len(SCALAR_SYSTEMS),
            matrix_families=len(MATRIX_FAMILIES),
            mutation_policies=len(MUTATION_POLICIES),
            trial_profiles=len(TRIAL_PROFILES),
            logical_candidates=self.size,
        )
