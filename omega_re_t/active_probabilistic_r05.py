"""Active Bayesian experiment selection for finite authorized model classes.

R0.5 works over declared finite hypotheses and finite experiment outcome
supports.  It does not infer inaccessible implementation details.  Posterior
concentration is a statement about the supplied model class and observations.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Hashable, Iterable, Mapping, Sequence

Experiment = Hashable
Outcome = Hashable


def _normalise(weights: Mapping[str, float]) -> dict[str, float]:
    if not weights:
        raise ValueError("weights cannot be empty")
    checked: dict[str, float] = {}
    total = 0.0
    for key, value in weights.items():
        number = float(value)
        if not math.isfinite(number) or number < 0.0:
            raise ValueError("weights must be finite and non-negative")
        checked[str(key)] = number
        total += number
    if total <= 0.0:
        raise ValueError("weights must contain positive mass")
    return {key: value / total for key, value in sorted(checked.items())}


def entropy_bits(distribution: Mapping[str, float]) -> float:
    probabilities = _normalise(distribution)
    return -sum(p * math.log2(p) for p in probabilities.values() if p > 0.0)


@dataclass(frozen=True)
class FiniteHypothesis:
    hypothesis_id: str
    likelihoods: Mapping[Experiment, Mapping[Outcome, float]]
    complexity: float = 0.0

    def __post_init__(self) -> None:
        if not self.hypothesis_id.strip():
            raise ValueError("hypothesis_id cannot be blank")
        if not math.isfinite(self.complexity) or self.complexity < 0.0:
            raise ValueError("complexity must be finite and non-negative")
        if not self.likelihoods:
            raise ValueError("likelihoods cannot be empty")
        for experiment, distribution in self.likelihoods.items():
            if not distribution:
                raise ValueError(f"empty outcome support for {experiment!r}")
            values = [float(value) for value in distribution.values()]
            if any(not math.isfinite(value) or value < 0.0 for value in values):
                raise ValueError("likelihoods must be finite and non-negative")
            if sum(values) <= 0.0:
                raise ValueError("likelihood distribution must have positive mass")

    def probability(self, experiment: Experiment, outcome: Outcome) -> float:
        distribution = self.likelihoods[experiment]
        total = sum(float(value) for value in distribution.values())
        return float(distribution.get(outcome, 0.0)) / total


@dataclass(frozen=True)
class ExperimentScore:
    experiment: Experiment
    expected_information_gain_bits: float
    expected_entropy_bits: float
    cost: float
    risk: float
    utility: float
    outcome_support: tuple[Outcome, ...]


@dataclass(frozen=True)
class ActiveObservation:
    experiment: Experiment
    outcome: Outcome
    posterior: Mapping[str, float]
    entropy_bits: float


@dataclass(frozen=True)
class ActiveCampaignReport:
    initial_posterior: Mapping[str, float]
    final_posterior: Mapping[str, float]
    observations: tuple[ActiveObservation, ...]
    spent_cost: float
    spent_risk: float
    stopped_reason: str
    claim: str = "finite_model_class_behavioral_inference_only"


def posterior_update(
    hypotheses: Sequence[FiniteHypothesis],
    prior: Mapping[str, float],
    experiment: Experiment,
    outcome: Outcome,
    *,
    likelihood_floor: float = 1.0e-15,
    complexity_penalty: float = 0.0,
) -> dict[str, float]:
    if likelihood_floor <= 0.0 or not math.isfinite(likelihood_floor):
        raise ValueError("likelihood_floor must be finite and positive")
    prior_norm = _normalise(prior)
    log_weights: dict[str, float] = {}
    for hypothesis in hypotheses:
        if hypothesis.hypothesis_id not in prior_norm:
            raise ValueError(f"missing prior for {hypothesis.hypothesis_id}")
        probability = max(likelihood_floor, hypothesis.probability(experiment, outcome))
        log_weights[hypothesis.hypothesis_id] = (
            math.log(prior_norm[hypothesis.hypothesis_id])
            + math.log(probability)
            - complexity_penalty * hypothesis.complexity
        )
    peak = max(log_weights.values())
    return _normalise({key: math.exp(value - peak) for key, value in log_weights.items()})


def predictive_outcomes(
    hypotheses: Sequence[FiniteHypothesis],
    posterior: Mapping[str, float],
    experiment: Experiment,
) -> dict[Outcome, float]:
    posterior_norm = _normalise(posterior)
    support: set[Outcome] = set()
    for hypothesis in hypotheses:
        support.update(hypothesis.likelihoods[experiment])
    result = {
        outcome: sum(
            posterior_norm[hypothesis.hypothesis_id]
            * hypothesis.probability(experiment, outcome)
            for hypothesis in hypotheses
        )
        for outcome in support
    }
    total = sum(result.values())
    if total <= 0.0:
        raise ValueError("predictive distribution has no mass")
    return {key: value / total for key, value in sorted(result.items(), key=lambda item: repr(item[0]))}


def score_experiment(
    hypotheses: Sequence[FiniteHypothesis],
    posterior: Mapping[str, float],
    experiment: Experiment,
    *,
    cost: float = 1.0,
    risk: float = 0.0,
    cost_weight: float = 0.05,
    risk_weight: float = 1.0,
) -> ExperimentScore:
    if cost < 0.0 or risk < 0.0:
        raise ValueError("cost and risk must be non-negative")
    prior_entropy = entropy_bits(posterior)
    predictive = predictive_outcomes(hypotheses, posterior, experiment)
    expected_entropy = 0.0
    for outcome, probability in predictive.items():
        updated = posterior_update(hypotheses, posterior, experiment, outcome)
        expected_entropy += probability * entropy_bits(updated)
    information_gain = max(0.0, prior_entropy - expected_entropy)
    utility = information_gain - cost_weight * cost - risk_weight * risk
    return ExperimentScore(
        experiment=experiment,
        expected_information_gain_bits=information_gain,
        expected_entropy_bits=expected_entropy,
        cost=float(cost),
        risk=float(risk),
        utility=utility,
        outcome_support=tuple(predictive),
    )


def select_experiment(
    hypotheses: Sequence[FiniteHypothesis],
    posterior: Mapping[str, float],
    experiments: Iterable[Experiment],
    *,
    costs: Mapping[Experiment, float] | None = None,
    risks: Mapping[Experiment, float] | None = None,
    authorized: Iterable[Experiment] | None = None,
) -> ExperimentScore:
    candidates = tuple(dict.fromkeys(experiments))
    if not candidates:
        raise ValueError("experiments cannot be empty")
    allowed = set(candidates if authorized is None else authorized)
    scores = [
        score_experiment(
            hypotheses,
            posterior,
            experiment,
            cost=(costs or {}).get(experiment, 1.0),
            risk=(risks or {}).get(experiment, 0.0),
        )
        for experiment in candidates
        if experiment in allowed
    ]
    if not scores:
        raise PermissionError("no authorized experiment remains")
    return max(scores, key=lambda item: (item.utility, item.expected_information_gain_bits, -item.cost, repr(item.experiment)))


def run_active_campaign(
    hypotheses: Sequence[FiniteHypothesis],
    prior: Mapping[str, float],
    experiments: Sequence[Experiment],
    oracle: Callable[[Experiment], Outcome],
    *,
    costs: Mapping[Experiment, float] | None = None,
    risks: Mapping[Experiment, float] | None = None,
    authorized: Iterable[Experiment] | None = None,
    max_rounds: int = 8,
    cost_budget: float = math.inf,
    risk_budget: float = math.inf,
    entropy_target_bits: float = 0.05,
) -> ActiveCampaignReport:
    if max_rounds < 0:
        raise ValueError("max_rounds cannot be negative")
    posterior = _normalise(prior)
    initial = dict(posterior)
    observations: list[ActiveObservation] = []
    spent_cost = 0.0
    spent_risk = 0.0
    used: set[Experiment] = set()
    stop = "round_budget_exhausted"
    for _ in range(max_rounds):
        if entropy_bits(posterior) <= entropy_target_bits:
            stop = "entropy_target_reached"
            break
        remaining = [experiment for experiment in experiments if experiment not in used]
        if not remaining:
            stop = "experiment_space_exhausted"
            break
        score = select_experiment(
            hypotheses,
            posterior,
            remaining,
            costs=costs,
            risks=risks,
            authorized=authorized,
        )
        if spent_cost + score.cost > cost_budget:
            stop = "cost_budget_blocked"
            break
        if spent_risk + score.risk > risk_budget:
            stop = "risk_budget_blocked"
            break
        outcome = oracle(score.experiment)
        posterior = posterior_update(hypotheses, posterior, score.experiment, outcome)
        spent_cost += score.cost
        spent_risk += score.risk
        used.add(score.experiment)
        observations.append(
            ActiveObservation(
                experiment=score.experiment,
                outcome=outcome,
                posterior=dict(posterior),
                entropy_bits=entropy_bits(posterior),
            )
        )
    return ActiveCampaignReport(
        initial_posterior=initial,
        final_posterior=dict(posterior),
        observations=tuple(observations),
        spent_cost=spent_cost,
        spent_risk=spent_risk,
        stopped_reason=stop,
    )
