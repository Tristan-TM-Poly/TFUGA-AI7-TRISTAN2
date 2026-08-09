"""Dimension Spectrum: keep multiple declared dimension functors separate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class DimensionFunctional:
    name: str
    compute: Callable[[Any], float]
    domain: str

    def __call__(self, obj: Any) -> float:
        value = float(self.compute(obj))
        if value < 0:
            raise ValueError(f"{self.name} returned a negative dimension")
        return value


@dataclass(frozen=True)
class DimensionSpectrum:
    values: tuple[tuple[str, float], ...]

    def as_dict(self) -> dict[str, float]:
        return dict(self.values)


def dimension_spectrum(
    obj: Any,
    functionals: Iterable[DimensionFunctional],
) -> DimensionSpectrum:
    result = tuple((functional.name, functional(obj)) for functional in functionals)
    if len({name for name, _ in result}) != len(result):
        raise ValueError("dimension functional names must be unique")
    return DimensionSpectrum(result)
