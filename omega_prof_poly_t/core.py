"""Omega-PROF-POLY-T: OAK-safe professor augmentation primitives.

This module is intentionally small and dependency-free. It turns course,
research, lab, IP, and partnership signals into transparent scores and next
actions for professor-facing dashboards.

Boundary: this is a decision-support prototype. It must not automate academic
judgment, student evaluation, IP disclosure, or institutional decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple


class OAKStatus(str, Enum):
    """Operational OAK status for a recommendation."""

    CANON = "canon"
    PROTOTYPE = "prototype"
    EXPLORATORY = "exploratory"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class Evidence:
    """Minimal source/evidence pointer.

    `source` can be a URL, local file path, paper DOI, course file, meeting note,
    or institutional policy reference. `confidence` is deliberately bounded.
    """

    source: str
    claim: str
    confidence: float = 0.5

    def normalized_confidence(self) -> float:
        return clamp01(self.confidence)


@dataclass(frozen=True)
class ProfessorSignal:
    """A professor/project/cours signal in normalized coordinates."""

    name: str
    teaching_value: float = 0.0
    research_value: float = 0.0
    student_value: float = 0.0
    industry_value: float = 0.0
    ip_value: float = 0.0
    feasibility: float = 0.0
    reproducibility: float = 0.0
    ethics_safety: float = 0.0
    confidentiality_risk: float = 0.0
    academic_integrity_risk: float = 0.0
    overclaim_risk: float = 0.0
    evidence: Tuple[Evidence, ...] = field(default_factory=tuple)

    def vector(self) -> Dict[str, float]:
        return {
            "teaching_value": clamp01(self.teaching_value),
            "research_value": clamp01(self.research_value),
            "student_value": clamp01(self.student_value),
            "industry_value": clamp01(self.industry_value),
            "ip_value": clamp01(self.ip_value),
            "feasibility": clamp01(self.feasibility),
            "reproducibility": clamp01(self.reproducibility),
            "ethics_safety": clamp01(self.ethics_safety),
            "confidentiality_risk": clamp01(self.confidentiality_risk),
            "academic_integrity_risk": clamp01(self.academic_integrity_risk),
            "overclaim_risk": clamp01(self.overclaim_risk),
        }


@dataclass(frozen=True)
class OAKDecision:
    """Transparent decision-support output."""

    signal_name: str
    status: OAKStatus
    score: float
    benefits: Dict[str, float]
    risks: Dict[str, float]
    warnings: Tuple[str, ...]
    next_actions: Tuple[str, ...]
    evidence_count: int


DEFAULT_BENEFIT_WEIGHTS: Mapping[str, float] = {
    "teaching_value": 0.18,
    "research_value": 0.18,
    "student_value": 0.14,
    "industry_value": 0.10,
    "ip_value": 0.08,
    "feasibility": 0.12,
    "reproducibility": 0.12,
    "ethics_safety": 0.08,
}

DEFAULT_RISK_WEIGHTS: Mapping[str, float] = {
    "confidentiality_risk": 0.34,
    "academic_integrity_risk": 0.33,
    "overclaim_risk": 0.33,
}


def clamp01(value: float) -> float:
    """Clamp a numeric value to the [0, 1] interval."""

    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return float(value)


def weighted_sum(values: Mapping[str, float], weights: Mapping[str, float]) -> float:
    """Compute a normalized weighted sum over shared keys."""

    total_weight = sum(max(0.0, float(weight)) for weight in weights.values())
    if total_weight == 0:
        return 0.0
    total = 0.0
    for key, weight in weights.items():
        total += clamp01(values.get(key, 0.0)) * max(0.0, float(weight))
    return clamp01(total / total_weight)


def evaluate_signal(
    signal: ProfessorSignal,
    benefit_weights: Mapping[str, float] = DEFAULT_BENEFIT_WEIGHTS,
    risk_weights: Mapping[str, float] = DEFAULT_RISK_WEIGHTS,
) -> OAKDecision:
    """Evaluate one signal with explicit benefits, risks, and OAK warnings."""

    values = signal.vector()
    benefits = {key: values[key] for key in benefit_weights}
    risks = {key: values[key] for key in risk_weights}

    benefit_score = weighted_sum(values, benefit_weights)
    risk_score = weighted_sum(values, risk_weights)

    evidence_bonus = min(0.08, 0.02 * len(signal.evidence))
    score = clamp01(benefit_score - 0.55 * risk_score + evidence_bonus)

    warnings: List[str] = []
    next_actions: List[str] = []

    if len(signal.evidence) == 0:
        warnings.append("No evidence attached: keep exploratory until sources are linked.")
        next_actions.append("Attach course files, papers, protocols, policies, or meeting notes as evidence.")

    if values["confidentiality_risk"] >= 0.6:
        warnings.append("High confidentiality/IP risk: route through IP-OAK Gate before sharing.")
        next_actions.append("Classify output as public, confidential, patentable, trade secret, or open-source candidate.")

    if values["academic_integrity_risk"] >= 0.6:
        warnings.append("High academic integrity risk: professor must define permitted AI use and evaluation policy.")
        next_actions.append("Generate an AI-use policy and rubric before student deployment.")

    if values["overclaim_risk"] >= 0.6:
        warnings.append("High overclaim risk: separate fact, model, simulation, hypothesis, and proof.")
        next_actions.append("Create an OAK falsification checklist and M-minus anti-claim note.")

    if values["reproducibility"] < 0.4:
        warnings.append("Low reproducibility: do not promote beyond prototype.")
        next_actions.append("Add deterministic tests, datasets, scripts, uncertainty estimates, and versioned outputs.")

    if values["ethics_safety"] < 0.5:
        warnings.append("Ethics/safety score is weak: require human review before deployment.")
        next_actions.append("Add consent, privacy, fairness, accessibility, and safety checks.")

    if not next_actions:
        next_actions.extend(
            [
                "Create a DCT++ packet: Document, Code, Test, Data, Risk, Ethics, Status, Next, Links.",
                "Run a small pilot with professor review and measurable success criteria.",
            ]
        )

    if risk_score >= 0.75 or values["ethics_safety"] < 0.25:
        status = OAKStatus.BLOCKED
    elif score >= 0.72 and len(signal.evidence) >= 2 and values["reproducibility"] >= 0.65:
        status = OAKStatus.CANON
    elif score >= 0.45 and values["feasibility"] >= 0.45:
        status = OAKStatus.PROTOTYPE
    else:
        status = OAKStatus.EXPLORATORY

    return OAKDecision(
        signal_name=signal.name,
        status=status,
        score=round(score, 4),
        benefits={k: round(v, 4) for k, v in benefits.items()},
        risks={k: round(v, 4) for k, v in risks.items()},
        warnings=tuple(warnings),
        next_actions=tuple(next_actions),
        evidence_count=len(signal.evidence),
    )


def rank_signals(signals: Iterable[ProfessorSignal]) -> List[OAKDecision]:
    """Rank professor-facing opportunities by OAK score, high to low."""

    decisions = [evaluate_signal(signal) for signal in signals]
    return sorted(decisions, key=lambda decision: decision.score, reverse=True)


def build_project_forge_prompt(
    disciplines: Sequence[str],
    goal: str,
    constraints: Sequence[str] = (),
) -> str:
    """Generate a compact prompt for an inter-engineering project forge."""

    discipline_block = ", ".join(disciplines) if disciplines else "intergenie"
    constraint_block = "\n".join(f"- {item}" for item in constraints) or "- OAK-safe, measurable, feasible in one term."
    return (
        "Generate an OAK-safe Polytechnique Montreal inter-engineering project.\n"
        f"Disciplines: {discipline_block}\n"
        f"Goal: {goal}\n"
        "Constraints:\n"
        f"{constraint_block}\n"
        "Return: problem, professor roles, student skills, equipment, prototype, tests, risks, IP status, next action."
    )
