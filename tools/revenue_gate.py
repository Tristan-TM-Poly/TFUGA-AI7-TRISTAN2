"""Value Gate for Ω-AIT-RESEARCH-FACTORY-T.

Scores a branch as a value hypothesis. This is planning only; it is not a
financial claim, forecast, or instruction.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValueGateReport:
    score: int
    interpretation: str
    recommended_line: str
    safe_next_action: str


def score_value_gate(
    *,
    pain: int = 0,
    urgency: int = 0,
    budget_fit: int = 0,
    repeatability: int = 0,
    proof: int = 0,
    risk: int = 0,
    competition: int = 0,
    complexity: int = 0,
) -> ValueGateReport:
    """Return a conservative value score.

    Inputs should be small integers, typically 0..5.
    """

    score = pain + urgency + budget_fit + repeatability + proof - risk - competition - complexity
    if score >= 12:
        interpretation = "strong value hypothesis, still needs evidence and review"
        line = "product_or_service_experiment"
        next_action = "prepare reviewed value experiment with proof and risk notes"
    elif score >= 6:
        interpretation = "moderate value hypothesis"
        line = "technical_note_or_demo"
        next_action = "build demo and gather feedback safely"
    elif score >= 1:
        interpretation = "weak value hypothesis"
        line = "internal_tool_or_research"
        next_action = "increase proof or clarify user pain"
    else:
        interpretation = "not yet a value hypothesis"
        line = "research_only"
        next_action = "keep as research until pain, proof, or repeatability improves"

    return ValueGateReport(score, interpretation, line, next_action)
