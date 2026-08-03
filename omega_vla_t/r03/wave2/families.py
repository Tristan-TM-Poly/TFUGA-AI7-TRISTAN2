"""Addressable Operator Universe catalog for Ω-VLA Wave 2.

The catalog declares stable operator-family identities and metadata. A catalog
entry is not a theorem and not every family has a numerical materializer yet.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable

import numpy as np

from .sparse import CSRMatrix, SparseOperator


class FamilyCatalogError(ValueError):
    pass


@dataclass(frozen=True)
class OperatorFamily:
    family_id: str
    realm: str
    order: str
    name: str
    semantic_class: str
    parameters: tuple[str, ...]
    assumptions: tuple[str, ...]
    candidate_properties: tuple[str, ...]
    applications: tuple[str, ...]
    maturity: str = "declared"
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def __post_init__(self) -> None:
        if not self.family_id or any(character.isspace() for character in self.family_id):
            raise FamilyCatalogError("family_id must be non-empty and whitespace-free")
        if self.maturity not in {"declared", "reference_fixture", "tested", "formal_target"}:
            raise FamilyCatalogError("invalid family maturity")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()


class OperatorFamilyCatalog:
    def __init__(self, families: Iterable[OperatorFamily]) -> None:
        ordered = tuple(sorted(families, key=lambda value: value.family_id))
        identifiers = [value.family_id for value in ordered]
        if len(identifiers) != len(set(identifiers)):
            raise FamilyCatalogError("operator family identifiers must be unique")
        self._families = ordered
        self._index = {value.family_id: value for value in ordered}

    def __len__(self) -> int:
        return len(self._families)

    def __iter__(self):
        return iter(self._families)

    def get(self, family_id: str) -> OperatorFamily:
        try:
            return self._index[family_id]
        except KeyError as exc:
            raise FamilyCatalogError(f"unknown operator family: {family_id}") from exc

    def search(
        self,
        *,
        realm: str | None = None,
        semantic_class: str | None = None,
        application: str | None = None,
        text: str | None = None,
    ) -> tuple[OperatorFamily, ...]:
        query = None if text is None else text.casefold()
        result = []
        for family in self._families:
            if realm is not None and family.realm != realm:
                continue
            if semantic_class is not None and family.semantic_class != semantic_class:
                continue
            if application is not None and application not in family.applications:
                continue
            haystack = " ".join(
                (
                    family.family_id,
                    family.name,
                    family.realm,
                    family.order,
                    family.semantic_class,
                    *family.parameters,
                    *family.assumptions,
                    *family.candidate_properties,
                    *family.applications,
                )
            ).casefold()
            if query is not None and query not in haystack:
                continue
            result.append(family)
        return tuple(result)

    def summary(self) -> dict[str, Any]:
        realms: dict[str, int] = {}
        classes: dict[str, int] = {}
        maturities: dict[str, int] = {}
        for family in self._families:
            realms[family.realm] = realms.get(family.realm, 0) + 1
            classes[family.semantic_class] = classes.get(family.semantic_class, 0) + 1
            maturities[family.maturity] = maturities.get(family.maturity, 0) + 1
        return {
            "families": len(self),
            "realms": dict(sorted(realms.items())),
            "semantic_classes": dict(sorted(classes.items())),
            "maturities": dict(sorted(maturities.items())),
            "theorem_claimed": False,
            "scientific_validation_claimed": False,
        }

    def digest(self) -> str:
        payload = json.dumps(
            [value.to_dict() for value in self._families],
            sort_keys=True,
            separators=(",", ":"),
        )
        return sha256(payload.encode("utf-8")).hexdigest()


def _family(
    realm: str,
    order: str,
    name: str,
    semantic_class: str,
    *,
    parameters: Iterable[str] = (),
    assumptions: Iterable[str] = (),
    properties: Iterable[str] = (),
    applications: Iterable[str] = (),
    maturity: str = "declared",
) -> OperatorFamily:
    slug = name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")
    return OperatorFamily(
        family_id=f"{realm}.{order}.{slug}",
        realm=realm,
        order=order,
        name=name,
        semantic_class=semantic_class,
        parameters=tuple(parameters),
        assumptions=tuple(assumptions),
        candidate_properties=tuple(properties),
        applications=tuple(applications),
        maturity=maturity,
    )


def _expand(
    realm: str,
    order: str,
    semantic_class: str,
    names: Iterable[str],
    *,
    parameters: Iterable[str] = (),
    assumptions: Iterable[str] = (),
    properties: Iterable[str] = (),
    applications: Iterable[str] = (),
) -> list[OperatorFamily]:
    return [
        _family(
            realm,
            order,
            name,
            semantic_class,
            parameters=parameters,
            assumptions=assumptions,
            properties=properties,
            applications=applications,
        )
        for name in names
    ]


def default_family_catalog() -> OperatorFamilyCatalog:
    families: list[OperatorFamily] = []

    families += _expand(
        "foundations",
        "elementary",
        "algebraic",
        (
            "identity", "zero", "scalar multiplication", "projection", "reflection",
            "rotation", "permutation", "restriction", "extension", "embedding",
            "quotient map", "coordinate map", "basis change", "duality map",
            "adjoint", "pseudoinverse", "rank one update", "low rank update",
            "direct sum", "tensor product",
        ),
        parameters=("dimension", "scalar_system", "units"),
        applications=("all",),
    )

    families += _expand(
        "matrix_science",
        "structured",
        "matrix",
        (
            "diagonal", "bidiagonal", "tridiagonal", "banded", "block diagonal",
            "block triangular", "upper triangular", "lower triangular", "symmetric",
            "skew symmetric", "Hermitian", "skew Hermitian", "normal", "unitary",
            "orthogonal", "positive semidefinite", "positive definite", "Toeplitz",
            "Hankel", "circulant", "Vandermonde", "Cauchy", "Hilbert", "Hadamard",
            "permutation matrix", "companion matrix", "Jordan block", "Hessenberg",
            "Laplacian matrix", "incidence matrix", "adjacency matrix", "Gram matrix",
            "covariance matrix", "correlation matrix", "stochastic matrix",
            "doubly stochastic matrix", "M matrix", "Z matrix", "Metzler matrix",
            "Hamiltonian matrix", "symplectic matrix", "density matrix",
            "Pauli operator", "Gell Mann operator", "random Gaussian matrix",
            "random orthogonal matrix", "random unitary matrix", "sparse random matrix",
        ),
        parameters=("dimension", "bandwidth", "block_shape", "seed"),
        properties=("structure_dependent",),
        applications=("numerical_linear_algebra", "statistics", "physics"),
    )

    families += _expand(
        "spectral",
        "functions",
        "matrix_function",
        (
            "exponential", "logarithm", "square root", "inverse square root",
            "matrix sign", "sine", "cosine", "hyperbolic sine", "hyperbolic cosine",
            "resolvent", "spectral projector", "polynomial functional calculus",
            "rational functional calculus", "Chebyshev approximation", "Pade approximation",
            "Krylov function action", "fractional power", "absolute value",
            "polar factor", "matrix softmax",
        ),
        parameters=("function", "branch", "tolerance", "method"),
        assumptions=("domain_of_matrix_function",),
        applications=("dynamics", "control", "quantum", "numerical_linear_algebra"),
    )

    families += _expand(
        "differential",
        "continuous",
        "differential_operator",
        (
            "first derivative", "second derivative", "gradient", "divergence", "curl",
            "Laplacian", "biharmonic", "directional derivative", "material derivative",
            "Lie derivative", "exterior derivative", "codifferential", "Hodge Laplacian",
            "Jacobian operator", "Hessian operator", "Fréchet derivative",
            "Gâteaux derivative", "covariant derivative", "connection Laplacian",
            "Laplace Beltrami", "Dirac operator", "d'Alembert operator",
            "fractional Laplacian", "Riesz derivative", "Caputo derivative",
            "advection operator", "diffusion operator", "reaction diffusion operator",
            "elasticity operator", "Stokes operator", "Navier Stokes linearization",
            "Maxwell curl curl", "Schrodinger Hamiltonian", "Fokker Planck operator",
        ),
        parameters=("domain", "boundary_conditions", "coefficients", "regularity"),
        assumptions=("declared_domain", "boundary_conditions"),
        applications=("pde", "physics", "geometry"),
    )

    families += _expand(
        "discrete_geometry",
        "graphs_complexes",
        "combinatorial_operator",
        (
            "graph gradient", "graph divergence", "combinatorial Laplacian",
            "normalized graph Laplacian", "random walk Laplacian", "magnetic Laplacian",
            "signed graph Laplacian", "directed graph Laplacian", "hypergraph Laplacian",
            "simplicial boundary", "simplicial coboundary", "Hodge Laplacian zero forms",
            "Hodge Laplacian one forms", "Hodge Laplacian two forms",
            "cellular boundary", "persistent Laplacian", "sheaf Laplacian",
            "connection Laplacian graph", "nonbacktracking operator", "Bethe Hessian",
            "graph diffusion", "graph wavelet", "graph scattering", "coarse graining",
            "multilevel prolongation", "multilevel restriction", "incidence lift",
            "line graph transform", "clique expansion", "star expansion",
        ),
        parameters=("complex", "weights", "orientation", "order"),
        assumptions=("valid_incidence",),
        applications=("networks", "topology", "HGFM"),
    )

    families += _expand(
        "tensor",
        "multilinear",
        "tensor_operator",
        (
            "mode one product", "mode two product", "mode n product", "contraction",
            "partial trace", "tensor transpose", "symmetrizer", "antisymmetrizer",
            "Khatri Rao product", "Kronecker product", "Hadamard product", "tensor unfolding",
            "tensor folding", "CP reconstruction", "Tucker reconstruction", "HOSVD map",
            "Tensor Train core map", "Tensor Ring map", "MPS transfer operator",
            "MPO transfer operator", "tensor network contraction", "tensor permutation",
            "tensor diagonal", "tensor identity", "Levi Civita contraction",
            "metric raising", "metric lowering", "Einstein contraction", "wedge product",
            "Clifford product",
        ),
        parameters=("shape", "axes", "rank", "symmetry"),
        applications=("tensor_science", "quantum", "machine_learning", "materials"),
    )

    families += _expand(
        "dynamics_control",
        "evolution",
        "evolution_operator",
        (
            "state transition", "Koopman", "Perron Frobenius", "dynamic mode decomposition",
            "extended DMD", "generator of semigroup", "transfer operator", "monodromy",
            "Floquet operator", "Lyapunov operator", "Riccati operator", "controllability Gramian",
            "observability Gramian", "Kalman gain", "LQR feedback", "MPC prediction map",
            "reachability map", "observability map", "balanced truncation", "Hankel operator",
            "delay embedding", "Carleman lift", "Markov transition", "Bellman operator",
            "policy evaluation", "consensus operator", "synchronization operator",
            "master stability operator", "bifurcation Jacobian", "Poincare map",
        ),
        parameters=("time", "parameters", "horizon", "measure"),
        applications=("dynamics", "control", "learning"),
    )

    families += _expand(
        "physics",
        "equations",
        "physical_operator",
        (
            "mass matrix", "damping matrix", "stiffness matrix", "elasticity tensor map",
            "strain displacement", "stress divergence", "heat diffusion", "wave propagation",
            "Helmholtz", "Poisson", "Maxwell Faraday", "Maxwell Ampere", "Maxwell block operator",
            "photonic transfer matrix", "scattering matrix", "quantum Hamiltonian",
            "creation operator", "annihilation operator", "number operator", "density evolution",
            "Liouvillian", "MHD induction", "MHD momentum", "Vlasov transport",
            "plasma dielectric tensor", "crystal dynamical matrix", "phonon operator",
            "Raman mixing matrix", "MEMS coupled operator", "battery diffusion",
            "electrochemical Jacobian", "gravitational wave operator", "Dirac Hamiltonian",
            "gauge covariant derivative", "lattice gauge plaquette", "protein contact Laplacian",
            "neural covariance operator", "EEG graph operator", "fluid projection",
            "vorticity operator",
        ),
        parameters=("units", "material_parameters", "boundary_conditions", "discretization"),
        assumptions=("dimensionally_consistent",),
        applications=("physics", "engineering", "spectroscopy"),
    )

    families += _expand(
        "transforms",
        "analysis_synthesis",
        "transform_operator",
        (
            "discrete Fourier", "inverse discrete Fourier", "FFT", "DCT", "DST",
            "Hadamard transform", "Haar wavelet", "Daubechies wavelet", "continuous wavelet",
            "short time Fourier", "Gabor", "Radon", "inverse Radon", "Hilbert transform",
            "Laplace transform", "Z transform", "Mellin transform", "chirp Z transform",
            "graph Fourier", "graph wavelet transform", "scattering transform", "SVD transform",
            "PCA transform", "ICA transform", "Koopman transform", "FFWT candidate",
            "FFWT N candidate", "CVCD compression map", "LOG compression", "EXP reconstruction",
        ),
        parameters=("basis", "scale", "normalization", "boundary"),
        applications=("signals", "spectroscopy", "compression", "HGFM"),
    )

    families += _expand(
        "optimization_probability",
        "inference",
        "optimization_operator",
        (
            "orthogonal projection convex set", "proximal operator", "gradient step",
            "Newton step", "Gauss Newton", "Levenberg Marquardt", "KKT block operator",
            "normal equation", "least squares projector", "covariance operator",
            "precision operator", "conditional expectation", "Bayes update linearized",
            "Fisher information", "score covariance", "optimal transport map",
            "Sinkhorn operator", "Wasserstein gradient", "ensemble Kalman update",
            "particle covariance", "kernel integral operator", "Gaussian process covariance",
            "RKHS embedding", "CCA operator", "whitening", "Mahalanobis metric",
            "robust covariance", "sparse coding dictionary", "compressed sensing map",
            "restricted isometry test operator",
        ),
        parameters=("objective", "constraints", "distribution", "regularization"),
        applications=("optimization", "statistics", "AI"),
    )

    references = {
        "foundations.elementary.identity",
        "foundations.elementary.zero",
        "matrix_science.structured.diagonal",
        "matrix_science.structured.circulant",
        "matrix_science.structured.hilbert",
        "matrix_science.structured.permutation_matrix",
        "differential.continuous.first_derivative",
        "differential.continuous.second_derivative",
        "discrete_geometry.graphs_complexes.combinatorial_laplacian",
        "physics.equations.mass_matrix",
        "physics.equations.stiffness_matrix",
    }
    families = [
        OperatorFamily(**{
            **family.to_dict(),
            "maturity": "reference_fixture" if family.family_id in references else family.maturity,
            "theorem_claimed": False,
            "scientific_validation_claimed": False,
        })
        for family in families
    ]
    return OperatorFamilyCatalog(families)


def materialize_reference(
    family_id: str,
    dimension: int,
    *,
    parameter: float = 1.0,
) -> SparseOperator:
    """Materialize a small deterministic reference for selected families."""

    if dimension <= 0:
        raise FamilyCatalogError("dimension must be positive")
    catalog = default_family_catalog()
    family = catalog.get(family_id)
    if family.maturity != "reference_fixture":
        raise FamilyCatalogError(f"family has no reference materializer: {family_id}")

    if family_id == "foundations.elementary.identity":
        matrix = CSRMatrix.identity(dimension)
    elif family_id == "foundations.elementary.zero":
        matrix = CSRMatrix.from_coo(dimension, dimension, ())
    elif family_id in {
        "matrix_science.structured.diagonal",
        "physics.equations.mass_matrix",
        "physics.equations.stiffness_matrix",
    }:
        matrix = CSRMatrix.diagonal([parameter * (index + 1) for index in range(dimension)])
    elif family_id == "matrix_science.structured.circulant":
        entries = []
        for row in range(dimension):
            entries.append((row, row, parameter))
            entries.append((row, (row + 1) % dimension, 1.0))
        matrix = CSRMatrix.from_coo(dimension, dimension, entries)
    elif family_id == "matrix_science.structured.hilbert":
        dense = np.fromfunction(lambda i, j: 1.0 / (i + j + 1.0), (dimension, dimension))
        matrix = CSRMatrix.from_dense(dense)
    elif family_id == "matrix_science.structured.permutation_matrix":
        matrix = CSRMatrix.from_coo(
            dimension,
            dimension,
            ((row, (row + 1) % dimension, 1.0) for row in range(dimension)),
        )
    elif family_id == "differential.continuous.first_derivative":
        entries = []
        for row in range(dimension):
            if row > 0:
                entries.append((row, row - 1, -0.5))
            if row + 1 < dimension:
                entries.append((row, row + 1, 0.5))
        matrix = CSRMatrix.from_coo(dimension, dimension, entries)
    elif family_id in {
        "differential.continuous.second_derivative",
        "discrete_geometry.graphs_complexes.combinatorial_laplacian",
    }:
        matrix = CSRMatrix.laplacian_1d(dimension)
    else:
        raise FamilyCatalogError(f"unimplemented reference materializer: {family_id}")

    return SparseOperator(
        name=family.name,
        matrix=matrix,
        tags=(family.realm, family.order, family.semantic_class),
    )
