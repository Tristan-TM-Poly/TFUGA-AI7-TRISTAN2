from __future__ import annotations

from dataclasses import dataclass

from .urban_mine import StockRecord


@dataclass(frozen=True, slots=True)
class UrbanMineAssetRecord:
    domain: str
    zone: str
    year: int
    material: str
    stock_mass_kg: float
    accessible_fraction: float = 1.0
    recovery_yield: float = 1.0

    def __post_init__(self) -> None:
        if not self.domain:
            raise ValueError("domain must be non-empty")
        if self.stock_mass_kg < 0:
            raise ValueError("stock_mass_kg must be non-negative")
        if not 0 <= self.accessible_fraction <= 1:
            raise ValueError("accessible_fraction must be in [0, 1]")
        if not 0 <= self.recovery_yield <= 1:
            raise ValueError("recovery_yield must be in [0, 1]")

    def to_stock_record(self) -> StockRecord:
        return StockRecord(
            zone=self.zone,
            year=self.year,
            material=self.material,
            mass_kg=self.stock_mass_kg,
            recoverable_fraction=self.accessible_fraction * self.recovery_yield,
        )


def electronics_mine_record(**kwargs) -> UrbanMineAssetRecord:
    return UrbanMineAssetRecord(domain="electronics", **kwargs)


def battery_mine_record(**kwargs) -> UrbanMineAssetRecord:
    return UrbanMineAssetRecord(domain="battery", **kwargs)


def building_mine_record(**kwargs) -> UrbanMineAssetRecord:
    return UrbanMineAssetRecord(domain="building", **kwargs)


def adapt_asset_records(records: tuple[UrbanMineAssetRecord, ...]) -> tuple[StockRecord, ...]:
    converted = [record.to_stock_record() for record in records]
    converted.sort(key=lambda record: (record.zone, record.year, record.material))
    return tuple(converted)
