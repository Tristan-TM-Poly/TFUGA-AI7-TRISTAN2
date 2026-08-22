from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from hashlib import sha256
import json
from typing import Iterable, Mapping, Sequence


class EpistemicStatus(IntEnum):
    """Conservative evidence ladder.

    Ordering is only used as a minimum-support guard. It does not claim that all
    scientific evidence forms are totally ordered in reality.
    """

    FALSIFIED = -1
    GENERATED = 0
    SPECULATIVE = 1
    HYPOTHESIS = 2
    DERIVED = 3
    SIMULATED = 4
    OBSERVED = 5
    REPLICATED = 6
    CAUSALLY_SUPPORTED = 7


_MUTATING_ACTIONS = frozenset({"execute", "publish", "spend", "govern", "write"})


@dataclass(frozen=True)
class AuthorityEnvelope:
    allowed_actions: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def from_actions(cls, *actions: str) -> "AuthorityEnvelope":
        return cls(frozenset(a.strip().lower() for a in actions if a.strip()))

    def allows(self, action: str) -> bool:
        return action.strip().lower() in self.allowed_actions


@dataclass(frozen=True)
class Residual:
    residual_id: str
    impact: float
    uncertainty: float
    dependency_centrality: float
    expected_information_gain: float
    downstream_leverage: float = 1.0
    cost: float = 0.0
    risk: float = 0.0
    complexity: float = 0.0

    def priority(self) -> float:
        numerator = (
            max(self.impact, 0.0)
            * max(self.uncertainty, 0.0)
            * max(self.dependency_centrality, 0.0)
            * max(self.expected_information_gain, 0.0)
            * max(self.downstream_leverage, 0.0)
        )
        denominator = 1.0 + max(self.cost, 0.0) + max(self.risk, 0.0) + max(self.complexity, 0.0)
        return numerator / denominator


@dataclass(frozen=True)
class TransformationMetrics:
    verified_gain: float = 0.0
    information_gain: float = 0.0
    transfer: float = 0.0
    regenerability: float = 0.0
    optionality: float = 0.0
    future_work_eliminated: float = 0.0
    complexity: float = 0.0
    risk: float = 0.0
    human_friction: float = 0.0
    epistemic_debt: float = 0.0
    complexity_rent: float = 0.0

    def utility(self) -> float:
        capability_term = (
            max(self.verified_gain, 0.0)
            * max(self.transfer, 0.0)
            * max(self.regenerability, 0.0)
            * max(self.optionality, 0.0)
        )
        numerator = capability_term + max(self.information_gain, 0.0) + max(self.future_work_eliminated, 0.0)
        denominator = (
            1.0
            + max(self.complexity, 0.0)
            + max(self.risk, 0.0)
            + max(self.human_friction, 0.0)
            + max(self.epistemic_debt, 0.0)
        )
        return numerator / denominator

    def pays_complexity_rent(self) -> bool:
        return self.utility() > max(self.complexity_rent, 0.0)


@dataclass(frozen=True)
class ProofCarryingTransformation:
    transformation_id: str
    before_hash: str
    after_hash: str
    generator_id: str
    verifier_id: str
    action: str
    authority: AuthorityEnvelope
    input_status: EpistemicStatus
    output_status: EpistemicStatus
    evidence_status: EpistemicStatus
    provenance: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    rollback: str | None = None
    compensation: str | None = None
    risk_score: float = 0.0
    metrics: TransformationMetrics = field(default_factory=TransformationMetrics)


@dataclass(frozen=True)
class KernelDecision:
    accepted: bool
    reasons: tuple[str, ...]
    utility: float
    persist: bool


@dataclass(frozen=True)
class CapabilityCrystal:
    name: str
    contract: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    generator: str
    evidence: tuple[str, ...]
    tests: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    version: str = "0.1.0"

    def digest(self) -> str:
        payload = {
            "name": self.name,
            "contract": self.contract,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "generator": self.generator,
            "evidence": self.evidence,
            "tests": self.tests,
            "dependencies": self.dependencies,
            "provenance": self.provenance,
            "version": self.version,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return sha256(canonical.encode("utf-8")).hexdigest()


class MorphogenesisKernel:
    """Minimal proof-carrying morphogenesis court.

    The kernel is intentionally conservative: it selects among candidates but does
    not execute external side effects itself.
    """

    def validate(self, tx: ProofCarryingTransformation) -> KernelDecision:
        reasons: list[str] = []
        action = tx.action.strip().lower()

        if not tx.before_hash or not tx.after_hash:
            reasons.append("state hashes are required")
        if tx.generator_id == tx.verifier_id:
            reasons.append("Generator != Judge violated")
        if not tx.provenance:
            reasons.append("provenance is required")
        if not tx.tests:
            reasons.append("at least one test is required")
        if not tx.authority.allows(action):
            reasons.append(f"authority does not allow action: {action}")

        if tx.output_status == EpistemicStatus.FALSIFIED:
            pass
        elif tx.evidence_status == EpistemicStatus.FALSIFIED:
            reasons.append("falsified evidence cannot support a promoted claim")
        elif tx.output_status > tx.evidence_status:
            reasons.append("epistemic inflation: output exceeds supporting evidence")

        if tx.input_status == EpistemicStatus.GENERATED and tx.output_status >= EpistemicStatus.OBSERVED:
            if tx.evidence_status < EpistemicStatus.OBSERVED:
                reasons.append("Generated cannot become Observed without observed evidence")

        if action in _MUTATING_ACTIONS and tx.risk_score >= 0.7:
            if not tx.rollback and not tx.compensation:
                reasons.append("high-risk mutation requires rollback or compensation")

        utility = tx.metrics.utility()
        persist = not reasons and tx.metrics.pays_complexity_rent()
        return KernelDecision(not reasons, tuple(reasons), utility, persist)

    def rank_residuals(self, residuals: Iterable[Residual]) -> list[Residual]:
        return sorted(residuals, key=lambda r: (-r.priority(), r.residual_id))

    def select_candidate(
        self,
        candidates: Sequence[ProofCarryingTransformation],
        baseline_utility: float = 0.0,
    ) -> ProofCarryingTransformation | None:
        """Select the best valid candidate only if it beats DO_NOTHING/baseline."""
        best: ProofCarryingTransformation | None = None
        best_utility = baseline_utility
        for candidate in candidates:
            decision = self.validate(candidate)
            if decision.accepted and decision.utility > best_utility:
                best = candidate
                best_utility = decision.utility
        return best

    @staticmethod
    def should_create_meta_level(
        verified_out_of_sample_gain: float,
        meta_complexity_cost: float,
        expressible_by_current_kernel: bool,
    ) -> bool:
        if expressible_by_current_kernel:
            return False
        return verified_out_of_sample_gain > meta_complexity_cost

    @staticmethod
    def regeneration_closure(
        required_components: Iterable[str],
        rebuilt_components: Iterable[str],
    ) -> float:
        required = set(required_components)
        rebuilt = set(rebuilt_components)
        if not required:
            return 1.0
        return len(required & rebuilt) / len(required)

    @staticmethod
    def evidence_dependency_blast_radius(
        dependency_graph: Mapping[str, Iterable[str]],
        root: str,
    ) -> tuple[str, ...]:
        seen: set[str] = set()
        stack = [root]
        while stack:
            current = stack.pop()
            for child in dependency_graph.get(current, ()):
                if child not in seen:
                    seen.add(child)
                    stack.append(child)
        return tuple(sorted(seen))
