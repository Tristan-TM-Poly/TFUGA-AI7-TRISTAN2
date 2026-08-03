"""Reversible addresses for the Ω-VLA logical frontier."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterator, Mapping

from .catalogs import CATALOG, Catalog


@dataclass(frozen=True)
class FrontierAddress:
    """One coordinate in the finite catalogs underlying the logical frontier."""

    layer: str
    program: str
    coordinates: tuple[tuple[str, str], ...]

    def as_mapping(self) -> dict[str, str]:
        return dict(self.coordinates)

    def canonical(self) -> str:
        coordinate_text = ";".join(f"{k}={v}" for k, v in self.coordinates)
        return f"layer={self.layer}|program={self.program}|{coordinate_text}"

    def digest(self) -> str:
        return sha256(self.canonical().encode("utf-8")).hexdigest()


class FrontierCodec:
    """Map integer indices to structured addresses without materializing them."""

    def __init__(self, catalog: Catalog = CATALOG) -> None:
        catalog.validate()
        self.catalog = catalog
        self.dimension_names = catalog.dimension_names()
        self.dimension_values = tuple(
            catalog.dimensions[name] for name in self.dimension_names
        )
        self.radices = tuple(len(values) for values in self.dimension_values)
        self._coordinate_size = 1
        for radix in self.radices:
            self._coordinate_size *= radix
        self._program_size = self._coordinate_size * len(catalog.programs)
        self.size = self._program_size * len(catalog.layers)

    def encode(self, address: FrontierAddress) -> int:
        try:
            layer_index = self.catalog.layers.index(address.layer)
            program_index = self.catalog.programs.index(address.program)
        except ValueError as exc:
            raise ValueError("unknown layer or program") from exc

        supplied = address.as_mapping()
        if tuple(supplied) != self.dimension_names:
            raise ValueError(
                "address dimensions must match canonical order: "
                + ", ".join(self.dimension_names)
            )

        coordinate_index = 0
        multiplier = 1
        for name, values, radix in reversed(
            tuple(zip(self.dimension_names, self.dimension_values, self.radices))
        ):
            try:
                value_index = values.index(supplied[name])
            except ValueError as exc:
                raise ValueError(f"unknown value {supplied[name]!r} for {name}") from exc
            coordinate_index += value_index * multiplier
            multiplier *= radix

        return (
            layer_index * self._program_size
            + program_index * self._coordinate_size
            + coordinate_index
        )

    def decode(self, index: int) -> FrontierAddress:
        if index < 0 or index >= self.size:
            raise IndexError(f"frontier index must be in [0, {self.size})")

        layer_index, remainder = divmod(index, self._program_size)
        program_index, coordinate_index = divmod(
            remainder, self._coordinate_size
        )

        coordinate_indices: list[int] = [0] * len(self.radices)
        value = coordinate_index
        for position in range(len(self.radices) - 1, -1, -1):
            value, coordinate_indices[position] = divmod(value, self.radices[position])

        coordinates = tuple(
            (name, values[value_index])
            for name, values, value_index in zip(
                self.dimension_names,
                self.dimension_values,
                coordinate_indices,
            )
        )
        return FrontierAddress(
            layer=self.catalog.layers[layer_index],
            program=self.catalog.programs[program_index],
            coordinates=coordinates,
        )

    def sample_indices(self, count: int, seed: int = 0) -> tuple[int, ...]:
        """Deterministic full-period-style sampling without replacement.

        The arithmetic progression uses a step coprime with the frontier size.
        This avoids allocating a permutation of a potentially enormous range.
        """

        if count < 0:
            raise ValueError("count cannot be negative")
        if count > self.size:
            raise ValueError("count cannot exceed logical frontier size")
        if count == 0:
            return ()

        start = int.from_bytes(
            sha256(f"start:{seed}".encode()).digest()[:8], "big"
        ) % self.size
        step = int.from_bytes(
            sha256(f"step:{seed}".encode()).digest()[:8], "big"
        ) % self.size
        step = max(step, 1)

        from math import gcd

        while gcd(step, self.size) != 1:
            step += 1
            if step >= self.size:
                step = 1

        return tuple((start + i * step) % self.size for i in range(count))

    def iter_sample(self, count: int, seed: int = 0) -> Iterator[FrontierAddress]:
        for index in self.sample_indices(count=count, seed=seed):
            yield self.decode(index)

    def address_from_mapping(
        self,
        layer: str,
        program: str,
        coordinates: Mapping[str, str],
    ) -> FrontierAddress:
        return FrontierAddress(
            layer=layer,
            program=program,
            coordinates=tuple(
                (name, coordinates[name]) for name in self.dimension_names
            ),
        )
