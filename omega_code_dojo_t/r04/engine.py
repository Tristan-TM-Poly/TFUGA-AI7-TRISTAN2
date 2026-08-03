from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from .families import FAMILY_BY_ID, solve
from .hashing import stable_id
from .models import (
    AttemptStatus,
    FamilyMetrics,
    ProblemStatus,
    ResolutionPolicy,
    ResolutionReceipt,
    ResolutionRecord,
)
from .portfolio import DEFAULT_PORTFOLIO, ProblemPortfolio
from .verifier import ExactFixtureVerifier, attempt_record


@dataclass
class ResolutionEngine:
    portfolio: ProblemPortfolio = DEFAULT_PORTFOLIO
    verifier: ExactFixtureVerifier = ExactFixtureVerifier()

    def run(self, policy: ResolutionPolicy) -> ResolutionReceipt:
        records: list[ResolutionRecord] = []
        total_cost = 0
        for problem in self.portfolio.materialize(policy):
            if policy.permanent_total_cap is not None and len(records) >= policy.permanent_total_cap:
                break
            family = FAMILY_BY_ID[problem.family_id]
            attempts = []
            selected_strategy_id: str | None = None
            for attempt_index, strategy in enumerate(
                family.strategies[: policy.max_attempts_per_problem], start=1
            ):
                exception: BaseException | None = None
                observed: Any = None
                try:
                    observed = solve(strategy.strategy_id, problem.input_payload)
                except BaseException as exc:
                    exception = exc
                result = self.verifier.verify(
                    problem,
                    strategy,
                    observed_output=observed,
                    exception=exception,
                )
                cost = _attempt_cost(problem.input_payload, strategy.exact)
                total_cost += cost
                attempts.append(
                    attempt_record(
                        problem=problem,
                        strategy=strategy,
                        attempt_index=attempt_index,
                        result=result,
                        cost_units=cost,
                    )
                )
                if result.status is AttemptStatus.VERIFIED:
                    selected_strategy_id = strategy.strategy_id
                    break
            solved = selected_strategy_id is not None
            records.append(
                ResolutionRecord(
                    problem=problem,
                    status=(
                        ProblemStatus.SOLVED_FIXTURE if solved else ProblemStatus.UNRESOLVED
                    ),
                    attempts=tuple(attempts),
                    selected_strategy_id=selected_strategy_id,
                    proof_obligations=(
                        "fixture_output_matches_independent_oracle",
                        "all_failed_candidates_preserved_as_counterexamples",
                        "no_general_correctness_claim_from_finite_fixture",
                    ),
                )
            )

        family_metrics = _family_metrics(records)
        solved_count = sum(record.solved for record in records)
        campaign_id = stable_id(
            "resolution-campaign",
            {
                "policy": policy.to_dict(),
                "record_ids": [record.problem.problem_id for record in records],
                "selected": [record.selected_strategy_id for record in records],
            },
            length=24,
        )
        receipt = ResolutionReceipt(
            campaign_id=campaign_id,
            system_version="R0.4",
            logical_problem_space=self.portfolio.logical_problem_space,
            materialized_problems=len(records),
            solved_problems=solved_count,
            unresolved_problems=len(records) - solved_count,
            total_attempts=sum(len(record.attempts) for record in records),
            total_cost_units=total_cost,
            permanent_total_cap=policy.permanent_total_cap,
            records=tuple(records),
            family_metrics=family_metrics,
            claims={
                "synthetic_fixture_resolution_claimed": True,
                "general_algorithm_correctness_claimed": False,
                "open_problem_solution_claimed": False,
                "codewars_affiliation_claimed": False,
                "neural_training_claimed": False,
                "human_learning_claimed": False,
                "no_permanent_total_cap_claimed": policy.permanent_total_cap is None,
            },
        )
        return receipt.with_hash()


def _attempt_cost(payload: Any, exact: bool) -> int:
    if isinstance(payload, dict):
        size = sum(_size(value) for value in payload.values())
    else:
        size = _size(payload)
    return max(1, size * (2 if exact else 1))


def _size(value: Any) -> int:
    if isinstance(value, (str, bytes, list, tuple, set, dict)):
        if isinstance(value, dict):
            return 1 + sum(_size(item) for item in value.values())
        return 1 + sum(_size(item) for item in value) if not isinstance(value, (str, bytes)) else max(1, len(value))
    return 1


def _family_metrics(records: list[ResolutionRecord]) -> tuple[FamilyMetrics, ...]:
    buckets: dict[str, list[ResolutionRecord]] = defaultdict(list)
    for record in records:
        buckets[record.problem.family_id].append(record)
    metrics = []
    for family_id in sorted(buckets):
        items = buckets[family_id]
        metrics.append(
            FamilyMetrics(
                family_id=family_id,
                attempted=len(items),
                solved=sum(item.solved for item in items),
                total_attempts=sum(len(item.attempts) for item in items),
                fallback_solves=sum(item.solved and item.fallback_depth > 0 for item in items),
                counterexamples=sum(
                    attempt.counterexample_signature is not None
                    for item in items
                    for attempt in item.attempts
                ),
            )
        )
    return tuple(metrics)
