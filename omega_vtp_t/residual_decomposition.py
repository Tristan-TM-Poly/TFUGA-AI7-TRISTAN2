"""Reusable residual decomposition objects for Ω-VTP-T++.

A central OAK rule is that one scalar residual is not enough for differential
systems. This module tracks named residual components so failures become
inspectable and reusable rather than hidden in one norm.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

import numpy as np


@dataclass(frozen=True)
class ResidualComponent:
    name: str
    value: float
    tolerance: float
    weight: float = 1.0

    @property
    def normalized(self) -> float:
        return float(abs(self.value) / max(abs(self.tolerance), np.finfo(float).eps))

    @property
    def passed(self) -> bool:
        return abs(self.value) <= abs(self.tolerance)


@dataclass(frozen=True)
class ResidualDecomposition:
    components: Tuple[ResidualComponent, ...]
    total_weighted_normalized: float
    worst_component: str
    oak_status: str


def decompose_residuals(components: Iterable[ResidualComponent]) -> ResidualDecomposition:
    """Aggregate named residual components into an OAK report."""

    comps = tuple(components)
    if not comps:
        return ResidualDecomposition(tuple(), 0.0, "none", "empty")

    weighted = [c.weight * c.normalized for c in comps]
    total = float(np.sum(weighted))
    worst_idx = int(np.argmax(weighted))
    passed_all = all(c.passed for c in comps)

    if passed_all:
        status = "certified"
    elif total <= len(comps) * 10:
        status = "experimental_residual_watch"
    else:
        status = "residual_high_m_minus_candidate"

    return ResidualDecomposition(
        components=comps,
        total_weighted_normalized=total,
        worst_component=comps[worst_idx].name,
        oak_status=status,
    )


def residual_dict(report: ResidualDecomposition) -> dict[str, float | str | bool]:
    """Flatten a residual report for JSON/YAML style logging."""

    out: dict[str, float | str | bool] = {
        "total_weighted_normalized": report.total_weighted_normalized,
        "worst_component": report.worst_component,
        "oak_status": report.oak_status,
    }
    for component in report.components:
        prefix = component.name
        out[f"{prefix}.value"] = component.value
        out[f"{prefix}.tolerance"] = component.tolerance
        out[f"{prefix}.normalized"] = component.normalized
        out[f"{prefix}.passed"] = component.passed
    return out
