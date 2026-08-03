"""Adaptive campaign conductor combining posterior, design, leases and calibration gates."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Callable, Iterable, Mapping


@dataclass(frozen=True)
class CampaignBudget:
    max_rounds: int
    max_cost_units: float
    max_failures: int
    max_risk: float


@dataclass(frozen=True)
class CampaignStep:
    sequence: int
    experiment_id: str
    cost_units: float
    risk: float
    success: bool
    evidence_digest: str
    posterior_entropy: float
    novelty_mass: float


@dataclass(frozen=True)
class CampaignCheckpoint:
    next_sequence: int
    consumed_cost_units: float
    failures: int
    chain_digest: str
    stopped_reason: str
    permanent_total_cap: None = None


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def run_adaptive_campaign(
    experiment_ids: Iterable[str],
    *,
    budget: CampaignBudget,
    cost: Callable[[str], float],
    risk: Callable[[str], float],
    execute: Callable[[str], Mapping[str, object]],
    posterior_entropy: Callable[[int], float],
    novelty_mass: Callable[[int], float],
    previous_digest: str = "sha256:" + "0" * 64,
) -> tuple[tuple[CampaignStep, ...], CampaignCheckpoint]:
    if budget.max_rounds <= 0 or budget.max_cost_units < 0 or budget.max_failures < 0 or not 0 <= budget.max_risk <= 1:
        raise ValueError("invalid campaign budget")
    steps: list[CampaignStep] = []
    consumed = 0.0
    failures = 0
    chain = previous_digest
    stopped = "frontier_exhausted"
    seen: set[str] = set()
    for sequence, experiment_id in enumerate(experiment_ids):
        if sequence >= budget.max_rounds:
            stopped = "round_budget"
            break
        if experiment_id in seen:
            raise ValueError("duplicate experiment id")
        seen.add(experiment_id)
        candidate_cost = float(cost(experiment_id))
        candidate_risk = float(risk(experiment_id))
        if not math.isfinite(candidate_cost) or candidate_cost < 0 or not 0 <= candidate_risk <= 1:
            raise ValueError("invalid candidate cost or risk")
        if candidate_risk > budget.max_risk:
            stopped = "risk_gate"
            break
        if consumed + candidate_cost > budget.max_cost_units:
            stopped = "cost_budget"
            break
        evidence = execute(experiment_id)
        success = bool(evidence.get("success", False))
        evidence_digest = _digest(evidence)
        step = CampaignStep(
            sequence=sequence,
            experiment_id=experiment_id,
            cost_units=candidate_cost,
            risk=candidate_risk,
            success=success,
            evidence_digest=evidence_digest,
            posterior_entropy=float(posterior_entropy(sequence)),
            novelty_mass=float(novelty_mass(sequence)),
        )
        if not math.isfinite(step.posterior_entropy) or step.posterior_entropy < 0 or not 0 <= step.novelty_mass <= 1:
            raise ValueError("invalid posterior metrics")
        steps.append(step)
        consumed += candidate_cost
        if not success:
            failures += 1
            if failures > budget.max_failures:
                stopped = "failure_budget"
                chain = _digest({"previous": chain, "step": asdict(step)})
                break
        chain = _digest({"previous": chain, "step": asdict(step)})
    checkpoint = CampaignCheckpoint(
        next_sequence=len(steps),
        consumed_cost_units=consumed,
        failures=failures,
        chain_digest=chain,
        stopped_reason=stopped,
    )
    return tuple(steps), checkpoint
