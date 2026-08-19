from __future__ import annotations

from dataclasses import dataclass, field, replace
from math import exp, log
from typing import Mapping


@dataclass(frozen=True)
class BondChannel:
    """Normalized structural descriptor for a bonding channel.

    Scores are intentionally dimensionless descriptors, not ab-initio observables.
    They are suitable for ranking metadata only and must never replace DFT/DFPT.
    """

    label: str
    orientation: str
    covalent: bool
    density_per_cell: float
    distance_angstrom: float
    stiffness_score: float

    def __post_init__(self) -> None:
        if self.density_per_cell < 0:
            raise ValueError("density_per_cell must be non-negative")
        if self.distance_angstrom <= 0:
            raise ValueError("distance_angstrom must be positive")
        if not 0.0 <= self.stiffness_score <= 1.0:
            raise ValueError("stiffness_score must be in [0, 1]")


@dataclass(frozen=True)
class OrbitalChannel:
    label: str
    direction: str
    fermi_weight: float
    dos_fraction: float

    def __post_init__(self) -> None:
        for name, value in (("fermi_weight", self.fermi_weight), ("dos_fraction", self.dos_fraction)):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")


@dataclass(frozen=True)
class PhononChannel:
    label: str
    polarization: str
    omega_log_k: float
    lambda_ep: float
    stability_margin: float

    def __post_init__(self) -> None:
        if self.omega_log_k <= 0:
            raise ValueError("omega_log_k must be positive")
        if self.lambda_ep < 0:
            raise ValueError("lambda_ep must be non-negative")


@dataclass(frozen=True)
class SuperconductingCandidate:
    """Minimal BOP (bond-orbital-phonon) state used by Ω-SC-HG-T∞.

    `phase_ordering_ceiling_k` is an externally supplied ceiling/estimate. This
    module deliberately does not infer a BKT transition from pairing data.
    """

    name: str
    formula: str
    dimensionality: str
    bonds: tuple[BondChannel, ...]
    orbitals: tuple[OrbitalChannel, ...]
    phonons: tuple[PhononChannel, ...]
    phase_ordering_ceiling_k: float
    synthesis_score: float
    defect_robustness: float
    substrate_robustness: float
    metadata: Mapping[str, str | float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.phase_ordering_ceiling_k < 0:
            raise ValueError("phase_ordering_ceiling_k must be non-negative")
        for name, value in (
            ("synthesis_score", self.synthesis_score),
            ("defect_robustness", self.defect_robustness),
            ("substrate_robustness", self.substrate_robustness),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")

    @property
    def lambda_total(self) -> float:
        return sum(channel.lambda_ep for channel in self.phonons)

    @property
    def omega_log_k(self) -> float:
        lam = self.lambda_total
        if lam <= 0:
            return 0.0
        return exp(sum(p.lambda_ep * log(p.omega_log_k) for p in self.phonons) / lam)

    @property
    def minimum_stability_margin(self) -> float:
        return min((p.stability_margin for p in self.phonons), default=float("-inf"))

    @property
    def has_interlayer_covalent_bond(self) -> bool:
        return any(b.covalent and b.orientation.lower() in {"interlayer", "out-of-plane", "z"} for b in self.bonds)

    def pairing_tc_k(self, mu_star: float = 0.10, *, lambda_scale: float = 1.0, omega_scale: float = 1.0) -> float:
        """McMillan/Allen-Dynes-style screening proxy.

        This is a cheap triage model, not a substitute for converged anisotropic
        Eliashberg calculations. `omega_log_k` is expressed in kelvin.
        """
        if not 0.0 <= mu_star < 1.0:
            raise ValueError("mu_star must be in [0, 1)")
        lam = self.lambda_total * lambda_scale
        omega = self.omega_log_k * omega_scale
        if lam <= 0 or omega <= 0:
            return 0.0
        denominator = lam - mu_star * (1.0 + 0.62 * lam)
        if denominator <= 0:
            return 0.0
        exponent = -1.04 * (1.0 + lam) / denominator
        return (omega / 1.2) * exp(exponent)

    def usable_tc_k(self, mu_star: float = 0.10) -> float:
        return min(self.pairing_tc_k(mu_star), self.phase_ordering_ceiling_k)

    def with_scaled_phonons(self, *, lambda_scale: float = 1.0, omega_scale: float = 1.0) -> "SuperconductingCandidate":
        phonons = tuple(
            replace(p, lambda_ep=p.lambda_ep * lambda_scale, omega_log_k=p.omega_log_k * omega_scale)
            for p in self.phonons
        )
        return replace(self, phonons=phonons)
