"""Typed generalized residuals for UVTC research feedback."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from .model import stable_digest


class ResidualKind(str, Enum):
    NUMERIC = "numeric"
    LOGICAL = "logical"
    CAUSAL = "causal"
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    EXPERIMENTAL = "experimental"


@dataclass(frozen=True, slots=True)
class ResidualRecord:
    residual_id: str
    kind: ResidualKind
    observed_ref: str
    predicted_ref: str
    metric: str
    magnitude: float
    uncertainty: float = 0.0
    provenance: str = ""

    def __post_init__(self) -> None:
        if self.magnitude < 0 or self.uncertainty < 0:
            raise ValueError("residual magnitude and uncertainty must be non-negative")

    @property
    def fingerprint(self) -> str:
        return stable_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class ResidualGenome:
    records: tuple[ResidualRecord, ...]

    def by_kind(self, kind: ResidualKind) -> tuple[ResidualRecord, ...]:
        return tuple(record for record in self.records if record.kind == kind)

    def research_priority(self) -> tuple[str, ...]:
        """Rank by an uncertainty-aware residual upper proxy, not causal importance."""
        ranked = sorted(
            self.records,
            key=lambda r: (r.magnitude + 2.0 * r.uncertainty, r.residual_id),
            reverse=True,
        )
        return tuple(record.residual_id for record in ranked)
