"""Compile explicit zero-counting envelopes into reciprocal-zero tail bounds.

For nontrivial zeta zeros rho=beta+i gamma and centered-square reciprocal
coordinate lambda=-1/(rho-1/2)^2,

    |lambda| = 1 / ((beta-1/2)^2 + gamma^2) <= 1/gamma^2.

If the positive-ordinate zero count satisfies

    N(t) <= a t log t + b t + c log t + d   for t >= T0,

then for T>=T0,

    sum_{gamma>T} |lambda|
      <= sum_{gamma>T} gamma^-2
      <= 2 int_T^infinity N(t) t^-3 dt
      <= [2a(log T+1)+2b]/T
         + [c(log T+1/2)+d]/T^2.

Also sup_{gamma>T}|lambda| <= T^-2.

This module is rigorous conditional on a separately certified counting envelope.
It does not hardcode literature constants and never claims RH.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ZeroCountEnvelope:
    a_t_log_t: float
    b_t: float
    c_log_t: float
    d_const: float
    valid_from: float
    source_id: str
    certified: bool = False

    def validate(self) -> None:
        values = (
            self.a_t_log_t,
            self.b_t,
            self.c_log_t,
            self.d_const,
            self.valid_from,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("zero-count envelope parameters must be finite")
        if self.valid_from <= 1.0:
            raise ValueError("valid_from must exceed 1")
        if not self.source_id.strip():
            raise ValueError("source_id is required")


@dataclass(frozen=True)
class ReciprocalTailBound:
    height: float
    radius_upper: float
    absolute_mass_upper: float
    source_id: str
    source_envelope_certified: bool
    analytically_usable_for_r9: bool
    epistemic_status: str
    proves_rh: bool = False


def zero_count_upper(t: float, envelope: ZeroCountEnvelope) -> float:
    envelope.validate()
    t = float(t)
    if not math.isfinite(t) or t < envelope.valid_from:
        raise ValueError("t must be finite and within the certified envelope domain")
    return (
        envelope.a_t_log_t * t * math.log(t)
        + envelope.b_t * t
        + envelope.c_log_t * math.log(t)
        + envelope.d_const
    )


def reciprocal_tail_bound(height: float, envelope: ZeroCountEnvelope) -> ReciprocalTailBound:
    """Compile N(t) envelope into R9-compatible radius and absolute-mass bounds."""

    envelope.validate()
    T = float(height)
    if not math.isfinite(T) or T < envelope.valid_from:
        raise ValueError("height must be finite and at least envelope.valid_from")
    if T <= 1.0:
        raise ValueError("height must exceed 1")

    logT = math.log(T)
    mass = (
        (2.0 * envelope.a_t_log_t * (logT + 1.0) + 2.0 * envelope.b_t) / T
        + (
            envelope.c_log_t * (logT + 0.5)
            + envelope.d_const
        )
        / (T * T)
    )
    if mass < 0.0:
        raise ValueError(
            "compiled envelope gives a negative tail upper bound; source envelope or simplification is invalid"
        )
    radius = 1.0 / (T * T)
    certified = bool(envelope.certified)
    return ReciprocalTailBound(
        height=T,
        radius_upper=radius,
        absolute_mass_upper=mass,
        source_id=envelope.source_id,
        source_envelope_certified=certified,
        analytically_usable_for_r9=certified,
        epistemic_status=(
            "CERTIFIED_ZERO_COUNT_TO_RECIPROCAL_TAIL_BOUND"
            if certified
            else "CONDITIONAL_ON_UNCERTIFIED_ZERO_COUNT_ENVELOPE"
        ),
    )
