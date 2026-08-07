from __future__ import annotations

from itertools import combinations

from .backends import emit_dot_u64, static_instruction_count, supported_variants
from .models import Candidate


def estimate_builtin_candidates(architecture: str) -> list[Candidate]:
    """Create deterministic static candidates.

    Scores are ranking heuristics only. Runtime performance claims require native
    benchmarking on the target microarchitecture.
    """

    architecture_norm = architecture.lower().replace("-", "_")
    candidates: list[Candidate] = []
    for variant in supported_variants(architecture_norm):
        assembly = emit_dot_u64(architecture_norm, variant)
        instruction_count = static_instruction_count(assembly)
        if architecture_norm in {"x86_64", "amd64"}:
            loop_cost = 8.0 if variant == "indexed" else 9.0
            memory_score = 2.0
        else:
            loop_cost = 7.0
            memory_score = 2.0
        candidates.append(
            Candidate(
                name=f"dot_u64/{architecture_norm}/{variant}",
                architecture=architecture_norm,
                variant=variant,
                estimated_cycles=loop_cost,
                code_size_score=float(instruction_count),
                memory_score=memory_score,
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
    return sorted(front, key=lambda item: (item.estimated_cycles, item.code_size_score, item.name))


def pairwise_tradeoffs(candidates: list[Candidate]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for left, right in combinations(candidates, 2):
        rows.append(
            {
                "left": left.name,
                "right": right.name,
                "left_dominates": dominates(left, right),
                "right_dominates": dominates(right, left),
                "estimated_cycle_delta": left.estimated_cycles - right.estimated_cycles,
                "code_size_delta": left.code_size_score - right.code_size_score,
            }
        )
    return rows
