from __future__ import annotations

from dataclasses import dataclass

from .dual import SpectralDualCertificate, fraction_text


@dataclass(frozen=True)
class FormalTheoremSpec:
    theorem_id: str
    backend_target: str
    assumptions: tuple[str, ...]
    conclusion: str
    source_scope: str
    status: str = "theorem_spec_only"

    def to_dict(self) -> dict:
        return {
            "theorem_id": self.theorem_id,
            "backend_target": self.backend_target,
            "assumptions": list(self.assumptions),
            "conclusion": self.conclusion,
            "source_scope": self.source_scope,
            "status": self.status,
            "kernel_checked": False,
            "proof_claimed": False,
            "rh_solved_claimed": False,
        }


def build_finite_certificate_theorem_spec(
    certificate: SpectralDualCertificate,
) -> FormalTheoremSpec:
    certificate.validate()
    degree = certificate.polynomial.degree
    assumptions = (
        "mu is a normalized finite positive measure",
        f"supp(mu) subset [-{fraction_text(certificate.spectral_radius)}, {fraction_text(certificate.spectral_radius)}]",
        "domain-control assumption is independently discharged before theorem promotion",
        f"moments m_0..m_{degree} equal the supplied exact normalized moments",
        "p(x) <= 0 on the non-positive spectral interval",
        "p(x) <= 1 on the positive spectral interval",
    )
    conclusion = (
        "mu((0,+infinity)) >= "
        + fraction_text(certificate.moment_objective)
    )
    return FormalTheoremSpec(
        theorem_id="finite-spectral-moment-dual-minorant",
        backend_target="Lean4/mathlib",
        assumptions=assumptions,
        conclusion=conclusion,
        source_scope="abstract_finite_spectral_certificate_kernel_not_zeta_adapter",
    )
