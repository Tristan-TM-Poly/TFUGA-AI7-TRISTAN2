"""Deterministic MetaScienceBench-T v0.1.

The benchmark compares a fixed experiment policy with an adaptive disagreement-
mining policy under equal toy budgets. It is deliberately tiny: the goal is to
make the meta-science loop executable and falsifiable, not to claim scientific
superiority from a synthetic fixture.
"""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from math import log2

from .models import (
    BenchmarkReport,
    ClaimPacket,
    Experiment,
    Representation,
    StrategyName,
    StrategyResult,
    TheoryGenome,
    ToyProblem,
)
from .oak import evaluate_oak, meta_oak_mutation_campaign


def build_fixture() -> ToyProblem:
    shared = ("observable:y", "domain:x>=0")
    linear = TheoryGenome(
        theory_id="T_linear",
        assumptions=("deterministic", "y=x"),
        domain="x>=0",
        falsifiers=("observe y != x beyond tolerance",),
        representations=(
            Representation("symbolic", "y=x", shared + ("order:1",)),
            Representation("program", "lambda x: x", shared + ("order:1",)),
        ),
        model_kind="linear",
    )
    quadratic = TheoryGenome(
        theory_id="T_quadratic",
        assumptions=("deterministic", "y=x^2"),
        domain="x>=0",
        falsifiers=("observe y != x^2 beyond tolerance",),
        representations=(
            Representation("symbolic", "y=x^2", shared + ("order:2",)),
            Representation("program", "lambda x: x*x", shared + ("order:2",)),
        ),
        model_kind="quadratic",
    )
    return ToyProblem(
        theories=(linear, quadratic),
        experiments=(
            Experiment("E_fixed_alias", x=1.0, cost=1.0),
            Experiment("E_discriminating", x=2.0, cost=1.0),
        ),
        true_theory_id="T_linear",
    )


def _cvcd_invariants(problem: ToyProblem) -> tuple[str, ...]:
    sets = [
        set(rep.invariants)
        for theory in problem.theories
        for rep in theory.representations
    ]
    if not sets:
        return ()
    return tuple(sorted(set.intersection(*sets)))


def _prediction_disagreement(problem: ToyProblem, experiment: Experiment) -> float:
    predictions = [theory.predict(experiment.x) for theory in problem.theories]
    mean = sum(predictions) / len(predictions)
    variance = sum((value - mean) ** 2 for value in predictions) / len(predictions)
    return variance / max(experiment.cost, 1e-15)


def select_experiment(problem: ToyProblem, strategy: StrategyName) -> Experiment:
    if strategy == "fixed":
        return problem.experiments[0]
    if strategy == "adaptive":
        return max(
            problem.experiments,
            key=lambda exp: (_prediction_disagreement(problem, exp), -exp.cost, exp.experiment_id),
        )
    raise ValueError(f"unsupported strategy: {strategy}")


def _true_theory(problem: ToyProblem) -> TheoryGenome:
    for theory in problem.theories:
        if theory.theory_id == problem.true_theory_id:
            return theory
    raise ValueError(f"unknown true theory: {problem.true_theory_id}")


def _provenance_digest(
    strategy: StrategyName,
    experiment: Experiment,
    observation: float,
    survivors: tuple[str, ...],
) -> str:
    canonical = (
        f"strategy={strategy}|experiment={experiment.experiment_id}|x={experiment.x:.17g}|"
        f"observation={observation:.17g}|survivors={','.join(survivors)}"
    )
    return "sha256:" + sha256(canonical.encode("utf-8")).hexdigest()


def run_strategy(problem: ToyProblem, strategy: StrategyName) -> StrategyResult:
    experiment = select_experiment(problem, strategy)
    observation = _true_theory(problem).predict(experiment.x)
    survivors = tuple(
        theory.theory_id
        for theory in problem.theories
        if abs(theory.predict(experiment.x) - observation) <= problem.tolerance
    )
    before = log2(len(problem.theories)) if len(problem.theories) > 1 else 0.0
    after = log2(len(survivors)) if len(survivors) > 1 else 0.0
    knowledge_gain = before - after
    residual = min(
        abs(theory.predict(experiment.x) - observation)
        for theory in problem.theories
        if theory.theory_id in survivors
    )
    claim = ClaimPacket(
        claim=f"{strategy} leaves {len(survivors)} surviving theory/theories",
        provenance=_provenance_digest(strategy, experiment, observation, survivors),
        uncertainty=problem.tolerance,
        baseline_declared=True,
        reproducible=True,
        unit_consistent=True,
        falsifier_declared=True,
        survivor_count=len(survivors),
        residual=residual,
        residual_tolerance=problem.tolerance,
    )
    oak = evaluate_oak(claim)
    verified_gain = knowledge_gain / experiment.cost if oak.decision == "PROMOTE" else 0.0
    return StrategyResult(
        strategy=strategy,
        selected_experiment=experiment,
        observation=observation,
        survivors=survivors,
        knowledge_gain_bits=knowledge_gain,
        verified_gain_per_cost=verified_gain,
        disagreement_score=_prediction_disagreement(problem, experiment),
        cvcd_invariants=_cvcd_invariants(problem),
        claim=claim,
        oak=oak,
    )


def run_benchmark(problem: ToyProblem | None = None) -> BenchmarkReport:
    problem = problem or build_fixture()
    fixed = run_strategy(problem, "fixed")
    adaptive = run_strategy(problem, "adaptive")
    campaign = meta_oak_mutation_campaign(adaptive.claim)

    promoted: StrategyName = (
        "adaptive"
        if adaptive.verified_gain_per_cost > fixed.verified_gain_per_cost
        and adaptive.oak.decision == "PROMOTE"
        and campaign.mutation_score == 1.0
        else "fixed"
    )
    m_plus = (
        f"strategy:{promoted}",
        f"cvcd:{'|'.join(adaptive.cvcd_invariants)}",
        f"meta_oak_mutation_score:{campaign.mutation_score:.3f}",
    )
    m_minus = tuple(
        ["fixed_policy:underdetermined"]
        + [f"epistemic_fault:{fault}" for fault in campaign.detected_faults]
        + [f"missed_epistemic_fault:{fault}" for fault in campaign.missed_faults]
    )
    return BenchmarkReport(
        fixed=fixed,
        adaptive=adaptive,
        mutation_campaign=campaign,
        promoted_strategy=promoted,
        m_plus=m_plus,
        m_minus=m_minus,
    )


def report_as_dict(report: BenchmarkReport) -> dict[str, object]:
    return asdict(report)
