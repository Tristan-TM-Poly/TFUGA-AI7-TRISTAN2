"""Observed-history benchmark for Capability OS cross-skill transplant.

The benchmark is intentionally finite and repository-local. It compares a naive
local-PASS policy with a governed policy over frozen historical cases derived
from PRs #501-#508. Agreement with history is not causal proof of engineering
benefit, and historical action is not assumed optimal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class TraceCase:
    case_id: str
    source_pr: int
    local_pass: bool
    independent_residual: bool
    authority_widening: bool
    observed_action: str
    evidence_class: str = "repository_history"

    @classmethod
    def from_dict(cls, payload: dict) -> "TraceCase":
        return cls(
            case_id=str(payload["case_id"]),
            source_pr=int(payload["source_pr"]),
            local_pass=bool(payload["local_pass"]),
            independent_residual=bool(payload["independent_residual"]),
            authority_widening=bool(payload.get("authority_widening", False)),
            observed_action=str(payload["observed_action"]),
            evidence_class=str(payload.get("evidence_class", "repository_history")),
        )


def naive_local_policy(case: TraceCase) -> str:
    return "PROMOTE" if case.local_pass else "HOLD"


def governed_policy(case: TraceCase) -> str:
    if not case.local_pass or case.authority_widening:
        return "HOLD"
    if case.independent_residual:
        return "CONTINUE"
    return "CRYSTALLIZE"


@dataclass(frozen=True)
class PolicyReplayReport:
    case_count: int
    naive_matches: int
    governed_matches: int
    naive_accuracy: float
    governed_accuracy: float
    match_delta: float
    avoided_premature_promotions: int
    regressions: tuple[str, ...]
    decision: str
    oak_boundary: str = (
        "PASS means the governed finite policy matches the supplied frozen repository-history labels "
        "at least as well as the naive local-PASS baseline and avoids declared premature promotions; "
        "it does not prove causal engineering savings, historical optimality, or external validity."
    )


def replay_policy_benchmark(cases: Iterable[TraceCase]) -> PolicyReplayReport:
    items = tuple(cases)
    if not items:
        return PolicyReplayReport(0, 0, 0, 0.0, 0.0, 0.0, 0, ("missing_trace_cases",), "HOLD")

    naive_matches = 0
    governed_matches = 0
    avoided = 0
    regressions: list[str] = []
    for case in items:
        naive = naive_local_policy(case)
        governed = governed_policy(case)
        if naive == case.observed_action:
            naive_matches += 1
        if governed == case.observed_action:
            governed_matches += 1
        if naive == "PROMOTE" and governed != "PROMOTE" and case.independent_residual:
            avoided += 1
        if naive == case.observed_action and governed != case.observed_action:
            regressions.append(case.case_id)

    n = len(items)
    naive_accuracy = naive_matches / n
    governed_accuracy = governed_matches / n
    delta = governed_accuracy - naive_accuracy
    decision = "PASS" if governed_accuracy >= naive_accuracy and not regressions else "HOLD"
    return PolicyReplayReport(
        n,
        naive_matches,
        governed_matches,
        naive_accuracy,
        governed_accuracy,
        delta,
        avoided,
        tuple(regressions),
        decision,
    )
