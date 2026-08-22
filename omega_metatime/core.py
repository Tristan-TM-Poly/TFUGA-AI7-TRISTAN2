from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Sequence


class TemporalRegime(str, Enum):
    EXPLORE = "EXPLORE"
    VERIFY = "VERIFY"
    BUILD = "BUILD"
    ATTACK = "ATTACK"
    COMPRESS = "COMPRESS"
    HARVEST = "HARVEST"
    RESTORE = "RESTORE"


@dataclass(frozen=True)
class TemporalCounters:
    elapsed_hours: float
    ideas: int = 0
    hypotheses: int = 0
    formalisms: int = 0
    code_changes: int = 0
    prototypes: int = 0
    validations: int = 0
    reuses: int = 0
    mastery_units: int = 0

    def _hours(self) -> float:
        if self.elapsed_hours <= 0:
            raise ValueError("elapsed_hours must be > 0")
        return self.elapsed_hours

    def activity_density(self) -> float:
        total = (
            self.ideas
            + self.hypotheses
            + self.formalisms
            + self.code_changes
            + self.prototypes
            + self.validations
            + self.reuses
            + self.mastery_units
        )
        return total / self._hours()

    def verified_capability_velocity(self) -> float:
        return (self.validations + self.mastery_units) / self._hours()

    def proof_bandwidth(self) -> float:
        claims = max(self.ideas + self.hypotheses, 1)
        return min(1.0, self.validations / claims)


@dataclass(frozen=True)
class CapabilityDelta:
    elapsed_hours: float
    verified_gain: float = 0.0
    retention: float = 0.0
    transfer: float = 0.0
    reuse: float = 0.0
    regenerability: float = 0.0
    future_option_value: float = 0.0
    attention: float = 0.0
    compute: float = 0.0
    complexity: float = 0.0
    risk: float = 0.0
    epistemic_debt: float = 0.0

    def omega_density(self) -> float:
        if self.elapsed_hours <= 0:
            raise ValueError("elapsed_hours must be > 0")
        numerator = (
            max(self.verified_gain, 0.0)
            + max(self.retention, 0.0)
            + max(self.transfer, 0.0)
            + max(self.reuse, 0.0)
            + max(self.regenerability, 0.0)
            + max(self.future_option_value, 0.0)
        )
        denominator = (
            self.elapsed_hours
            * (
                1.0
                + max(self.attention, 0.0)
                + max(self.compute, 0.0)
                + max(self.complexity, 0.0)
                + max(self.risk, 0.0)
                + max(self.epistemic_debt, 0.0)
            )
        )
        return numerator / denominator


@dataclass(frozen=True)
class TemporalState:
    active_branches: int = 0
    proof_bandwidth: float = 1.0
    residual_uncertainty: float = 0.0
    evidence_debt: float = 0.0
    prototype_readiness: float = 0.0
    branch_overlap: float = 0.0
    adversarial_need: float = 0.0
    harvest_readiness: float = 0.0
    fatigue: float = 0.0


@dataclass(frozen=True)
class StrategyGenome:
    strategy_id: str
    expected_verified_gain: float
    expected_information_gain: float
    transfer: float
    regenerability: float
    future_work_eliminated: float
    time_cost: float
    attention_cost: float = 0.0
    compute_cost: float = 0.0
    complexity_cost: float = 0.0
    risk_cost: float = 0.0
    epistemic_debt: float = 0.0
    generator_id: str = "generator"
    verifier_id: str = "verifier"

    def utility(self) -> float:
        if self.generator_id == self.verifier_id:
            return float("-inf")
        numerator = (
            max(self.expected_verified_gain, 0.0)
            + max(self.expected_information_gain, 0.0)
            + max(self.transfer, 0.0)
            + max(self.regenerability, 0.0)
            + max(self.future_work_eliminated, 0.0)
        )
        denominator = (
            max(self.time_cost, 0.0)
            + max(self.attention_cost, 0.0)
            + max(self.compute_cost, 0.0)
            + max(self.complexity_cost, 0.0)
            + max(self.risk_cost, 0.0)
            + max(self.epistemic_debt, 0.0)
            + 1.0
        )
        return numerator / denominator


@dataclass(frozen=True)
class StudentBaselineTwin:
    baseline_hours: float
    candidate_hours: float
    baseline_retention: float
    candidate_retention: float
    baseline_transfer: float
    candidate_transfer: float
    baseline_calibration: float
    candidate_calibration: float

    def validated_speedup(self) -> float | None:
        if self.baseline_hours <= 0 or self.candidate_hours <= 0:
            raise ValueError("hours must be > 0")
        if self.candidate_retention < self.baseline_retention:
            return None
        if self.candidate_transfer < self.baseline_transfer:
            return None
        if self.candidate_calibration < self.baseline_calibration:
            return None
        return self.baseline_hours / self.candidate_hours


@dataclass(frozen=True)
class TemporalCrystal:
    period_id: str
    capabilities: tuple[str, ...] = ()
    proofs: tuple[str, ...] = ()
    failures: tuple[str, ...] = ()
    reusable_primitives: tuple[str, ...] = ()
    deleted_or_absorbed: tuple[str, ...] = ()
    next_frontier: str = ""
    provenance: tuple[str, ...] = ()
    version: str = "0.1.0"

    def digest(self) -> str:
        payload = {
            "period_id": self.period_id,
            "capabilities": self.capabilities,
            "proofs": self.proofs,
            "failures": self.failures,
            "reusable_primitives": self.reusable_primitives,
            "deleted_or_absorbed": self.deleted_or_absorbed,
            "next_frontier": self.next_frontier,
            "provenance": self.provenance,
            "version": self.version,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return sha256(canonical.encode("utf-8")).hexdigest()


class MetaTimeEngine:
    """Conservative temporal-capability controller.

    It generates recommendations and proofs-of-better candidates but does not
    execute external, financial, publication, or governance side effects.
    """

    def choose_regime(self, state: TemporalState) -> TemporalRegime:
        if state.fatigue >= 0.8:
            return TemporalRegime.RESTORE
        if state.branch_overlap >= 0.6 and state.active_branches >= 6:
            return TemporalRegime.COMPRESS
        if state.evidence_debt >= 0.6 or state.proof_bandwidth < 0.2:
            return TemporalRegime.VERIFY
        if state.adversarial_need >= 0.7:
            return TemporalRegime.ATTACK
        if state.harvest_readiness >= 0.75:
            return TemporalRegime.HARVEST
        if state.prototype_readiness >= 0.7:
            return TemporalRegime.BUILD
        if state.residual_uncertainty >= 0.7:
            return TemporalRegime.EXPLORE
        return TemporalRegime.VERIFY

    def should_open_branch(
        self,
        *,
        expected_verified_gain: float,
        opportunity_cost: float,
        proof_bandwidth: float,
        active_branches: int,
        max_branches: int = 8,
    ) -> bool:
        if active_branches >= max_branches:
            return False
        if proof_bandwidth < 0.2:
            return False
        return expected_verified_gain > opportunity_cost

    def should_automate(
        self,
        *,
        future_work_eliminated: float,
        build_cost: float,
        maintenance_cost: float,
        risk_cost: float,
        complexity_cost: float,
    ) -> bool:
        return future_work_eliminated > (
            build_cost + maintenance_cost + risk_cost + complexity_cost
        )

    def should_create_meta_level(
        self,
        *,
        verified_out_of_sample_gain: float,
        complexity_cost: float,
        risk_cost: float,
        debt_cost: float,
        expressible_by_current_kernel: bool,
    ) -> bool:
        if expressible_by_current_kernel:
            return False
        return verified_out_of_sample_gain > (complexity_cost + risk_cost + debt_cost)

    def select_strategy(
        self,
        strategies: Sequence[StrategyGenome],
        *,
        baseline_utility: float = 0.0,
    ) -> StrategyGenome | None:
        valid = [s for s in strategies if s.utility() > baseline_utility]
        if not valid:
            return None
        return max(valid, key=lambda s: (s.utility(), s.strategy_id))

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
    def crystallize(
        *,
        period_id: str,
        capabilities: Sequence[str],
        proofs: Sequence[str],
        failures: Sequence[str],
        reusable_primitives: Sequence[str],
        deleted_or_absorbed: Sequence[str],
        next_frontier: str,
        provenance: Sequence[str] = (),
    ) -> TemporalCrystal:
        return TemporalCrystal(
            period_id=period_id,
            capabilities=tuple(capabilities[:3]),
            proofs=tuple(proofs[:3]),
            failures=tuple(failures[:3]),
            reusable_primitives=tuple(reusable_primitives[:3]),
            deleted_or_absorbed=tuple(deleted_or_absorbed[:3]),
            next_frontier=next_frontier,
            provenance=tuple(provenance),
        )

    @staticmethod
    def minimum_generator_cover(
        capability_requirements: dict[str, set[str]],
        generator_outputs: dict[str, set[str]],
    ) -> tuple[str, ...]:
        """Greedy cover for a small regenerative seed.

        This is a heuristic, not a proof of globally minimal set cover.
        """
        required = set().union(*capability_requirements.values()) if capability_requirements else set()
        uncovered = set(required)
        chosen: list[str] = []
        remaining = dict(generator_outputs)

        while uncovered:
            ranked = sorted(
                (
                    (len(outputs & uncovered), generator_id)
                    for generator_id, outputs in remaining.items()
                ),
                key=lambda x: (-x[0], x[1]),
            )
            if not ranked or ranked[0][0] == 0:
                break
            _, best = ranked[0]
            chosen.append(best)
            uncovered -= remaining.pop(best)
        return tuple(chosen)
