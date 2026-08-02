from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from random import Random
from typing import Iterable
import math


@dataclass(frozen=True)
class FourVector:
    e: float
    px: float
    py: float
    pz: float

    def __add__(self, other: "FourVector") -> "FourVector":
        return FourVector(self.e + other.e, self.px + other.px, self.py + other.py, self.pz + other.pz)

    def __sub__(self, other: "FourVector") -> "FourVector":
        return FourVector(self.e - other.e, self.px - other.px, self.py - other.py, self.pz - other.pz)

    def dot(self, other: "FourVector") -> float:
        return self.e * other.e - self.px * other.px - self.py * other.py - self.pz * other.pz

    @property
    def mass2(self) -> float:
        return self.dot(self)

    @property
    def spatial_norm(self) -> float:
        return sqrt(self.px * self.px + self.py * self.py + self.pz * self.pz)

    def close(self, other: "FourVector", atol: float = 1e-10) -> bool:
        return all(abs(a - b) <= atol for a, b in zip(self.as_tuple(), other.as_tuple()))

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.e, self.px, self.py, self.pz)


@dataclass(frozen=True)
class TwoBodyEvent:
    incoming: tuple[FourVector, FourVector]
    outgoing: tuple[FourVector, FourVector]
    theta: float
    phi: float
    weight: float
    metadata: dict[str, float | str]

    def conservation_residual(self) -> FourVector:
        return (self.incoming[0] + self.incoming[1]) - (self.outgoing[0] + self.outgoing[1])

    def mandelstam(self) -> dict[str, float]:
        p1, p2 = self.incoming
        p3, p4 = self.outgoing
        return {
            "s": (p1 + p2).mass2,
            "t": (p1 - p3).mass2,
            "u": (p1 - p4).mass2,
        }

    def on_shell_residuals(self) -> tuple[float, float, float, float]:
        masses = [float(self.metadata.get(f"m{i}", 0.0)) for i in range(1, 5)]
        vectors = [*self.incoming, *self.outgoing]
        return tuple(vector.mass2 - mass * mass for vector, mass in zip(vectors, masses))


def kallen(x: float, y: float, z: float) -> float:
    return x * x + y * y + z * z - 2.0 * (x * y + x * z + y * z)


def two_body_cm_event(
    sqrt_s: float,
    m1: float,
    m2: float,
    m3: float,
    m4: float,
    theta: float,
    phi: float = 0.0,
    weight: float = 1.0,
    metadata: dict[str, float | str] | None = None,
) -> TwoBodyEvent:
    if sqrt_s <= 0:
        raise ValueError("sqrt_s must be positive")
    s = sqrt_s * sqrt_s
    if sqrt_s < m1 + m2 or sqrt_s < m3 + m4:
        raise ValueError("Center-of-mass energy is below a two-body threshold")
    pin = sqrt(max(0.0, kallen(s, m1 * m1, m2 * m2))) / (2.0 * sqrt_s)
    pout = sqrt(max(0.0, kallen(s, m3 * m3, m4 * m4))) / (2.0 * sqrt_s)
    e1 = (s + m1 * m1 - m2 * m2) / (2.0 * sqrt_s)
    e2 = (s + m2 * m2 - m1 * m1) / (2.0 * sqrt_s)
    e3 = (s + m3 * m3 - m4 * m4) / (2.0 * sqrt_s)
    e4 = (s + m4 * m4 - m3 * m3) / (2.0 * sqrt_s)
    st, ct = sin(theta), cos(theta)
    cp, sp = cos(phi), sin(phi)
    event_meta: dict[str, float | str] = {"sqrt_s": sqrt_s, "m1": m1, "m2": m2, "m3": m3, "m4": m4}
    if metadata:
        event_meta.update(metadata)
    return TwoBodyEvent(
        incoming=(FourVector(e1, 0.0, 0.0, pin), FourVector(e2, 0.0, 0.0, -pin)),
        outgoing=(FourVector(e3, pout * st * cp, pout * st * sp, pout * ct), FourVector(e4, -pout * st * cp, -pout * st * sp, -pout * ct)),
        theta=theta,
        phi=phi,
        weight=weight,
        metadata=event_meta,
    )


def qed_emu_matrix_element_squared_massless(s: float, t: float, u: float, alpha: float = 1 / 137.035999084) -> float:
    """Spin-averaged tree-level QED proxy for distinct massless charged fermions.

    Formula: 2 e^4 (s^2 + u^2) / t^2. It is intentionally labelled with
    its assumptions and is not used near the forward t=0 singular limit.
    """
    if abs(t) < 1e-15:
        raise ValueError("Forward scattering singularity requires a regulator or angular cut")
    e2 = 4.0 * pi * alpha
    return 2.0 * e2 * e2 * (s * s + u * u) / (t * t)


def qed_emu_dsigma_domega_massless(s: float, theta: float, alpha: float = 1 / 137.035999084) -> float:
    if not 0.0 < theta < pi:
        raise ValueError("theta must lie strictly between 0 and pi")
    t = -0.5 * s * (1.0 - cos(theta))
    u = -0.5 * s * (1.0 + cos(theta))
    m2 = qed_emu_matrix_element_squared_massless(s, t, u, alpha)
    return m2 / (64.0 * pi * pi * s)


def qed_emu_event(sqrt_s: float, theta: float, phi: float = 0.0, *, electron_mass_gev: float = 0.00051099895, muon_mass_gev: float = 0.1056583755) -> TwoBodyEvent:
    event = two_body_cm_event(
        sqrt_s, electron_mass_gev, muon_mass_gev, electron_mass_gev, muon_mass_gev,
        theta, phi, metadata={"process": "e- mu- -> e- mu-", "model": "tree-level QED kinematics"},
    )
    invariants = event.mandelstam()
    if sqrt_s > 20.0 * muon_mass_gev and 0.001 < theta < pi - 0.001:
        weight = qed_emu_dsigma_domega_massless(invariants["s"], theta)
    else:
        weight = 1.0
    return TwoBodyEvent(event.incoming, event.outgoing, event.theta, event.phi, weight, event.metadata)


def generate_qed_emu_events(count: int, sqrt_s: float, theta_min: float = 0.05, theta_max: float = pi - 0.05, seed: int = 0) -> list[TwoBodyEvent]:
    if count < 0:
        raise ValueError("count must be non-negative")
    if not 0.0 < theta_min < theta_max < pi:
        raise ValueError("invalid angular interval")
    rng = Random(seed)
    events: list[TwoBodyEvent] = []
    for _ in range(count):
        theta = rng.uniform(theta_min, theta_max)
        phi = rng.uniform(0.0, 2.0 * pi)
        events.append(qed_emu_event(sqrt_s, theta, phi))
    return events


def two_flavor_probability(theta: float, delta_m2_ev2: float, baseline_km: float, energy_gev: float) -> float:
    """Vacuum two-flavour oscillation probability using the standard 1.267 convention."""
    if energy_gev <= 0 or baseline_km < 0:
        raise ValueError("energy must be positive and baseline non-negative")
    phase = 1.267 * delta_m2_ev2 * baseline_km / energy_gev
    return (sin(2.0 * theta) ** 2) * (sin(phase) ** 2)


def decay_lifetime_from_width(width_gev: float, hbar_gev_s: float = 6.582119569e-25) -> float:
    if width_gev <= 0:
        raise ValueError("width must be positive")
    return hbar_gev_s / width_gev


def lorentzian(x: float, center: float, width: float, area: float = 1.0) -> float:
    if width <= 0:
        raise ValueError("width must be positive")
    gamma = 0.5 * width
    return area * gamma / (pi * ((x - center) ** 2 + gamma * gamma))


def gaussian_smear(value: float, sigma: float, rng: Random) -> float:
    if sigma < 0:
        raise ValueError("sigma must be non-negative")
    return rng.gauss(value, sigma)


def detector_smear_event(event: TwoBodyEvent, relative_energy_sigma: float = 0.01, angular_sigma: float = 0.001, seed: int = 0) -> TwoBodyEvent:
    if relative_energy_sigma < 0 or angular_sigma < 0:
        raise ValueError("resolution parameters must be non-negative")
    rng = Random(seed)
    theta = min(pi, max(0.0, gaussian_smear(event.theta, angular_sigma, rng)))
    phi = gaussian_smear(event.phi, angular_sigma, rng) % (2.0 * pi)
    vectors: list[FourVector] = []
    for vector in event.outgoing:
        scale = max(0.0, gaussian_smear(1.0, relative_energy_sigma, rng))
        vectors.append(FourVector(vector.e * scale, vector.px * scale, vector.py * scale, vector.pz * scale))
    metadata = dict(event.metadata)
    metadata.update({"detector_smeared": "true", "relative_energy_sigma": relative_energy_sigma, "angular_sigma": angular_sigma})
    return TwoBodyEvent(event.incoming, (vectors[0], vectors[1]), theta, phi, event.weight, metadata)


def invariant_residual_summary(events: Iterable[TwoBodyEvent]) -> dict[str, float]:
    max_energy = max_momentum = max_shell = 0.0
    count = 0
    for event in events:
        count += 1
        residual = event.conservation_residual()
        max_energy = max(max_energy, abs(residual.e))
        max_momentum = max(max_momentum, abs(residual.px), abs(residual.py), abs(residual.pz))
        max_shell = max(max_shell, *(abs(value) for value in event.on_shell_residuals()))
    return {"count": float(count), "max_energy_residual": max_energy, "max_momentum_residual": max_momentum, "max_on_shell_residual": max_shell}
