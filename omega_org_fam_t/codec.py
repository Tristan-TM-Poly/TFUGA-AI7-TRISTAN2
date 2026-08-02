"""Constant-memory mixed-radix addressing for billions of family cells."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .registry import OrganicRegistry

@dataclass(frozen=True, slots=True)
class DecodedAddress:
    index: int
    coordinate: dict[str, str]

class MixedRadixCodec:
    def __init__(self, registry: OrganicRegistry):
        self.registry = registry
        self.radices = registry.radices
        self._positions = {axis.name: {value: i for i, value in enumerate(axis.values)} for axis in registry.axes}

    def decode(self, index: int) -> DecodedAddress:
        if not 0 <= index < self.registry.family_space_size:
            raise IndexError(f"index {index} outside [0,{self.registry.family_space_size})")
        remainder = index
        digits = [0] * len(self.radices)
        for position in range(len(self.radices)-1, -1, -1):
            remainder, digits[position] = divmod(remainder, self.radices[position])
        coordinate = {axis.name: axis.values[digit] for axis, digit in zip(self.registry.axes, digits)}
        return DecodedAddress(index=index, coordinate=coordinate)

    def encode(self, coordinate: Mapping[str, str]) -> int:
        index = 0
        for axis, radix in zip(self.registry.axes, self.radices):
            try:
                digit = self._positions[axis.name][coordinate[axis.name]]
            except KeyError as exc:
                raise ValueError(f"unknown or missing value for axis {axis.name}") from exc
            index = index * radix + digit
        return index

    def compact_id(self, index: int) -> str:
        if not 0 <= index < self.registry.family_space_size:
            raise IndexError(index)
        return f"ORG2-FAM-{index:09X}"
