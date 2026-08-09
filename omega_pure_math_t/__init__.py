"""Ω-PURE-MATH-T∞: executable pure-mathematics research kernel."""

from .bracket_spectrum import (
    BracketSpectrum,
    Leaf,
    Node,
    all_parenthesizations,
    associativity_defect,
    bracket_spectrum,
    evaluate_tree,
    zero_triple_defect_on,
)
from .core import (
    Claim,
    ClaimStatus,
    OAKFinding,
    OAKReport,
    TheorySpec,
    fertile_compression_score,
    invariant_defect,
    law_defect,
    oak_audit_claims,
)
from .factor_bricks import (
    BrickLanguage,
    FactorizationWitness,
    compose_witnesses,
    minimum_recorded_length,
    subadditivity_certificate,
)
from .invariants import (
    Invariant,
    InvariantComparison,
    compare_invariants,
    cvcd_matrix,
    invariant_preorder,
)
from .negative_math import (
    NegativeMathEntry,
    NegativeMathRegistry,
    minimal_sufficient_subsets,
)
from .structural_dna import StructuralDNA
from .theorem_protocol import (
    MUTATION_AXES,
    QUESTION_KINDS,
    THEOREM_CANDIDATES,
    ResearchQuestion,
    generate_research_protocol,
    protocol_as_dict,
)

__all__ = [
    "BracketSpectrum",
    "BrickLanguage",
    "Claim",
    "ClaimStatus",
    "FactorizationWitness",
    "Invariant",
    "InvariantComparison",
    "Leaf",
    "MUTATION_AXES",
    "NegativeMathEntry",
    "NegativeMathRegistry",
    "Node",
    "OAKFinding",
    "OAKReport",
    "QUESTION_KINDS",
    "ResearchQuestion",
    "StructuralDNA",
    "THEOREM_CANDIDATES",
    "TheorySpec",
    "all_parenthesizations",
    "associativity_defect",
    "bracket_spectrum",
    "compare_invariants",
    "compose_witnesses",
    "cvcd_matrix",
    "evaluate_tree",
    "fertile_compression_score",
    "generate_research_protocol",
    "invariant_defect",
    "invariant_preorder",
    "law_defect",
    "minimal_sufficient_subsets",
    "minimum_recorded_length",
    "oak_audit_claims",
    "protocol_as_dict",
    "subadditivity_certificate",
    "zero_triple_defect_on",
]
