"""Temporal bottleneck migration tracking for measured resource evidence."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class BottleneckObservation:
    revision: str
    shares: Mapping[str, float]


@dataclass(frozen=True)
class BottleneckTransition:
    from_revision: str
    to_revision: str
    from_resource: str
    to_resource: str
    changed: bool


@dataclass(frozen=True)
class BottleneckDynamicsReport:
    dominant_resources: tuple[tuple[str, str], ...]
    transitions: tuple[BottleneckTransition, ...]
    migration_count: int
    status: str = "measured-bottleneck-dynamics"
    oak_warning: str = (
        "Dominant measured resource share is an operational bottleneck signal. "
        "It is not by itself proof of causal limitation or a conservation law."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _dominant(shares: Mapping[str, float]) -> str:
    if not shares:
        raise ValueError("shares cannot be empty")
    for name, value in shares.items():
        if value < 0:
            raise ValueError(f"share must be non-negative: {name}")
    return max(shares, key=lambda name: (shares[name], name))


def trace_bottleneck_migration(
    observations: Sequence[BottleneckObservation],
) -> BottleneckDynamicsReport:
    rows = tuple(observations)
    if not rows:
        raise ValueError("at least one observation is required")
    dominant = tuple((row.revision, _dominant(row.shares)) for row in rows)
    transitions = tuple(
        BottleneckTransition(
            from_revision=left[0],
            to_revision=right[0],
            from_resource=left[1],
            to_resource=right[1],
            changed=left[1] != right[1],
        )
        for left, right in zip(dominant, dominant[1:])
    )
    return BottleneckDynamicsReport(
        dominant_resources=dominant,
        transitions=transitions,
        migration_count=sum(row.changed for row in transitions),
    )
