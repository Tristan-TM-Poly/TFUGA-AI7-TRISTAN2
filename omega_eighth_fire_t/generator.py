from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Residual:
    domain: str
    description: str
    beneficiaries: tuple[str, ...]
    severity: float
    uncertainty: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.severity <= 1.0 or not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("severity and uncertainty must be in [0,1]")


@dataclass(frozen=True)
class Candidate:
    kind: str
    description: str
    expected_gain: float
    expected_cost: float
    expected_capture: float

    @property
    def priority(self) -> float:
        return round(self.expected_gain / (self.expected_cost + self.expected_capture + 1e-9), 9)


def generate_candidates(residual: Residual) -> tuple[Candidate, ...]:
    base = max(0.05, residual.severity * (1.0 - 0.5 * residual.uncertainty))
    candidates = (
        Candidate("reuse", f"Reuse existing capacity for: {residual.description}", base * 0.55, 0.10, 0.05),
        Candidate("learning", f"Generate a learning intervention for: {residual.description}", base * 0.75, 0.25, 0.08),
        Candidate("tool", f"Build a minimal tool for: {residual.description}", base * 0.80, 0.35, 0.12),
        Candidate("protocol", f"Create a reusable protocol for: {residual.description}", base * 0.70, 0.20, 0.04),
        Candidate("jit_coalition", f"Create a temporary bounded coalition for: {residual.description}", base * 0.90, 0.45, 0.10),
    )
    return tuple(sorted(candidates, key=lambda x: (-x.priority, x.kind)))
