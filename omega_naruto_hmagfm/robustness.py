"""Decision robustness analysis for Ω-NARUTO OAKMerge."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Sequence

from .core import AgentProposal, oak_merge


@dataclass(frozen=True)
class ProposalPerturbation:
    proposal_id: str
    confidence_delta: float = 0.0
    uncertainty_delta: float = 0.0
    risk_delta: float = 0.0
    remove_evidence_count: int = 0


@dataclass(frozen=True)
class RobustnessScenario:
    name: str
    perturbations: tuple[ProposalPerturbation, ...]


@dataclass(frozen=True)
class ScenarioDecision:
    scenario: str
    winner_id: str | None
    changed: bool


@dataclass(frozen=True)
class DecisionRobustness:
    base_winner_id: str | None
    scenario_decisions: tuple[ScenarioDecision, ...]
    stable_fraction: float
    unstable_scenarios: tuple[str, ...]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _apply(
    proposals: Sequence[AgentProposal],
    perturbations: Sequence[ProposalPerturbation],
) -> tuple[AgentProposal, ...]:
    by_id = {item.proposal_id: item for item in proposals}
    for perturbation in perturbations:
        if perturbation.proposal_id not in by_id:
            raise ValueError(
                f"unknown proposal_id in perturbation: {perturbation.proposal_id}"
            )
        original = by_id[perturbation.proposal_id]
        remove_count = max(0, perturbation.remove_evidence_count)
        remaining_evidence = tuple(original.evidence[remove_count:])
        shared_risk = _clamp(
            max(original.safety_risk, original.privacy_risk, original.ip_risk)
            + perturbation.risk_delta
        )
        by_id[perturbation.proposal_id] = replace(
            original,
            confidence=_clamp(original.confidence + perturbation.confidence_delta),
            uncertainty=_clamp(original.uncertainty + perturbation.uncertainty_delta),
            safety_risk=shared_risk,
            privacy_risk=shared_risk,
            ip_risk=shared_risk,
            evidence=remaining_evidence,
        )
    return tuple(by_id[item.proposal_id] for item in proposals)


def analyze_decision_robustness(
    proposals: Iterable[AgentProposal],
    scenarios: Iterable[RobustnessScenario],
) -> DecisionRobustness:
    """Measure whether OAKMerge's local winner survives bounded perturbations.

    This is a software sensitivity diagnostic, not a proof that the winner is
    scientifically true or globally optimal.
    """

    items = tuple(proposals)
    scenario_items = tuple(scenarios)
    base = oak_merge(items).accepted
    base_id = base.proposal_id if base is not None else None

    decisions: list[ScenarioDecision] = []
    for scenario in scenario_items:
        perturbed = _apply(items, scenario.perturbations)
        winner = oak_merge(perturbed).accepted
        winner_id = winner.proposal_id if winner is not None else None
        decisions.append(
            ScenarioDecision(
                scenario=scenario.name,
                winner_id=winner_id,
                changed=winner_id != base_id,
            )
        )

    if not decisions:
        stable_fraction = 1.0
    else:
        stable_fraction = sum(not item.changed for item in decisions) / len(decisions)

    return DecisionRobustness(
        base_winner_id=base_id,
        scenario_decisions=tuple(decisions),
        stable_fraction=stable_fraction,
        unstable_scenarios=tuple(
            item.scenario for item in decisions if item.changed
        ),
    )


def default_robustness_scenarios(
    accepted_id: str,
    rival_id: str,
) -> tuple[RobustnessScenario, ...]:
    """Return deterministic stress cases for one accepted/rival pair."""

    return (
        RobustnessScenario(
            "accepted_confidence_minus_0_15",
            (ProposalPerturbation(accepted_id, confidence_delta=-0.15),),
        ),
        RobustnessScenario(
            "accepted_uncertainty_plus_0_15",
            (ProposalPerturbation(accepted_id, uncertainty_delta=0.15),),
        ),
        RobustnessScenario(
            "accepted_remove_one_evidence",
            (ProposalPerturbation(accepted_id, remove_evidence_count=1),),
        ),
        RobustnessScenario(
            "rival_confidence_plus_0_10",
            (ProposalPerturbation(rival_id, confidence_delta=0.10),),
        ),
        RobustnessScenario(
            "accepted_risk_plus_0_30",
            (ProposalPerturbation(accepted_id, risk_delta=0.30),),
        ),
    )
