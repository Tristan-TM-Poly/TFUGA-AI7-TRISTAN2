"""FTPCI-Omega auto meta-generation engine.

This module is intentionally small, deterministic, and dependency-free. It does
not claim to prove physics. It creates candidate meta-theory configurations,
scores them with OAK/fertility heuristics, keeps a top-16 beam, and records a
bottom-16 negative-memory set.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Dict, Iterable, List, Sequence


AXES_16: Sequence[str] = (
    "trace_quality",
    "compression_depth",
    "factor_rank",
    "sparsity_level",
    "invariant_preservation",
    "oak_attack_strength",
    "negative_memory_projection",
    "fertility_threshold",
    "decompression_depth",
    "codex_depth_2n",
    "prototype_minimality",
    "residual_search_intensity",
    "bridge_domain_count",
    "anti_hype_threshold",
    "reconstruction_tolerance",
    "compute_budget",
)


SEED_THEORIES: Sequence[str] = (
    "Residual Physics Finder",
    "Projective Regime Recollement",
    "FTPCI-Omega Lattice16",
    "HGFM Modern Physics Map",
    "OAK Adversarial Physics Engine",
    "Cold Plasma Tensor Benchmark",
    "Codex 2^n Decompression",
    "Negative Memory Pruning",
    "Fertility Gradient Router",
    "Tensor Sparse Canon Compiler",
    "Missing Theory Finder",
    "Projective Dark Sector",
    "Vacuum Local-Global Recollement",
    "Time as Trace Order",
    "Black Hole Compression Node",
    "Neutrino Flavor Tensor",
)


@dataclass(frozen=True)
class Candidate:
    id: str
    parent: str
    cycle: int
    seed: str
    axes: Dict[str, int]
    fertility: float
    oak_score: float
    reuse: float
    prototype_value: float
    cost: float
    risk: float
    hype: float
    complexity: float
    total: float
    status: str
    next_action: str


def _hash_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def _axis_value(seed: str, cycle: int, axis: str, parent: str = "root") -> int:
    return _hash_int(f"{parent}|{seed}|{cycle}|{axis}") % 16


def build_candidate(seed: str, cycle: int, parent: str = "root") -> Candidate:
    axes = {axis: _axis_value(seed, cycle, axis, parent) for axis in AXES_16}

    trace = axes["trace_quality"] / 15
    compression = axes["compression_depth"] / 15
    invariant = axes["invariant_preservation"] / 15
    oak = axes["oak_attack_strength"] / 15
    neg_mem = axes["negative_memory_projection"] / 15
    fertility_axis = axes["fertility_threshold"] / 15
    prototype = axes["prototype_minimality"] / 15
    residual = axes["residual_search_intensity"] / 15
    bridges = axes["bridge_domain_count"] / 15
    anti_hype = axes["anti_hype_threshold"] / 15
    tolerance = axes["reconstruction_tolerance"] / 15
    budget = axes["compute_budget"] / 15
    sparsity = axes["sparsity_level"] / 15
    rank = axes["factor_rank"] / 15
    decompress = axes["decompression_depth"] / 15
    codex = axes["codex_depth_2n"] / 15

    fertility = 10 * (
        0.20 * fertility_axis
        + 0.18 * residual
        + 0.17 * bridges
        + 0.15 * invariant
        + 0.15 * compression
        + 0.15 * codex
    )
    oak_score = min(
        1.0,
        0.25 * trace + 0.25 * oak + 0.20 * anti_hype + 0.15 * neg_mem + 0.15 * invariant,
    )
    reuse = 10 * (0.25 * compression + 0.25 * sparsity + 0.20 * invariant + 0.15 * codex + 0.15 * bridges)
    prototype_value = 10 * (0.35 * prototype + 0.25 * trace + 0.20 * oak + 0.20 * residual)

    cost = 1 + 8 * (0.35 * budget + 0.25 * rank + 0.20 * decompress + 0.20 * (1 - sparsity))
    risk = 1 + 8 * (0.35 * (1 - oak) + 0.25 * (1 - trace) + 0.20 * (1 - neg_mem) + 0.20 * tolerance)
    hype = 1 + 8 * (0.50 * (1 - anti_hype) + 0.25 * decompress + 0.25 * (1 - oak))
    complexity = 1 + 8 * (0.40 * rank + 0.30 * decompress + 0.30 * (1 - sparsity))

    total = (fertility * oak_score * reuse * prototype_value) / (cost + risk + hype + complexity + 1)
    status = "selected" if total >= 5.0 and oak_score >= 0.55 else "quarantine"
    next_action = "decompress into codex/test/prototype" if status == "selected" else "keep compressed; attack or add to negative memory"

    candidate_id = f"amg-{cycle:02d}-{_hash_int(seed + parent + str(cycle)) % 10000:04d}"
    return Candidate(
        id=candidate_id,
        parent=parent,
        cycle=cycle,
        seed=seed,
        axes=axes,
        fertility=round(fertility, 3),
        oak_score=round(oak_score, 3),
        reuse=round(reuse, 3),
        prototype_value=round(prototype_value, 3),
        cost=round(cost, 3),
        risk=round(risk, 3),
        hype=round(hype, 3),
        complexity=round(complexity, 3),
        total=round(total, 3),
        status=status,
        next_action=next_action,
    )


def expand_beam(beam: Iterable[Candidate], cycle: int) -> List[Candidate]:
    candidates: List[Candidate] = []
    for parent in beam:
        for seed in SEED_THEORIES:
            child_seed = f"{parent.seed} × {seed}"
            candidates.append(build_candidate(child_seed, cycle, parent=parent.id))
    return candidates


def run_generation(cycles: int = 16, beam_width: int = 16) -> Dict[str, object]:
    beam = [build_candidate(seed, 0) for seed in SEED_THEORIES]
    beam = sorted(beam, key=lambda candidate: candidate.total, reverse=True)[:beam_width]
    negative_memory: List[Candidate] = []
    history: List[Dict[str, object]] = []

    for cycle in range(1, cycles + 1):
        candidates = expand_beam(beam, cycle)
        ranked = sorted(candidates, key=lambda candidate: candidate.total, reverse=True)
        beam = ranked[:beam_width]
        failures = ranked[-beam_width:]
        negative_memory.extend(failures)
        history.append(
            {
                "cycle": cycle,
                "top": [asdict(candidate) for candidate in beam[:3]],
                "bottom": [asdict(candidate) for candidate in failures[:3]],
                "best_total": beam[0].total,
                "best_seed": beam[0].seed,
            }
        )

    return {
        "engine": "FTPCI-Omega Auto Meta-Generation",
        "cycles": cycles,
        "beam_width": beam_width,
        "axes": list(AXES_16),
        "top16": [asdict(candidate) for candidate in beam],
        "negative_memory_bottom16": [
            asdict(candidate) for candidate in sorted(negative_memory, key=lambda candidate: candidate.total)[:beam_width]
        ],
        "history": history,
        "oak_note": "Architectural search output; not a physical proof. Promote only after tests, predictions, and validation.",
    }


def main() -> None:
    print(json.dumps(run_generation(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
