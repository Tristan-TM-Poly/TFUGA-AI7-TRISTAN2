"""Machine-readable branch canon for Ω-PURE-MATH-T∞."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class BranchSpec:
    identifier: str
    title: str
    status: str
    implementation: str | None
    baseline_family: tuple[str, ...]
    promotion_target: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


BRANCH_CANON = (
    BranchSpec("Ω-PURE-MATH-T∞", "Pure mathematics architecture", "executable", "core.py", ("mathematical structures", "category-theoretic organization"), "specialized theorem families"),
    BranchSpec("Ω-RPU-T∞", "Representation geometry", "executable", "representation_geometry.py", ("representation theory", "multi-objective optimization"), "task-specific equivalence theorems"),
    BranchSpec("Ω-REP-FLOW-T", "Representation flows", "research-program", None, ("gradient flows", "information geometry"), "define a concrete representation manifold"),
    BranchSpec("Ω-TENSOR-SPECTRUM-T∞", "Tensor Spectrum", "executable", "tensor_spectrum.py", ("tensor algebra", "representation theory"), "equivariant channel classification"),
    BranchSpec("Ω-SYMMETRIC-TENSOR-SPECTRUM", "Equivariant Tensor Spectrum", "formalized", "tensor_spectrum.py", ("symmetric/exterior powers", "representation theory"), "specialize group G and modules"),
    BranchSpec("Ω-SUPERPOSED-TENSOR-T∞", "Superposed tensor topologies", "research-program", None, ("tensor networks", "graphical calculi"), "define admissible topology space and equivalence"),
    BranchSpec("Ω-BRACKET-SPECTRUM-T∞", "Bracket Spectrum", "executable", "bracket_spectrum.py", ("associators", "Catalan objects", "associahedra"), "rotation-graph invariants and exact distances"),
    BranchSpec("Ω-PARENTHESIS-FIELD-T", "Parenthesization field", "executable", "bracket_spectrum.py", ("associahedra", "nonassociative algebras"), "edgewise associator statistics on nonassociative families"),
    BranchSpec("Ω-DEFECT-ALGEBRA-T∞", "Defect algebra", "executable", "defect_hierarchy.py", ("commutators", "associators", "cohomological obstructions"), "closed algebra of selected defect operators"),
    BranchSpec("Ω-COMMUTATOR-HIERARCHY-T∞", "Higher defect hierarchy", "executable", "defect_hierarchy.py", ("Lie brackets", "higher algebra"), "classify vanishing levels in specialized algebras"),
    BranchSpec("Ω-FACTOR-BRICKS-T∞", "Relative brick factorization", "executable", "factor_bricks.py", ("factorization theory", "monoidal categories"), "nontrivial brick languages and uniqueness results"),
    BranchSpec("Ω-FACTOR-TREE-T∞", "Factorization trees", "executable", "factor_tree.py", ("decomposition trees", "term rewriting"), "scalable exact search and provenance"),
    BranchSpec("Ω-PRIME-RELATIVE-T∞", "Relative irreducibility spectrum", "formalized", "factor_bricks.py", ("irreducibility", "factorization monoids"), "domain-specific irreducibility theorems"),
    BranchSpec("Ω-LOGEXP-GEOMETRY-T∞", "LOG/EXP geometry", "adapter", "omega_logexp_morph_t", ("Lie theory", "functional calculus"), "logarithm obstruction atlas"),
    BranchSpec("Ω-GENERATOR-GEOMETRY-T", "Generator geometry", "adapter", "omega_logexp_morph_t", ("matrix logarithms", "Lie semigroups"), "branch/obstruction classification"),
    BranchSpec("Ω-INVARIANT-COMPILER-T∞", "Invariant compiler", "executable", "invariants.py", ("invariant theory", "orbit classification"), "collision-driven invariant synthesis"),
    BranchSpec("Ω-INVARIANT-LATTICE-T∞", "Invariant preorder/lattice", "executable", "invariants.py", ("lattices", "sufficient statistics"), "conditions for meets/joins"),
    BranchSpec("Ω-CLASSIFICATION-COMPLETENESS-T", "Invariant completeness", "executable", "finite_classification.py", ("complete invariants", "orbit spaces"), "nontrivial finite-group minimal bases"),
    BranchSpec("Ω-OBSTRUCTION-T∞", "Obstruction-first mathematics", "executable", "invariants.py", ("obstruction theory", "preserved invariants"), "cheap-first obstruction compiler"),
    BranchSpec("Ω-OBSTRUCTION-VECTOR-T", "Obstruction vector", "research-program", None, ("multi-criteria diagnostics",), "common normalization space"),
    BranchSpec("Ω-HGFM-MATH-T∞", "Formal HGFM", "executable", "hgfm_formal.py", ("hypergraphs", "multiscale graphs", "renormalization"), "nontrivial scale-invariant classes"),
    BranchSpec("Ω-HGFM-RENORMALIZATION-T", "HGFM renormalization", "formalized", "hgfm_formal.py", ("renormalization", "graph coarse-graining"), "fixed-point theorem"),
    BranchSpec("Ω-MYCELIAL-CONNECTIVITY-T", "Mycelial connectivity", "research-program", None, ("Menger connectivity", "network robustness"), "path-independence metric and baselines"),
    BranchSpec("Ω-CVCD-PURE-T∞", "Cross-representation difference calculus", "executable", "invariants.py", ("distance matrices", "representation stability"), "transformation-law-qualified tensors"),
    BranchSpec("Ω-RESIDUAL-OF-RESIDUAL-T∞", "Residual towers", "executable", "residuals.py", ("iterative refinement", "contraction mappings"), "function-space convergence theorem"),
    BranchSpec("Ω-MOINDRE-CALCUL-T∞", "Minimal calculation", "formalized", "representation_geometry.py", ("rewrite systems", "arithmetic circuit complexity"), "exact finite rewrite geodesics"),
    BranchSpec("Ω-CALC-GEODESIC-T", "Calculation geodesics", "formalized", "representation_geometry.py", ("shortest paths", "term rewriting"), "rewrite-graph adapter"),
    BranchSpec("Ω-PROOF-GEOMETRY-T∞", "Proof geometry", "executable", "proof_geometry.py", ("proof theory", "hypergraphs"), "proof-space distances with logical equivalence"),
    BranchSpec("Ω-PROOF-THERMODYNAMICS-T∞", "Finite proof thermodynamics", "executable", "proof_geometry.py", ("partition functions", "proof complexity"), "controlled infinite-space conditions"),
    BranchSpec("Ω-PROOF-COMPRESSION-T", "Proof library compression", "executable", "proof_compression.py", ("lemma reuse", "minimum description length"), "larger finite optimization benchmark and formal proof supports"),
    BranchSpec("Ω-NEGATIVE-MATH-T∞", "Negative mathematics", "executable", "negative_math.py", ("counterexample databases", "minimal hypotheses"), "automatic assumption repair loop"),
    BranchSpec("Ω-MINIMAL-HYPOTHESIS-T", "Minimal hypothesis kernels", "executable", "negative_math.py", ("independence", "axiom minimization"), "formal proof-oracle adapter"),
    BranchSpec("Ω-SEQUENCE-ANALYTIC-T∞", "Analytic sequence atlas", "research-program", None, ("generating functions", "interpolation", "recurrences"), "canonical cost model"),
    BranchSpec("Ω-ZERO-TOMOGRAPHY-T∞", "Log-potential zero tomography", "executable", "zero_tomography.py", ("potential theory", "Poincare-Lelong/Jensen methods"), "noise/resolution error bounds"),
    BranchSpec("Ω-ZERO-MULTISCALE-T", "Multiscale zero tomography", "formalized", "zero_tomography.py", ("mollifiers", "scale-space methods"), "kernelized stability benchmark"),
    BranchSpec("Ω-NOETHER-DEFECT-T∞", "Noether defect calculus", "research-program", None, ("Noether theorem", "broken symmetries"), "specialized variational identity"),
    BranchSpec("Ω-INVARIANT-DEFECT-DUALITY-T", "Invariant-defect duality", "formalized", "invariants.py", ("stabilizers", "cocycles"), "precise algebraic setting"),
    BranchSpec("Ω-META-THEORY-T∞", "Finite meta-theory objects", "executable", "theory_evolution.py", ("metalogic", "theory morphisms"), "logic-aware consequence closure"),
    BranchSpec("Ω-THEORY-DISTANCE-T", "Theory distance", "executable", "theory_evolution.py", ("set distances", "logical distance"), "semantic-equivalence quotient"),
    BranchSpec("Ω-THEORY-FITNESS-T", "Theory fitness vector", "formalized", "core.py", ("multi-objective evaluation",), "calibrated component metrics"),
    BranchSpec("Ω-THEORY-MUTATION-T∞", "Theory mutation", "executable", "theory_evolution.py", ("axiom variation", "model theory"), "countermodel-guided mutation"),
    BranchSpec("Ω-DUALITY-GENERATOR-T∞", "Duality generator", "research-program", None, ("duality theory", "adjunctions"), "specialize a category and involution"),
    BranchSpec("Ω-LOCAL-GLOBAL-T∞", "Local-global compiler", "executable", "local_global.py", ("sheaves", "cohomology", "descent"), "specialized sheaf/cohomology obstruction examples"),
    BranchSpec("Ω-DISCRETE-CONTINUOUS-BRIDGE-T∞", "Discrete-continuous bridge", "research-program", None, ("discretization", "Gamma convergence", "numerical analysis"), "choose topology and convergence rate"),
    BranchSpec("Ω-DIMENSION-SPECTRUM-T∞", "Dimension Spectrum", "executable", "dimension_spectrum.py", ("topological/Hausdorff/spectral dimensions",), "domain-qualified dimension registry"),
    BranchSpec("Ω-HYPERNUMBER-T∞", "Multigraded hypernumber scaffold", "formalized", "multigraded.py", ("graded algebras", "Cayley-Dickson algebras"), "nontrivial algebra with axioms and examples"),
    BranchSpec("Ω-MULTI-GRADED-PRODUCT-T∞", "Multigraded product", "executable", "multigraded.py", ("graded algebras", "operads"), "coherence laws and nontrivial multi-output examples"),
    BranchSpec("Ω-INFORMATION-GEOMETRY-OF-MATH-T", "Information geometry of representations", "formalized", "representation_geometry.py", ("information geometry", "rate-distortion"), "probabilistic channel semantics"),
    BranchSpec("Ω-MATHEMATICAL-COMPILER-T∞", "Mathematical compiler", "executable", "theorem_protocol.py", ("automated theorem discovery", "formal methods"), "proof-assistant and countermodel adapters"),
    BranchSpec("Ω-STRUCTURAL-DNA-T∞", "Structural DNA", "executable", "structural_dna.py", ("feature invariants", "classification signatures"), "collision-driven invariant discovery"),
    BranchSpec("Ω-MATHEMATICAL-EVOLUTION-T∞", "Self-correcting theory evolution", "executable", "theory_evolution.py", ("theory revision", "counterexample-guided refinement"), "closed evidence→mutation→proof loop"),
)


VALID_STATUSES = frozenset({"executable", "formalized", "adapter", "research-program"})


def validate_canon() -> tuple[str, ...]:
    errors: list[str] = []
    identifiers = [branch.identifier for branch in BRANCH_CANON]
    if len(identifiers) != len(set(identifiers)):
        errors.append("duplicate branch identifiers")
    for branch in BRANCH_CANON:
        if branch.status not in VALID_STATUSES:
            errors.append(f"{branch.identifier}: invalid status {branch.status}")
        if branch.status == "executable" and not branch.implementation:
            errors.append(f"{branch.identifier}: executable branch lacks implementation")
    return tuple(errors)


def canon_summary() -> dict[str, Any]:
    counts = {status: 0 for status in sorted(VALID_STATUSES)}
    for branch in BRANCH_CANON:
        counts[branch.status] += 1
    return {
        "branch_count": len(BRANCH_CANON),
        "status_counts": counts,
        "valid": not validate_canon(),
        "errors": validate_canon(),
        "branches": [branch.to_dict() for branch in BRANCH_CANON],
    }
