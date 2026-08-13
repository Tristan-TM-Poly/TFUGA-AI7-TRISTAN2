from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .closure import compute_closure
from .core import Rule


@dataclass(frozen=True)
class SeedGain:
    candidate: str
    derived_added: frozenset[str]

    @property
    def gain(self) -> int:
        return len(self.derived_added)


@dataclass(frozen=True)
class ClosureCurvature:
    left: str
    right: str
    baseline_size: int
    left_size: int
    right_size: int
    joint_size: int
    curvature: int


def single_seed_gain(seeds: Iterable[str], rules: Iterable[Rule], candidate: str) -> SeedGain:
    seed_set = frozenset(seeds)
    ordered_rules = tuple(rules)
    baseline = compute_closure(seed_set, ordered_rules)
    augmented = compute_closure(seed_set | {candidate}, ordered_rules)
    derived = augmented.reachable.difference(baseline.reachable).difference({candidate})
    return SeedGain(candidate=str(candidate), derived_added=frozenset(derived))


def closure_gradient(
    seeds: Iterable[str],
    rules: Iterable[Rule],
    candidates: Iterable[str],
) -> tuple[SeedGain, ...]:
    seed_set = frozenset(seeds)
    ordered_rules = tuple(rules)
    gains = [single_seed_gain(seed_set, ordered_rules, str(candidate)) for candidate in candidates]
    return tuple(sorted(gains, key=lambda item: (-item.gain, item.candidate)))


def pairwise_seed_curvature(
    seeds: Iterable[str],
    rules: Iterable[Rule],
    left: str,
    right: str,
) -> ClosureCurvature:
    if left == right:
        raise ValueError("pairwise curvature requires two distinct candidates")
    seed_set = frozenset(seeds)
    ordered_rules = tuple(rules)

    def closure_size(extra: Iterable[str]) -> int:
        return len(compute_closure(seed_set | frozenset(extra), ordered_rules).reachable)

    baseline = closure_size(())
    left_size = closure_size((left,))
    right_size = closure_size((right,))
    joint = closure_size((left, right))
    curvature = joint - left_size - right_size + baseline
    return ClosureCurvature(
        left=str(left),
        right=str(right),
        baseline_size=baseline,
        left_size=left_size,
        right_size=right_size,
        joint_size=joint,
        curvature=curvature,
    )
