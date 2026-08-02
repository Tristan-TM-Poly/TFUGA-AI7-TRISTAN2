"""Deterministic M⁻ ablation experiments.

The ablation compares two controllers on the same ordered failure stream:
one controller records and applies negative-memory rules; the other does not.
The result is an engineering measurement of recurrence prevention, not a claim
that M⁻ improves every domain or every decision.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any, Iterable, Sequence

from .models import MMinusRule, stable_id


@dataclass(frozen=True)
class FailureCase:
    case_id: str
    pattern: str
    domain: str
    cost: float
    should_block: bool
    context: str = ""

    @classmethod
    def build(
        cls,
        pattern: str,
        domain: str,
        cost: float,
        should_block: bool,
        context: str = "",
    ) -> "FailureCase":
        return cls(
            case_id=stable_id(
                "failure-case",
                {
                    "pattern": pattern,
                    "domain": domain,
                    "cost": cost,
                    "should_block": should_block,
                    "context": context,
                },
            ),
            pattern=pattern,
            domain=domain,
            cost=cost,
            should_block=should_block,
            context=context,
        )


@dataclass(frozen=True)
class TrialOutcome:
    case_id: str
    controller: str
    attempted: bool
    blocked: bool
    failure_observed: bool
    repeated_failure: bool
    false_block: bool
    cost_incurred: float
    matched_rule_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ControllerMetrics:
    controller: str
    total_cases: int
    attempts: int
    blocks: int
    failures: int
    repeated_failures: int
    prevented_failures: int
    false_blocks: int
    total_cost: float
    precision: float
    recall: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MMinusAblationReport:
    cases_digest: str
    with_memory: ControllerMetrics
    without_memory: ControllerMetrics
    cost_reduction: float
    repeated_failure_reduction: float
    net_prevention_gain: int
    rules: tuple[MMinusRule, ...]
    outcomes: tuple[TrialOutcome, ...]
    boundary: str = (
        "This ablation measures deterministic recurrence handling on supplied fixtures. "
        "It does not prove universal scientific, organizational, or economic benefit."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "cases_digest": self.cases_digest,
            "with_memory": self.with_memory.to_dict(),
            "without_memory": self.without_memory.to_dict(),
            "cost_reduction": self.cost_reduction,
            "repeated_failure_reduction": self.repeated_failure_reduction,
            "net_prevention_gain": self.net_prevention_gain,
            "rules": [rule.to_dict() for rule in self.rules],
            "outcomes": [outcome.to_dict() for outcome in self.outcomes],
            "boundary": self.boundary,
        }


class MMinusController:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self.rules: dict[tuple[str, str], MMinusRule] = {}
        self.failure_counts: dict[tuple[str, str], int] = {}

    def process(self, case: FailureCase) -> TrialOutcome:
        key = (case.domain, case.pattern)
        rule = self.rules.get(key) if self.enabled else None
        if rule is not None:
            false_block = not case.should_block
            return TrialOutcome(
                case_id=case.case_id,
                controller="with_mminus",
                attempted=False,
                blocked=True,
                failure_observed=False,
                repeated_failure=False,
                false_block=false_block,
                cost_incurred=0.0,
                matched_rule_id=rule.rule_id,
            )

        previous_failures = self.failure_counts.get(key, 0)
        failure_observed = case.should_block
        repeated = failure_observed and previous_failures > 0
        if failure_observed:
            self.failure_counts[key] = previous_failures + 1
            if self.enabled:
                self.rules[key] = MMinusRule(
                    trigger=case.pattern,
                    root_cause=f"Observed deterministic failure pattern in {case.domain}",
                    forbidden_inference=(
                        "Do not repeat the same action under materially equivalent "
                        "conditions without a discriminating redesign."
                    ),
                    safe_replacement=(
                        "Run the prevention test or alter the causal conditions before retry."
                    ),
                    prevention_test=f"fixture::{case.case_id}",
                    domain=case.domain,
                    severity=3,
                    source_event_ids=(case.case_id,),
                )
        return TrialOutcome(
            case_id=case.case_id,
            controller="with_mminus" if self.enabled else "without_mminus",
            attempted=True,
            blocked=False,
            failure_observed=failure_observed,
            repeated_failure=repeated,
            false_block=False,
            cost_incurred=case.cost,
            matched_rule_id=None,
        )


def _metrics(controller: str, outcomes: Sequence[TrialOutcome], cases: Sequence[FailureCase]) -> ControllerMetrics:
    selected = [outcome for outcome in outcomes if outcome.controller == controller]
    by_case = {case.case_id: case for case in cases}
    true_positive_blocks = sum(
        outcome.blocked and by_case[outcome.case_id].should_block for outcome in selected
    )
    false_blocks = sum(outcome.false_block for outcome in selected)
    actual_blockable = sum(by_case[outcome.case_id].should_block for outcome in selected)
    precision = true_positive_blocks / max(true_positive_blocks + false_blocks, 1)
    recall = true_positive_blocks / max(actual_blockable, 1)
    return ControllerMetrics(
        controller=controller,
        total_cases=len(selected),
        attempts=sum(outcome.attempted for outcome in selected),
        blocks=sum(outcome.blocked for outcome in selected),
        failures=sum(outcome.failure_observed for outcome in selected),
        repeated_failures=sum(outcome.repeated_failure for outcome in selected),
        prevented_failures=true_positive_blocks,
        false_blocks=false_blocks,
        total_cost=sum(outcome.cost_incurred for outcome in selected),
        precision=precision,
        recall=recall,
    )


def run_mminus_ablation(cases: Iterable[FailureCase]) -> MMinusAblationReport:
    case_list = list(cases)
    if not case_list:
        raise ValueError("at least one failure case is required")
    for case in case_list:
        if not case.pattern.strip() or not case.domain.strip():
            raise ValueError("failure cases require pattern and domain")
        if case.cost < 0:
            raise ValueError("failure case cost must be non-negative")

    enabled = MMinusController(enabled=True)
    disabled = MMinusController(enabled=False)
    outcomes: list[TrialOutcome] = []
    for case in case_list:
        outcomes.append(enabled.process(case))
        outcomes.append(disabled.process(case))

    with_metrics = _metrics("with_mminus", outcomes, case_list)
    without_metrics = _metrics("without_mminus", outcomes, case_list)
    cost_reduction = (
        (without_metrics.total_cost - with_metrics.total_cost)
        / max(without_metrics.total_cost, 1e-12)
    )
    repeated_reduction = (
        (without_metrics.repeated_failures - with_metrics.repeated_failures)
        / max(without_metrics.repeated_failures, 1)
    )
    digest_payload = "\n".join(
        f"{case.case_id}|{case.pattern}|{case.domain}|{case.cost}|{case.should_block}"
        for case in case_list
    )
    digest = sha256(digest_payload.encode("utf-8")).hexdigest()
    return MMinusAblationReport(
        cases_digest=digest,
        with_memory=with_metrics,
        without_memory=without_metrics,
        cost_reduction=cost_reduction,
        repeated_failure_reduction=repeated_reduction,
        net_prevention_gain=(
            with_metrics.prevented_failures - with_metrics.false_blocks
        ),
        rules=tuple(enabled.rules.values()),
        outcomes=tuple(outcomes),
    )


def canonical_ablation_fixture() -> tuple[FailureCase, ...]:
    """Return a mixed fixture containing recurrence and near-match controls."""

    rows = [
        ("missing_baseline", "science", 8.0, True, "result claims superiority"),
        ("missing_baseline", "science", 8.0, True, "same claim, second model"),
        ("missing_baseline", "science", 8.0, True, "same claim, third model"),
        ("unit_mismatch", "science", 5.0, True, "pressure mixed Pa and kPa"),
        ("unit_mismatch", "science", 5.0, True, "second pressure pipeline"),
        ("unsafe_direct_mutation", "software", 13.0, True, "deployment without sandbox"),
        ("unsafe_direct_mutation", "software", 13.0, True, "second deployment attempt"),
        ("doc_symbol_missing", "software", 3.0, True, "README names absent API"),
        ("doc_symbol_missing", "software", 3.0, True, "second stale README"),
        ("known_safe_read", "software", 1.0, False, "read-only repository scan"),
        ("calibrated_measurement", "science", 4.0, False, "traceable instrument"),
        ("user_interview", "product", 2.0, False, "consented discovery interview"),
        ("unverified_revenue_projection", "product", 6.0, True, "forecast described as fact"),
        ("unverified_revenue_projection", "product", 6.0, True, "repeated forecast"),
    ]
    return tuple(FailureCase.build(*row) for row in rows)
