"""Core empirical complexity atlas.

The module intentionally uses only the Python standard library so the first
prototype can run in the repository without introducing a dependency surface.
It supports multivariate polynomial/log feature discovery, finite-domain model
certificates, local log-elasticities, interaction Hessians and simple regime
boundary detection.

OAK rule
--------
An :class:`EmpiricalResourceModel` describes observed finite-domain behaviour.
It MUST NOT be promoted to a mathematical Big-O/Theta theorem without a
separate algorithmic or formal proof.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from itertools import product
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


_EPS = 1e-15


@dataclass(frozen=True)
class ResourceSample:
    """One measured execution point.

    ``variables`` contains the explanatory state vector (sizes, sparsity,
    batch, etc.). ``resources`` contains measured outputs (wall time, memory,
    energy proxies, quality, ...). Metadata is deliberately free-form so a
    machine/software/provenance fingerprint can accompany every observation.
    """

    variables: Mapping[str, float]
    resources: Mapping[str, float]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.variables:
            raise ValueError("a ResourceSample needs at least one variable")
        if not self.resources:
            raise ValueError("a ResourceSample needs at least one resource")
        for namespace, values in (("variables", self.variables), ("resources", self.resources)):
            for name, value in values.items():
                if not math.isfinite(float(value)):
                    raise ValueError(f"{namespace}.{name} must be finite")


@dataclass(frozen=True)
class FeatureSpec:
    """Serializable symbolic basis term used by an empirical law."""

    kind: str
    variables: tuple[str, ...] = ()
    powers: tuple[int, ...] = ()

    @property
    def label(self) -> str:
        if self.kind == "constant":
            return "1"
        if self.kind == "log":
            return f"log({self.variables[0]})"
        if self.kind == "xlogx":
            v = self.variables[0]
            return f"{v}*log({v})"
        if self.kind == "monomial":
            parts: list[str] = []
            for variable, power in zip(self.variables, self.powers):
                if power == 0:
                    continue
                parts.append(variable if power == 1 else f"{variable}^{power}")
            return "*".join(parts) or "1"
        raise ValueError(f"unsupported feature kind: {self.kind}")

    def evaluate(self, point: Mapping[str, float]) -> float:
        if self.kind == "constant":
            return 1.0
        if self.kind == "monomial":
            value = 1.0
            for variable, power in zip(self.variables, self.powers):
                value *= float(point[variable]) ** power
            return value
        variable = self.variables[0]
        x = float(point[variable])
        if x <= 0:
            raise ValueError(f"{self.kind} feature requires {variable} > 0")
        if self.kind == "log":
            return math.log(x)
        if self.kind == "xlogx":
            return x * math.log(x)
        raise ValueError(f"unsupported feature kind: {self.kind}")


def generate_feature_library(
    variable_names: Sequence[str],
    *,
    max_total_degree: int = 2,
    include_logs: bool = True,
    include_xlogx: bool = True,
    max_features: int = 256,
) -> list[FeatureSpec]:
    """Generate a bounded symbolic candidate library.

    The polynomial part contains all monomials whose total degree is in
    ``[1, max_total_degree]``. Optional log and x*log(x) terms cover two common
    non-polynomial scaling families. The hard feature cap prevents accidental
    combinatorial benchmark/model explosions.
    """

    names = tuple(variable_names)
    if not names:
        raise ValueError("variable_names cannot be empty")
    if max_total_degree < 1:
        raise ValueError("max_total_degree must be >= 1")

    features = [FeatureSpec("constant")]
    for powers in product(range(max_total_degree + 1), repeat=len(names)):
        degree = sum(powers)
        if 1 <= degree <= max_total_degree:
            features.append(FeatureSpec("monomial", names, tuple(powers)))

    if include_logs:
        features.extend(FeatureSpec("log", (name,)) for name in names)
    if include_xlogx:
        features.extend(FeatureSpec("xlogx", (name,)) for name in names)

    # Stable order makes certificates and diffs reproducible.
    features = [features[0]] + sorted(features[1:], key=lambda f: (f.kind, f.label))
    if len(features) > max_features:
        raise ValueError(
            f"candidate feature library has {len(features)} terms; "
            f"raise max_features explicitly above {max_features} if intentional"
        )
    return features


def _solve_linear_system(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Gauss-Jordan solve with partial pivoting for small prototype systems."""

    n = len(rhs)
    augmented = [row[:] + [rhs_value] for row, rhs_value in zip(matrix, rhs)]
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) <= _EPS:
            # Ridge regularisation should normally prevent this. Returning a
            # deterministic zero coefficient is safer than amplifying noise.
            augmented[pivot][column] = _EPS
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(n):
            if row == column:
                continue
            factor = augmented[row][column]
            if abs(factor) <= _EPS:
                continue
            augmented[row] = [
                a - factor * b
                for a, b in zip(augmented[row], augmented[column])
            ]
    return [augmented[row][-1] for row in range(n)]


def _ridge_least_squares(
    x_rows: Sequence[Sequence[float]],
    y: Sequence[float],
    *,
    ridge: float,
) -> list[float]:
    if not x_rows:
        raise ValueError("no design rows")
    p = len(x_rows[0])
    xtx = [[0.0 for _ in range(p)] for _ in range(p)]
    xty = [0.0 for _ in range(p)]
    for row, target in zip(x_rows, y):
        for i in range(p):
            xty[i] += row[i] * target
            for j in range(p):
                xtx[i][j] += row[i] * row[j]
    for i in range(p):
        # Scale the tiny stabilizer to the observed column energy. We avoid
        # penalising the intercept more strongly than necessary.
        scale = max(abs(xtx[i][i]), 1.0)
        xtx[i][i] += ridge * scale
    return _solve_linear_system(xtx, xty)


@dataclass
class EmpiricalResourceModel:
    """Finite-domain empirical law and its OAK certificate."""

    target: str
    variables: tuple[str, ...]
    features: tuple[FeatureSpec, ...]
    coefficients: tuple[float, ...]
    n_samples: int
    domain: Mapping[str, tuple[float, float]]
    rmse: float
    r2: float
    ridge: float
    status: str = "empirical-fit"
    epistemic_level: str = "L2-out-of-sample-not-yet-a-proof"

    def predict(self, point: Mapping[str, float]) -> float:
        missing = [name for name in self.variables if name not in point]
        if missing:
            raise KeyError(f"missing model variables: {missing}")
        return sum(
            coefficient * feature.evaluate(point)
            for coefficient, feature in zip(self.coefficients, self.features)
        )

    def equation(self, *, coefficient_digits: int = 6, threshold: float = 1e-12) -> str:
        terms: list[str] = []
        for coefficient, feature in zip(self.coefficients, self.features):
            if abs(coefficient) <= threshold:
                continue
            terms.append(f"{coefficient:.{coefficient_digits}g}*{feature.label}")
        return f"{self.target} ~= " + (" + ".join(terms) if terms else "0")

    def in_domain(self, point: Mapping[str, float]) -> bool:
        return all(
            low <= float(point[name]) <= high
            for name, (low, high) in self.domain.items()
            if name in point
        )

    def certificate(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "status": self.status,
            "epistemic_level": self.epistemic_level,
            "equation": self.equation(),
            "variables": list(self.variables),
            "domain": {k: list(v) for k, v in self.domain.items()},
            "n_samples": self.n_samples,
            "rmse": self.rmse,
            "r2": self.r2,
            "ridge": self.ridge,
            "oak_warning": (
                "Finite-domain empirical scaling only; this certificate does not "
                "establish asymptotic Big-O/Theta complexity."
            ),
        }


def fit_resource_model(
    samples: Sequence[ResourceSample],
    target: str,
    *,
    max_total_degree: int = 2,
    include_logs: bool = True,
    include_xlogx: bool = True,
    ridge: float = 1e-10,
    max_features: int = 256,
) -> EmpiricalResourceModel:
    """Fit one resource surface over a common multivariate state vector."""

    if len(samples) < 2:
        raise ValueError("at least two samples are required")
    variables = tuple(sorted(samples[0].variables))
    for sample in samples:
        if tuple(sorted(sample.variables)) != variables:
            raise ValueError("all samples must expose the same variable names")
        if target not in sample.resources:
            raise KeyError(f"resource target {target!r} missing from a sample")

    features = generate_feature_library(
        variables,
        max_total_degree=max_total_degree,
        include_logs=include_logs,
        include_xlogx=include_xlogx,
        max_features=max_features,
    )
    if any(float(sample.variables[name]) <= 0 for sample in samples for name in variables):
        # Polynomial laws still work for zero-valued variables; remove only the
        # transforms that are undefined on the measured domain.
        features = [f for f in features if f.kind not in {"log", "xlogx"}]

    x_rows = [[feature.evaluate(sample.variables) for feature in features] for sample in samples]
    y = [float(sample.resources[target]) for sample in samples]
    coefficients = _ridge_least_squares(x_rows, y, ridge=ridge)
    predictions = [sum(c * x for c, x in zip(coefficients, row)) for row in x_rows]
    residuals = [actual - predicted for actual, predicted in zip(y, predictions)]
    mse = sum(value * value for value in residuals) / len(residuals)
    mean_y = sum(y) / len(y)
    ss_tot = sum((value - mean_y) ** 2 for value in y)
    ss_res = sum(value * value for value in residuals)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > _EPS else (1.0 if ss_res <= _EPS else 0.0)
    domain = {
        name: (
            min(float(sample.variables[name]) for sample in samples),
            max(float(sample.variables[name]) for sample in samples),
        )
        for name in variables
    }
    return EmpiricalResourceModel(
        target=target,
        variables=variables,
        features=tuple(features),
        coefficients=tuple(coefficients),
        n_samples=len(samples),
        domain=domain,
        rmse=math.sqrt(mse),
        r2=r2,
        ridge=ridge,
    )


class ComplexityAtlas:
    """Living collection of measurements, empirical laws and local geometry."""

    schema_version = "omega-compute-physics-atlas/v0.1"

    def __init__(
        self,
        *,
        name: str = "atlas",
        machine: Mapping[str, Any] | None = None,
        software: Mapping[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.machine = dict(machine or {})
        self.software = dict(software or {})
        self.samples: list[ResourceSample] = []
        self.models: dict[str, EmpiricalResourceModel] = {}

    def add_sample(self, sample: ResourceSample) -> None:
        self.samples.append(sample)

    def extend(self, samples: Iterable[ResourceSample]) -> None:
        self.samples.extend(samples)

    def fit(
        self,
        target: str,
        *,
        max_total_degree: int = 2,
        include_logs: bool = True,
        include_xlogx: bool = True,
        ridge: float = 1e-10,
        max_features: int = 256,
    ) -> EmpiricalResourceModel:
        model = fit_resource_model(
            self.samples,
            target,
            max_total_degree=max_total_degree,
            include_logs=include_logs,
            include_xlogx=include_xlogx,
            ridge=ridge,
            max_features=max_features,
        )
        self.models[target] = model
        return model

    def predict(self, target: str, point: Mapping[str, float]) -> float:
        return self.models[target].predict(point)

    def elasticity(
        self,
        target: str,
        point: Mapping[str, float],
        *,
        relative_step: float = 1e-4,
    ) -> dict[str, float]:
        """Return local d log(resource) / d log(variable) exponents."""

        model = self.models[target]
        result: dict[str, float] = {}
        factor = 1.0 + relative_step
        if factor <= 1.0:
            raise ValueError("relative_step must be positive")
        for variable in model.variables:
            x = float(point[variable])
            if x <= 0:
                raise ValueError("elasticity requires strictly positive coordinates")
            plus = dict(point)
            minus = dict(point)
            plus[variable] = x * factor
            minus[variable] = x / factor
            y_plus = model.predict(plus)
            y_minus = model.predict(minus)
            if y_plus <= 0 or y_minus <= 0:
                raise ValueError("log-elasticity requires positive model predictions")
            result[variable] = (
                math.log(y_plus) - math.log(y_minus)
            ) / (
                math.log(plus[variable]) - math.log(minus[variable])
            )
        return result

    def interaction_hessian(
        self,
        target: str,
        point: Mapping[str, float],
        *,
        relative_step: float = 5e-4,
    ) -> dict[str, dict[str, float]]:
        """Finite-difference Hessian of log-resource in log-coordinate space."""

        model = self.models[target]
        factor = 1.0 + relative_step
        result: dict[str, dict[str, float]] = {name: {} for name in model.variables}
        for j in model.variables:
            x = float(point[j])
            if x <= 0:
                raise ValueError("interaction Hessian requires positive coordinates")
            plus = dict(point)
            minus = dict(point)
            plus[j] = x * factor
            minus[j] = x / factor
            e_plus = self.elasticity(target, plus, relative_step=relative_step)
            e_minus = self.elasticity(target, minus, relative_step=relative_step)
            denominator = math.log(plus[j]) - math.log(minus[j])
            for i in model.variables:
                result[i][j] = (e_plus[i] - e_minus[i]) / denominator
        return result

    def path_scaling_exponent(
        self,
        target: str,
        point: Mapping[str, float],
        direction: Mapping[str, float],
    ) -> float:
        """Directional scaling exponent for x_i -> lambda**u_i * x_i."""

        elasticity = self.elasticity(target, point)
        return sum(elasticity[name] * float(direction.get(name, 0.0)) for name in elasticity)

    def phase_boundaries(
        self,
        variable: str,
        target: str,
        *,
        jump_threshold: float = 0.5,
    ) -> list[dict[str, float]]:
        """Detect simple 1-D empirical scaling-regime changes.

        Samples are sorted by one coordinate and adjacent log-log slopes are
        compared. For multi-dimensional campaigns this should be applied to a
        controlled slice; the function deliberately labels its output
        ``empirical`` rather than claiming a hardware/algorithmic cause.
        """

        points = sorted(
            (
                float(sample.variables[variable]),
                float(sample.resources[target]),
            )
            for sample in self.samples
            if variable in sample.variables
            and target in sample.resources
            and float(sample.variables[variable]) > 0
            and float(sample.resources[target]) > 0
        )
        if len(points) < 3:
            return []
        slopes: list[float] = []
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            if x1 == x0:
                slopes.append(float("nan"))
                continue
            slopes.append((math.log(y1) - math.log(y0)) / (math.log(x1) - math.log(x0)))
        boundaries: list[dict[str, float]] = []
        for index in range(1, len(slopes)):
            before, after = slopes[index - 1], slopes[index]
            if not (math.isfinite(before) and math.isfinite(after)):
                continue
            jump = abs(after - before)
            if jump >= jump_threshold:
                x_left, _ = points[index]
                x_right, _ = points[index + 1]
                boundaries.append(
                    {
                        "location": math.sqrt(x_left * x_right),
                        "slope_before": before,
                        "slope_after": after,
                        "jump": jump,
                        "status": "empirical-regime-candidate",
                    }
                )
        return boundaries

    def resource_contract(
        self,
        point: Mapping[str, float],
        bounds: Mapping[str, float],
    ) -> dict[str, Any]:
        predictions = {target: self.predict(target, point) for target in bounds}
        checks = {target: predictions[target] <= float(limit) for target, limit in bounds.items()}
        return {
            "point": dict(point),
            "predictions": predictions,
            "bounds": dict(bounds),
            "checks": checks,
            "passes": all(checks.values()),
            "oak_warning": "Contract is model-conditioned and valid only within its certified domain.",
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema_version,
            "name": self.name,
            "machine": self.machine,
            "software": self.software,
            "samples": [
                {
                    "variables": dict(sample.variables),
                    "resources": dict(sample.resources),
                    "metadata": dict(sample.metadata),
                }
                for sample in self.samples
            ],
            "models": {
                name: {
                    **model.certificate(),
                    "features": [
                        {
                            "kind": feature.kind,
                            "variables": list(feature.variables),
                            "powers": list(feature.powers),
                            "label": feature.label,
                        }
                        for feature in model.features
                    ],
                    "coefficients": list(model.coefficients),
                }
                for name, model in self.models.items()
            },
        }

    def write_json(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return destination
