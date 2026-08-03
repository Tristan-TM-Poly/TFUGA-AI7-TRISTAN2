"""Canonical registry for the seven Clay millennium problems.

The registry is an engineering representation, not a substitute for the
original official statements or the mathematical literature.
"""
from __future__ import annotations

from .models import ProblemId, ProblemSpec, ProblemStatus


_REGISTRY: dict[ProblemId, ProblemSpec] = {
    ProblemId.POINCARE: ProblemSpec(
        problem_id=ProblemId.POINCARE,
        title="Poincaré conjecture",
        status=ProblemStatus.SOLVED_BENCHMARK,
        domain=("geometric topology", "differential geometry", "geometric analysis"),
        statement=(
            "Every closed simply connected three-dimensional manifold is "
            "homeomorphic to the three-sphere."
        ),
        accepted_outcomes=("reconstruct a certified dependency map of the accepted proof",),
        canonical_objects=("3-manifold", "Ricci flow", "surgery", "entropy", "geometrization"),
        barriers=(
            "formation and classification of singularities",
            "control of surgery and non-collapsing",
            "translation from geometric flow to topological conclusion",
        ),
        forbidden_shortcuts=(
            "treating numerical flow as a proof",
            "assuming singularities are automatically removable",
            "using geometrization as an unproved premise in a reconstruction benchmark",
        ),
        benchmark_role="positive-control dataset for proof decomposition and hidden-assumption detection",
    ),
    ProblemId.RIEMANN: ProblemSpec(
        problem_id=ProblemId.RIEMANN,
        title="Riemann hypothesis",
        status=ProblemStatus.OPEN,
        domain=("analytic number theory", "spectral theory", "complex analysis"),
        statement="Every non-trivial zero of the Riemann zeta function has real part one half.",
        accepted_outcomes=("prove the critical-line statement", "construct a valid off-line zero"),
        canonical_objects=("zeta function", "critical strip", "explicit formula", "prime distribution", "L-functions"),
        barriers=(
            "finite zero verification does not imply the universal statement",
            "spectral analogies require an actual self-adjoint operator and complete correspondence",
            "positivity criteria require exact domains and both directions of equivalence",
        ),
        forbidden_shortcuts=(
            "extrapolating from finitely many verified zeros",
            "fitting a spectrum without proving operator existence",
            "assuming an equivalent criterion is easier without a new estimate",
        ),
    ),
    ProblemId.P_VS_NP: ProblemSpec(
        problem_id=ProblemId.P_VS_NP,
        title="P versus NP",
        status=ProblemStatus.OPEN,
        domain=("computational complexity", "circuit complexity", "proof complexity"),
        statement="Determine whether every polynomial-time verifiable language is polynomial-time decidable.",
        accepted_outcomes=("prove P equals NP", "prove P differs from NP"),
        canonical_objects=("Turing machines", "circuits", "reductions", "lower bounds", "proof systems"),
        barriers=(
            "relativization",
            "natural-proofs style obstructions",
            "algebrization",
            "restricted-model lower bounds may not lift to the general model",
        ),
        forbidden_shortcuts=(
            "confusing exponential behavior of one algorithm with a lower bound",
            "transferring non-uniform results to uniform classes without proof",
            "inferring worst-case hardness from average-case experiments",
        ),
    ),
    ProblemId.NAVIER_STOKES: ProblemSpec(
        problem_id=ProblemId.NAVIER_STOKES,
        title="Navier–Stokes existence and smoothness",
        status=ProblemStatus.OPEN,
        domain=("partial differential equations", "harmonic analysis", "fluid mechanics"),
        statement=(
            "For the specified three-dimensional incompressible Navier–Stokes setting, "
            "prove global regularity or construct admissible finite-time breakdown."
        ),
        accepted_outcomes=("prove global regularity", "construct admissible finite-time singularity"),
        canonical_objects=("velocity", "pressure", "vorticity", "energy", "enstrophy", "critical scaling"),
        barriers=(
            "supercritical transfer of control to small scales",
            "weak solutions need not supply the desired smoothness",
            "numerical blow-up signatures may be discretization artifacts",
        ),
        forbidden_shortcuts=(
            "assuming smoothness while deriving the bound intended to prove smoothness",
            "using a cutoff-dependent estimate as a uniform estimate",
            "equating an Euler mechanism with a Navier–Stokes mechanism",
        ),
    ),
    ProblemId.YANG_MILLS: ProblemSpec(
        problem_id=ProblemId.YANG_MILLS,
        title="Yang–Mills existence and mass gap",
        status=ProblemStatus.OPEN,
        domain=("quantum field theory", "constructive field theory", "gauge theory"),
        statement=(
            "Construct a non-trivial four-dimensional quantum Yang–Mills theory for a compact "
            "simple gauge group and prove a strictly positive mass gap."
        ),
        accepted_outcomes=("construct the theory and prove a positive mass gap",),
        canonical_objects=("gauge fields", "Wilson loops", "Euclidean measure", "Hamiltonian", "spectrum", "renormalization"),
        barriers=(
            "continuum and infinite-volume limits must both exist",
            "a lattice gap may vanish in the continuum limit",
            "gauge invariance and positivity properties must survive construction",
        ),
        forbidden_shortcuts=(
            "treating lattice simulation as constructive existence",
            "assuming a uniform gap from finite-volume observations",
            "using formal path integrals as a complete measure-theoretic construction",
        ),
    ),
    ProblemId.HODGE: ProblemSpec(
        problem_id=ProblemId.HODGE,
        title="Hodge conjecture",
        status=ProblemStatus.OPEN,
        domain=("algebraic geometry", "topology", "Hodge theory"),
        statement=(
            "For smooth projective complex varieties, determine whether rational Hodge classes "
            "of type (p,p) are rational combinations of algebraic cycle classes."
        ),
        accepted_outcomes=("prove the rational Hodge conjecture", "construct a valid counterexample to the stated form"),
        canonical_objects=("cycles", "cohomology", "Hodge decomposition", "cycle class map", "correspondences"),
        barriers=(
            "analytic representatives need not be algebraic cycles",
            "special-family arguments may not globalize",
            "integral and rational forms must not be conflated",
        ),
        forbidden_shortcuts=(
            "inferring surjectivity from matching dimensions alone",
            "confusing the integral Hodge conjecture with the rational conjecture",
            "assuming deformation preserves an algebraic cycle without proof",
        ),
    ),
    ProblemId.BSD: ProblemSpec(
        problem_id=ProblemId.BSD,
        title="Birch and Swinnerton-Dyer conjecture",
        status=ProblemStatus.OPEN,
        domain=("arithmetic geometry", "number theory", "elliptic curves"),
        statement=(
            "Relate the rank and finer arithmetic invariants of an elliptic curve over the rationals "
            "to the order and leading term of its L-function at the central point."
        ),
        accepted_outcomes=("prove the full conjectural relation", "construct a valid counterexample"),
        canonical_objects=("elliptic curve", "rational points", "L-function", "Selmer group", "regulator", "Tate–Shafarevich group"),
        barriers=(
            "analytic rank must be certified exactly, not estimated from floating point samples",
            "finiteness assumptions can hide circular reasoning",
            "low-rank theorems do not automatically extend to arbitrary rank",
        ),
        forbidden_shortcuts=(
            "declaring exact vanishing order from unstable numerical differentiation",
            "assuming finiteness of an arithmetic group when it is part of the difficulty",
            "generalizing from a finite database of curves",
        ),
    ),
}


def get_problem(problem_id: ProblemId | str) -> ProblemSpec:
    return _REGISTRY[ProblemId(problem_id)]


def all_problems() -> tuple[ProblemSpec, ...]:
    return tuple(_REGISTRY[problem_id] for problem_id in ProblemId)


def validate_registry() -> tuple[str, ...]:
    errors: list[str] = []
    if set(_REGISTRY) != set(ProblemId):
        missing = set(ProblemId) - set(_REGISTRY)
        extra = set(_REGISTRY) - set(ProblemId)
        errors.append(f"registry mismatch: missing={sorted(x.value for x in missing)}, extra={sorted(x.value for x in extra)}")
    for spec in all_problems():
        errors.extend(f"{spec.problem_id.value}: {error}" for error in spec.validate())
    solved = [spec for spec in all_problems() if spec.status == ProblemStatus.SOLVED_BENCHMARK]
    if len(solved) != 1 or solved[0].problem_id != ProblemId.POINCARE:
        errors.append("exactly Poincaré must be the solved benchmark in R0.1")
    return tuple(errors)
