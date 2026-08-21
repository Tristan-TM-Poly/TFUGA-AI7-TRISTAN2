"""Minimum sufficient swarm court for Virtual Tristan populations.

This module evaluates finite supplied VirtualTristanPopulation members against
supplied probe outcomes. It does not execute autonomous agents or infer causal
independence from role labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Mapping

from omega_capability_os_t.core import stable_digest
from omega_capability_os_t.virtual_tristan import VirtualTristanPopulation


@dataclass(frozen=True)
class SwarmProbeResult:
    tristan_id: str
    covered_residuals: tuple[str, ...]
    verified_outputs: tuple[str, ...]
    evidence_score: float
    cost: float = 1.0

    def __post_init__(self) -> None:
        if not self.tristan_id.strip():
            raise ValueError("tristan_id must be non-empty")
        if not 0.0 <= self.evidence_score <= 1.0:
            raise ValueError("evidence_score must be in [0,1]")
        if self.cost < 0:
            raise ValueError("cost must be >= 0")


@dataclass(frozen=True)
class MarginalContribution:
    tristan_id: str
    residual_gain: int
    output_gain: int
    evidence_gain: float
    contribution_score: float


@dataclass(frozen=True)
class MinimumSufficientSwarmReport:
    selected_ids: tuple[str, ...]
    removed_ids: tuple[str, ...]
    contributions: tuple[MarginalContribution, ...]
    required_residuals: tuple[str, ...]
    required_outputs: tuple[str, ...]
    min_evidence_score: float
    decision: str
    blockers: tuple[str, ...]
    fingerprint: str
    oak_boundary: str = (
        "MINIMAL means minimum cardinality among the supplied finite members under the supplied probes and frozen coverage/evidence constraints. "
        "It does not prove universal minimality, causal contribution, agent intelligence, or independence."
    )


def _aggregate(results: Iterable[SwarmProbeResult], selected: set[str]) -> tuple[set[str], set[str], float]:
    residuals: set[str] = set()
    outputs: set[str] = set()
    evidence_values: list[float] = []
    for result in results:
        if result.tristan_id not in selected:
            continue
        residuals.update(result.covered_residuals)
        outputs.update(result.verified_outputs)
        evidence_values.append(result.evidence_score)
    evidence = min(evidence_values) if evidence_values else 0.0
    return residuals, outputs, evidence


def _satisfies(
    results: tuple[SwarmProbeResult, ...],
    selected: set[str],
    required_residuals: set[str],
    required_outputs: set[str],
    min_evidence_score: float,
) -> bool:
    residuals, outputs, evidence = _aggregate(results, selected)
    return required_residuals <= residuals and required_outputs <= outputs and evidence >= min_evidence_score


def marginal_contributions(
    population: VirtualTristanPopulation,
    probe_results: Iterable[SwarmProbeResult],
) -> tuple[MarginalContribution, ...]:
    results = tuple(probe_results)
    member_ids = {m.tristan_id for m in population.members}
    unknown = sorted({r.tristan_id for r in results} - member_ids)
    if unknown:
        raise ValueError(f"probe results reference unknown members: {unknown}")

    full_ids = set(member_ids)
    full_residuals, full_outputs, full_evidence = _aggregate(results, full_ids)
    contributions: list[MarginalContribution] = []
    for tristan_id in sorted(member_ids):
        reduced = set(full_ids)
        reduced.remove(tristan_id)
        residuals, outputs, evidence = _aggregate(results, reduced)
        residual_gain = len(full_residuals - residuals)
        output_gain = len(full_outputs - outputs)
        evidence_gain = max(0.0, full_evidence - evidence)
        score = residual_gain + output_gain + evidence_gain
        contributions.append(MarginalContribution(tristan_id, residual_gain, output_gain, round(evidence_gain, 6), round(score, 6)))
    return tuple(contributions)


def minimum_sufficient_swarm(
    population: VirtualTristanPopulation,
    probe_results: Iterable[SwarmProbeResult],
    *,
    required_residuals: Iterable[str],
    required_outputs: Iterable[str],
    min_evidence_score: float = 0.0,
) -> MinimumSufficientSwarmReport:
    if not 0.0 <= min_evidence_score <= 1.0:
        raise ValueError("min_evidence_score must be in [0,1]")

    req_res = tuple(sorted({str(x) for x in required_residuals if str(x)}))
    req_out = tuple(sorted({str(x) for x in required_outputs if str(x)}))
    member_ids = tuple(sorted(m.tristan_id for m in population.members))

    if population.decision != "READY":
        blockers = ("population_not_ready",)
        payload = {"population": population.fingerprint, "blockers": blockers}
        return MinimumSufficientSwarmReport((), member_ids, (), req_res, req_out, min_evidence_score, "HOLD", blockers, stable_digest(payload))

    results = tuple(probe_results)
    result_ids = {r.tristan_id for r in results}
    blockers: list[str] = []
    if set(member_ids) - result_ids:
        blockers.append("missing_member_probe_results")
    unknown = sorted(result_ids - set(member_ids))
    if unknown:
        blockers.append("unknown_member_probe_results")

    if blockers:
        payload = {"population": population.fingerprint, "blockers": blockers, "required_residuals": req_res, "required_outputs": req_out}
        return MinimumSufficientSwarmReport((), member_ids, (), req_res, req_out, min_evidence_score, "HOLD", tuple(sorted(blockers)), stable_digest(payload))

    contributions = marginal_contributions(population, results)
    selected: tuple[str, ...] | None = None
    req_res_set = set(req_res)
    req_out_set = set(req_out)
    for size in range(0, len(member_ids) + 1):
        feasible: list[tuple[float, tuple[str, ...]]] = []
        for combo in combinations(member_ids, size):
            chosen = set(combo)
            if not _satisfies(results, chosen, req_res_set, req_out_set, min_evidence_score):
                continue
            cost = sum(r.cost for r in results if r.tristan_id in chosen)
            feasible.append((cost, combo))
        if feasible:
            feasible.sort(key=lambda x: (x[0], x[1]))
            selected = feasible[0][1]
            break

    if selected is None:
        blockers.append("no_sufficient_swarm_in_supplied_population")
        selected = ()
        decision = "HOLD"
    else:
        decision = "MINIMAL"

    removed = tuple(x for x in member_ids if x not in set(selected))
    payload = {
        "population": population.fingerprint,
        "selected": selected,
        "removed": removed,
        "required_residuals": req_res,
        "required_outputs": req_out,
        "min_evidence_score": min_evidence_score,
        "decision": decision,
        "blockers": blockers,
    }
    return MinimumSufficientSwarmReport(selected, removed, contributions, req_res, req_out, min_evidence_score, decision, tuple(blockers), stable_digest(payload))
