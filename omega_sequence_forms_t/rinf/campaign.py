"""Adaptive finite campaigns over the unbounded R∞ research program."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import heapq
import json
import math
import time
from typing import Callable, Iterable, Iterator, Mapping, Sequence

from .address import CellSpace, iter_addresses
from .catalog import catalog_payload
from .models import (
    CampaignBudget,
    CampaignCellResult,
    CampaignReceipt,
    CellAddress,
)


@dataclass(frozen=True)
class CellEstimate:
    address: CellAddress
    novelty: float
    evidence_gain: float
    coverage_gain: float
    counterexample_gain: float
    estimated_cost: float
    risk: float
    dependencies_ready: bool = True

    @property
    def marginal_value(self) -> float:
        positive = self.novelty + self.evidence_gain + self.coverage_gain + self.counterexample_gain
        return max(0.0, positive - self.risk)

    @property
    def value_cost_ratio(self) -> float:
        if self.estimated_cost <= 0:
            return math.inf if self.marginal_value > 0 else 0.0
        return self.marginal_value / self.estimated_cost


CellEstimator = Callable[[CellAddress], CellEstimate]
CellExecutor = Callable[[CellEstimate], CampaignCellResult]


def deterministic_estimator(address: CellAddress) -> CellEstimate:
    """Stable baseline prioritizer used by fixtures and dry runs."""

    digest = sha256(address.render().encode("ascii")).digest()
    values = [int.from_bytes(digest[offset : offset + 2], "big") / 65535 for offset in range(0, 12, 2)]
    novelty, evidence, coverage, counterexample, cost_raw, risk = values
    family_bonus = 0.5 if address.family < 32 else 0.0
    transformation_bonus = 0.3 if address.transformation < 64 else 0.0
    return CellEstimate(
        address=address,
        novelty=novelty + family_bonus,
        evidence_gain=evidence + transformation_bonus,
        coverage_gain=coverage,
        counterexample_gain=counterexample,
        estimated_cost=0.1 + 4.9 * cost_raw,
        risk=0.75 * risk,
        dependencies_ready=(digest[-1] % 7 != 0),
    )


def dry_run_executor(estimate: CellEstimate) -> CampaignCellResult:
    digest = sha256((estimate.address.render() + ":execute").encode("ascii")).digest()
    accepted = estimate.dependencies_ready and estimate.value_cost_ratio >= 0.5
    counterexample = digest[0] % 11 == 0
    status = "candidate_generated" if accepted else "deferred"
    failure_codes = ()
    if not estimate.dependencies_ready:
        failure_codes = ("dependency_not_ready",)
    elif not accepted:
        failure_codes = ("low_value_cost_ratio",)
    candidate_ids = (f"candidate.{estimate.address.digest()[:16]}",) if accepted else ()
    residue_ids = (f"counterexample.{estimate.address.digest()[16:32]}",) if counterexample else ()
    return CampaignCellResult(
        address=estimate.address,
        status=status,
        marginal_value=estimate.marginal_value,
        estimated_cost=estimate.estimated_cost,
        candidate_ids=candidate_ids,
        residue_ids=residue_ids,
        failure_codes=failure_codes,
    )


@dataclass
class AdaptiveFrontier:
    estimator: CellEstimator
    heap: list[tuple[float, int, CellEstimate]] = field(default_factory=list)
    seen: set[CellAddress] = field(default_factory=set)
    _counter: int = 0

    def add(self, address: CellAddress) -> None:
        if address in self.seen:
            return
        self.seen.add(address)
        estimate = self.estimator(address)
        priority = -estimate.value_cost_ratio
        heapq.heappush(self.heap, (priority, self._counter, estimate))
        self._counter += 1

    def extend(self, addresses: Iterable[CellAddress]) -> None:
        for address in addresses:
            self.add(address)

    def pop(self) -> CellEstimate:
        if not self.heap:
            raise IndexError("empty frontier")
        return heapq.heappop(self.heap)[2]

    def __bool__(self) -> bool:
        return bool(self.heap)


def _neighbors(address: CellAddress, space: CellSpace) -> Iterator[CellAddress]:
    values = list(address.as_mapping().values())
    for axis, size in enumerate(space.shape):
        for delta in (-1, 1):
            candidate = list(values)
            candidate[axis] = (candidate[axis] + delta) % size
            yield CellAddress(*candidate)


def run_campaign(
    *,
    campaign_id: str,
    seed: int,
    budget: CampaignBudget,
    estimator: CellEstimator = deterministic_estimator,
    executor: CellExecutor = dry_run_executor,
    space: CellSpace | None = None,
    initial_frontier: int = 4096,
    expansion_per_accept: int = 4,
) -> CampaignReceipt:
    if initial_frontier <= 0:
        raise ValueError("initial_frontier must be positive")
    if expansion_per_accept < 0:
        raise ValueError("expansion_per_accept must be non-negative")
    space = space or CellSpace()
    catalog = catalog_payload()
    frontier = AdaptiveFrontier(estimator)
    addresses = iter_addresses(space=space, seed=seed)
    for _ in range(min(initial_frontier, space.logical_cells)):
        frontier.add(next(addresses))

    started = time.monotonic()
    results: list[CampaignCellResult] = []
    compute_spent = 0.0
    accepted = 0
    rejected = 0
    counterexamples = 0
    stop_reason = "frontier_exhausted"

    while frontier:
        if budget.wall_time_seconds is not None and time.monotonic() - started >= budget.wall_time_seconds:
            stop_reason = "wall_time_budget"
            break
        if budget.compute_units is not None and compute_spent >= budget.compute_units:
            stop_reason = "compute_budget"
            break
        if budget.materialized_cell_cap is not None and len(results) >= budget.materialized_cell_cap:
            stop_reason = "campaign_materialized_cell_cap"
            break

        estimate = frontier.pop()
        if estimate.marginal_value < budget.minimum_marginal_value:
            stop_reason = "marginal_value_threshold"
            break
        if estimate.value_cost_ratio < budget.minimum_value_cost_ratio:
            stop_reason = "value_cost_threshold"
            break
        if budget.compute_units is not None and compute_spent + estimate.estimated_cost > budget.compute_units:
            stop_reason = "next_cell_exceeds_compute_budget"
            break

        result = executor(estimate)
        results.append(result)
        compute_spent += estimate.estimated_cost
        if result.candidate_ids:
            accepted += len(result.candidate_ids)
            for neighbor in list(_neighbors(result.address, space))[:expansion_per_accept]:
                frontier.add(neighbor)
        else:
            rejected += 1
        counterexamples += len(result.residue_ids)

    return CampaignReceipt(
        campaign_id=campaign_id,
        catalog_digest=str(catalog["catalog_digest"]),
        seed=seed,
        budget=budget,
        selected_cells=len(frontier.seen),
        executed_cells=len(results),
        accepted_candidates=accepted,
        rejected_candidates=rejected,
        counterexamples=counterexamples,
        results=results,
        stop_reason=stop_reason,
    )


def campaign_summary(receipt: CampaignReceipt) -> dict[str, object]:
    payload = receipt.to_dict()
    payload["receipt_digest"] = receipt.digest()
    payload["results"] = {
        "count": len(receipt.results),
        "accepted": sum(bool(result.candidate_ids) for result in receipt.results),
        "deferred": sum(not result.candidate_ids for result in receipt.results),
        "counterexamples": sum(len(result.residue_ids) for result in receipt.results),
        "mean_value_cost_ratio": (
            sum(result.value_cost_ratio for result in receipt.results) / len(receipt.results)
            if receipt.results else 0.0
        ),
    }
    return payload
