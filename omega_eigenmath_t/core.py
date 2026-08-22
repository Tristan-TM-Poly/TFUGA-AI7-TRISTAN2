from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Sequence


class MathClaimStatus(str, Enum):
    UNPROVEN = "UNPROVEN"
    SPECULATIVE = "SPECULATIVE"
    COMPUTATIONALLY_SUPPORTED = "COMPUTATIONALLY_SUPPORTED"
    PROVED_SPECIAL_CASE = "PROVED_SPECIAL_CASE"
    FORMALLY_PROVED = "FORMALLY_PROVED"
    INDEPENDENTLY_VERIFIED = "INDEPENDENTLY_VERIFIED"
    FALSIFIED = "FALSIFIED"


class NoveltyStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    REPRODUCED = "REPRODUCED"
    REFORMALIZED = "REFORMALIZED"
    NEW_DERIVATION = "NEW_DERIVATION"
    NEW_THEOREM_CANDIDATE = "NEW_THEOREM_CANDIDATE"
    EXTERNALLY_VERIFIED_NEW_THEOREM = "EXTERNALLY_VERIFIED_NEW_THEOREM"


_PROMOTION_RANK = {
    MathClaimStatus.UNPROVEN: 0,
    MathClaimStatus.SPECULATIVE: 1,
    MathClaimStatus.COMPUTATIONALLY_SUPPORTED: 2,
    MathClaimStatus.PROVED_SPECIAL_CASE: 3,
    MathClaimStatus.FORMALLY_PROVED: 4,
    MathClaimStatus.INDEPENDENTLY_VERIFIED: 5,
}


@dataclass(frozen=True)
class ProblemGenome:
    problem_id: str
    title: str
    exact_statement: str
    axioms: tuple[str, ...] = ()
    definitions: tuple[str, ...] = ()
    known_results: tuple[str, ...] = ()
    residual_ids: tuple[str, ...] = ()
    boss_locked_unproven: bool = False
    version: str = "0.1.0"

    def digest(self) -> str:
        return _digest(asdict(self))


@dataclass(frozen=True)
class FormalizationReceipt:
    human_statement_hash: str
    formal_statement_hash: str
    formal_system: str
    translator_id: str
    reviewer_id: str
    fidelity_checks: tuple[str, ...] = ()
    unresolved_ambiguities: tuple[str, ...] = ()

    @property
    def faithful_candidate(self) -> bool:
        return (
            bool(self.human_statement_hash)
            and bool(self.formal_statement_hash)
            and bool(self.formal_system)
            and self.translator_id != self.reviewer_id
            and bool(self.fidelity_checks)
            and not self.unresolved_ambiguities
        )


@dataclass(frozen=True)
class ProofObligation:
    obligation_id: str
    problem_id: str
    statement: str
    assumptions: tuple[str, ...]
    dependencies: tuple[str, ...]
    status: MathClaimStatus
    producer_id: str
    verifier_id: str
    falsifier_id: str
    provenance: tuple[str, ...]
    tests: tuple[str, ...] = ()
    proof_artifact: str | None = None
    computational_evidence: tuple[str, ...] = ()
    formalization: FormalizationReceipt | None = None
    independent_replay: tuple[str, ...] = ()
    community_acceptance_receipt: str | None = None
    novelty_status: NoveltyStatus = NoveltyStatus.UNKNOWN

    def digest(self) -> str:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["novelty_status"] = self.novelty_status.value
        return _digest(payload)


@dataclass(frozen=True)
class ProofDecision:
    accepted: bool
    promotable: bool
    final_status: MathClaimStatus
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class MathematicalResidual:
    residual_id: str
    statement: str
    expected_information_gain: float
    expected_residual_reduction: float
    transfer: float
    proof_value: float
    cost: float = 0.0
    uncertainty: float = 0.0
    complexity: float = 0.0

    def priority(self) -> float:
        numerator = (
            max(self.expected_information_gain, 0.0)
            * max(self.expected_residual_reduction, 0.0)
            * max(self.transfer, 0.0)
            * max(self.proof_value, 0.0)
        )
        denominator = 1.0 + max(self.cost, 0.0) + max(self.uncertainty, 0.0) + max(self.complexity, 0.0)
        return numerator / denominator


@dataclass(frozen=True)
class FailureCrystal:
    failure_id: str
    pattern: str
    failure_mechanism: str
    detector: str
    minimal_counterexample: str | None = None
    scope: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def digest(self) -> str:
        return _digest(asdict(self))


@dataclass(frozen=True)
class ProofCrystal:
    crystal_id: str
    statement: str
    assumptions: tuple[str, ...]
    dependencies: tuple[str, ...]
    proof_artifact: str
    formal_system: str
    provenance: tuple[str, ...]
    tests: tuple[str, ...]
    independent_replay: tuple[str, ...]
    novelty_status: NoveltyStatus
    version: str = "0.1.0"

    def digest(self) -> str:
        payload = asdict(self)
        payload["novelty_status"] = self.novelty_status.value
        return _digest(payload)


@dataclass(frozen=True)
class ProofDebtLedger:
    generated_obligations: int = 0
    checked_obligations: int = 0
    hidden_assumptions: int = 0
    unreplayed_proofs: int = 0
    unsupported_promotions: int = 0

    def debt(self) -> int:
        unchecked = max(self.generated_obligations - self.checked_obligations, 0)
        return unchecked + self.hidden_assumptions + self.unreplayed_proofs + self.unsupported_promotions

    def mode(self, max_debt: int) -> str:
        return "VERIFY_ATTACK_COMPRESS" if self.debt() >= max_debt else "GENERATE"


@dataclass(frozen=True)
class MetaImprovementReceipt:
    improvement_id: str
    verified_out_of_sample_gain: float
    complexity_cost: float
    risk_debt: float
    epistemic_debt: float
    expressible_by_current_kernel: bool
    frozen_tests: tuple[str, ...]
    generator_id: str
    judge_id: str

    def promote_meta_level(self, margin: float = 0.0) -> bool:
        if self.generator_id == self.judge_id or not self.frozen_tests:
            return False
        if self.expressible_by_current_kernel:
            return False
        burden = self.complexity_cost + self.risk_debt + self.epistemic_debt + margin
        return self.verified_out_of_sample_gain > burden


@dataclass(frozen=True)
class RegenerationSeed:
    proof_crystal_digests: tuple[str, ...]
    failure_crystal_digests: tuple[str, ...]
    constitution: tuple[str, ...]
    version: str = "0.1.0"

    def digest(self) -> str:
        return _digest(asdict(self))


class ProofCourt:
    """Fail-closed mathematical claim court.

    It does not prove mathematics. It checks whether metadata/evidence is sufficient
    for a requested epistemic status and prevents boss problems from being internally
    self-promoted to solved.
    """

    CONSTITUTION = (
        "Generated != Proven",
        "Formalized != FaithfullyFormalized",
        "NumericallySupported != Universal",
        "Reproduced != Novel",
        "Novel != Important",
        "EquivalentOnTests != Equivalent",
        "Generator != Judge",
        "SelfImprovement != SelfApproval",
        "MillenniumCandidate != MillenniumSolved",
    )

    @staticmethod
    def _independent_roles(obligation: ProofObligation) -> bool:
        return len({obligation.producer_id, obligation.verifier_id, obligation.falsifier_id}) == 3

    def judge(self, problem: ProblemGenome, obligation: ProofObligation) -> ProofDecision:
        reasons: list[str] = []
        requested = obligation.status

        if obligation.problem_id != problem.problem_id:
            reasons.append("obligation/problem mismatch")
        if not obligation.statement.strip():
            reasons.append("statement is required")
        if not obligation.provenance:
            reasons.append("provenance is required")
        if not obligation.tests:
            reasons.append("at least one discriminating test is required")
        if not self._independent_roles(obligation):
            reasons.append("Generator != Judge != Falsifier violated")

        if requested in {MathClaimStatus.FORMALLY_PROVED, MathClaimStatus.INDEPENDENTLY_VERIFIED}:
            if not obligation.proof_artifact:
                reasons.append("formal promotion requires a proof artifact")
            if obligation.formalization is None or not obligation.formalization.faithful_candidate:
                reasons.append("formal promotion requires an independently reviewed faithful-formalization candidate")

        if requested is MathClaimStatus.INDEPENDENTLY_VERIFIED and not obligation.independent_replay:
            reasons.append("independent verification requires at least one replay receipt")

        if requested in {MathClaimStatus.FORMALLY_PROVED, MathClaimStatus.INDEPENDENTLY_VERIFIED}:
            if obligation.computational_evidence and not obligation.proof_artifact:
                reasons.append("NumericalEvidence != Proof")

        if problem.boss_locked_unproven and requested in {
            MathClaimStatus.FORMALLY_PROVED,
            MathClaimStatus.INDEPENDENTLY_VERIFIED,
        }:
            if not obligation.community_acceptance_receipt:
                reasons.append("boss problem remains BOSS_LOCKED_UNPROVEN without external community-acceptance receipt")

        if requested is MathClaimStatus.FALSIFIED:
            accepted = not [r for r in reasons if r not in {"formal promotion requires a proof artifact"}]
            return ProofDecision(accepted, False, MathClaimStatus.FALSIFIED, tuple(reasons))

        accepted = not reasons
        return ProofDecision(accepted, accepted, requested if accepted else MathClaimStatus.UNPROVEN, tuple(reasons))

    def crystallize(self, problem: ProblemGenome, obligation: ProofObligation) -> ProofCrystal | FailureCrystal | None:
        decision = self.judge(problem, obligation)
        if not decision.accepted:
            return None
        if obligation.status is MathClaimStatus.FALSIFIED:
            return FailureCrystal(
                failure_id=f"failure:{obligation.obligation_id}",
                pattern=obligation.statement,
                failure_mechanism="counterexample_or_discriminating_test",
                detector="replay obligation tests",
                minimal_counterexample=obligation.tests[0] if obligation.tests else None,
                scope=(problem.problem_id,),
                provenance=obligation.provenance,
            )
        if obligation.status is not MathClaimStatus.INDEPENDENTLY_VERIFIED:
            return None
        assert obligation.proof_artifact is not None
        assert obligation.formalization is not None
        return ProofCrystal(
            crystal_id=f"proof:{obligation.obligation_id}",
            statement=obligation.statement,
            assumptions=obligation.assumptions,
            dependencies=obligation.dependencies,
            proof_artifact=obligation.proof_artifact,
            formal_system=obligation.formalization.formal_system,
            provenance=obligation.provenance,
            tests=obligation.tests,
            independent_replay=obligation.independent_replay,
            novelty_status=obligation.novelty_status,
        )


class AttackEngine:
    """Metadata-level red team. It never substitutes for a formal kernel."""

    def attack(self, obligation: ProofObligation) -> tuple[FailureCrystal, ...]:
        failures: list[FailureCrystal] = []
        if obligation.producer_id == obligation.verifier_id:
            failures.append(self._failure(obligation, "generator_judge_collision", "producer and verifier are identical"))
        if not obligation.assumptions and "assume" in obligation.statement.lower():
            failures.append(self._failure(obligation, "hidden_assumption", "statement signals assumptions but none are declared"))
        if obligation.status in {MathClaimStatus.FORMALLY_PROVED, MathClaimStatus.INDEPENDENTLY_VERIFIED} and not obligation.proof_artifact:
            failures.append(self._failure(obligation, "missing_proof_artifact", "formal status requested without formal proof artifact"))
        if obligation.formalization and obligation.formalization.unresolved_ambiguities:
            failures.append(self._failure(obligation, "formalization_gap", "formalization has unresolved ambiguities"))
        if obligation.computational_evidence and obligation.status in {MathClaimStatus.FORMALLY_PROVED, MathClaimStatus.INDEPENDENTLY_VERIFIED} and not obligation.proof_artifact:
            failures.append(self._failure(obligation, "numerical_to_universal_jump", "computational evidence was promoted as proof"))
        if obligation.obligation_id in obligation.dependencies:
            failures.append(self._failure(obligation, "direct_circularity", "obligation depends on itself"))
        return tuple(failures)

    @staticmethod
    def _failure(obligation: ProofObligation, pattern: str, mechanism: str) -> FailureCrystal:
        return FailureCrystal(
            failure_id=f"{obligation.obligation_id}:{pattern}",
            pattern=pattern,
            failure_mechanism=mechanism,
            detector=pattern,
            scope=(obligation.problem_id,),
            provenance=obligation.provenance,
        )


class ResidualEngine:
    @staticmethod
    def rank(residuals: Iterable[MathematicalResidual]) -> list[MathematicalResidual]:
        return sorted(residuals, key=lambda r: (-r.priority(), r.residual_id))


class RegenerationEngine:
    @staticmethod
    def distill(
        proofs: Sequence[ProofCrystal],
        failures: Sequence[FailureCrystal],
        constitution: Sequence[str] = ProofCourt.CONSTITUTION,
    ) -> RegenerationSeed:
        return RegenerationSeed(
            proof_crystal_digests=tuple(sorted(p.digest() for p in proofs)),
            failure_crystal_digests=tuple(sorted(f.digest() for f in failures)),
            constitution=tuple(constitution),
        )

    @staticmethod
    def closure(required_digests: Iterable[str], rebuilt_digests: Iterable[str]) -> float:
        required = set(required_digests)
        rebuilt = set(rebuilt_digests)
        if not required:
            return 1.0
        return len(required & rebuilt) / len(required)


def millennium_problem_genomes() -> tuple[ProblemGenome, ...]:
    """Canonical R0 metadata only; exact official statements belong in external source records."""
    titles = (
        ("bsd", "Birch and Swinnerton-Dyer Conjecture"),
        ("hodge", "Hodge Conjecture"),
        ("navier_stokes", "Navier-Stokes Existence and Smoothness"),
        ("p_vs_np", "P versus NP"),
        ("riemann", "Riemann Hypothesis"),
        ("yang_mills", "Yang-Mills Existence and Mass Gap"),
    )
    return tuple(
        ProblemGenome(
            problem_id=pid,
            title=title,
            exact_statement="External authoritative statement required; R0 does not duplicate or reinterpret it.",
            boss_locked_unproven=True,
        )
        for pid, title in titles
    )


def to_morphogenesis_residual(residual: MathematicalResidual):
    """Adapter to the repository's generic Ω Meta-Morphogenesis kernel."""
    from omega_morphogenesis import Residual

    return Residual(
        residual_id=residual.residual_id,
        impact=residual.expected_residual_reduction,
        uncertainty=residual.uncertainty,
        dependency_centrality=residual.proof_value,
        expected_information_gain=residual.expected_information_gain,
        downstream_leverage=residual.transfer,
        cost=residual.cost,
        complexity=residual.complexity,
    )


def _digest(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return sha256(canonical.encode("utf-8")).hexdigest()
