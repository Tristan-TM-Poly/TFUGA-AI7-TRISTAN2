"""Ω Meta-Theory R0.8: challenge credit, mutation, and frozen external evaluation.

R0.8 extends R0.7 without allowing the system-under-test to redefine success.
Challenge credit is a bounded counterfactual attribution signal, challenge
mutation is selected only when it discriminates candidate bases under frozen
criteria, and ties remain HOLD rather than receiving fabricated winners.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .adversarial_authority import ChallengeAuthority
from .closure import compute_closure
from .core import Rule
from .cross_context import ProbeFamily


@dataclass(frozen=True)
class FrozenEvaluator:
    evaluator_id: str
    criterion_id: str
    min_transfer_ratio: float = 1.0

    def __post_init__(self) -> None:
        if not self.evaluator_id or not self.criterion_id:
            raise ValueError("evaluator_id and criterion_id must be non-empty")
        if not 0.0 <= float(self.min_transfer_ratio) <= 1.0:
            raise ValueError("min_transfer_ratio must be in [0, 1]")


@dataclass(frozen=True)
class ChallengeCredit:
    family: str
    before_ratio: float
    after_ratio: float
    ratio_gain: float
    resolved_observables: frozenset[str]
    remaining_missing: frozenset[str]
    oak_boundary: str = (
        "credit is counterfactual attribution under the supplied before/after bases and rules; "
        "it is not proof that the challenge causally produced the repair"
    )


def _ratio_and_missing(
    basis: frozenset[str],
    rules: tuple[Rule, ...],
    family: ProbeFamily,
) -> tuple[float, frozenset[str]]:
    closure = compute_closure(basis, rules)
    retained = family.observables & closure.reachable
    missing = frozenset(family.observables.difference(closure.reachable))
    ratio = 1.0 if not family.observables else len(retained) / len(family.observables)
    return ratio, missing


def challenge_credit(
    before_basis: Iterable[str],
    after_basis: Iterable[str],
    rules: Iterable[Rule],
    families: Iterable[ProbeFamily],
) -> tuple[ChallengeCredit, ...]:
    before = frozenset(str(item) for item in before_basis)
    after = frozenset(str(item) for item in after_basis)
    ordered_rules = tuple(rules)
    results: list[ChallengeCredit] = []
    for family in families:
        before_ratio, before_missing = _ratio_and_missing(before, ordered_rules, family)
        after_ratio, after_missing = _ratio_and_missing(after, ordered_rules, family)
        results.append(
            ChallengeCredit(
                family=family.name,
                before_ratio=before_ratio,
                after_ratio=after_ratio,
                ratio_gain=after_ratio - before_ratio,
                resolved_observables=frozenset(before_missing.difference(after_missing)),
                remaining_missing=after_missing,
            )
        )
    return tuple(results)


@dataclass(frozen=True)
class FrozenChallengeOutcome:
    candidate_id: str
    retained_ratio: float
    passed: bool
    missing: frozenset[str]


@dataclass(frozen=True)
class FrozenChallengeReport:
    evaluator: FrozenEvaluator
    family: ProbeFamily
    outcomes: tuple[FrozenChallengeOutcome, ...]
    authority_independent: bool
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "PASS means declared roles were separated and the supplied candidates were evaluated under frozen declared criteria; "
        "it does not prove external-world independence or universal robustness"
    )


def evaluate_frozen_challenge(
    candidate_bases: dict[str, Iterable[str]],
    rules: Iterable[Rule],
    family: ProbeFamily,
    evaluator: FrozenEvaluator,
    authority: ChallengeAuthority,
) -> FrozenChallengeReport:
    ordered_rules = tuple(rules)
    outcomes: list[FrozenChallengeOutcome] = []
    for candidate_id, basis_values in sorted(candidate_bases.items()):
        ratio, missing = _ratio_and_missing(
            frozenset(str(item) for item in basis_values), ordered_rules, family
        )
        outcomes.append(
            FrozenChallengeOutcome(
                candidate_id=str(candidate_id),
                retained_ratio=ratio,
                passed=ratio >= evaluator.min_transfer_ratio,
                missing=missing,
            )
        )

    blockers: list[str] = []
    if not candidate_bases:
        blockers.append("missing_candidate_bases")
    if not authority.independent:
        blockers.append("generator_verifier_challenge_authority_not_independent")
    if evaluator.evaluator_id in {authority.generator_id, authority.verifier_id}:
        blockers.append("external_evaluator_role_collapsed")

    return FrozenChallengeReport(
        evaluator=evaluator,
        family=family,
        outcomes=tuple(outcomes),
        authority_independent=authority.independent,
        oak_status="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
    )


@dataclass(frozen=True)
class ChallengeMutationCandidate:
    family: ProbeFamily
    information_gain_proxy: float
    pass_count: int
    fail_count: int


@dataclass(frozen=True)
class ChallengeMutationDecision:
    seed_family: ProbeFamily
    candidates: tuple[ChallengeMutationCandidate, ...]
    selected: ProbeFamily | None
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "information gain is a finite discrimination proxy over declared candidate bases; "
        "a selected mutation is not an optimal experiment or independent truth"
    )


def mutate_challenge_by_information_gain(
    seed_family: ProbeFamily,
    candidate_observables: Iterable[str],
    candidate_bases: dict[str, Iterable[str]],
    rules: Iterable[Rule],
    evaluator: FrozenEvaluator,
    authority: ChallengeAuthority,
) -> ChallengeMutationDecision:
    """Select one-observable mutations that maximally split declared candidates.

    The proxy is 4*p*(1-p), where p is the candidate pass fraction under the
    frozen evaluator. It is maximal at an even split and zero when every
    candidate receives the same verdict. Equal maxima remain HOLD.
    """

    if not candidate_bases:
        return ChallengeMutationDecision(
            seed_family, (), None, "HOLD", ("missing_candidate_bases",)
        )
    if not authority.independent or evaluator.evaluator_id in {
        authority.generator_id,
        authority.verifier_id,
    }:
        return ChallengeMutationDecision(
            seed_family,
            (),
            None,
            "HOLD",
            ("challenge_evaluation_authority_not_separated",),
        )

    mutations: list[ChallengeMutationCandidate] = []
    for observable in sorted({str(item) for item in candidate_observables}):
        if observable in seed_family.observables:
            continue
        family = ProbeFamily.make(
            f"{seed_family.name}+{observable}",
            set(seed_family.observables) | {observable},
        )
        report = evaluate_frozen_challenge(
            candidate_bases, rules, family, evaluator, authority
        )
        pass_count = sum(1 for outcome in report.outcomes if outcome.passed)
        total = len(report.outcomes)
        fail_count = total - pass_count
        p = pass_count / total
        score = 4.0 * p * (1.0 - p)
        mutations.append(
            ChallengeMutationCandidate(family, score, pass_count, fail_count)
        )

    if not mutations:
        return ChallengeMutationDecision(
            seed_family, (), None, "HOLD", ("no_admissible_challenge_mutations",)
        )

    best_score = max(item.information_gain_proxy for item in mutations)
    best = [item for item in mutations if item.information_gain_proxy == best_score]
    if best_score <= 0.0:
        return ChallengeMutationDecision(
            seed_family,
            tuple(mutations),
            None,
            "HOLD",
            ("no_discriminating_mutation",),
        )
    if len(best) != 1:
        return ChallengeMutationDecision(
            seed_family,
            tuple(mutations),
            None,
            "HOLD",
            ("information_gain_tie_requires_additional_evidence",),
        )

    return ChallengeMutationDecision(
        seed_family,
        tuple(mutations),
        best[0].family,
        "PASS",
        (),
    )
