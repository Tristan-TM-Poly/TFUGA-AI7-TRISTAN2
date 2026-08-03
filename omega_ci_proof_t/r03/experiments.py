from __future__ import annotations

from typing import Any, Mapping, Sequence

from .models import ExperimentCandidate, ExperimentPortfolio

_SENSITIVE = {"merge", "release", "publish", "read_secrets", "modify_security_policy", "financial_transaction"}


class ExperimentAllocator:
    def allocate(self, candidates: Sequence[ExperimentCandidate], *, budget: float, max_safety_risk: float = 0.25) -> ExperimentPortfolio:
        if budget < 0:
            raise ValueError("budget cannot be negative")
        selected: list[ExperimentCandidate] = []
        rejected: dict[str, str] = {}
        consumed = 0.0
        information = 0.0
        for candidate in sorted(candidates, key=lambda item: (-item.utility, item.experiment_id)):
            if candidate.required_capability in _SENSITIVE:
                rejected[candidate.experiment_id] = "sensitive capability is forbidden in A3"
                continue
            if candidate.safety_risk > max_safety_risk:
                rejected[candidate.experiment_id] = "safety risk exceeds planning threshold"
                continue
            if consumed + candidate.total_cost > budget + 1e-12:
                rejected[candidate.experiment_id] = "insufficient experiment budget"
                continue
            selected.append(candidate)
            consumed += candidate.total_cost
            information += candidate.expected_information_gain
        return ExperimentPortfolio(
            selected=tuple(selected), rejected=rejected, budget=budget,
            consumed_budget=consumed, expected_information_gain=information,
        )


def candidates_from_mapping(raw: Mapping[str, Any]) -> tuple[ExperimentCandidate, ...]:
    return tuple(
        ExperimentCandidate(
            experiment_id=str(item["experiment_id"]), description=str(item["description"]),
            expected_information_gain=float(item["expected_information_gain"]),
            compute_cost=float(item["compute_cost"]), human_cost=float(item["human_cost"]),
            safety_risk=float(item["safety_risk"]),
            affected_claim_ids=tuple(str(value) for value in item.get("affected_claim_ids", ())),
            required_capability=str(item.get("required_capability", "run_tests")),
        )
        for item in raw.get("experiments", [])
    )
