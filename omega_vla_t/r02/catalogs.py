"""Canonical, finite catalogs used to address the Ω-VLA logical frontier."""

from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from operator import mul
from typing import Iterable, Mapping


LAYERS: tuple[str, ...] = (
    "scalars_and_rings",
    "vector_spaces",
    "affine_geometry",
    "duality",
    "metrics_and_forms",
    "matrix_algebra",
    "operator_algebras",
    "spectral_theory",
    "factorizations",
    "multivariable_differential_calculus",
    "vector_calculus",
    "differential_forms",
    "differential_geometry",
    "symplectic_geometry",
    "lie_theory",
    "clifford_geometric_algebra",
    "tensor_calculus",
    "tensor_decompositions",
    "discrete_calculus",
    "graph_calculus",
    "higher_complexes",
    "hgfm_hypergraphs",
    "functional_analysis",
    "numerical_linear_algebra",
    "optimization",
    "dynamical_systems",
    "control_and_estimation",
    "probabilistic_linear_algebra",
    "cvcd_and_transforms",
    "physics_compilers",
    "formalization_and_proof",
    "oak_and_negative_memory",
)


PROGRAMS: tuple[str, ...] = (
    "adaptive_multiobjective_bases",
    "invariant_preserving_bases",
    "noise_robust_bases",
    "local_atlas_bases",
    "hierarchical_tensor_bases",
    "symmetry_adapted_bases",
    "irregular_data_bases",
    "continuous_basis_morphogenesis",
    "eigenvalue_flows",
    "multiscale_pseudospectra",
    "robust_invariant_subspaces",
    "commutator_coupling_detection",
    "hybrid_factorizations",
    "dynamic_graph_spectra",
    "hypergraph_spectra",
    "compressed_operator_functions",
    "adaptive_metric_gradient",
    "uncertain_divergence",
    "generalized_curl",
    "anisotropic_laplacians",
    "singular_fields",
    "multiboundary_flux",
    "nonlocal_vector_calculus",
    "probabilistic_vector_calculus",
    "operator_curvature",
    "learning_model_curvature",
    "discrete_connections",
    "hypergraph_geodesics",
    "numerical_parallel_transport",
    "matrix_manifold_geometry",
    "low_rank_manifolds",
    "cvcd_geometric_atlas",
    "adaptive_tensor_rank",
    "oak_safe_cp_decomposition",
    "dynamic_tensor_train",
    "tensor_network_pde",
    "residual_tensors",
    "uncertainty_tensors",
    "symmetry_tensors",
    "guarded_hypercomplex_tensors",
    "graph_hodge",
    "simplicial_hodge",
    "hypergraph_hodge",
    "discrete_conservation",
    "mimetic_operators",
    "cross_scale_couplings",
    "operator_persistent_topology",
    "hgfm_coarse_graining",
    "generative_preconditioners",
    "adaptive_krylov",
    "multiprecision_solvers",
    "interval_certification",
    "automatic_instability_detection",
    "automatic_solver_selection",
    "distributed_sparse_benchmarks",
    "out_of_core_computation",
    "raman_spectroscopy",
    "crystal_elasticity",
    "maxwell_photonics",
    "fluid_turbulence",
    "plasma_dynamics",
    "quantum_operator_science",
    "ai_latent_spaces",
    "operator_reverse_engineering",
)


DIMENSIONS: Mapping[str, tuple[str, ...]] = {
    "scalar": (
        "real",
        "complex",
        "rational",
        "finite_field",
        "interval",
        "quaternion",
        "clifford",
        "octonion_guarded",
        "sedenion_exploratory",
    ),
    "space": (
        "finite_vector",
        "affine",
        "inner_product",
        "banach",
        "hilbert",
        "sobolev",
        "tangent_bundle",
        "cotangent_bundle",
        "graph_chain",
        "simplicial_chain",
        "hypergraph_chain",
        "tensor_network",
    ),
    "geometry": (
        "euclidean",
        "hermitian",
        "indefinite",
        "riemannian",
        "symplectic",
        "information",
        "learned_metric",
        "discrete_hodge",
    ),
    "operator": (
        "matrix",
        "differential",
        "integral",
        "incidence",
        "laplacian",
        "projection",
        "resolvent",
        "semigroup",
        "koopman",
        "perron_frobenius",
        "tensor_network",
        "cross_scale",
        "nonlocal",
        "stochastic",
        "symbolic",
        "learned",
    ),
    "discretization": (
        "exact_symbolic",
        "finite_difference",
        "finite_volume",
        "finite_element",
        "spectral_element",
        "discrete_exterior",
        "graph",
        "simplicial",
        "hypergraph",
        "meshfree",
    ),
    "regime": (
        "linear",
        "weakly_nonlinear",
        "strongly_nonlinear",
        "stationary",
        "transient",
        "periodic",
        "stochastic",
        "singular",
        "multiscale",
        "high_dimensional",
    ),
    "application": (
        "pure_mathematics",
        "raman",
        "crystals",
        "solid_mechanics",
        "fluids",
        "plasmas",
        "maxwell",
        "photonics",
        "quantum",
        "control",
        "inverse_problems",
        "machine_learning",
        "graph_science",
        "signal_processing",
        "batteries",
        "reverse_engineering",
    ),
    "question": (
        "existence",
        "uniqueness",
        "stability",
        "convergence",
        "conditioning",
        "invariance",
        "compression",
        "identifiability",
        "controllability",
        "observability",
        "approximation",
        "counterexample",
    ),
    "method": (
        "direct_proof",
        "spectral",
        "variational",
        "energy_estimate",
        "fixed_point",
        "topological",
        "probabilistic",
        "interval_arithmetic",
        "formal_assistant",
        "numerical_falsification",
    ),
    "epistemic": (
        "idea",
        "defined",
        "numeric_fixture",
        "proposition",
        "counterexample",
        "formal_skeleton",
    ),
}


@dataclass(frozen=True)
class Catalog:
    layers: tuple[str, ...]
    programs: tuple[str, ...]
    dimensions: Mapping[str, tuple[str, ...]]

    def validate(self) -> None:
        if len(self.layers) != 32:
            raise ValueError("the canonical layer catalog must contain 32 layers")
        if len(self.programs) != 64:
            raise ValueError("the canonical program catalog must contain 64 programs")
        if len(set(self.layers)) != len(self.layers):
            raise ValueError("layer identifiers must be unique")
        if len(set(self.programs)) != len(self.programs):
            raise ValueError("program identifiers must be unique")
        if not self.dimensions:
            raise ValueError("at least one frontier dimension is required")
        for name, values in self.dimensions.items():
            if not name or not values:
                raise ValueError("dimension names and values must be non-empty")
            if len(set(values)) != len(values):
                raise ValueError(f"duplicate values in dimension {name}")

    def dimension_names(self) -> tuple[str, ...]:
        return tuple(self.dimensions)

    def radices(self) -> tuple[int, ...]:
        return tuple(len(self.dimensions[name]) for name in self.dimension_names())

    def logical_frontier_size(self) -> int:
        return reduce(mul, self.radices(), 1) * len(self.layers) * len(self.programs)

    def summary(self) -> dict[str, object]:
        self.validate()
        return {
            "layers": len(self.layers),
            "programs": len(self.programs),
            "dimensions": {
                name: len(values) for name, values in self.dimensions.items()
            },
            "logical_frontier_cells": self.logical_frontier_size(),
            "permanent_total_cap": None,
        }

    def iter_dimension_values(self) -> Iterable[tuple[str, str]]:
        for dimension, values in self.dimensions.items():
            for value in values:
                yield dimension, value


CATALOG = Catalog(layers=LAYERS, programs=PROGRAMS, dimensions=DIMENSIONS)
CATALOG.validate()
