"""Meta-synergy composition over validated or review-only primitives."""
from __future__ import annotations

import itertools
from typing import Iterable

from .models import MetaSynergy, SynergyCandidate, stable_id
from .ontology import type_compatibility


def _candidate_io(candidate: SynergyCandidate) -> tuple[set[str], set[str]]:
    inputs = {contract.source_type for contract in candidate.proposed_interfaces}
    outputs = {contract.target_type for contract in candidate.proposed_interfaces}
    return inputs or {"artifact"}, outputs or {"artifact"}


def compose_meta_synergies(candidates: Iterable[SynergyCandidate], max_chain: int = 4, top_k: int = 20) -> list[MetaSynergy]:
    candidates = list(candidates)
    metas: list[MetaSynergy] = []
    for length in range(2, min(max_chain, len(candidates)) + 1):
        for chain in itertools.permutations(candidates, length):
            if len({item.id for item in chain}) != length:
                continue
            compatibilities: list[float] = []
            composition: list[str] = []
            losses: list[str] = []
            invariants: set[str] = set()
            for left, right in zip(chain, chain[1:]):
                _, left_outputs = _candidate_io(left)
                right_inputs, _ = _candidate_io(right)
                compatibility = type_compatibility(left_outputs, right_inputs)
                compatibilities.append(compatibility)
                composition.append(f"{left.id} -> {right.id} ({compatibility:.3f})")
                for contract in left.proposed_interfaces + right.proposed_interfaces:
                    invariants.update(contract.preserved_invariants)
                    losses.extend(contract.declared_losses)
            if not compatibilities or min(compatibilities) < 0.25:
                continue
            uncertainty = min(1.0, sum(item.tensor.uncertainty for item in chain) / len(chain) + 0.04 * (length - 1))
            value = max(0.0, min(1.0, sum(item.score for item in chain) / len(chain) * min(compatibilities) - 0.05 * (length - 1) + 0.2))
            reversibility = sum(1.0 if not item.proposed_interfaces or all(contract.reversible for contract in item.proposed_interfaces) else 0.4 for item in chain) / len(chain)
            metas.append(
                MetaSynergy(
                    id=stable_id("MSY", [item.id for item in chain]),
                    candidate_ids=[item.id for item in chain],
                    ordered_systems=list(dict.fromkeys(system for item in chain for system in item.systems)),
                    composition=composition,
                    conserved_invariants=sorted(invariants),
                    propagated_losses=sorted(set(losses)),
                    propagated_uncertainty=round(uncertainty, 6),
                    estimated_value=round(value, 6),
                    reversibility=round(reversibility, 6),
                )
            )
    unique = {item.id: item for item in metas}
    return sorted(unique.values(), key=lambda item: (-item.estimated_value, item.id))[:top_k]
