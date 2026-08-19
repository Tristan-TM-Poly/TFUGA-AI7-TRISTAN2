"""Core data models for Ω-AI-TRISTAN-LAB."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OAKStatus(str, Enum):
    """Lifecycle status for an idea/prototype under OAK discipline."""

    IDEA = "IDEA"
    MODEL = "MODEL"
    PROTO = "PROTO"
    TESTED = "TESTED"
    BENCHMARKED = "BENCHMARKED"
    OAK_PASS = "OAK_PASS"
    CANON = "CANON"
    IP_LOCK = "IP_LOCK"


@dataclass(frozen=True)
class TheoryCard:
    """Structured representation of an idea before it becomes code."""

    name: str
    purpose: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    algorithm: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    revenue_hypotheses: list[str] = field(default_factory=list)
    oak_status: OAKStatus = OAKStatus.IDEA
    next_action: str = "Define the smallest falsifiable prototype."


@dataclass(frozen=True)
class OAKReport:
    """Operational Anti-hallucination Kernel report."""

    status: OAKStatus
    score: float
    strengths: list[str]
    weaknesses: list[str]
    missing_evidence: list[str]
    negative_memory: list[str]
    next_action: str

    def passed(self, threshold: float = 0.72) -> bool:
        return self.score >= threshold and self.status in {
            OAKStatus.TESTED,
            OAKStatus.BENCHMARKED,
            OAKStatus.OAK_PASS,
            OAKStatus.CANON,
        }


@dataclass(frozen=True)
class BayesAxisScore:
    """Multi-axis posterior-like score used by Bayes-Tristan."""

    truth: float
    utility: float
    fertility: float
    testability: float
    safety: float
    novelty: float
    revenue: float
    compressibility: float

    def clamp(self) -> "BayesAxisScore":
        values = {
            field_name: max(0.0, min(1.0, getattr(self, field_name)))
            for field_name in self.__dataclass_fields__
        }
        return BayesAxisScore(**values)

    def weighted_total(self, weights: dict[str, float] | None = None) -> float:
        default_weights = {
            "truth": 0.18,
            "utility": 0.15,
            "fertility": 0.14,
            "testability": 0.15,
            "safety": 0.14,
            "novelty": 0.08,
            "revenue": 0.08,
            "compressibility": 0.08,
        }
        active_weights = weights or default_weights
        numerator = sum(getattr(self, axis) * weight for axis, weight in active_weights.items())
        denominator = sum(active_weights.values()) or 1.0
        return numerator / denominator


@dataclass(frozen=True)
class IPClassification:
    """Preliminary IP classification. Not legal advice."""

    label: str
    confidence: float
    rationale: list[str]
    safe_public_actions: list[str]
    blocked_actions: list[str]
    next_action: str


@dataclass(frozen=True)
class RevenuePath:
    """Revenue hypothesis with OAK-safe caveats."""

    name: str
    customer: str
    value_proposition: str
    validation_test: str
    risks: list[str]
    effort: str
    confidence: float


@dataclass(frozen=True)
class AgentStep:
    """A single step in an agentic plan."""

    name: str
    action: str
    expected_output: str
    oak_check: str
    done: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
