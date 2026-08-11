from __future__ import annotations

from dataclasses import dataclass
from math import inf
from typing import Any, Iterable, Mapping

DEFAULT_OBJECTIVES = {
    "behavioral_pass_rate": "max",
    "activation_precision": "max",
    "activation_recall": "max",
    "oak_score": "max",
    "novelty": "max",
    "reuse": "max",
    "risk": "min",
    "cost": "min",
    "complexity": "min",
}

HARD_GATE_KEYS = ("lint_pass", "eval_coverage_pass", "trust_reviewed")


@dataclass(frozen=True)
class ArenaCandidate:
    name: str
    metrics: Mapping[str, float]
    gates: Mapping[str, bool]
    provenance: Mapping[str, Any] | None = None


def gate_failures(candidate: ArenaCandidate, required=HARD_GATE_KEYS) -> list[str]:
    return [key for key in required if not bool(candidate.gates.get(key, False))]


def dominates(
    a: ArenaCandidate,
    b: ArenaCandidate,
    objectives: Mapping[str, str] = DEFAULT_OBJECTIVES,
) -> bool:
    """Return true iff a is no worse on every shared objective and strictly better on one."""
    better = False
    compared = 0
    for key, direction in objectives.items():
        if key not in a.metrics or key not in b.metrics:
            continue
        av = float(a.metrics[key])
        bv = float(b.metrics[key])
        compared += 1
        if direction == "max":
            if av < bv:
                return False
            if av > bv:
                better = True
        elif direction == "min":
            if av > bv:
                return False
            if av < bv:
                better = True
        else:
            raise ValueError(f"unknown objective direction {direction!r} for {key}")
    return compared > 0 and better


def pareto_front(
    candidates: Iterable[ArenaCandidate],
    objectives=DEFAULT_OBJECTIVES,
    require_gates: bool = True,
) -> list[ArenaCandidate]:
    pool = list(candidates)
    if require_gates:
        pool = [candidate for candidate in pool if not gate_failures(candidate)]
    front = []
    for candidate in pool:
        if not any(
            dominates(other, candidate, objectives)
            for other in pool
            if other is not candidate
        ):
            front.append(candidate)
    return sorted(front, key=lambda candidate: candidate.name)


def nondominated_sort(
    candidates: Iterable[ArenaCandidate],
    objectives=DEFAULT_OBJECTIVES,
    require_gates: bool = True,
) -> list[list[ArenaCandidate]]:
    remaining = list(candidates)
    if require_gates:
        remaining = [candidate for candidate in remaining if not gate_failures(candidate)]
    fronts = []
    while remaining:
        front = pareto_front(remaining, objectives, require_gates=False)
        if not front:
            break
        fronts.append(front)
        chosen = {id(candidate) for candidate in front}
        remaining = [candidate for candidate in remaining if id(candidate) not in chosen]
    return fronts


def crowding_distance(front: Iterable[ArenaCandidate], objectives=DEFAULT_OBJECTIVES) -> dict[str, float]:
    front = list(front)
    if not front:
        return {}
    distance = {candidate.name: 0.0 for candidate in front}
    for key in objectives:
        present = [candidate for candidate in front if key in candidate.metrics]
        if len(present) < 2:
            continue
        ordered = sorted(present, key=lambda candidate: float(candidate.metrics[key]))
        low = float(ordered[0].metrics[key])
        high = float(ordered[-1].metrics[key])
        distance[ordered[0].name] = inf
        distance[ordered[-1].name] = inf
        span = high - low
        if span == 0:
            continue
        for index in range(1, len(ordered) - 1):
            previous = float(ordered[index - 1].metrics[key])
            following = float(ordered[index + 1].metrics[key])
            if distance[ordered[index].name] != inf:
                distance[ordered[index].name] += (following - previous) / span
    return distance


def select_diverse(
    candidates: Iterable[ArenaCandidate],
    slots: int,
    objectives=DEFAULT_OBJECTIVES,
) -> list[ArenaCandidate]:
    if slots < 1:
        return []
    selected = []
    for front in nondominated_sort(candidates, objectives):
        if len(selected) + len(front) <= slots:
            selected.extend(front)
            continue
        distance = crowding_distance(front, objectives)
        ranked = sorted(front, key=lambda candidate: (-distance[candidate.name], candidate.name))
        selected.extend(ranked[: slots - len(selected)])
        break
    return selected


def arena_report(
    candidates: Iterable[ArenaCandidate],
    slots: int | None = None,
    objectives=DEFAULT_OBJECTIVES,
) -> dict[str, Any]:
    candidates = list(candidates)
    blocked = [
        {"name": candidate.name, "gate_failures": gate_failures(candidate)}
        for candidate in candidates
        if gate_failures(candidate)
    ]
    fronts = nondominated_sort(candidates, objectives)
    report = {
        "selection_mode": "multi_objective_pareto",
        "scalar_fitness": "NOT_USED",
        "candidate_count": len(candidates),
        "eligible_count": sum(1 for candidate in candidates if not gate_failures(candidate)),
        "blocked": blocked,
        "fronts": [[candidate.name for candidate in front] for front in fronts],
        "objectives": dict(objectives),
        "note": "Pareto rank is selection evidence, not behavioral proof or promotion authorization.",
    }
    if slots is not None:
        report["selected"] = [candidate.name for candidate in select_diverse(candidates, slots, objectives)]
    return report
