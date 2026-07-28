"""HGFM TensorBench: bounded 16×16×16 governed tensor optimization.

The benchmark is synthetic and frozen in source. It measures whether a
hyperedge-aware candidate generator can recover the exact governed optimum
with fewer objective evaluations than exhaustive search. It does not establish
universal optimization superiority or validate a physical theory.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Iterable, Sequence

BENCHMARK_ID = "HGFM-TENSORBENCH-R0.1-16X16X16"
AXIS_SIZE = 16

KERNELS = (
    "HGFM-nD", "TFUGA", "FFWT-ND", "Tensor-CVCD", "DCT-Omega", "OAKGate",
    "OmniDomain", "OmniIR", "TOVM", "AI-7", "MGHFM-TGNT", "TFACC",
    "PEFA", "LC-Fractal-Mycelium", "Alexandrie-Yggdrasil", "AUTO2-AIT",
)
OPERATORS = (
    "SENSE", "FFWT_EXTRACT", "HGFM_TENSORIZE", "EXPAND",
    "PRIME_FACTORIZE", "SYNERGY_COMPOSE", "OPTIMIZE_ACTION", "SIMULATE",
    "MODEL_TOURNAMENT", "FALSIFY", "UNCERTAINTY_QUANTIFY",
    "CVCD_COMPRESS", "DCT_COMPILE", "OAK_GATE", "MEMORIZE_ROLLBACK",
    "CANONIZE",
)
DOMAINS = (
    "mathematics", "fundamental_physics", "electromagnetism", "energy",
    "optics_spectroscopy", "chemistry", "materials", "quantum",
    "climate_gaia", "infrastructure", "artificial_intelligence", "software",
    "knowledge_education", "games_simulation", "publication_ip_company",
    "durable_human_system",
)

# The sparse order-three relations are the frozen R0.1 HGFM side information.
# The first tuple is intentionally the canonical target.
HYPEREDGES = (
    (0, 6, 0, 14.0, "HGFM TensorBench"),
    (8, 12, 1, 8.2, "TOVM proof-carrying physics compiler"),
    (12, 6, 3, 8.0, "PEFA energy optimizer"),
    (5, 13, 11, 7.8, "OAKGate software selector"),
    (2, 1, 4, 7.4, "FFWT spectroscopy discovery"),
    (11, 9, 0, 7.0, "TFACC counterexample compiler"),
    (14, 14, 12, 6.6, "Alexandrie evidence memory"),
    (15, 12, 11, 6.5, "AUTO2 production compiler"),
    # Attractive but redundant: CVCD debt should demote it.
    (1, 3, 14, 10.0, "duplicated expansion-publication coupling"),
    # Attractive but authority-invalid: OAK should quarantine it.
    (9, 15, 15, 14.0, "unauthorized autonomous human canonization"),
)

KERNEL_BASE = (2.2, 4.6, 4.1, 4.0, 4.5, 4.4, 3.9, 4.0,
               4.2, 4.7, 3.7, 3.8, 4.1, 3.9, 4.3, 4.5)
OPERATOR_BASE = (2.8, 3.9, 3.8, 4.5, 3.3, 4.0, 2.4, 3.7,
                 4.2, 4.1, 3.9, 4.0, 4.4, 4.5, 3.8, 4.6)
DOMAIN_BASE = (2.3, 4.0, 3.9, 4.1, 3.8, 3.7, 3.6, 3.9,
               3.8, 3.7, 4.4, 4.5, 4.0, 3.8, 4.3, 4.2)


@dataclass(frozen=True)
class Cell:
    kernel: int
    operator: int
    domain: int
    raw_potential: float
    evidence: float
    debt: float
    scale_coherence: float
    hyperedge_bonus: float
    governed_score: float
    admissible: bool
    quarantine_reasons: tuple[str, ...]

    @property
    def coordinate(self) -> tuple[int, int, int]:
        return (self.kernel, self.operator, self.domain)

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["coordinate"] = list(self.coordinate)
        value["kernel_name"] = KERNELS[self.kernel]
        value["operator_name"] = OPERATORS[self.operator]
        value["domain_name"] = DOMAINS[self.domain]
        return value


@dataclass(frozen=True)
class SolverResult:
    name: str
    best: Cell
    evaluated_coordinates: tuple[tuple[int, int, int], ...]
    canonical_regret: float
    evaluation_fraction: float
    pareto_coverage: float

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "best": self.best.to_dict(),
            "evaluations": len(self.evaluated_coordinates),
            "evaluation_fraction": self.evaluation_fraction,
            "canonical_regret": self.canonical_regret,
            "pareto_coverage": self.pareto_coverage,
        }


def _hyperedge_bonus(i: int, j: int, k: int) -> float:
    return sum(edge[3] for edge in HYPEREDGES if edge[:3] == (i, j, k))


def _scale_coherence(i: int, j: int, k: int) -> float:
    # Deterministic multi-scale proxy, preregistered rather than fitted.
    aligned = int(i % 4 == k % 4) + int(j % 4 == (i + k) % 4)
    dyadic = 1.0 / (1.0 + abs((i % 8) - (k % 8)))
    return 0.55 * aligned + 0.70 * dyadic


def _evidence(i: int, j: int, k: int) -> float:
    execution = 1.0 if j in {7, 8, 9, 10, 12, 13, 14} else 0.45
    kernel = 0.85 if i in {4, 5, 8, 15} else 0.58
    domain = 0.80 if k in {0, 1, 2, 3, 5, 11} else 0.60
    return 2.0 * execution + 1.2 * kernel + 0.8 * domain


def _debt(i: int, j: int, k: int) -> float:
    complexity = 0.15 * ((i * 7 + j * 3 + k * 5) % 9)
    duplication = 8.5 if (i, j, k) == (1, 3, 14) else 0.0
    authority = 1.5 if k in {14, 15} and j in {3, 15} else 0.0
    return complexity + duplication + authority


def _admissibility(i: int, j: int, k: int) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if (i, j, k) == (9, 15, 15):
        reasons.append("self-expanding authority is forbidden")
    if j == 15 and i not in {4, 5, 8, 15}:
        reasons.append("CANONIZE requires a governance-capable kernel")
    if k == 15 and j in {3, 15} and i in {9, 15}:
        reasons.append("durable-human-system expansion requires explicit human review")
    return (not reasons, tuple(reasons))


def evaluate_cell(
    coordinate: tuple[int, int, int],
    *,
    use_ffwt: bool = True,
    use_hgfm: bool = True,
    use_cvcd: bool = True,
    use_oak: bool = True,
) -> Cell:
    i, j, k = coordinate
    if not all(0 <= value < AXIS_SIZE for value in coordinate):
        raise ValueError("coordinates must lie in [0, 15]")
    scale = _scale_coherence(i, j, k) if use_ffwt else 0.0
    hyperedge = _hyperedge_bonus(i, j, k) if use_hgfm else 0.0
    evidence = _evidence(i, j, k)
    debt = _debt(i, j, k) if use_cvcd else 0.0
    admissible, reasons = _admissibility(i, j, k)
    raw = (
        KERNEL_BASE[i] + OPERATOR_BASE[j] + DOMAIN_BASE[k]
        + scale + hyperedge + 0.45 * evidence
    )
    governed = raw - debt
    if use_oak and not admissible:
        governed = -1.0e12
    return Cell(
        kernel=i,
        operator=j,
        domain=k,
        raw_potential=raw,
        evidence=evidence,
        debt=debt,
        scale_coherence=scale,
        hyperedge_bonus=hyperedge,
        governed_score=governed,
        admissible=admissible,
        quarantine_reasons=reasons,
    )


def all_coordinates() -> tuple[tuple[int, int, int], ...]:
    return tuple(
        (i, j, k)
        for i in range(AXIS_SIZE)
        for j in range(AXIS_SIZE)
        for k in range(AXIS_SIZE)
    )


def pareto_front(cells: Iterable[Cell]) -> tuple[tuple[int, int, int], ...]:
    admissible = [cell for cell in cells if cell.admissible]
    front: list[tuple[int, int, int]] = []
    for cell in admissible:
        dominated = any(
            other.raw_potential >= cell.raw_potential
            and other.evidence >= cell.evidence
            and other.debt <= cell.debt
            and (
                other.raw_potential > cell.raw_potential
                or other.evidence > cell.evidence
                or other.debt < cell.debt
            )
            for other in admissible
        )
        if not dominated:
            front.append(cell.coordinate)
    return tuple(sorted(front))


def _best(cells: Iterable[Cell]) -> Cell:
    return max(cells, key=lambda cell: (cell.governed_score, tuple(-x for x in cell.coordinate)))


def _result(
    name: str,
    coordinates: Iterable[tuple[int, int, int]],
    canonical: Cell,
    exact_pareto: set[tuple[int, int, int]],
    **evaluation_flags: bool,
) -> SolverResult:
    unique = tuple(dict.fromkeys(coordinates))
    cells = [evaluate_cell(c, **evaluation_flags) for c in unique]
    best = _best(cells)
    found_front = set(pareto_front(cells)) & exact_pareto
    return SolverResult(
        name=name,
        best=best,
        evaluated_coordinates=unique,
        canonical_regret=max(0.0, canonical.governed_score - evaluate_cell(best.coordinate).governed_score),
        evaluation_fraction=len(unique) / (AXIS_SIZE ** 3),
        pareto_coverage=len(found_front) / max(1, len(exact_pareto)),
    )


def solve_exhaustive() -> tuple[Cell, set[tuple[int, int, int]]]:
    cells = [evaluate_cell(c) for c in all_coordinates()]
    return _best(cells), set(pareto_front(cells))


def solve_random(
    canonical: Cell,
    exact_pareto: set[tuple[int, int, int]],
    *,
    seed: int = 1701,
    budget: int = 256,
) -> SolverResult:
    if not 1 <= budget <= AXIS_SIZE ** 3:
        raise ValueError("random budget must be in [1, 4096]")
    rng = random.Random(seed)
    coordinates = rng.sample(list(all_coordinates()), budget)
    return _result("random", coordinates, canonical, exact_pareto)


def solve_greedy(
    canonical: Cell,
    exact_pareto: set[tuple[int, int, int]],
) -> SolverResult:
    start = (
        max(range(AXIS_SIZE), key=KERNEL_BASE.__getitem__),
        max(range(AXIS_SIZE), key=OPERATOR_BASE.__getitem__),
        max(range(AXIS_SIZE), key=DOMAIN_BASE.__getitem__),
    )
    current = start
    evaluated: list[tuple[int, int, int]] = []
    for _ in range(4):
        changed = False
        for axis in range(3):
            neighborhood = []
            for value in range(AXIS_SIZE):
                candidate = list(current)
                candidate[axis] = value
                coordinate = tuple(candidate)
                neighborhood.append(coordinate)
                evaluated.append(coordinate)
            best = _best(evaluate_cell(c) for c in neighborhood).coordinate
            if best != current:
                current = best
                changed = True
        if not changed:
            break
    return _result("greedy_coordinate", evaluated, canonical, exact_pareto)


def hgfm_candidate_coordinates(*, use_hyperedges: bool = True) -> tuple[tuple[int, int, int], ...]:
    top_i = sorted(range(AXIS_SIZE), key=KERNEL_BASE.__getitem__, reverse=True)[:4]
    top_j = sorted(range(AXIS_SIZE), key=OPERATOR_BASE.__getitem__, reverse=True)[:4]
    top_k = sorted(range(AXIS_SIZE), key=DOMAIN_BASE.__getitem__, reverse=True)[:4]
    candidates: set[tuple[int, int, int]] = {
        (i, j, k) for i in top_i for j in top_j for k in top_k
    }
    if use_hyperedges:
        for i, j, k, _, _ in HYPEREDGES:
            candidates.add((i, j, k))
            candidates.update((x, j, k) for x in range(AXIS_SIZE))
            candidates.update((i, x, k) for x in range(AXIS_SIZE))
            candidates.update((i, j, x) for x in range(AXIS_SIZE))
    return tuple(sorted(candidates))


def solve_hgfm(
    canonical: Cell,
    exact_pareto: set[tuple[int, int, int]],
    *,
    use_ffwt: bool = True,
    use_hgfm: bool = True,
    use_cvcd: bool = True,
    use_oak: bool = True,
) -> SolverResult:
    return _result(
        "hgfm_full" if all((use_ffwt, use_hgfm, use_cvcd, use_oak)) else "hgfm_ablation",
        hgfm_candidate_coordinates(use_hyperedges=use_hgfm),
        canonical,
        exact_pareto,
        use_ffwt=use_ffwt,
        use_hgfm=use_hgfm,
        use_cvcd=use_cvcd,
        use_oak=use_oak,
    )


def run_benchmark() -> dict[str, object]:
    canonical, exact_pareto = solve_exhaustive()
    exhaustive = _result(
        "exhaustive", all_coordinates(), canonical, exact_pareto
    )
    random_runs = [
        solve_random(canonical, exact_pareto, seed=seed)
        for seed in (17, 101, 1701, 4096, 65537)
    ]
    greedy = solve_greedy(canonical, exact_pareto)
    hgfm = solve_hgfm(canonical, exact_pareto)
    ablations = {
        "without_ffwt": solve_hgfm(canonical, exact_pareto, use_ffwt=False),
        "without_hgfm": solve_hgfm(canonical, exact_pareto, use_hgfm=False),
        "without_cvcd": solve_hgfm(canonical, exact_pareto, use_cvcd=False),
        "without_oak": solve_hgfm(canonical, exact_pareto, use_oak=False),
    }
    without_oak = ablations["without_oak"]
    checks = {
        "cube_has_4096_cells": len(all_coordinates()) == 4096,
        "hgfm_recovers_exact_optimum": hgfm.best.coordinate == canonical.coordinate,
        "hgfm_zero_regret": hgfm.canonical_regret <= 1.0e-12,
        "hgfm_evaluates_under_20_percent": hgfm.evaluation_fraction < 0.20,
        "greedy_has_positive_regret": greedy.canonical_regret > 0.0,
        "hgfm_ablation_has_positive_regret": ablations["without_hgfm"].canonical_regret > 0.0,
        "oak_ablation_selects_quarantined_cell": not without_oak.best.admissible,
        "cvcd_ablation_changes_selection": ablations["without_cvcd"].best.coordinate != canonical.coordinate,
        "ffwt_ablation_changes_score_or_selection": (
            ablations["without_ffwt"].best.coordinate != canonical.coordinate
            or abs(ablations["without_ffwt"].best.governed_score - canonical.governed_score) > 1.0e-12
        ),
        "random_is_not_perfect_across_all_seeds": any(run.canonical_regret > 0.0 for run in random_runs),
    }
    payload: dict[str, object] = {
        "benchmark_id": BENCHMARK_ID,
        "scope": "synthetic governed tensor optimization only",
        "shape": [AXIS_SIZE, AXIS_SIZE, AXIS_SIZE],
        "cell_count": AXIS_SIZE ** 3,
        "canonical_optimum": canonical.to_dict(),
        "exact_pareto_size": len(exact_pareto),
        "solvers": {
            "exhaustive": exhaustive.to_dict(),
            "greedy": greedy.to_dict(),
            "hgfm": hgfm.to_dict(),
            "random": [run.to_dict() for run in random_runs],
        },
        "ablations": {name: result.to_dict() for name, result in ablations.items()},
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "non_claims": [
            "No universal optimization superiority.",
            "No physical, mathematical, commercial, or safety validation.",
            "Hyperedge side information is preregistered and is not free in real applications.",
            "Synthetic success does not establish cross-domain transfer.",
        ],
    }
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    payload["result_sha256"] = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hgfm-tensorbench")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    result = run_benchmark()
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
