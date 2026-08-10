from __future__ import annotations

from dataclasses import dataclass
from math import tanh
from typing import Iterable, Sequence

from .models import DendriticBranchState


@dataclass(frozen=True)
class BranchIntegrator:
    """Deterministic nonlinear branch model used as an explicit testable baseline.

    This is not asserted to be a universal biophysical dendrite model. It exists
    to test whether compartment/address information improves a specified task.
    """

    state: DendriticBranchState

    def integrate(self, inputs: Iterable[float]) -> float:
        drive = sum(float(x) for x in inputs)
        shifted = self.state.gain * (drive - self.state.threshold)
        calcium_gain = max(0.0, 1.0 + self.state.local_calcium)
        return self.state.saturation * tanh(shifted * calcium_gain)


@dataclass(frozen=True)
class SomaIntegrator:
    """Aggregates already-computed branch outputs."""

    bias: float = 0.0
    gain: float = 1.0

    def integrate(self, branch_outputs: Sequence[float]) -> float:
        if self.gain <= 0.0:
            raise ValueError("gain must be > 0")
        return tanh(self.gain * (sum(float(x) for x in branch_outputs) + self.bias))


def address_aware_response(
    branches: Sequence[BranchIntegrator],
    addressed_inputs: Sequence[Sequence[float]],
    *,
    soma: SomaIntegrator | None = None,
) -> float:
    """Reference implementation for P1: dendritic-address information.

    Callers can compare this result/model loss against an address-agnostic
    scalar-sum baseline under the same data split.
    """

    if len(branches) != len(addressed_inputs):
        raise ValueError("each branch must receive exactly one input group")
    soma = soma or SomaIntegrator()
    return soma.integrate(
        [branch.integrate(inputs) for branch, inputs in zip(branches, addressed_inputs)]
    )
