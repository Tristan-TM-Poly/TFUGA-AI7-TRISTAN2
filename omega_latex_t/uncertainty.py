from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

from .ast import Text
from .math_ir import DimensionError, parse_unit
from .models import DocumentIR


class UncertaintyError(ValueError):
    pass


@dataclass(frozen=True)
class Measurement:
    value: float
    uncertainty: float
    unit: str = ""
    method: str = "unspecified"
    coverage: float | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "Measurement":
        try:
            value = float(data["value"]); uncertainty = float(data.get("uncertainty", 0.0))
        except (KeyError, TypeError, ValueError) as exc:
            raise UncertaintyError("measurement requires numeric value and uncertainty") from exc
        coverage_raw = data.get("coverage")
        item = cls(value=value, uncertainty=uncertainty, unit=str(data.get("unit", "")), method=str(data.get("method", "unspecified")), coverage=None if coverage_raw is None else float(coverage_raw))
        item.validate(); return item

    def validate(self) -> None:
        if not math.isfinite(self.value): raise UncertaintyError("measurement value must be finite")
        if not math.isfinite(self.uncertainty) or self.uncertainty < 0: raise UncertaintyError("uncertainty must be finite and >= 0")
        if self.coverage is not None and not (0 < self.coverage <= 1): raise UncertaintyError("coverage must be in (0, 1]")
        if self.unit:
            try: parse_unit(self.unit)
            except DimensionError as exc: raise UncertaintyError(f"unsupported measurement unit {self.unit!r}: {exc}") from exc

    def to_mapping(self) -> dict[str, Any]:
        return {"value": self.value, "uncertainty": self.uncertainty, "unit": self.unit, "method": self.method, "coverage": self.coverage}


def is_measurement(value: Any) -> bool:
    return isinstance(value, Mapping) and "value" in value and "uncertainty" in value


def validate_result(value: Any) -> tuple[dict[str, str], ...]:
    if not is_measurement(value): return ()
    try: Measurement.from_mapping(value)
    except UncertaintyError as exc: return ({"code": "RESULT_UNCERTAINTY_INVALID", "severity": "error", "message": str(exc)},)
    return ()


def render_result_latex(value: Any) -> str:
    if not is_measurement(value): return Text(str(value)).render()
    measurement = Measurement.from_mapping(value); body = f"{measurement.value:g}"
    if measurement.uncertainty: body += rf" \pm {measurement.uncertainty:g}"
    if measurement.unit: body += rf"\,\text{{{Text(measurement.unit).render()}}}"
    return body


def uncertainty_ledger(doc: DocumentIR) -> dict[str, Any]:
    entries = []
    for key in sorted(doc.results):
        value = doc.results[key]; findings = list(validate_result(value))
        if is_measurement(value):
            try: normalized = Measurement.from_mapping(value).to_mapping()
            except UncertaintyError: normalized = dict(value)
            entries.append({"result_key": key, "measurement": normalized, "findings": findings})
    return {"semantic_hash": doc.semantic_hash(), "entries": entries, "count": len(entries), "boundary": "reported uncertainty is a modeled metadata object; it is not automatically calibrated, independent, Gaussian or complete"}


def _same_unit(items: Sequence[Measurement]) -> str:
    units = {item.unit for item in items}
    if len(units) > 1: raise UncertaintyError("add/sub propagation requires identical unit strings; unit conversion is not implicit")
    return next(iter(units)) if units else ""


def propagate_independent(operation: str, items: Sequence[Measurement]) -> Measurement:
    values = list(items)
    if not values: raise UncertaintyError("at least one measurement is required")
    for item in values: item.validate()
    op = operation.lower()
    if op in {"add", "sum"}:
        return Measurement(sum(i.value for i in values), math.sqrt(sum(i.uncertainty ** 2 for i in values)), _same_unit(values), method="independent-rss")
    if op == "sub":
        if len(values) != 2: raise UncertaintyError("sub propagation requires exactly two measurements")
        return Measurement(values[0].value-values[1].value, math.hypot(values[0].uncertainty, values[1].uncertainty), _same_unit(values), method="independent-rss")
    if op in {"mul", "product"}:
        product = 1.0
        for item in values: product *= item.value
        variance = 0.0
        for index, item in enumerate(values):
            derivative = 1.0
            for j, other in enumerate(values):
                if j != index: derivative *= other.value
            variance += (derivative * item.uncertainty) ** 2
        unit = "*".join(item.unit for item in values if item.unit) or ""
        return Measurement(product, math.sqrt(variance), unit, method="first-order-independent")
    if op == "div":
        if len(values) != 2: raise UncertaintyError("div propagation requires exactly two measurements")
        numerator, denominator = values
        if denominator.value == 0: raise UncertaintyError("division by zero central value")
        value = numerator.value / denominator.value
        variance = (numerator.uncertainty / denominator.value) ** 2 + (numerator.value * denominator.uncertainty / (denominator.value ** 2)) ** 2
        unit = numerator.unit
        if denominator.unit: unit = f"{unit}/{denominator.unit}" if unit else f"1/{denominator.unit}"
        return Measurement(value, math.sqrt(variance), unit, method="first-order-independent")
    raise UncertaintyError(f"unsupported propagation operation {operation!r}")
