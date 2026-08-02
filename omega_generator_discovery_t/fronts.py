"""Canonical registry for the ten coupled discovery fronts."""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class FrontSpec:
    identifier: str
    name: str
    purpose: str
    first_falsifiable_test: str
    maturity: str = "R0.1 executable scaffold"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


FRONTS: tuple[FrontSpec, ...] = (
    FrontSpec("spectral_logexp", "Ω-SPECTRAL-LOGEXP-T", "Physical-shape spectral generator discovery", "Recover shift, width, and amplitude on synthetic Lorentzians"),
    FrontSpec("generator_operator", "Ω-GENERATOR-OPERATOR-T", "Learn generators rather than only next-step maps", "Predict an affine scalar trajectory out of sample"),
    FrontSpec("semigroup_microscope", "Ω-SEMIGROUP-RESIDUAL-MICROSCOPE", "Detect hidden state or regime changes", "Separate exact semigroup data from a perturbed two-step map"),
    FrontSpec("crystal_holonomy", "Ω-CRYSTAL-HOLONOMY-TWIN", "Measure orientation-loop residuals", "Closed quaternion loop returns identity within tolerance"),
    FrontSpec("order_designer", "Ω-COMMUTATOR-EXPERIMENT-DESIGNER", "Rank AB versus BA protocol sensitivity", "Detect noncommuting shear operators"),
    FrontSpec("morph_compiler", "Ω-MORPH-COMPILER-T", "Compile transformations into typed MorphIR", "Reject invalid residuals and preserve sectors/invariants"),
    FrontSpec("epistemic_dynamics", "Ω-EPISTEMIC-DYNAMICS-T", "Track evidence growth versus concept growth", "Flag concept expansion without new evidence"),
    FrontSpec("autolab_oak", "Ω-AUTOLAB-OAK-T", "Prioritize safe informative experiments", "Block irreversible or excessive-risk candidates"),
    FrontSpec("morph_lab_protocol", "Ω-MORPH-LAB-PROTOCOL", "Describe composable instrument interfaces", "Require safety limits and rollback recipe"),
    FrontSpec("generator_syndrome", "Ω-GENERATOR-SYNDROME-T", "Diagnose drift, events, and model failure", "Classify a small operator perturbation as drift"),
)


def front_registry() -> tuple[FrontSpec, ...]:
    return FRONTS
