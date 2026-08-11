"""Condition-aware adaptive root continuation for Ω-ROOTFLOW-T∞."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .continuation import match_roots, newton_refine
from .core import _coefficients, derivative_value, polynomial_value, root_jacobian, roots

ComplexArray = npt.NDArray[np.complex128]


@dataclass(frozen=True)
class AdaptiveContinuationStep:
    parameter: float
    step_size: float
    attempts: int
    coefficients: ComplexArray
    roots: ComplexArray
    predictor_residual: float
    corrected_residual: float
    minimum_derivative: float


@dataclass(frozen=True)
class AdaptiveContinuationResult:
    steps: tuple[AdaptiveContinuationStep, ...]
    rejected_attempts: int
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    @property
    def final_roots(self) -> ComplexArray:
        return self.steps[-1].roots.copy()

    @property
    def minimum_step_size(self) -> float:
        accepted = [step.step_size for step in self.steps[1:]]
        return float(min(accepted)) if accepted else 0.0


def continue_roots_adaptive(
    start_coefficients: npt.ArrayLike,
    end_coefficients: npt.ArrayLike,
    *,
    initial_step: float = 0.125,
    minimum_step: float = 1e-5,
    maximum_step: float = 0.25,
    predictor_tolerance: float = 1e-3,
    newton_tolerance: float = 1e-12,
    singularity_tolerance: float = 1e-8,
    maximum_accepted_steps: int = 10000,
) -> AdaptiveContinuationResult:
    """Track roots along a straight coefficient path using adaptive step size.

    A step is accepted only when the differential predictor remains within the
    configured polynomial-residual budget, Newton correction succeeds, and the
    corrected spectrum remains outside the configured simple-root singularity
    floor.  Failed attempts shrink the coefficient-space step and are counted
    explicitly instead of being hidden.
    """
    start = _coefficients(start_coefficients)
    end = _coefficients(end_coefficients)
    if start.shape != end.shape:
        raise ValueError("start and end coefficients must have identical degree")
    if not (0 < minimum_step <= initial_step <= maximum_step <= 1.0):
        raise ValueError("require 0 < minimum_step <= initial_step <= maximum_step <= 1")
    if predictor_tolerance <= 0 or newton_tolerance <= 0 or singularity_tolerance <= 0:
        raise ValueError("tolerances must be positive")
    if maximum_accepted_steps <= 0:
        raise ValueError("maximum_accepted_steps must be positive")

    delta_total = end - start
    current_roots = roots(start)
    initial_residual = float(max(abs(polynomial_value(start, r)) for r in current_roots))
    initial_derivative = float(min(abs(derivative_value(start, r)) for r in current_roots))
    if initial_derivative <= singularity_tolerance:
        raise np.linalg.LinAlgError("adaptive continuation starts on or too near the discriminant")

    records: list[AdaptiveContinuationStep] = [
        AdaptiveContinuationStep(
            parameter=0.0,
            step_size=0.0,
            attempts=1,
            coefficients=start.copy(),
            roots=current_roots.copy(),
            predictor_residual=0.0,
            corrected_residual=initial_residual,
            minimum_derivative=initial_derivative,
        )
    ]
    rejected_attempts = 0
    parameter = 0.0
    step_size = float(initial_step)

    while parameter < 1.0 - 1e-15:
        if len(records) - 1 >= maximum_accepted_steps:
            raise RuntimeError("adaptive continuation exceeded maximum_accepted_steps")
        step_size = min(step_size, 1.0 - parameter)
        attempts = 0

        while True:
            attempts += 1
            t1 = parameter + step_size
            coeff0 = start + parameter * delta_total
            coeff1 = start + t1 * delta_total
            delta = coeff1 - coeff0
            accepted = False
            predictor_residual = float("inf")
            corrected_residual = float("inf")
            minimum_derivative = 0.0

            try:
                jac = root_jacobian(
                    coeff0,
                    current_roots,
                    singularity_tolerance=singularity_tolerance,
                )
                predicted = current_roots + jac @ delta
                predictor_residual = float(
                    max(abs(polynomial_value(coeff1, root)) for root in predicted)
                )

                corrected = np.empty_like(predicted)
                for index, guess in enumerate(predicted):
                    corrected[index], _, _ = newton_refine(
                        coeff1,
                        complex(guess),
                        tolerance=newton_tolerance,
                        singularity_tolerance=min(singularity_tolerance, 1e-12),
                    )

                # Direct roots provide an independent OAK assignment reference;
                # they are not used as the differential predictor.
                corrected = match_roots(corrected, roots(coeff1))
                corrected_residual = float(
                    max(abs(polynomial_value(coeff1, root)) for root in corrected)
                )
                minimum_derivative = float(
                    min(abs(derivative_value(coeff1, root)) for root in corrected)
                )
                correction_budget = max(100.0 * newton_tolerance, 1e-10)
                accepted = bool(
                    predictor_residual <= predictor_tolerance
                    and corrected_residual <= correction_budget
                    and minimum_derivative > singularity_tolerance
                )
            except np.linalg.LinAlgError:
                accepted = False

            if accepted:
                parameter = float(t1)
                current_roots = corrected
                records.append(
                    AdaptiveContinuationStep(
                        parameter=parameter,
                        step_size=float(step_size),
                        attempts=attempts,
                        coefficients=coeff1.copy(),
                        roots=current_roots.copy(),
                        predictor_residual=predictor_residual,
                        corrected_residual=corrected_residual,
                        minimum_derivative=minimum_derivative,
                    )
                )

                ratio = predictor_residual / predictor_tolerance
                if ratio < 0.05:
                    step_size = min(maximum_step, 1.6 * step_size)
                elif ratio > 0.5:
                    step_size = max(minimum_step, 0.75 * step_size)
                break

            rejected_attempts += 1
            step_size *= 0.5
            if step_size < minimum_step:
                raise np.linalg.LinAlgError(
                    f"adaptive continuation stalled near t={parameter:.12g}; "
                    "requested path approaches or crosses an unresolved singular region"
                )

    return AdaptiveContinuationResult(
        steps=tuple(records),
        rejected_attempts=rejected_attempts,
        status="OAK_PASS_ADAPTIVE_CONTINUATION",
    )
