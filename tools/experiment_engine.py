"""Experiment Engine for Ω-AIT-RESEARCH-FACTORY-T.

Builds conservative experiment plans from hypotheses. It plans only; it does not
execute external actions or replace domain review.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExperimentPlan:
    hypothesis: str
    baseline: str
    metric: str
    test_data: str
    expected_failure: str
    success_condition: str
    residue: str
    next_iteration: str
    ready: bool


def build_experiment_plan(
    *,
    hypothesis: str,
    baseline: str = "define a simple baseline",
    metric: str = "define measurable metric",
    test_data: str = "define small safe test dataset",
    expected_failure: str = "state how the hypothesis could fail",
    success_condition: str = "state minimum success threshold",
    residue: str = "record unexplained remainder",
) -> ExperimentPlan:
    fields = [hypothesis, baseline, metric, test_data, expected_failure, success_condition]
    ready = all(bool(field and field.strip()) for field in fields)
    next_iteration = "run toy test in sandbox" if ready else "complete missing experiment fields"
    return ExperimentPlan(
        hypothesis=hypothesis,
        baseline=baseline,
        metric=metric,
        test_data=test_data,
        expected_failure=expected_failure,
        success_condition=success_condition,
        residue=residue,
        next_iteration=next_iteration,
        ready=ready,
    )
