"""Typed objects for MetaScienceBench-T v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


StrategyName = Literal["fixed", "adaptive"]


@dataclass(frozen=True, slots=True)
class Representation:
    name: str
    expression: str
    invariants: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TheoryGenome:
    theory_id: str
    assumptions: tuple[str, ...]
    domain: str
    falsifiers: tuple[str, ...]
    representations: tuple[Representation, ...]
    model_kind: Literal["linear", "quadratic"]

    def predict(self, x: float) -> float:
        if self.model_kind == "linear":
            return x
        if self.model_kind == "quadratic":
            return x * x
        raise ValueError(f"unsupported model kind: {self.model_kind}")


@dataclass(frozen=True, slots=True)
class Experiment:
    experiment_id: str
    x: float
    cost: float = 1.0
    observable: str = "y"


@dataclass(frozen=True, slots=True)
class ToyProblem:
    theories: tuple[TheoryGenome, ...]
    experiments: tuple[Experiment, ...]
    true_theory_id: str
    tolerance: float = 1e-12


@dataclass(frozen=True, slots=True)
class ClaimPacket:
    claim: str
    provenance: str
    uncertainty: float
    baseline_declared: bool
    reproducible: bool
    unit_consistent: bool
    falsifier_declared: bool
    survivor_count: int
    residual: float
    residual_tolerance: float


@dataclass(frozen=True, slots=True)
class OAKReport:
    decision: Literal["PROMOTE", "CONDITIONAL", "BLOCK"]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MutationCampaign:
    injected: int
    detected: int
    mutation_score: float
    detected_faults: tuple[str, ...]
    missed_faults: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StrategyResult:
    strategy: StrategyName
    selected_experiment: Experiment
    observation: float
    survivors: tuple[str, ...]
    knowledge_gain_bits: float
    verified_gain_per_cost: float
    disagreement_score: float
    cvcd_invariants: tuple[str, ...]
    claim: ClaimPacket
    oak: OAKReport


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    fixed: StrategyResult
    adaptive: StrategyResult
    mutation_campaign: MutationCampaign
    promoted_strategy: StrategyName
    m_plus: tuple[str, ...]
    m_minus: tuple[str, ...]
