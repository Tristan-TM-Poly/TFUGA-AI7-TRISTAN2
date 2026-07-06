"""Tiny mutation probes for Ω-CS-SOFTWARE-TRUTH.

This is not a full mutation-testing engine. It is a minimal OAK hook that makes
regressions explicit by running validator reports against intentionally altered
callables supplied by the user or future automation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .oak_validator import OAKReport, OAKValidator
from .software_state import SoftwareState


@dataclass(frozen=True)
class MutationResult:
    mutant_name: str
    killed: bool
    report: OAKReport


def probe_mutant(state: SoftwareState, mutant_name: str, mutant: Callable[..., object]) -> MutationResult:
    """Return killed=True when the current examples catch the mutant."""

    mutated_state = SoftwareState(
        name=f"{state.name}::{mutant_name}",
        target=mutant,
        contract=state.contract,
        examples=state.examples,
        environment=state.environment,
        status="mutation-probe",
    )
    report = OAKValidator().validate(mutated_state)
    return MutationResult(mutant_name=mutant_name, killed=not report.passed, report=report)
