from __future__ import annotations

from dataclasses import dataclass


ALLOWED_STATUSES = {"ESTABLISHED", "DEFINITION", "MODEL", "HYPOTHESIS", "CONJECTURE"}


@dataclass(frozen=True)
class Claim:
    claim_id: str
    statement: str
    status: str
    falsifier: str

    def __post_init__(self) -> None:
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(f"unsupported epistemic status: {self.status}")


CLAIMS: tuple[Claim, ...] = (
    Claim(
        "HPM-001",
        "For a specified joint distribution P(X,H), Shannon/Gibbs entropy obeys the chain rule S(X,H)=S(H)+E_H[S(X|H)].",
        "ESTABLISHED",
        "A correctly normalized finite distribution violating the entropy chain rule beyond numerical tolerance.",
    ),
    Claim(
        "HPM-002",
        "The hypergraph in Ω-HYPERPHASE-MAT-T is a representation of effective interactions/organization, not an assertion that matter is literally a hypergraph.",
        "DEFINITION",
        "Not empirical; invalidate by changing the model semantics explicitly.",
    ),
    Claim(
        "HPM-003",
        "Allowing multiple admissible hypergraph states defines a finite annealed-topology statistical model with a joint partition sum over X and H.",
        "MODEL",
        "Internal inconsistency, failed normalization, or failure to reduce to the fixed-topology ensemble when only one H is allowed.",
    ),
    Claim(
        "HPM-004",
        "Higher-order interaction topology can provide useful order observables for some real materials beyond pair-only representations.",
        "HYPOTHESIS",
        "Across a preregistered material family, pair-only baselines match or outperform the hypergraph observables out of sample at lower complexity.",
    ),
    Claim(
        "HPM-005",
        "Coincident softening of a thermodynamic stability Hessian and a hypergraph spectral mode can act as an early-warning signature in selected material transitions.",
        "HYPOTHESIS",
        "No reproducible predictive gain over conventional susceptibilities/structure descriptors on held-out transition data.",
    ),
    Claim(
        "HPM-006",
        "A finite exact-enumeration response peak is a finite-size crossover/pseudocritical marker, not by itself proof of a thermodynamic singularity.",
        "ESTABLISHED",
        "A mathematical thermodynamic-limit derivation establishing a singularity; finite data alone do not falsify this guardrail.",
    ),
)
