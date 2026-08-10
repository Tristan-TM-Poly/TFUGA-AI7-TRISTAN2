from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO

SHORT_TON_TO_METRIC_TONNE = 0.90718474


@dataclass(frozen=True, slots=True)
class EPASMMObservation:
    year: int
    material: str
    management_pathway: str
    short_tons: float
    metric_tonnes: float
    unit: str = "US_short_ton"
    claim_boundary: str = "normalized_bridge_not_arbitrary_epa_webpage_parser"


def short_tons_to_metric_tonnes(value: float) -> float:
    if value < 0:
        raise ValueError("mass must be non-negative")
    return value * SHORT_TON_TO_METRIC_TONNE


def parse_epa_smm_normalized_csv(text: str) -> tuple[EPASMMObservation, ...]:
    """Parse a normalized bridge table transcribed/exported from EPA SMM tables.

    This intentionally does not pretend that every EPA HTML/XLS/PDF layout has one
    stable machine schema. Acquisition and table-specific extraction stay outside
    this pure validation layer.
    """
    reader = csv.DictReader(StringIO(text))
    required = {"year", "material", "management_pathway", "short_tons"}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError(f"EPA normalized CSV requires columns {sorted(required)}")
    result: list[EPASMMObservation] = []
    for row in reader:
        year = int(row["year"])
        material = row["material"].strip()
        pathway = row["management_pathway"].strip()
        short_tons = float(row["short_tons"])
        if not material or not pathway or short_tons < 0:
            raise ValueError("EPA normalized rows require non-negative mass and non-empty labels")
        result.append(
            EPASMMObservation(
                year=year,
                material=material,
                management_pathway=pathway,
                short_tons=short_tons,
                metric_tonnes=short_tons_to_metric_tonnes(short_tons),
            )
        )
    return tuple(result)
