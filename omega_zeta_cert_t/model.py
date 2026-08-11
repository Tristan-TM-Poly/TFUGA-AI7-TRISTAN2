from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from hashlib import sha256
import json
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

    def validate(self) -> None:
        if self.max_order < 1:
            raise ValueError("max_order must be >= 1")
        if self.window_count < 1:
            raise ValueError("window_count must be >= 1")
        if self.base_support_radius <= 0:
            raise ValueError("base_support_radius must be positive")

    @property
    def conservative_support_radius(self) -> float:
        """Worst-case convolution support radius for order-k products.

        This is a bookkeeping bound, not a theorem about zeta correlations.
        """
        self.validate()
        return self.max_order * self.base_support_radius

    @property
    def observable_count(self) -> int:
        """Count symmetric moment coordinates up to max_order.

        For cross-moments, order-k symmetric coordinates equal combinations
        with repetition C(n+k-1, k). Without cross moments we keep one moment
        per window per order.
        """
        from math import comb

        self.validate()
        if not self.include_cross_moments:
            return self.max_order * self.window_count
        return sum(
            comb(self.window_count + order - 1, order)
            for order in range(1, self.max_order + 1)
        )


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
        """Bounded value-of-information score, intentionally heuristic."""
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
