"""Reusable Discovery Dynamics primitives for MetaScienceBench-T R0.2.

These objects are deliberately small and deterministic. Names such as
"epistemic Jacobian" and "unknown-unknown radar" denote research-program
interfaces, not claims that the toy metrics equal true scientific knowledge or
that unknown unknowns can be directly observed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Callable, Mapping, Protocol, Sequence

from .benchmark import build_fixture
from .models import TheoryGenome


@dataclass(frozen=True, slots=True)
class ScientificIR:
    """Minimal scientific intermediate representation.

    The IR is intentionally declarative: it carries variables, relations,
    units, assumptions, observables, domain, tests and provenance without
    pretending to prove that the source object was translated faithfully.
    """

    object_id: str
    variables: tuple[str, ...]
    relations: tuple[str, ...]
    units: tuple[tuple[str, str], ...]
    assumptions: tuple[str, ...]
    observables: tuple[str, ...]
    domain: str
    tests: tuple[str, ...]
    provenance: str

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.object_id.strip():
            errors.append("missing_object_id")
        if not self.provenance.strip():
            errors.append("missing_provenance")
        if len(set(self.variables)) != len(self.variables):
            errors.append("duplicate_variables")
        variable_set = set(self.variables)
        for observable in self.observables:
            if observable not in variable_set:
                errors.append(f"observable_not_declared:{observable}")
        unit_names = [name for name, _ in self.units]
        if len(set(unit_names)) != len(unit_names):
            errors.append("duplicate_unit_bindings")
        for name in unit_names:
            if name not in variable_set:
                errors.append(f"unit_for_unknown_variable:{name}")
        if not self.relations:
            errors.append("missing_relations")
        if not self.tests:
            errors.append("missing_tests")
        return tuple(errors)


class DiscoveryABI(Protocol):
    """Small interface that lets theory-like objects plug into discovery tools."""

    def predict(self, x: float) -> float: ...

    def explain(self) -> tuple[str, ...]: ...

    def falsify(self, x: float, observation: float, tolerance: float) -> bool: ...

    def uncertainty(self) -> float: ...

    def provenance(self) -> str: ...

    def cost(self) -> float: ...

    def domain(self) -> str: ...

    def represent(self) -> tuple[str, ...]: ...


@dataclass(frozen=True, slots=True)
class TheoryAdapter:
    """Adapter from the R0.1 TheoryGenome to the R0.2 Discovery ABI."""

    theory: TheoryGenome
    tolerance: float = 1e-12
    evaluation_cost: float = 1.0

    def predict(self, x: float) -> float:
        return self.theory.predict(x)

    def explain(self) -> tuple[str, ...]:
        return tuple(rep.expression for rep in self.theory.representations)

    def falsify(self, x: float, observation: float, tolerance: float | None = None) -> bool:
        tol = self.tolerance if tolerance is None else tolerance
        return abs(self.predict(x) - observation) > tol

    def uncertainty(self) -> float:
        return self.tolerance

    def provenance(self) -> str:
        return f"theory:{self.theory.theory_id}"

    def cost(self) -> float:
        return self.evaluation_cost

    def domain(self) -> str:
        return self.theory.domain

    def represent(self) -> tuple[str, ...]:
        return tuple(rep.name for rep in self.theory.representations)


@dataclass(frozen=True, slots=True)
class EpistemicJacobianReport:
    x: float
    step: float
    utility_left: float
    utility_center: float
    utility_right: float
    derivative: float
    utility_name: str = "prediction_disagreement_surrogate"
    oak_boundary: str = "local surrogate sensitivity; not a gradient of truth"


def disagreement_utility(theories: Sequence[TheoryGenome], x: float) -> float:
    if not theories:
        raise ValueError("at least one theory is required")
    predictions = [theory.predict(x) for theory in theories]
    mean = sum(predictions) / len(predictions)
    return sum((value - mean) ** 2 for value in predictions) / len(predictions)


def epistemic_jacobian(
    theories: Sequence[TheoryGenome],
    x: float,
    *,
    step: float = 1e-5,
) -> EpistemicJacobianReport:
    """Central-difference sensitivity of a declared information surrogate."""

    if step <= 0:
        raise ValueError("step must be positive")
    left = disagreement_utility(theories, x - step)
    center = disagreement_utility(theories, x)
    right = disagreement_utility(theories, x + step)
    derivative = (right - left) / (2.0 * step)
    return EpistemicJacobianReport(x, step, left, center, right, derivative)


@dataclass(frozen=True, slots=True)
class ResidualGenome:
    residuals: tuple[float, ...]
    mean: float
    rms: float
    slope: float
    sign_change_rate: float
    lag1_correlation: float
    signatures: tuple[str, ...]


def _linear_slope(values: Sequence[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    if denominator == 0.0:
        return 0.0
    return sum((i - x_mean) * (value - y_mean) for i, value in enumerate(values)) / denominator


def _lag1_correlation(values: Sequence[float]) -> float:
    if len(values) < 3:
        return 0.0
    left = values[:-1]
    right = values[1:]
    lm = sum(left) / len(left)
    rm = sum(right) / len(right)
    numerator = sum((a - lm) * (b - rm) for a, b in zip(left, right))
    dl = sum((a - lm) ** 2 for a in left)
    dr = sum((b - rm) ** 2 for b in right)
    if dl <= 0.0 or dr <= 0.0:
        return 0.0
    return numerator / sqrt(dl * dr)


def compile_residual_genome(residuals: Sequence[float]) -> ResidualGenome:
    if not residuals:
        raise ValueError("at least one residual is required")
    values = tuple(float(value) for value in residuals)
    n = len(values)
    mean = sum(values) / n
    rms = sqrt(sum(value * value for value in values) / n)
    slope = _linear_slope(values)
    changes = sum(
        1 for a, b in zip(values, values[1:]) if a != 0.0 and b != 0.0 and (a > 0) != (b > 0)
    )
    sign_change_rate = changes / max(n - 1, 1)
    lag1 = _lag1_correlation(values)
    scale = max(rms, 1e-15)
    signatures: list[str] = []
    if abs(mean) / scale >= 0.25:
        signatures.append("systematic_bias_candidate")
    if abs(slope) / scale >= 0.20:
        signatures.append("trend_candidate")
    if sign_change_rate >= 0.60:
        signatures.append("oscillation_candidate")
    if abs(lag1) >= 0.70:
        signatures.append("serial_structure_candidate")
    if not signatures:
        signatures.append("no_simple_structure_detected")
    return ResidualGenome(values, mean, rms, slope, sign_change_rate, lag1, tuple(signatures))


@dataclass(frozen=True, slots=True)
class CounterexampleCandidate:
    x: float
    predicted: float
    observed: float
    residual: float
    falsifies: bool


def compile_counterexample(
    theory: DiscoveryABI,
    observer: Callable[[float], float],
    candidates: Sequence[float],
    *,
    tolerance: float = 1e-12,
) -> CounterexampleCandidate:
    """Search a declared finite candidate set for the strongest residual."""

    if not candidates:
        raise ValueError("at least one candidate point is required")
    scored: list[CounterexampleCandidate] = []
    for x in candidates:
        predicted = theory.predict(float(x))
        observed = float(observer(float(x)))
        residual = abs(predicted - observed)
        scored.append(
            CounterexampleCandidate(float(x), predicted, observed, residual, residual > tolerance)
        )
    return max(scored, key=lambda item: (item.residual, item.x))


@dataclass(frozen=True, slots=True)
class RepresentationRoute:
    route_id: str
    solve_cost: float
    transform_cost: float
    roundtrip_loss: float
    invariant_retention: float

    def score(self, *, loss_penalty: float = 10.0, invariant_penalty: float = 10.0) -> float:
        return (
            self.solve_cost
            + self.transform_cost
            + loss_penalty * self.roundtrip_loss
            + invariant_penalty * (1.0 - self.invariant_retention)
        )


@dataclass(frozen=True, slots=True)
class ArbitrageDecision:
    selected: RepresentationRoute
    eligible_routes: tuple[str, ...]
    rejected_routes: tuple[str, ...]
    score: float


def representation_arbitrage(
    routes: Sequence[RepresentationRoute],
    *,
    max_roundtrip_loss: float = 0.05,
    min_invariant_retention: float = 0.95,
) -> ArbitrageDecision:
    """Select the lowest-cost route that passes explicit fidelity gates."""

    eligible = tuple(
        route
        for route in routes
        if route.roundtrip_loss <= max_roundtrip_loss
        and route.invariant_retention >= min_invariant_retention
    )
    if not eligible:
        raise ValueError("no representation route passes the fidelity gates")
    selected = min(eligible, key=lambda route: (route.score(), route.route_id))
    eligible_ids = tuple(route.route_id for route in eligible)
    rejected_ids = tuple(route.route_id for route in routes if route not in eligible)
    return ArbitrageDecision(selected, eligible_ids, rejected_ids, selected.score())


@dataclass(frozen=True, slots=True)
class UnknownUnknownSignal:
    x: float
    disagreement: float
    residual_surprise: float
    representation_instability: float
    coverage_gap: float
    score: float
    oak_boundary: str = "heuristic candidate signal; not evidence that an unknown unknown exists"


def unknown_unknown_radar(
    points: Sequence[float],
    theories: Sequence[TheoryGenome],
    observer: Callable[[float], float],
    *,
    representation_instability: Mapping[float, float] | None = None,
    coverage: Mapping[float, float] | None = None,
) -> tuple[UnknownUnknownSignal, ...]:
    """Rank locations where several declared weakness signals coincide."""

    if not points:
        return ()
    representation_instability = representation_instability or {}
    coverage = coverage or {}
    raw: list[tuple[float, float, float, float, float]] = []
    for raw_x in points:
        x = float(raw_x)
        disagreement = disagreement_utility(theories, x)
        residual = min(abs(theory.predict(x) - observer(x)) for theory in theories)
        instability = max(0.0, float(representation_instability.get(x, 0.0)))
        coverage_gap = 1.0 - min(1.0, max(0.0, float(coverage.get(x, 0.0))))
        raw.append((x, disagreement, residual, instability, coverage_gap))

    maxima = [max(item[i] for item in raw) for i in range(1, 5)]

    def norm(value: float, maximum: float) -> float:
        return value / maximum if maximum > 0.0 else 0.0

    signals = []
    for x, disagreement, residual, instability, coverage_gap in raw:
        components = (
            norm(disagreement, maxima[0]),
            norm(residual, maxima[1]),
            norm(instability, maxima[2]),
            norm(coverage_gap, maxima[3]),
        )
        score = sum(components) / len(components)
        signals.append(
            UnknownUnknownSignal(x, disagreement, residual, instability, coverage_gap, score)
        )
    return tuple(sorted(signals, key=lambda signal: (-signal.score, signal.x)))


@dataclass(frozen=True, slots=True)
class InvariantTransportMap:
    source_domain: str
    target_domain: str
    mapping: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class InvariantTransportReport:
    source_domain: str
    target_domain: str
    transported: tuple[str, ...]
    missing: tuple[str, ...]
    certified_for_declared_map: bool


def transport_invariants(
    invariants: Sequence[str],
    transport: InvariantTransportMap,
) -> InvariantTransportReport:
    lookup = dict(transport.mapping)
    transported = tuple(lookup[item] for item in invariants if item in lookup)
    missing = tuple(item for item in invariants if item not in lookup)
    return InvariantTransportReport(
        transport.source_domain,
        transport.target_domain,
        transported,
        missing,
        not missing,
    )


@dataclass(frozen=True, slots=True)
class DiscoveryDynamicsReport:
    scientific_ir_valid: bool
    scientific_ir_errors: tuple[str, ...]
    jacobian: EpistemicJacobianReport
    residual_genome: ResidualGenome
    counterexample: CounterexampleCandidate
    arbitrage: ArbitrageDecision
    radar: tuple[UnknownUnknownSignal, ...]
    transport: InvariantTransportReport


def run_discovery_dynamics_demo() -> DiscoveryDynamicsReport:
    """Deterministic cross-primitive R0.2 fixture used by CI and documentation."""

    problem = build_fixture()
    linear, quadratic = problem.theories
    adapter = TheoryAdapter(linear)
    ir = ScientificIR(
        object_id="T_linear",
        variables=("x", "y"),
        relations=("y=x",),
        units=(("x", "arb"), ("y", "arb")),
        assumptions=linear.assumptions,
        observables=("y",),
        domain=linear.domain,
        tests=linear.falsifiers,
        provenance="fixture:MetaScienceBench-T:R0.2",
    )
    jacobian = epistemic_jacobian(problem.theories, 2.0)
    xs = (0.5, 1.0, 1.5, 2.0)
    residuals = tuple(quadratic.predict(x) - linear.predict(x) for x in xs)
    residual_genome = compile_residual_genome(residuals)
    counterexample = compile_counterexample(adapter, quadratic.predict, (0.0, 1.0, 2.0, 3.0))
    routes = (
        RepresentationRoute("native", solve_cost=10.0, transform_cost=0.0, roundtrip_loss=0.0, invariant_retention=1.0),
        RepresentationRoute("transformed", solve_cost=2.0, transform_cost=1.0, roundtrip_loss=0.01, invariant_retention=0.99),
        RepresentationRoute("lossy-fast", solve_cost=0.1, transform_cost=0.1, roundtrip_loss=0.20, invariant_retention=0.70),
    )
    arbitrage = representation_arbitrage(routes)
    radar = unknown_unknown_radar(
        (0.0, 1.0, 2.0, 3.0),
        problem.theories,
        quadratic.predict,
        representation_instability={0.0: 0.0, 1.0: 0.0, 2.0: 0.2, 3.0: 1.0},
        coverage={0.0: 1.0, 1.0: 1.0, 2.0: 0.5, 3.0: 0.0},
    )
    transport = transport_invariants(
        ("observable:y", "domain:x>=0"),
        InvariantTransportMap(
            "toy-polynomial",
            "generic-response",
            (
                ("observable:y", "observable:response"),
                ("domain:x>=0", "domain:nonnegative-input"),
            ),
        ),
    )
    errors = ir.validate()
    return DiscoveryDynamicsReport(
        scientific_ir_valid=not errors,
        scientific_ir_errors=errors,
        jacobian=jacobian,
        residual_genome=residual_genome,
        counterexample=counterexample,
        arbitrage=arbitrage,
        radar=radar,
        transport=transport,
    )


def discovery_report_as_dict(report: DiscoveryDynamicsReport) -> dict[str, object]:
    return asdict(report)
