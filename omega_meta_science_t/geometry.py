"""Discovery Geometry & Algebra primitives for MetaScienceBench-T R0.3.

The names in this module are research-program interfaces. Every primitive is
bounded by an explicit finite probe set, candidate family, declared utility,
world set, evidence-dependence matrix, transform certificate, or program set.
Nothing here establishes global mathematical equivalence, causal discovery,
proof of novelty, or globally optimal scientific search.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from math import prod
from typing import Callable, Sequence

from .benchmark import build_fixture
from .discovery import DiscoveryABI, TheoryAdapter
from .models import TheoryGenome


@dataclass(frozen=True, slots=True)
class TheoryEquivalenceClass:
    member_ids: tuple[str, ...]
    probe_signature: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class TheoryQuotientReport:
    probes: tuple[float, ...]
    tolerance: float
    classes: tuple[TheoryEquivalenceClass, ...]
    oak_boundary: str = (
        "empirical equivalence on declared probes only; not mathematical or global theory equivalence"
    )


def empirical_theory_quotient(
    theories: Sequence[TheoryGenome],
    probes: Sequence[float],
    *,
    tolerance: float = 1e-9,
) -> TheoryQuotientReport:
    """Group theories with indistinguishable predictions on a declared probe set."""

    if not theories:
        raise ValueError("at least one theory is required")
    if not probes:
        raise ValueError("at least one probe is required")
    if tolerance <= 0.0:
        raise ValueError("tolerance must be positive")

    probe_tuple = tuple(float(x) for x in probes)
    buckets: dict[tuple[int, ...], list[str]] = {}
    for theory in theories:
        signature = tuple(round(theory.predict(x) / tolerance) for x in probe_tuple)
        buckets.setdefault(signature, []).append(theory.theory_id)

    classes = tuple(
        TheoryEquivalenceClass(tuple(sorted(member_ids)), signature)
        for signature, member_ids in sorted(buckets.items(), key=lambda item: tuple(sorted(item[1])))
    )
    return TheoryQuotientReport(probe_tuple, tolerance, classes)


@dataclass(frozen=True, slots=True)
class AdversarialTwinReport:
    base_provenance: str
    alpha: float
    anchors: tuple[float, ...]
    challenge_points: tuple[float, ...]
    max_anchor_error: float
    strongest_challenge_x: float
    max_challenge_divergence: float
    formula: str
    oak_boundary: str = (
        "best member of one declared anchor-preserving perturbation family; not a globally strongest rival theory"
    )


def compile_adversarial_twin(
    base: DiscoveryABI,
    anchors: Sequence[float],
    challenge_points: Sequence[float],
    alphas: Sequence[float],
) -> AdversarialTwinReport:
    """Find the strongest anchor-preserving polynomial perturbation in a finite family.

    Candidate twin:
        T_alpha(x) = T(x) + alpha * product_j (x - anchor_j)

    By construction it matches the base prediction on every declared anchor.
    """

    if not anchors:
        raise ValueError("at least one anchor is required")
    if not challenge_points:
        raise ValueError("at least one challenge point is required")
    if not alphas:
        raise ValueError("at least one alpha is required")

    anchor_tuple = tuple(float(x) for x in anchors)
    challenge_tuple = tuple(float(x) for x in challenge_points)

    def perturbation(x: float, alpha: float) -> float:
        return alpha * prod(x - anchor for anchor in anchor_tuple)

    scored: list[tuple[float, float, float, float]] = []
    for raw_alpha in alphas:
        alpha = float(raw_alpha)
        anchor_error = max(abs(perturbation(x, alpha)) for x in anchor_tuple)
        divergences = tuple((abs(perturbation(x, alpha)), x) for x in challenge_tuple)
        max_divergence, challenge_x = max(divergences, key=lambda item: (item[0], item[1]))
        scored.append((max_divergence, abs(alpha), alpha, challenge_x))

    max_divergence, _, alpha, challenge_x = max(scored, key=lambda item: (item[0], item[1], item[2]))
    max_anchor_error = max(abs(perturbation(x, alpha)) for x in anchor_tuple)
    factor_text = "*".join(f"(x-{anchor:g})" for anchor in anchor_tuple)
    return AdversarialTwinReport(
        base_provenance=base.provenance(),
        alpha=alpha,
        anchors=anchor_tuple,
        challenge_points=challenge_tuple,
        max_anchor_error=max_anchor_error,
        strongest_challenge_x=challenge_x,
        max_challenge_divergence=max_divergence,
        formula=f"T_twin(x)=T_base(x)+({alpha:g})*{factor_text}",
    )


@dataclass(frozen=True, slots=True)
class EvidenceIndependenceReport:
    evidence_ids: tuple[str, ...]
    dependence_matrix: tuple[tuple[float, ...], ...]
    matrix_valid: bool
    errors: tuple[str, ...]
    raw_count: int
    effective_count_surrogate: float
    redundancy_fraction: float
    oak_boundary: str = (
        "effective count is a declared redundancy surrogate, not a universal statistical effective sample size"
    )


def evidence_independence(
    evidence_ids: Sequence[str],
    dependence_matrix: Sequence[Sequence[float]],
    *,
    tolerance: float = 1e-12,
) -> EvidenceIndependenceReport:
    """Audit pairwise dependence and compute a bounded effective-count surrogate."""

    ids = tuple(str(item) for item in evidence_ids)
    matrix = tuple(tuple(float(value) for value in row) for row in dependence_matrix)
    n = len(ids)
    errors: list[str] = []
    if n == 0:
        errors.append("missing_evidence")
    if len(set(ids)) != len(ids):
        errors.append("duplicate_evidence_ids")
    if len(matrix) != n or any(len(row) != n for row in matrix):
        errors.append("matrix_shape_mismatch")
    else:
        for i in range(n):
            for j in range(n):
                value = matrix[i][j]
                if value < -tolerance or value > 1.0 + tolerance:
                    errors.append(f"dependence_out_of_range:{i}:{j}")
                if i == j and abs(value - 1.0) > tolerance:
                    errors.append(f"diagonal_not_one:{i}")
                if abs(value - matrix[j][i]) > tolerance:
                    errors.append(f"matrix_not_symmetric:{i}:{j}")
    errors = sorted(set(errors))
    valid = not errors
    if valid and n:
        total_dependence = sum(sum(row) for row in matrix)
        effective = (n * n) / total_dependence if total_dependence > 0.0 else float(n)
        effective = min(float(n), max(1.0, effective))
    else:
        effective = 0.0
    redundancy = 1.0 - effective / n if n else 1.0
    return EvidenceIndependenceReport(
        ids,
        matrix,
        valid,
        tuple(errors),
        n,
        effective,
        redundancy,
    )


@dataclass(frozen=True, slots=True)
class EpistemicHessianReport:
    point: tuple[float, ...]
    step: float
    hessian: tuple[tuple[float, ...], ...]
    utility_name: str
    symmetry_residual: float
    oak_boundary: str = (
        "second-order sensitivity of a declared utility surrogate; not curvature of truth or knowledge itself"
    )


def epistemic_hessian(
    utility: Callable[[tuple[float, ...]], float],
    point: Sequence[float],
    *,
    step: float = 1e-4,
    utility_name: str = "declared_utility_surrogate",
) -> EpistemicHessianReport:
    """Central finite-difference Hessian of an explicitly supplied utility."""

    if step <= 0.0:
        raise ValueError("step must be positive")
    x = tuple(float(value) for value in point)
    if not x:
        raise ValueError("point must be non-empty")
    n = len(x)
    center = float(utility(x))
    matrix = [[0.0 for _ in range(n)] for _ in range(n)]

    for i in range(n):
        plus = list(x)
        minus = list(x)
        plus[i] += step
        minus[i] -= step
        matrix[i][i] = (float(utility(tuple(plus))) - 2.0 * center + float(utility(tuple(minus)))) / (step * step)
        for j in range(i + 1, n):
            pp = list(x)
            pm = list(x)
            mp = list(x)
            mm = list(x)
            pp[i] += step; pp[j] += step
            pm[i] += step; pm[j] -= step
            mp[i] -= step; mp[j] += step
            mm[i] -= step; mm[j] -= step
            mixed = (
                float(utility(tuple(pp)))
                - float(utility(tuple(pm)))
                - float(utility(tuple(mp)))
                + float(utility(tuple(mm)))
            ) / (4.0 * step * step)
            matrix[i][j] = mixed
            matrix[j][i] = mixed

    symmetry_residual = max(
        abs(matrix[i][j] - matrix[j][i])
        for i in range(n)
        for j in range(n)
    )
    return EpistemicHessianReport(
        x,
        step,
        tuple(tuple(row) for row in matrix),
        utility_name,
        symmetry_residual,
    )


@dataclass(frozen=True, slots=True)
class ClaimConstraint:
    claim_id: str
    allowed_worlds: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class UnsatCoreReport:
    satisfiable: bool
    minimal_core: tuple[str, ...]
    searched_claim_count: int
    witness_worlds: tuple[str, ...]
    oak_boundary: str = (
        "minimal only within the declared finite world model and claim set"
    )


def minimal_unsat_core(claims: Sequence[ClaimConstraint]) -> UnsatCoreReport:
    """Return a cardinality-minimal inconsistent subset over finite allowed worlds."""

    items = tuple(claims)
    if not items:
        return UnsatCoreReport(True, (), 0, ())
    universe = set().union(*(set(claim.allowed_worlds) for claim in items))
    all_allowed = set(universe)
    for claim in items:
        all_allowed &= set(claim.allowed_worlds)
    if all_allowed:
        return UnsatCoreReport(True, (), len(items), tuple(sorted(all_allowed)))

    for size in range(1, len(items) + 1):
        for subset in combinations(items, size):
            allowed = set(universe)
            for claim in subset:
                allowed &= set(claim.allowed_worlds)
            if not allowed:
                return UnsatCoreReport(
                    False,
                    tuple(claim.claim_id for claim in subset),
                    len(items),
                    (),
                )
    raise RuntimeError("unsatisfiable claim set had no finite core")


@dataclass(frozen=True, slots=True)
class TransformCertificate:
    transform_id: str
    source_id: str
    target_id: str
    invariants_before: tuple[str, ...]
    invariants_after: tuple[str, ...]
    roundtrip_error: float
    max_roundtrip_error: float
    domain: str
    provenance: str


@dataclass(frozen=True, slots=True)
class TransformCertificateReport:
    certified: bool
    blockers: tuple[str, ...]
    certificate: TransformCertificate


def validate_transform_certificate(
    certificate: TransformCertificate,
) -> TransformCertificateReport:
    blockers: list[str] = []
    if not certificate.provenance.strip():
        blockers.append("missing_provenance")
    if not certificate.domain.strip():
        blockers.append("missing_domain")
    if certificate.max_roundtrip_error < 0.0 or certificate.roundtrip_error < 0.0:
        blockers.append("negative_error_bound")
    if certificate.roundtrip_error > certificate.max_roundtrip_error:
        blockers.append("roundtrip_error_exceeds_bound")
    missing = tuple(
        invariant
        for invariant in certificate.invariants_before
        if invariant not in set(certificate.invariants_after)
    )
    blockers.extend(f"lost_invariant:{item}" for item in missing)
    return TransformCertificateReport(not blockers, tuple(blockers), certificate)


@dataclass(frozen=True, slots=True)
class ScientificProgram:
    program_id: str
    steps: tuple[str, ...]
    cost: float
    verified_gain: float
    oak_pass: bool
    invariants: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ScientificSuperoptimizerReport:
    selected: ScientificProgram
    eligible_programs: tuple[str, ...]
    rejected: tuple[tuple[str, tuple[str, ...]], ...]
    savings_vs_most_expensive_eligible: float
    oak_boundary: str = (
        "finite candidate selection under declared constraints; not global scientific-program optimality"
    )


def scientific_superoptimize(
    programs: Sequence[ScientificProgram],
    *,
    min_verified_gain: float,
    required_invariants: Sequence[str] = (),
) -> ScientificSuperoptimizerReport:
    """Choose the least-cost program surviving explicit gain/OAK/invariant gates."""

    required = set(required_invariants)
    eligible: list[ScientificProgram] = []
    rejected: list[tuple[str, tuple[str, ...]]] = []
    for program in programs:
        blockers: list[str] = []
        if program.cost < 0.0:
            blockers.append("negative_cost")
        if not program.oak_pass:
            blockers.append("oak_block")
        if program.verified_gain < min_verified_gain:
            blockers.append("insufficient_verified_gain")
        missing = required - set(program.invariants)
        blockers.extend(f"missing_invariant:{item}" for item in sorted(missing))
        if blockers:
            rejected.append((program.program_id, tuple(blockers)))
        else:
            eligible.append(program)
    if not eligible:
        raise ValueError("no scientific program passes the declared gates")
    selected = min(eligible, key=lambda program: (program.cost, program.program_id))
    maximum_eligible_cost = max(program.cost for program in eligible)
    return ScientificSuperoptimizerReport(
        selected,
        tuple(program.program_id for program in eligible),
        tuple(rejected),
        maximum_eligible_cost - selected.cost,
    )


@dataclass(frozen=True, slots=True)
class DiscoveryGeometryAlgebraReport:
    quotient_coarse: TheoryQuotientReport
    quotient_refined: TheoryQuotientReport
    adversarial_twin: AdversarialTwinReport
    evidence: EvidenceIndependenceReport
    hessian: EpistemicHessianReport
    unsat_core: UnsatCoreReport
    transform: TransformCertificateReport
    superoptimizer: ScientificSuperoptimizerReport


def run_discovery_geometry_algebra_demo() -> DiscoveryGeometryAlgebraReport:
    """Deterministic R0.3 composition fixture for CI and documentation."""

    problem = build_fixture()
    linear = problem.theories[0]
    quotient_coarse = empirical_theory_quotient(problem.theories, (0.0, 1.0))
    quotient_refined = empirical_theory_quotient(problem.theories, (0.0, 1.0, 2.0))
    twin = compile_adversarial_twin(
        TheoryAdapter(linear),
        anchors=(0.0, 1.0),
        challenge_points=(2.0, 3.0),
        alphas=(-1.0, -0.5, 0.5, 1.0),
    )
    evidence = evidence_independence(
        ("E1", "E2", "E3"),
        (
            (1.0, 0.9, 0.0),
            (0.9, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
    )

    def portfolio_surrogate(point: tuple[float, ...]) -> float:
        a, b = point
        return -(a - 2.0) ** 2 - 2.0 * (b - 3.0) ** 2 + 0.5 * a * b

    hessian = epistemic_hessian(
        portfolio_surrogate,
        (2.0, 3.0),
        step=1e-4,
        utility_name="toy_portfolio_utility",
    )
    unsat = minimal_unsat_core(
        (
            ClaimConstraint("C1", ("A", "B")),
            ClaimConstraint("C2", ("B", "C")),
            ClaimConstraint("C3", ("A", "C")),
        )
    )
    transform = validate_transform_certificate(
        TransformCertificate(
            "symbolic_to_program_roundtrip",
            "symbolic:T_linear",
            "program:T_linear",
            ("observable:y", "domain:x>=0"),
            ("observable:y", "domain:x>=0", "execution:deterministic"),
            0.01,
            0.05,
            "x>=0",
            "fixture:MetaScienceBench-T:R0.3",
        )
    )
    superoptimizer = scientific_superoptimize(
        (
            ScientificProgram(
                "baseline",
                ("represent", "simulate", "validate", "report"),
                10.0,
                1.0,
                True,
                ("provenance", "reproducibility"),
            ),
            ScientificProgram(
                "compressed",
                ("represent", "validate", "report"),
                4.0,
                1.0,
                True,
                ("provenance", "reproducibility"),
            ),
            ScientificProgram(
                "cheap_but_invalid",
                ("report",),
                1.0,
                0.2,
                False,
                ("provenance",),
            ),
        ),
        min_verified_gain=1.0,
        required_invariants=("provenance", "reproducibility"),
    )
    return DiscoveryGeometryAlgebraReport(
        quotient_coarse,
        quotient_refined,
        twin,
        evidence,
        hessian,
        unsat,
        transform,
        superoptimizer,
    )


def report_as_dict(report: DiscoveryGeometryAlgebraReport) -> dict[str, object]:
    return asdict(report)
