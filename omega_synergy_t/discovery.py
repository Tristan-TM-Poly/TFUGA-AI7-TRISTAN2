"""Bounded candidate search, closure bridges and portfolio selection."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import itertools
from typing import Iterable

from .models import CreationDNA, InterfaceContract, SynergyCandidate, stable_id
from .ontology import jaccard, type_compatibility
from .scoring import build_candidate


@dataclass(slots=True)
class ClosureBridge:
    id: str
    provider: str
    target: str
    need_id: str
    capability_id: str
    contract: InterfaceContract
    expected_gain: float
    falsification_test: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "provider": self.provider,
            "target": self.target,
            "need_id": self.need_id,
            "capability_id": self.capability_id,
            "contract": self.contract.to_dict(),
            "expected_gain": self.expected_gain,
            "falsification_test": self.falsification_test,
        }


def _co_mentions(file_systems: dict[str, list[str]]) -> Counter[tuple[str, str]]:
    counter: Counter[tuple[str, str]] = Counter()
    for systems in file_systems.values():
        unique = sorted(set(systems))
        if len(unique) <= 80:
            counter.update(itertools.combinations(unique, 2))
    return counter


def discover_pairs(creations: Iterable[CreationDNA], file_systems: dict[str, list[str]], limit: int = 600) -> list[SynergyCandidate]:
    items = list(creations)
    co = _co_mentions(file_systems)
    token_buckets: dict[str, set[int]] = defaultdict(set)
    domain_buckets: dict[str, set[int]] = defaultdict(set)
    for index, item in enumerate(items):
        for token in item.tokens[:30]:
            token_buckets[token].add(index)
        for domain in item.domains[:6]:
            domain_buckets[domain].add(index)
    pairs: set[tuple[int, int]] = set()
    for bucket in [*token_buckets.values(), *domain_buckets.values()]:
        members = sorted(bucket)[:140]
        pairs.update(itertools.combinations(members, 2))
    pairs.update(itertools.combinations(range(min(60, len(items))), 2))

    def lookup(left: str, right: str) -> float:
        return min(1.0, co[tuple(sorted((left, right)))] / 4.0)

    candidates = [build_candidate([items[left], items[right]], lookup) for left, right in pairs]
    candidates.sort(key=lambda item: (-item.score, item.systems))
    return candidates[:limit]


def discover_n_order(creations: Iterable[CreationDNA], file_systems: dict[str, list[str]], max_order: int = 4, beam_width: int = 96, top_k: int = 25) -> dict[int, list[SynergyCandidate]]:
    if not 2 <= max_order <= 8:
        raise ValueError("max_order must be between 2 and 8")
    if beam_width < top_k or top_k < 1:
        raise ValueError("require beam_width >= top_k >= 1")
    items = list(creations)
    by_name = {item.name: item for item in items}
    pairs = discover_pairs(items, file_systems, limit=max(beam_width * 8, top_k * 12))
    output: dict[int, list[SynergyCandidate]] = {2: pairs[:top_k]}
    frontier = pairs[:beam_width]
    neighbor: dict[str, set[str]] = defaultdict(set)
    for candidate in pairs:
        left, right = candidate.systems
        neighbor[left].add(right)
        neighbor[right].add(left)

    for order in range(3, max_order + 1):
        expanded: dict[tuple[str, ...], SynergyCandidate] = {}
        for candidate in frontier:
            current = set(candidate.systems)
            pool = set().union(*(neighbor[name] for name in current)) - current
            if not pool:
                pool = set(by_name) - current
            for name in sorted(pool):
                names = tuple(sorted(current | {name}))
                if len(names) != order or names in expanded:
                    continue
                expanded[names] = build_candidate([by_name[item] for item in names])
        frontier = sorted(expanded.values(), key=lambda item: (-item.score, item.systems))[:beam_width]
        output[order] = frontier[:top_k]
        if not frontier:
            break
    return output


def closure_bridges(creations: Iterable[CreationDNA], threshold: float = 0.35) -> list[ClosureBridge]:
    items = list(creations)
    bridges: list[ClosureBridge] = []
    for provider in items:
        for target in items:
            if provider.id == target.id:
                continue
            for capability in provider.capabilities:
                for need in target.needs:
                    compatibility = type_compatibility(capability.output_types, need.desired_output_types)
                    if compatibility < threshold:
                        continue
                    source_type = capability.output_types[0] if capability.output_types else "artifact"
                    target_type = need.desired_output_types[0] if need.desired_output_types else "artifact"
                    contract = InterfaceContract(
                        id=stable_id("IFC", provider.id, target.id, capability.id, need.id),
                        source_type=source_type,
                        target_type=target_type,
                        mappings={source_type: target_type},
                        preserved_invariants=["provenance_preservation", "uncertainty_non_decrease_without_evidence"],
                        declared_losses=capability.losses,
                        tests=["schema_validation", "adapter_round_trip", "provenance_integrity"],
                        reversible=not capability.losses,
                        confidence=compatibility,
                    )
                    bridges.append(
                        ClosureBridge(
                            id=stable_id("BRG", provider.id, target.id, capability.id, need.id),
                            provider=provider.name,
                            target=target.name,
                            need_id=need.id,
                            capability_id=capability.id,
                            contract=contract,
                            expected_gain=round(compatibility * need.priority, 6),
                            falsification_test="Compare target alone, provider alone, composed adapter, and a simplest external baseline.",
                        )
                    )
    bridges.sort(key=lambda item: (-item.expected_gain, item.provider, item.target))
    return bridges


def select_portfolio(candidates: Iterable[SynergyCandidate], budget: float, max_items: int = 12, diversity_weight: float = 0.2) -> list[SynergyCandidate]:
    selected: list[SynergyCandidate] = []
    spent = 0.0
    remaining = list(candidates)
    while remaining and len(selected) < max_items:
        best = None
        best_utility = float("-inf")
        for candidate in remaining:
            cost = max(0.05, candidate.tensor.integration_cost + candidate.tensor.risk)
            if spent + cost > budget:
                continue
            overlap = max((jaccard(candidate.systems, item.systems) for item in selected), default=0.0)
            utility = candidate.score + diversity_weight * (1.0 - overlap) + 0.1 * candidate.tensor.option_value - 0.08 * cost
            if utility > best_utility:
                best, best_utility = candidate, utility
        if best is None:
            break
        selected.append(best)
        spent += max(0.05, best.tensor.integration_cost + best.tensor.risk)
        remaining.remove(best)
    return selected
