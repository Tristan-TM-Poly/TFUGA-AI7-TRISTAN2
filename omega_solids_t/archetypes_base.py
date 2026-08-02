from __future__ import annotations

from .models import EpistemicStatus, OrderClass, PhaseRecord, PropertyDomain, PropertyRecord, Quantity

REFERENCE_STATUS = EpistemicStatus.ESTABLISHED_THEORY
MODEL_STATUS = EpistemicStatus.MODEL_EXTRAPOLATION

def _q(
    value: float,
    unit: str,
    *,
    uncertainty: float | None = None,
    status: EpistemicStatus = MODEL_STATUS,
    method: str = "illustrative_reference_value",
) -> Quantity:
    return Quantity(
        value,
        unit,
        uncertainty,
        status,
        source="Ω-SOLID-T∞ archetype seed; replace with traceable dataset before use",
        method=method,
        conditions={"temperature_K": 293.15},
    )


def _p(
    name: str,
    domain: PropertyDomain,
    value: float,
    unit: str,
    *,
    uncertainty: float | None = None,
    status: EpistemicStatus = MODEL_STATUS,
    tensor: tuple[tuple[float, ...], ...] | None = None,
    note: str | None = None,
) -> PropertyRecord:
    return PropertyRecord(
        name,
        domain,
        _q(value, unit, uncertainty=uncertainty, status=status),
        tensor=tensor,
        note=note,
    )


def _phase(
    name: str,
    fraction: float,
    order: OrderClass,
    *,
    space_group: str | None = None,
) -> PhaseRecord:
    return PhaseRecord(
        name,
        fraction,
        order,
        space_group=space_group,
        status=MODEL_STATUS,
    )


