from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .families import FAMILY_BY_ID
from .hashing import stable_id
from .models import AttemptRecord, AttemptStatus, ProblemInstance, StrategySpec


@dataclass(frozen=True)
class VerificationResult:
    status: AttemptStatus
    observed_output: Any
    expected_output: Any
    counterexample_signature: str | None
    exception_type: str | None


class ExactFixtureVerifier:
    """Verifies original synthetic fixtures against an independent family oracle.

    This is not a proof of general algorithm correctness. It certifies only the
    materialized fixture instance and explicitly records the counterexample when a
    candidate disagrees with the oracle.
    """

    def verify(
        self,
        problem: ProblemInstance,
        strategy: StrategySpec,
        observed_output: Any = None,
        exception: BaseException | None = None,
    ) -> VerificationResult:
        if exception is not None:
            return VerificationResult(
                status=AttemptStatus.EXCEPTION,
                observed_output=None,
                expected_output=problem.expected_output,
                counterexample_signature=stable_id(
                    "counterexample",
                    {
                        "family": problem.family_id,
                        "strategy": strategy.strategy_id,
                        "input": dict(problem.input_payload),
                        "exception": type(exception).__name__,
                    },
                    length=24,
                ),
                exception_type=type(exception).__name__,
            )

        oracle_output = FAMILY_BY_ID[problem.family_id].oracle(problem.input_payload)
        if oracle_output != problem.expected_output:
            raise ValueError("stored expected output diverges from family oracle")
        if observed_output == oracle_output:
            return VerificationResult(
                status=AttemptStatus.VERIFIED,
                observed_output=observed_output,
                expected_output=oracle_output,
                counterexample_signature=None,
                exception_type=None,
            )
        return VerificationResult(
            status=AttemptStatus.WRONG_ANSWER,
            observed_output=observed_output,
            expected_output=oracle_output,
            counterexample_signature=stable_id(
                "counterexample",
                {
                    "family": problem.family_id,
                    "strategy": strategy.strategy_id,
                    "input": dict(problem.input_payload),
                    "expected": oracle_output,
                    "observed": observed_output,
                },
                length=24,
            ),
            exception_type=None,
        )


def attempt_record(
    *,
    problem: ProblemInstance,
    strategy: StrategySpec,
    attempt_index: int,
    result: VerificationResult,
    cost_units: int,
) -> AttemptRecord:
    return AttemptRecord(
        problem_id=problem.problem_id,
        strategy_id=strategy.strategy_id,
        attempt_index=attempt_index,
        status=result.status,
        observed_output=result.observed_output,
        expected_output=result.expected_output,
        cost_units=cost_units,
        counterexample_signature=result.counterexample_signature,
        exception_type=result.exception_type,
    )
