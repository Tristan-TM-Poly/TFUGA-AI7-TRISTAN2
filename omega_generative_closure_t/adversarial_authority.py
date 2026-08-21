"""Ω Meta-Theory R0.7: independent challenge authority and repair-overfit detection.

R0.7 attacks the R0.6 adversarial generator itself. A repair is not considered
robust merely because it closes probes synthesized from its own observed failures.
Independent/frozen challenge families are evaluated separately, diversity is
measured structurally, and generator/verifier/challenge-authority role collapse
is held rather than silently accepted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .closure import compute_closure
from .core import Rule
from .cross_context import ProbeFamily


@dataclass(frozen=True)
class ChallengeAuthority:
    generator_id: str
    verifier_id: str
    authority_id: str

    @property
    def independent(self) -> bool:
        return len({self.generator_id, self.verifier_id, self.authority_id}) == 3


@dataclass(frozen=True)
class ChallengeDiversityReport:
    family_count: int
    distinct_observable_count: int
    mean_pairwise_jaccard_distance: float
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "diversity is structural over declared observable sets; it is not semantic independence or external validity"
    )


def challenge_diversity(families: Iterable[ProbeFamily]) -> ChallengeDiversityReport:
    items = tuple(families)
    if not items:
        return ChallengeDiversityReport(0, 0, 0.0, "HOLD", ("missing_challenge_families",))

    union = frozenset().union(*(item.observables for item in items))
    distinct_sets = len({item.observables for item in items})
    distances: list[float] = []
    for index, left in enumerate(items):
        for right in items[index + 1 :]:
            pair_union = left.observables | right.observables
            overlap = left.observables & right.observables
            distances.append(0.0 if not pair_union else 1.0 - len(overlap) / len(pair_union))

    blockers: list[str] = []
    if len(items) < 2:
        blockers.append("insufficient_challenge_family_count")
    if distinct_sets < 2:
        blockers.append("duplicate_or_collapsed_challenge_families")
    mean_distance = 0.0 if not distances else sum(distances) / len(distances)
    if len(items) >= 2 and mean_distance == 0.0:
        blockers.append("zero_pairwise_challenge_diversity")

    return ChallengeDiversityReport(
        family_count=len(items),
        distinct_observable_count=len(union),
        mean_pairwise_jaccard_distance=mean_distance,
        oak_status="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
    )


@dataclass(frozen=True)
class FrozenChallengeEvaluation:
    family: str
    retained_ratio: float
    missing: frozenset[str]


@dataclass(frozen=True)
class RepairOverfitReport:
    generated_probe_pass: bool
    frozen_challenge_pass: bool
    authority_independent: bool
    diversity: ChallengeDiversityReport
    repair_overfit: bool
    evaluations: tuple[FrozenChallengeEvaluation, ...]
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "PASS means the supplied repaired basis survived the supplied frozen finite challenge families under separated declared roles; "
        "it is not proof of universal robustness, scientific truth, or semantic independence"
    )


def detect_repair_overfit(
    repaired_basis: Iterable[str],
    rules: Iterable[Rule],
    generated_probe_families: Iterable[ProbeFamily],
    frozen_challenge_families: Iterable[ProbeFamily],
    authority: ChallengeAuthority,
    *,
    min_transfer_ratio: float = 1.0,
) -> RepairOverfitReport:
    if not 0.0 <= float(min_transfer_ratio) <= 1.0:
        raise ValueError("min_transfer_ratio must be in [0, 1]")

    basis = frozenset(str(item) for item in repaired_basis)
    ordered_rules = tuple(rules)
    generated = tuple(generated_probe_families)
    frozen = tuple(frozen_challenge_families)
    if not generated:
        raise ValueError("at least one generated probe family is required")
    if not frozen:
        raise ValueError("at least one frozen challenge family is required")

    closure = compute_closure(basis, ordered_rules)

    def ratio(family: ProbeFamily) -> float:
        return 1.0 if not family.observables else len(family.observables & closure.reachable) / len(family.observables)

    generated_probe_pass = all(ratio(family) >= min_transfer_ratio for family in generated)
    evaluations = tuple(
        FrozenChallengeEvaluation(
            family=family.name,
            retained_ratio=ratio(family),
            missing=frozenset(family.observables.difference(closure.reachable)),
        )
        for family in frozen
    )
    frozen_challenge_pass = all(item.retained_ratio >= min_transfer_ratio for item in evaluations)
    diversity = challenge_diversity(frozen)
    repair_overfit = generated_probe_pass and not frozen_challenge_pass

    blockers: list[str] = []
    if not authority.independent:
        blockers.append("generator_verifier_challenge_authority_not_independent")
    if diversity.oak_status != "PASS":
        blockers.extend(diversity.blockers)
    if not generated_probe_pass:
        blockers.append("generated_probe_regression")
    if not frozen_challenge_pass:
        blockers.append("frozen_challenge_failure")
    if repair_overfit:
        blockers.append("repair_overfit_detected")

    return RepairOverfitReport(
        generated_probe_pass=generated_probe_pass,
        frozen_challenge_pass=frozen_challenge_pass,
        authority_independent=authority.independent,
        diversity=diversity,
        repair_overfit=repair_overfit,
        evaluations=evaluations,
        oak_status="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
    )
