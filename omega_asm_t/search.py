from __future__ import annotations

from itertools import combinations

from .backends import emit_dot_u64, static_instruction_count, supported_variants
from .cost_model import get_static_cost_profile
from .models import Candidate


def estimate_builtin_candidates(architecture: str) -> list[Candidate]:
    """Create deterministic P2 candidates from explicit versioned heuristics.

    `estimated_cost_units` are ordinal ranking units, not hardware cycles.
    Runtime performance claims require native measurement on the target CPU.
    """

    architecture_norm = architecture.lower().replace("-", "_")
    candidates: list[Candidate] = []
    for variant in supported_variants(architecture_norm):
        assembly = emit_dot_u64(architecture_norm, variant)
        instruction_count = static_instruction_count(assembly)
        profile = get_static_cost_profile(architecture_norm, variant)
        candidates.append(
            Candidate(
                name=f"dot_u64/{profile.architecture}/{variant}",
                architecture=profile.architecture,
                variant=variant,
                estimated_cost_units=profile.loop_cost_units,
                code_size_score=float(instruction_count),
                memory_score=profile.memory_score,
                cost_model_id=profile.model_id,
                cost_model_calibrated=profile.calibrated,
            )
        )
    return candidates


def dominates(left: Candidate, right: Candidate) -> bool:
    lvec = left.objective_vector()
    rvec = right.objective_vector()
    return all(a <= b for a, b in zip(lvec, rvec)) and any(
        a < b for a, b in zip(lvec, rvec)
    )


def pareto_front(candidates: list[Candidate]) -> list[Candidate]:
    front = [
        candidate
        for candidate in candidates
        if not any(
            dominates(other, candidate)
            for other in candidates
            if other is not candidate
        )
    ]
    return sorted(front, key=lambda item: (item.estimated_cost_units, item.code_size_score, item.name))


def pairwise_tradeoffs(candidates: list[Candidate]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for left, right in combinations(candidates, 2):
        rows.append(
            {
                "left": left.name,
                "right": right.name,
                "left_dominates": dominates(left, right),
                "right_dominates": dominates(right, left),
                "estimated_cost_unit_delta": left.estimated_cost_units - right.estimated_cost_units,
                "code_size_delta": left.code_size_score - right.code_size_score,
            }
        )
    return rows
