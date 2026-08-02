"""Unit-aware quantities and calibrated uncertainty records.

This module is intentionally small and dependency-free.  It provides explicit
quantity contracts and a conservative conversion registry; it does not replace
specialized metrology or uncertainty-propagation libraries.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite, sqrt
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class UnitDefinition:
    symbol: str
    dimension: str
    scale_to_base: float = 1.0
    offset_to_base: float = 0.0
    aliases: tuple[str, ...] = ()

    def to_base(self, value: float) -> float:
        return (float(value) + self.offset_to_base) * self.scale_to_base

    def from_base(self, value: float) -> float:
        return float(value) / self.scale_to_base - self.offset_to_base


_UNIT_DEFINITIONS = (
    UnitDefinition("1", "dimensionless", aliases=("dimensionless", "ratio")),
    UnitDefinition("%", "dimensionless", scale_to_base=0.01, aliases=("percent",)),
    UnitDefinition("m", "length"),
    UnitDefinition("mm", "length", scale_to_base=1.0e-3),
    UnitDefinition("um", "length", scale_to_base=1.0e-6, aliases=("µm",)),
    UnitDefinition("nm", "length", scale_to_base=1.0e-9),
    UnitDefinition("s", "time"),
    UnitDefinition("ms", "time", scale_to_base=1.0e-3),
    UnitDefinition("us", "time", scale_to_base=1.0e-6, aliases=("µs",)),
    UnitDefinition("Hz", "frequency"),
    UnitDefinition("kHz", "frequency", scale_to_base=1.0e3),
    UnitDefinition("MHz", "frequency", scale_to_base=1.0e6),
    UnitDefinition("GHz", "frequency", scale_to_base=1.0e9),
    UnitDefinition("K", "temperature"),
    UnitDefinition("degC", "temperature", offset_to_base=273.15, aliases=("°C", "C")),
    UnitDefinition("Pa", "pressure"),
    UnitDefinition("kPa", "pressure", scale_to_base=1.0e3),
    UnitDefinition("MPa", "pressure", scale_to_base=1.0e6),
    UnitDefinition("GPa", "pressure", scale_to_base=1.0e9),
    UnitDefinition("J", "energy"),
    UnitDefinition("mJ", "energy", scale_to_base=1.0e-3),
    UnitDefinition("uJ", "energy", scale_to_base=1.0e-6, aliases=("µJ",)),
    UnitDefinition("W", "power"),
    UnitDefinition("mW", "power", scale_to_base=1.0e-3),
    UnitDefinition("uW", "power", scale_to_base=1.0e-6, aliases=("µW",)),
    UnitDefinition("V", "voltage"),
    UnitDefinition("mV", "voltage", scale_to_base=1.0e-3),
    UnitDefinition("A", "current"),
    UnitDefinition("mA", "current", scale_to_base=1.0e-3),
    UnitDefinition("uA", "current", scale_to_base=1.0e-6, aliases=("µA",)),
    UnitDefinition("C", "charge"),
    UnitDefinition("mol", "amount"),
    UnitDefinition("mol/L", "concentration"),
    UnitDefinition("mmol/L", "concentration", scale_to_base=1.0e-3),
    UnitDefinition("kg", "mass"),
    UnitDefinition("g", "mass", scale_to_base=1.0e-3),
    UnitDefinition("mg", "mass", scale_to_base=1.0e-6),
    UnitDefinition("rad", "angle"),
    UnitDefinition("deg", "angle", scale_to_base=0.017453292519943295, aliases=("degree", "°")),
    UnitDefinition("m^-1", "wavenumber"),
    UnitDefinition("cm^-1", "wavenumber", scale_to_base=100.0),
    UnitDefinition("counts", "detector_counts"),
    UnitDefinition("a.u.", "arbitrary_intensity", aliases=("au", "arbitrary_unit")),
    UnitDefinition("pixel", "pixel"),
    UnitDefinition("byte", "information"),
    UnitDefinition("KiB", "information", scale_to_base=1024.0),
    UnitDefinition("MiB", "information", scale_to_base=1024.0**2),
    UnitDefinition("GiB", "information", scale_to_base=1024.0**3),
    UnitDefinition("CAD", "currency_cad"),
    UnitDefinition("USD", "currency_usd"),
)

_UNIT_BY_SYMBOL: dict[str, UnitDefinition] = {}
for _definition in _UNIT_DEFINITIONS:
    _UNIT_BY_SYMBOL[_definition.symbol] = _definition
    for _alias in _definition.aliases:
        _UNIT_BY_SYMBOL[_alias] = _definition


def unit_definition(symbol: str) -> UnitDefinition:
    try:
        return _UNIT_BY_SYMBOL[symbol]
    except KeyError as exc:
        raise ValueError(f"Unknown unit symbol: {symbol}") from exc


def compatible_units(left: str, right: str) -> bool:
    return unit_definition(left).dimension == unit_definition(right).dimension


def convert_value(value: float, source_unit: str, target_unit: str) -> float:
    source = unit_definition(source_unit)
    target = unit_definition(target_unit)
    if source.dimension != target.dimension:
        raise ValueError(
            f"Incompatible unit dimensions: {source_unit} ({source.dimension}) and "
            f"{target_unit} ({target.dimension})"
        )
    return target.from_base(source.to_base(float(value)))


def convert_uncertainty(value: float, source_unit: str, target_unit: str) -> float:
    source = unit_definition(source_unit)
    target = unit_definition(target_unit)
    if source.dimension != target.dimension:
        raise ValueError("Cannot convert uncertainty across dimensions")
    return abs(float(value) * source.scale_to_base / target.scale_to_base)


@dataclass(frozen=True, slots=True)
class CalibrationReference:
    calibration_id: str
    reference_id: str
    method: str
    valid_from: str | None = None
    valid_until: str | None = None
    environment: Mapping[str, str] = field(default_factory=dict)
    source_hash: str | None = None
    uncertainty_budget: Mapping[str, float] = field(default_factory=dict)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.calibration_id.strip():
            issues.append("calibration_id is required")
        if not self.reference_id.strip():
            issues.append("reference_id is required")
        if not self.method.strip():
            issues.append("calibration method is required")
        if any(value < 0 or not isfinite(value) for value in self.uncertainty_budget.values()):
            issues.append("uncertainty budget entries must be finite and non-negative")
        return issues

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Quantity:
    value: float
    unit: str
    standard_uncertainty: float
    distribution: str = "normal"
    coverage_factor: float = 1.0
    calibration_id: str | None = None
    validity_domain: Mapping[str, str] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()
    status: str = "measured_or_computed_quantity"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not isfinite(self.value):
            issues.append("quantity value must be finite")
        if not isfinite(self.standard_uncertainty) or self.standard_uncertainty < 0:
            issues.append("standard_uncertainty must be finite and non-negative")
        if not isfinite(self.coverage_factor) or self.coverage_factor <= 0:
            issues.append("coverage_factor must be finite and positive")
        try:
            unit_definition(self.unit)
        except ValueError as exc:
            issues.append(str(exc))
        if self.distribution not in {
            "normal",
            "uniform",
            "triangular",
            "student_t",
            "lognormal",
            "empirical",
            "unknown",
        }:
            issues.append(f"unsupported uncertainty distribution: {self.distribution}")
        return issues

    @classmethod
    def create(
        cls,
        value: float,
        unit: str,
        standard_uncertainty: float,
        *,
        distribution: str = "normal",
        coverage_factor: float = 1.0,
        calibration_id: str | None = None,
        validity_domain: Mapping[str, str] | None = None,
        provenance: Sequence[str] = (),
        status: str = "measured_or_computed_quantity",
    ) -> "Quantity":
        quantity = cls(
            value=float(value),
            unit=unit_definition(unit).symbol,
            standard_uncertainty=float(standard_uncertainty),
            distribution=distribution,
            coverage_factor=float(coverage_factor),
            calibration_id=calibration_id,
            validity_domain=dict(validity_domain or {}),
            provenance=tuple(provenance),
            status=status,
        )
        issues = quantity.validate()
        if issues:
            raise ValueError("; ".join(issues))
        return quantity

    def converted(self, target_unit: str) -> "Quantity":
        target = unit_definition(target_unit).symbol
        return Quantity.create(
            convert_value(self.value, self.unit, target),
            target,
            convert_uncertainty(self.standard_uncertainty, self.unit, target),
            distribution=self.distribution,
            coverage_factor=self.coverage_factor,
            calibration_id=self.calibration_id,
            validity_domain=self.validity_domain,
            provenance=self.provenance,
            status=self.status,
        )

    def expanded_uncertainty(self) -> float:
        return self.standard_uncertainty * self.coverage_factor

    def interval(self) -> tuple[float, float]:
        expanded = self.expanded_uncertainty()
        return self.value - expanded, self.value + expanded

    def relative_uncertainty(self) -> float | None:
        if self.value == 0:
            return None
        return abs(self.standard_uncertainty / self.value)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class QuantityVector:
    names: tuple[str, ...]
    quantities: tuple[Quantity, ...]
    covariance: tuple[tuple[float, ...], ...] = ()

    def validate(self) -> list[str]:
        issues: list[str] = []
        if len(self.names) != len(self.quantities):
            issues.append("quantity-vector names and quantities must have equal length")
        if len(set(self.names)) != len(self.names):
            issues.append("quantity-vector names must be unique")
        for name, quantity in zip(self.names, self.quantities):
            issues.extend(f"{name}: {issue}" for issue in quantity.validate())
        if self.covariance:
            size = len(self.quantities)
            if len(self.covariance) != size or any(len(row) != size for row in self.covariance):
                issues.append("covariance matrix must be square and match quantity count")
            else:
                for index in range(size):
                    if self.covariance[index][index] < 0:
                        issues.append("covariance diagonal must be non-negative")
                    for other in range(size):
                        if abs(self.covariance[index][other] - self.covariance[other][index]) > 1.0e-12:
                            issues.append("covariance matrix must be symmetric")
                            break
        return issues

    def combined_standard_uncertainty(self, sensitivities: Sequence[float]) -> float:
        if len(sensitivities) != len(self.quantities):
            raise ValueError("sensitivities must match quantity count")
        if not self.covariance:
            return sqrt(
                sum(
                    (float(sensitivity) * quantity.standard_uncertainty) ** 2
                    for sensitivity, quantity in zip(sensitivities, self.quantities)
                )
            )
        total = 0.0
        for i, left in enumerate(sensitivities):
            for j, right in enumerate(sensitivities):
                total += float(left) * float(right) * self.covariance[i][j]
        return sqrt(max(total, 0.0))

    def to_dict(self) -> dict[str, object]:
        return {
            "names": list(self.names),
            "quantities": [quantity.to_dict() for quantity in self.quantities],
            "covariance": [list(row) for row in self.covariance],
        }


def quantities_to_event_fields(
    values: Mapping[str, Quantity],
) -> tuple[dict[str, float], dict[str, str], dict[str, float], dict[str, object]]:
    payload_values: dict[str, float] = {}
    units: dict[str, str] = {}
    uncertainty: dict[str, float] = {}
    metadata: dict[str, object] = {}
    for name, quantity in values.items():
        issues = quantity.validate()
        if issues:
            raise ValueError(f"Invalid quantity {name}: {'; '.join(issues)}")
        payload_values[name] = quantity.value
        units[name] = quantity.unit
        uncertainty[name] = quantity.standard_uncertainty
        metadata[name] = {
            "distribution": quantity.distribution,
            "coverage_factor": quantity.coverage_factor,
            "calibration_id": quantity.calibration_id,
            "validity_domain": dict(quantity.validity_domain),
            "provenance": list(quantity.provenance),
            "status": quantity.status,
        }
    return payload_values, units, uncertainty, metadata


def unit_catalog_manifest() -> dict[str, object]:
    unique = {definition.symbol: definition for definition in _UNIT_DEFINITIONS}
    return {
        "schema": "omega_discovery_kernel.unit_catalog.v0.2",
        "unit_count": len(unique),
        "dimensions": sorted({definition.dimension for definition in unique.values()}),
        "units": [asdict(unique[symbol]) for symbol in sorted(unique)],
        "oak_boundary": (
            "The compact registry supports reproducible software contracts; domain metrology, "
            "calibration, correlations, traceability, and standards remain externally reviewable."
        ),
    }
