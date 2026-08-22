"""Cross-commit empirical regression ledger for Omega Compute Physics R0.6.

The ledger turns finite-domain ComplexityDiff evidence into reviewable events.
It deliberately distinguishes a resource regression from a mathematical
complexity-class regression.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

from .complexity_diff import ComplexityDiffReport


@dataclass(frozen=True)
class RegressionEvent:
    repository: str
    old_commit: str
    new_commit: str
    target: str
    severity: str
    regression_fraction: float
    max_relative_increase: float
    mean_relative_change: float
    domain_overlap_min: float
    requires_rebenchmark: bool
    status: str = "finite-domain-resource-regression-event"
    oak_warning: str = (
        "This event summarizes empirical or model-conditioned finite-domain evidence. "
        "It does not prove a change in Big-O/Theta complexity."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RegressionLedger:
    events: list[RegressionEvent] = field(default_factory=list)

    def append(self, event: RegressionEvent) -> None:
        key = (event.repository, event.old_commit, event.new_commit, event.target)
        if any((row.repository, row.old_commit, row.new_commit, row.target) == key for row in self.events):
            raise ValueError(f"duplicate regression event: {key}")
        self.events.append(event)

    def by_severity(self, severity: str) -> tuple[RegressionEvent, ...]:
        return tuple(row for row in self.events if row.severity == severity)

    def to_dict(self) -> dict[str, Any]:
        return {
            "events": [row.to_dict() for row in self.events],
            "status": "cross-commit-complexity-regression-ledger",
            "oak_warning": (
                "Ledger entries are finite-domain resource evidence and remeasurement triggers, "
                "not proofs of asymptotic complexity-class changes."
            ),
        }


def event_from_diff(
    report: ComplexityDiffReport,
    *,
    repository: str,
    old_commit: str,
    new_commit: str,
    warn_fraction: float = 0.20,
    critical_fraction: float = 0.60,
    warn_increase: float = 0.10,
    critical_increase: float = 0.50,
    min_domain_overlap: float = 0.70,
) -> RegressionEvent:
    overlap = min(report.domain_overlap.values(), default=1.0)
    if report.regression_fraction >= critical_fraction or report.max_relative_increase >= critical_increase:
        severity = "critical"
    elif report.regression_fraction >= warn_fraction or report.max_relative_increase >= warn_increase:
        severity = "warning"
    else:
        severity = "neutral"
    requires_rebenchmark = severity != "neutral" or overlap < min_domain_overlap
    return RegressionEvent(
        repository=repository,
        old_commit=old_commit,
        new_commit=new_commit,
        target=report.target,
        severity=severity,
        regression_fraction=report.regression_fraction,
        max_relative_increase=report.max_relative_increase,
        mean_relative_change=report.mean_relative_change,
        domain_overlap_min=overlap,
        requires_rebenchmark=requires_rebenchmark,
    )
