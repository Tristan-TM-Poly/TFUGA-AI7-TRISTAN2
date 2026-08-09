"""Research-question compiler and canonical candidate theorem registry."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .core import Claim, ClaimStatus


@dataclass(frozen=True)
class ResearchQuestion:
    kind: str
    question: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


QUESTION_KINDS = (
    "existence",
    "uniqueness",
    "closure",
    "invariance",
    "stability",
    "factorization",
    "classification",
    "extremum",
    "duality",
    "local-global",
    "approximation",
    "obstruction",
)


def generate_research_protocol(
    definition_name: str,
    *,
    object_symbol: str = "X",
    operation_symbol: str = "⋆",
) -> tuple[ResearchQuestion, ...]:
    """Generate the 12-question Ω protocol for a new definition."""

    x = object_symbol
    d = definition_name
    op = operation_symbol
    return (
        ResearchQuestion("existence", f"Does there exist {x} satisfying {d}?"),
        ResearchQuestion("uniqueness", f"When are two {d} objects equivalent/isomorphic?"),
        ResearchQuestion("closure", f"Is {d} closed under {op}?"),
        ResearchQuestion("invariance", f"Which admissible transformations preserve {d}?"),
        ResearchQuestion("stability", f"Is {d} stable under limits/perturbations?"),
        ResearchQuestion("factorization", f"How do {d} objects factor into simpler bricks?"),
        ResearchQuestion("classification", f"Which invariants classify {d} objects?"),
        ResearchQuestion("extremum", f"Which {d} objects extremize natural functionals?"),
        ResearchQuestion("duality", f"Does {d} admit a natural dual construction?"),
        ResearchQuestion("local-global", f"When do local {d} data glue globally?"),
        ResearchQuestion("approximation", f"Which simpler classes approximate {d}?"),
        ResearchQuestion("obstruction", f"Which invariants or defects obstruct {d}?"),
    )


THEOREM_CANDIDATES = (
    Claim(
        identifier="T1",
        title="Brick-length subadditivity",
        statement="ell_B(X⊗Y) <= ell_B(X)+ell_B(Y) when admissible witnesses compose",
        status=ClaimStatus.THEOREM,
        hypotheses=("factorizations compose in the chosen monoidal language",),
        dependencies=("constructive concatenation of factorization witnesses",),
    ),
    Claim(
        identifier="T2",
        title="Parenthesization diameter characterizes associativity",
        statement=(
            "Associativity implies D_A(x1,...,xn)=0 for every n; "
            "zero triple defect for all triples implies associativity"
        ),
        status=ClaimStatus.THEOREM,
        dependencies=("definition of associativity", "induction on binary parenthesizations"),
    ),
    Claim(
        identifier="T3",
        title="Invariant obstruction",
        statement=(
            "If admissible isomorphisms preserve I and I(X) != I(Y), "
            "then X and Y are not admissibly isomorphic"
        ),
        status=ClaimStatus.THEOREM,
        dependencies=("definition of invariant under admissible isomorphisms",),
    ),
    Claim(
        identifier="T4",
        title="Equivariant Tensor Spectrum classification",
        statement="Classify canonical equivariant channels of selected tensor products",
        status=ClaimStatus.CONJECTURE,
        oak_notes=("family-level research program; must specialize G,V,W",),
    ),
    Claim(
        identifier="T5",
        title="Minimal complete invariant basis",
        statement="Characterize existence and complexity of minimal complete invariant families",
        status=ClaimStatus.CONJECTURE,
    ),
    Claim(
        identifier="T6",
        title="Residual tower convergence",
        statement="Find sufficient conditions for ||r_n|| -> 0 under iterative residual modeling",
        status=ClaimStatus.CONJECTURE,
    ),
    Claim(
        identifier="T7",
        title="Minimal representation uniqueness",
        statement="Characterize when a task-optimal minimal representation is unique up to equivalence",
        status=ClaimStatus.CONJECTURE,
    ),
    Claim(
        identifier="T8",
        title="Robust logarithmic zero tomography",
        statement="Bound zero-location error reconstructed from sampled/noisy log|f|",
        status=ClaimStatus.CONJECTURE,
    ),
    Claim(
        identifier="T9",
        title="HGFM renormalization dimension",
        statement="Give conditions for scale-dimension invariance under an HGFM renormalization operator",
        status=ClaimStatus.CONJECTURE,
    ),
    Claim(
        identifier="T10",
        title="Proof-library compression",
        statement="Characterize optimal reusable lemma libraries for a finite theorem family",
        status=ClaimStatus.CONJECTURE,
    ),
    Claim(
        identifier="T11",
        title="Non-associative bracket-space geometry",
        statement="Relate algebraic associator data to metric geometry on the rotation graph of parenthesizations",
        status=ClaimStatus.CONJECTURE,
    ),
    Claim(
        identifier="T12",
        title="Defect-spectrum classification",
        statement="Determine classes of algebras separated by finite or hierarchical defect signatures",
        status=ClaimStatus.CONJECTURE,
    ),
)


MUTATION_AXES = (
    ("finite", "infinite"),
    ("discrete", "continuous"),
    ("linear", "nonlinear"),
    ("commutative", "noncommutative"),
    ("associative", "nonassociative"),
    ("exact", "approximate"),
    ("local", "global"),
    ("object", "dual"),
    ("construction", "obstruction"),
)


def protocol_as_dict(definition_name: str) -> dict[str, Any]:
    return {
        "definition": definition_name,
        "questions": [
            item.to_dict() for item in generate_research_protocol(definition_name)
        ],
        "mutation_axes": [list(pair) for pair in MUTATION_AXES],
        "candidate_theorems": [claim.to_dict() for claim in THEOREM_CANDIDATES],
    }
