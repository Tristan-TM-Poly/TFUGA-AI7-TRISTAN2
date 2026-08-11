from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from hashlib import sha256
import json
from math import comb
from typing import Iterable


class EpistemicStatus(str, Enum):
    EXTERNAL_REPORTED = "external_reported"
    REPRODUCED_NUMERICALLY = "reproduced_numerically"
    FORMAL_ARTIFACT = "formal_artifact"
    INDEPENDENTLY_REVIEWED = "independently_reviewed"
    THEOREM = "theorem"


class BarrierClass(str, Enum):
    WINDOW_OPTIMIZATION = "window_optimization"
    NEW_ARITHMETIC_INFORMATION = "new_arithmetic_information_required"
    FORMALIZATION_DEBT = "formalization_debt"
    HIDDEN_ASSUMPTION = "hidden_assumption"
    COUNTERMODEL_FAILURE = "countermodel_failure"
    NUMERICAL_ONLY = "numerical_only"
    SUPPORT_BUDGET = "support_budget_debt"
    NONCOMMUTATIVE_COMPRESSION = "noncommutative_compression_debt"


class MomentWordMode(str, Enum):
    """Equivalence relation used to compress operator words."""
    DIAGONAL = "diagonal_only"
    SYMMETRIC = "fully_symmetrized"
    CYCLIC = "cyclic_trace_words"
    FULL = "full_noncommutative_words"


def math_gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def necklace_count(alphabet_size: int, word_length: int) -> int:
    """Number of cyclic words (necklaces) of a fixed length."""
    if alphabet_size < 1 or word_length < 1:
        raise ValueError("alphabet_size and word_length must be positive")
    return sum(
        alphabet_size ** math_gcd(word_length, shift)
        for shift in range(word_length)
    ) // word_length


@dataclass(frozen=True)
class CertificateFamily:
    family_id: str
    current_bound: float
    method_ceiling: float
    fourier_support_radius: float
    status: EpistemicStatus = EpistemicStatus.EXTERNAL_REPORTED
    assumptions: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.family_id:
            raise ValueError("family_id is required")
        for name, value in (
            ("current_bound", self.current_bound),
            ("method_ceiling", self.method_ceiling),
        ):
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{name} must be in [0, 1]")
        if self.current_bound > self.method_ceiling:
            raise ValueError("current_bound cannot exceed method_ceiling")
        if self.fourier_support_radius <= 0:
            raise ValueError("fourier_support_radius must be positive")

    @property
    def headroom(self) -> float:
        self.validate()
        return self.method_ceiling - self.current_bound


@dataclass(frozen=True)
class MomentTensorSpec:
    max_order: int
    window_count: int
    base_support_radius: float
    include_cross_moments: bool = True
    word_mode: MomentWordMode = MomentWordMode.SYMMETRIC

    def validate(self) -> None:
        if self.max_order < 1:
            raise ValueError("max_order must be >= 1")
        if self.window_count < 1:
            raise ValueError("window_count must be >= 1")
        if self.base_support_radius <= 0:
            raise ValueError("base_support_radius must be positive")

    def count_at_order(self, order: int) -> int:
        if order < 1 or order > self.max_order:
            raise ValueError("order must lie in [1, max_order]")
        self.validate()
        mode = self.word_mode
        if not self.include_cross_moments or mode is MomentWordMode.DIAGONAL:
            return self.window_count
        if mode is MomentWordMode.SYMMETRIC:
            return comb(self.window_count + order - 1, order)
        if mode is MomentWordMode.CYCLIC:
            return necklace_count(self.window_count, order)
        if mode is MomentWordMode.FULL:
            return self.window_count ** order
        raise AssertionError(f"unsupported word mode {mode}")

    @property
    def conservative_support_radius(self) -> float:
        """Worst-case support-bookkeeping radius for order-k products.

        This is deliberately a conservative Minkowski-sum upper bound, not a
        theorem asserting that the corresponding zeta correlation is known.
        """
        self.validate()
        return self.max_order * self.base_support_radius

    @property
    def observable_count(self) -> int:
        self.validate()
        return sum(self.count_at_order(order) for order in range(1, self.max_order + 1))

    @property
    def order_counts(self) -> tuple[int, ...]:
        return tuple(self.count_at_order(order) for order in range(1, self.max_order + 1))


@dataclass(frozen=True)
class FrontierDecision:
    target_bound: float
    attainable_inside_declared_family: bool
    barrier: BarrierClass
    gap_from_current: float
    gap_beyond_ceiling: float
    required_support_radius_hint: float | None
    claim_boundary: str


@dataclass(frozen=True)
class ResearchRoute:
    route_id: str
    title: str
    expected_information_gain: float
    verification_strength: float
    novelty_potential: float
    estimated_cost: float
    epistemic_risk: float
    barrier_target: BarrierClass
    dependencies: tuple[str, ...] = ()

    def validate(self) -> None:
        for name in (
            "expected_information_gain",
            "verification_strength",
            "novelty_potential",
            "estimated_cost",
            "epistemic_risk",
        ):
            value = getattr(self, name)
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{name} must be in [0, 1]")

    @property
    def voi_score(self) -> float:
        self.validate()
        benefit = (
            0.45 * self.expected_information_gain
            + 0.30 * self.verification_strength
            + 0.25 * self.novelty_potential
        )
        penalty = 0.60 * self.estimated_cost + 0.40 * self.epistemic_risk
        return benefit - 0.45 * penalty


@dataclass(frozen=True)
class MMinusRecord:
    record_id: str
    barrier: BarrierClass
    summary: str
    falsifier: str
    source_refs: tuple[str, ...] = ()


@dataclass
class ResearchBundle:
    family: CertificateFamily
    target_bound: float
    moment_spec: MomentTensorSpec | None = None
    routes: list[ResearchRoute] = field(default_factory=list)
    mminus: list[MMinusRecord] = field(default_factory=list)

    def canonical_dict(self) -> dict:
        payload = {
            "family": asdict(self.family),
            "target_bound": self.target_bound,
            "moment_spec": asdict(self.moment_spec) if self.moment_spec else None,
            "routes": [asdict(route) for route in sorted(self.routes, key=lambda r: r.route_id)],
            "mminus": [asdict(item) for item in sorted(self.mminus, key=lambda r: r.record_id)],
            "rh_solved_claimed": False,
            "proof_claimed": False,
        }
        return _enum_to_value(payload)

    @property
    def digest(self) -> str:
        raw = json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":")).encode()
        return sha256(raw).hexdigest()


def _enum_to_value(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _enum_to_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_enum_to_value(v) for v in value]
    return value


def stable_cell_id(parts: Iterable[str]) -> str:
    material = "\x1f".join(parts).encode("utf-8")
    return "zeta-cert-" + sha256(material).hexdigest()[:20]
