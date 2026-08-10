from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StockRecord:
    zone: str
    year: int
    material: str
    mass_kg: float
    recoverable_fraction: float = 1.0

    def __post_init__(self) -> None:
        if self.mass_kg < 0:
            raise ValueError("mass_kg must be non-negative")
        if not 0 <= self.recoverable_fraction <= 1:
            raise ValueError("recoverable_fraction must be in [0, 1]")


def aggregate_recoverable_stock(records: tuple[StockRecord, ...]) -> dict[tuple[str, int, str], float]:
    result: dict[tuple[str, int, str], float] = defaultdict(float)
    for record in records:
        result[(record.zone, record.year, record.material)] += record.mass_kg * record.recoverable_fraction
    return dict(sorted(result.items()))
