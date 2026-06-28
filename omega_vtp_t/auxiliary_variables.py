"""Auxiliary-variable templates for polynomializing non-polynomial dynamics.

This module does not parse symbolic equations. It provides reusable templates and
metadata for OAK-safe transformations such as sin/cos, exp, and reciprocal
state augmentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class AuxiliaryVariableTemplate:
    name: str
    variables: Tuple[str, ...]
    constraints: Tuple[str, ...]
    derivative_rules: Tuple[str, ...]
    oak_warning: str


def sin_cos_template(base_variable: str = "x") -> AuxiliaryVariableTemplate:
    """Template for s=sin(x), c=cos(x)."""

    return AuxiliaryVariableTemplate(
        name="sin_cos_closure",
        variables=(f"s=sin({base_variable})", f"c=cos({base_variable})"),
        constraints=("s^2 + c^2 = 1",),
        derivative_rules=("ds/dt = c * dx/dt", "dc/dt = -s * dx/dt"),
        oak_warning="constraint s^2+c^2=1 must be monitored as an invariant",
    )


def exp_template(base_variable: str = "x") -> AuxiliaryVariableTemplate:
    """Template for y=exp(x)."""

    return AuxiliaryVariableTemplate(
        name="exp_closure",
        variables=(f"y=exp({base_variable})",),
        constraints=("y > 0",),
        derivative_rules=("dy/dt = y * dx/dt",),
        oak_warning="positivity of exp auxiliary variable must be monitored",
    )


def reciprocal_template(base_variable: str = "x") -> AuxiliaryVariableTemplate:
    """Template for q=1/x."""

    return AuxiliaryVariableTemplate(
        name="reciprocal_closure",
        variables=(f"q=1/{base_variable}",),
        constraints=(f"{base_variable} * q = 1", f"{base_variable} != 0"),
        derivative_rules=("dq/dt = -q^2 * dx/dt",),
        oak_warning="singularities near x=0 must be rejected or specially handled",
    )


def standard_auxiliary_templates(base_variable: str = "x") -> Tuple[AuxiliaryVariableTemplate, ...]:
    """Return common templates for polynomialization planning."""

    return (
        sin_cos_template(base_variable),
        exp_template(base_variable),
        reciprocal_template(base_variable),
    )
