"""Structural DNA fingerprints for finite, explicit feature signatures."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable, Mapping


def _canonical(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(str(value) for value in values)))


@dataclass(frozen=True)
class StructuralDNA:
    symmetries: tuple[str, ...] = ()
    invariants: tuple[str, ...] = ()
    defects: tuple[str, ...] = ()
    factorizations: tuple[str, ...] = ()
    dimensions: tuple[str, ...] = ()
    duals: tuple[str, ...] = ()
    limits: tuple[str, ...] = ()
    representations: tuple[str, ...] = ()
    obstructions: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, data: Mapping[str, Iterable[str]]) -> "StructuralDNA":
        allowed = cls.__dataclass_fields__
        unknown = set(data) - set(allowed)
        if unknown:
            raise ValueError(f"unknown StructuralDNA fields: {sorted(unknown)}")
        return cls(**{key: _canonical(values) for key, values in data.items()})

    def as_mapping(self) -> dict[str, tuple[str, ...]]:
        return {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
        }

    def digest(self) -> str:
        payload = json.dumps(self.as_mapping(), sort_keys=True, ensure_ascii=False)
        return sha256(payload.encode("utf-8")).hexdigest()

    def collision(self, other: "StructuralDNA") -> bool:
        return self == other

    def jaccard_distance(self, other: "StructuralDNA") -> float:
        left = {
            (field, value)
            for field, values in self.as_mapping().items()
            for value in values
        }
        right = {
            (field, value)
            for field, values in other.as_mapping().items()
            for value in values
        }
        union = left | right
        if not union:
            return 0.0
        return 1.0 - len(left & right) / len(union)

    def differing_fields(self, other: "StructuralDNA") -> tuple[str, ...]:
        return tuple(
            field
            for field in self.__dataclass_fields__
            if getattr(self, field) != getattr(other, field)
        )
