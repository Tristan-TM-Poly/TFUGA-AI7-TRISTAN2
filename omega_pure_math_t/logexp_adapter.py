"""Adapter from Ω-PURE-MATH-T∞ to the existing Ω-LOGEXP-MORPH kernel."""

from __future__ import annotations

from dataclasses import dataclass

from omega_logexp_morph_t import (
    Matrix,
    frobenius_norm,
    identity,
    matrix,
    matrix_exponential,
    matrix_logarithm_near_identity,
    max_row_sum_norm,
    shape,
    subtract,
)


@dataclass(frozen=True)
class LogExpRoundTrip:
    generator: Matrix
    transformation: Matrix
    recovered_generator: Matrix
    reconstructed_transformation: Matrix
    generator_error: float
    transformation_error: float


@dataclass(frozen=True)
class LogarithmGate:
    admissible_for_mercator: bool
    norm_from_identity: float
    reason: str


def near_identity_log_gate(transformation: Matrix) -> LogarithmGate:
    rows, columns = shape(transformation)
    if rows != columns:
        return LogarithmGate(False, float("inf"), "transformation is not square")
    delta = subtract(transformation, identity(rows))
    norm = max_row_sum_norm(delta)
    return LogarithmGate(
        admissible_for_mercator=norm < 1.0,
        norm_from_identity=norm,
        reason=(
            "inside ||T-I||_inf < 1 Mercator convergence region"
            if norm < 1.0
            else "outside the implemented Mercator convergence region"
        ),
    )


def generator_round_trip(rows: tuple[tuple[float, ...], ...]) -> LogExpRoundTrip:
    """exp -> local log -> exp with explicit reconstruction residuals."""

    generator = matrix(rows)
    transformation = matrix_exponential(generator)
    gate = near_identity_log_gate(transformation)
    if not gate.admissible_for_mercator:
        raise ValueError(gate.reason)
    recovered = matrix_logarithm_near_identity(transformation)
    reconstructed = matrix_exponential(recovered)
    return LogExpRoundTrip(
        generator=generator,
        transformation=transformation,
        recovered_generator=recovered,
        reconstructed_transformation=reconstructed,
        generator_error=frobenius_norm(subtract(recovered, generator)),
        transformation_error=frobenius_norm(subtract(reconstructed, transformation)),
    )
