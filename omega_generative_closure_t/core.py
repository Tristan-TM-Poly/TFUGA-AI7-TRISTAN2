from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Rule:
    name: str
    requires: frozenset[str]
    produces: frozenset[str]
    cost: float = 1.0
    evidence: float = 1.0

    @classmethod
    def make(cls, name: str, requires: Iterable[str], produces: Iterable[str], *, cost: float = 1.0, evidence: float = 1.0) -> "Rule":
        return cls(name=name, requires=frozenset(requires), produces=frozenset(produces), cost=float(cost), evidence=float(evidence))


@dataclass(frozen=True)
class ClosureReport:
    seeds: frozenset[str]
    reachable: frozenset[str]
    fired_rules: tuple[str, ...]
    rounds: int

    @property
    def gain(self) -> int:
        return len(self.reachable - self.seeds)


@dataclass(frozen=True)
class PrimitiveNecessity:
    primitive: str
    reachable_with: int
    reachable_without: int
    lost: frozenset[str]

    @property
    def necessity(self) -> int:
        return len(self.lost)


@dataclass(frozen=True)
class MaxMinVector:
    verified_value: float = 0.0
    evidence: float = 0.0
    reuse: float = 0.0
    reachability: float = 0.0
    regenerability: float = 0.0
    fertility: float = 0.0
    cost: float = 0.0
    structural_debt: float = 0.0
    proof_debt: float = 0.0
    semantic_debt: float = 0.0
    uncertainty: float = 0.0
    irreversibility: float = 0.0

    def numerator(self) -> float:
        return self.verified_value + self.evidence + self.reuse + self.reachability + self.regenerability + self.fertility

    def denominator(self) -> float:
        return 1.0 + self.cost + self.structural_debt + self.proof_debt + self.semantic_debt + self.uncertainty + self.irreversibility

    def power_density(self) -> float:
        return self.numerator() / self.denominator()


@dataclass(frozen=True)
class RepoCellDecision:
    repository: str
    decision: str
    unique_capabilities: tuple[str, ...] = ()
    max_overlap: float = 0.0
    overlap_with: str | None = None
    split_score: float = 0.0
    reasons: tuple[str, ...] = ()
