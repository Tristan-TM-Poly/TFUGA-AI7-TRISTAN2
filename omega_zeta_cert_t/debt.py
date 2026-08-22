from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .model import BarrierClass, CertificateFamily, MomentTensorSpec, MomentWordMode


class DebtStatus(str, Enum):
    INSIDE_DECLARED_BUDGET = "inside_declared_budget"
    REQUIRES_NEW_OR_REDUCED_SUPPORT_INPUT = "requires_new_or_reduced_support_input"
    REQUIRED = "required"
    CONDITIONAL = "conditional"
    REPRESENTATION_GATE = "representation_gate"


@dataclass(frozen=True)
class SupportDebt:
    order: int
    observable_count: int
    conservative_required_radius: float
    declared_known_radius: float
    excess_radius: float
    status: DebtStatus
    semantics: str = "conservative_minkowski_bookkeeping_not_arithmetic_theorem"

    def to_dict(self) -> dict:
        return {
            "order": self.order,
            "observable_count": self.observable_count,
            "conservative_required_radius": self.conservative_required_radius,
            "declared_known_radius": self.declared_known_radius,
            "excess_radius": self.excess_radius,
            "status": self.status.value,
            "semantics": self.semantics,
            "proof_claimed": False,
        }


@dataclass(frozen=True)
class TheoremObligation:
    obligation_id: str
    title: str
    barrier: BarrierClass
    status: DebtStatus
    minimal_requirement: str
    dependencies: tuple[str, ...] = ()
    source_class: str = "derived_research_obligation"

    def to_dict(self) -> dict:
        return {
            "obligation_id": self.obligation_id,
            "title": self.title,
            "barrier": self.barrier.value,
            "status": self.status.value,
            "minimal_requirement": self.minimal_requirement,
            "dependencies": list(self.dependencies),
            "source_class": self.source_class,
            "proof_claimed": False,
            "rh_solved_claimed": False,
        }


@dataclass(frozen=True)
class DualSensitivity:
    """Sensitivity supplied by an external or experimental dual optimization.

    The class deliberately does not estimate its own multiplier. A caller must
    supply the dual multiplier and provenance class explicitly.
    """
    observable_id: str
    dual_multiplier: float
    anticipated_observable_improvement: float
    theorem_cost: float
    source_class: str

    def validate(self) -> None:
        if not self.observable_id:
            raise ValueError("observable_id is required")
        if self.theorem_cost <= 0:
            raise ValueError("theorem_cost must be positive")
        if not self.source_class:
            raise ValueError("source_class is required")

    @property
    def shadow_value(self) -> float:
        self.validate()
        return abs(self.dual_multiplier) * abs(self.anticipated_observable_improvement)

    @property
    def theorem_voi(self) -> float:
        self.validate()
        return self.shadow_value / self.theorem_cost

    def to_dict(self) -> dict:
        return {
            "observable_id": self.observable_id,
            "dual_multiplier": self.dual_multiplier,
            "anticipated_observable_improvement": self.anticipated_observable_improvement,
            "theorem_cost": self.theorem_cost,
            "source_class": self.source_class,
            "shadow_value": self.shadow_value,
            "theorem_voi": self.theorem_voi,
            "score_semantics": "sensitivity_per_declared_cost_not_truth_probability",
            "proof_claimed": False,
        }


def compile_support_debt(
    spec: MomentTensorSpec,
    *,
    declared_known_radius: float,
) -> tuple[SupportDebt, ...]:
    spec.validate()
    if declared_known_radius <= 0:
        raise ValueError("declared_known_radius must be positive")
    rows: list[SupportDebt] = []
    for order in range(1, spec.max_order + 1):
        radius = order * spec.base_support_radius
        excess = max(0.0, radius - declared_known_radius)
        status = (
            DebtStatus.INSIDE_DECLARED_BUDGET
            if excess == 0
            else DebtStatus.REQUIRES_NEW_OR_REDUCED_SUPPORT_INPUT
        )
        rows.append(
            SupportDebt(
                order=order,
                observable_count=spec.count_at_order(order),
                conservative_required_radius=radius,
                declared_known_radius=declared_known_radius,
                excess_radius=excess,
                status=status,
            )
        )
    return tuple(rows)


def compile_theorem_obligations(
    family: CertificateFamily,
    target_bound: float,
    spec: MomentTensorSpec | None,
) -> tuple[TheoremObligation, ...]:
    family.validate()
    if not 0 <= target_bound <= 1:
        raise ValueError("target_bound must lie in [0,1]")

    obligations: list[TheoremObligation] = []
    if target_bound > family.method_ceiling:
        obligations.append(
            TheoremObligation(
                obligation_id="zeta-cross-declared-family-ceiling",
                title="New arithmetic information outside the declared certificate family",
                barrier=BarrierClass.NEW_ARITHMETIC_INFORMATION,
                status=DebtStatus.REQUIRED,
                minimal_requirement=(
                    "Exhibit and prove an arithmetic estimate, moment identity, support extension, "
                    "or alternative certificate input not already contained in the declared family."
                ),
                dependencies=("exact-family-ceiling-scope", "source-provenance"),
            )
        )

    if spec is not None:
        support = compile_support_debt(spec, declared_known_radius=family.fourier_support_radius)
        if any(row.excess_radius > 0 for row in support):
            obligations.append(
                TheoremObligation(
                    obligation_id="zeta-discharge-support-debt",
                    title="Discharge conservative Fourier-support debt",
                    barrier=BarrierClass.SUPPORT_BUDGET,
                    status=DebtStatus.CONDITIONAL,
                    minimal_requirement=(
                        "For every promoted higher/cross moment, prove the exact prime-side identity "
                        "and information range actually needed; conservative support bookkeeping alone is insufficient."
                    ),
                    dependencies=("moment-word-spec", "explicit-formula-adapter"),
                )
            )

        if spec.word_mode is MomentWordMode.CYCLIC:
            obligations.append(
                TheoremObligation(
                    obligation_id="zeta-no-unjustified-full-symmetrization",
                    title="Preserve noncommutative trace-word information",
                    barrier=BarrierClass.NONCOMMUTATIVE_COMPRESSION,
                    status=DebtStatus.REPRESENTATION_GATE,
                    minimal_requirement=(
                        "Do not identify cyclic trace words under arbitrary permutations unless an additional "
                        "commutation, adjoint, or symmetry theorem explicitly justifies that quotient."
                    ),
                    dependencies=("cyclic-trace-invariance", "countermodel-court"),
                )
            )

    obligations.append(
        TheoremObligation(
            obligation_id="zeta-polynomial-dual-domain-control",
            title="Control the domain of any future polynomial/SOS dual certificate",
            barrier=BarrierClass.HIDDEN_ASSUMPTION,
            status=DebtStatus.CONDITIONAL,
            minimal_requirement=(
                "Before using interval polynomial minorants as global spectral certificates, prove a suitable "
                "operator-norm/support bound or replace it with a tail-control theorem."
            ),
            dependencies=("spectral-dual-candidate",),
        )
    )
    return tuple(obligations)


def rank_sensitivities(items: tuple[DualSensitivity, ...]) -> tuple[DualSensitivity, ...]:
    for item in items:
        item.validate()
    return tuple(sorted(items, key=lambda item: (-item.theorem_voi, item.observable_id)))
