"""Deterministic finite falsification and minimized M-minus records."""
from __future__ import annotations

from hashlib import sha256
from typing import Mapping
import numpy as np

from .assumptions import Assumption, AssumptionKind, audit_assumptions
from .expressions import ExprError, relative_residual
from .models import Counterexample, EvidenceState, IdentityInstance, IdentitySchema, IdentityTestReport

TRIAL_COUNTS = {
    "smoke": 4,
    "standard": 16,
    "deep": 64,
    "adversarial": 96,
    "sparse": 32,
    "spectral": 48,
}


def _random_matrix(
    dimension: int,
    scalar_system: str,
    family: str,
    generator: np.random.Generator,
) -> np.ndarray:
    complex_mode = scalar_system == "complex"

    def dense() -> np.ndarray:
        value = generator.normal(size=(dimension, dimension))
        if complex_mode:
            value = value + 1j * generator.normal(size=(dimension, dimension))
        return value.astype(np.complex128)

    if family in {"dense", "noncommuting"}:
        return dense()
    if family in {"diagonal", "commuting"}:
        diagonal = generator.normal(size=dimension)
        if complex_mode:
            diagonal = diagonal + 1j * generator.normal(size=dimension)
        return np.diag(diagonal)
    if family == "symmetric":
        value = dense()
        return 0.5 * (value + value.T)
    if family == "hermitian":
        value = dense()
        return 0.5 * (value + value.conj().T)
    if family in {"orthogonal", "unitary"}:
        value = dense()
        if family == "orthogonal":
            value = value.real
        q, r = np.linalg.qr(value)
        diagonal = np.diag(r)
        phases = np.ones_like(diagonal, dtype=np.complex128)
        nonzero = np.abs(diagonal) > np.finfo(float).eps
        phases[nonzero] = diagonal[nonzero] / np.abs(diagonal[nonzero])
        return (q @ np.diag(np.conj(phases))).astype(np.complex128)
    if family == "projection":
        q, _ = np.linalg.qr(dense())
        rank = max(1, dimension // 2)
        basis = q[:, :rank]
        return basis @ basis.conj().T
    if family == "involution":
        q, _ = np.linalg.qr(dense())
        signs = np.where(np.arange(dimension) % 2 == 0, 1.0, -1.0)
        return q @ np.diag(signs) @ q.conj().T
    if family == "singular":
        value = dense()
        value[-1] = value[0]
        return value
    if family == "ill_conditioned":
        q, _ = np.linalg.qr(dense())
        values = np.logspace(0.0, -12.0, dimension)
        return q @ np.diag(values) @ q.conj().T
    if family == "nilpotent":
        return np.triu(dense(), 1)
    if family == "jordan":
        value = np.eye(dimension, dtype=np.complex128)
        for index in range(dimension - 1):
            value[index, index + 1] = 1.0
        return value
    raise ValueError(f"unknown matrix family {family!r}")


def _unitary(dimension: int, complex_mode: bool, rng: np.random.Generator) -> np.ndarray:
    family = "unitary" if complex_mode else "orthogonal"
    return _random_matrix(dimension, "complex" if complex_mode else "real", family, rng)


def _enforce_single(
    matrix: np.ndarray,
    kind: AssumptionKind,
    rng: np.random.Generator,
    scalar_system: str,
) -> np.ndarray:
    dimension = matrix.shape[0]
    if kind == AssumptionKind.SQUARE:
        return matrix
    if kind == AssumptionKind.SYMMETRIC:
        return 0.5 * (matrix + matrix.T)
    if kind == AssumptionKind.SKEW_SYMMETRIC:
        return 0.5 * (matrix - matrix.T)
    if kind == AssumptionKind.HERMITIAN:
        return 0.5 * (matrix + matrix.conj().T)
    if kind == AssumptionKind.UNITARY:
        return _unitary(dimension, True, rng)
    if kind == AssumptionKind.ORTHOGONAL:
        return _unitary(dimension, False, rng)
    if kind == AssumptionKind.PROJECTION:
        q = _unitary(dimension, scalar_system == "complex", rng)
        rank = max(1, dimension // 2)
        return q[:, :rank] @ q[:, :rank].conj().T
    if kind == AssumptionKind.INVOLUTION:
        q = _unitary(dimension, scalar_system == "complex", rng)
        signs = np.where(np.arange(dimension) % 2 == 0, 1.0, -1.0)
        return q @ np.diag(signs) @ q.conj().T
    if kind == AssumptionKind.INVERTIBLE:
        singular = np.linalg.svd(matrix, compute_uv=False)
        if singular.size == 0 or singular[-1] < 1e-6:
            return matrix + (1.0 + np.linalg.norm(matrix)) * np.eye(dimension)
        return matrix
    if kind == AssumptionKind.NORMAL:
        q = _unitary(dimension, scalar_system == "complex", rng)
        diagonal = rng.normal(size=dimension)
        if scalar_system == "complex":
            diagonal = diagonal + 1j * rng.normal(size=dimension)
        return q @ np.diag(diagonal) @ q.conj().T
    if kind == AssumptionKind.POSITIVE_SEMIDEFINITE:
        value = 0.5 * (matrix + matrix.conj().T)
        eigenvalues, vectors = np.linalg.eigh(value)
        return vectors @ np.diag(np.maximum(eigenvalues, 0.0)) @ vectors.conj().T
    return matrix


def generate_environment(
    schema: IdentitySchema,
    assumptions: tuple[Assumption, ...],
    *,
    dimension: int,
    scalar_system: str,
    matrix_family: str,
    seed: int,
) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    environment = {
        name: _random_matrix(dimension, scalar_system, matrix_family, rng)
        for name in schema.variables
    }
    priority = {
        AssumptionKind.PROJECTION: 0,
        AssumptionKind.UNITARY: 0,
        AssumptionKind.ORTHOGONAL: 0,
        AssumptionKind.INVOLUTION: 0,
        AssumptionKind.NORMAL: 1,
        AssumptionKind.HERMITIAN: 2,
        AssumptionKind.SYMMETRIC: 2,
        AssumptionKind.SKEW_SYMMETRIC: 2,
        AssumptionKind.POSITIVE_SEMIDEFINITE: 3,
        AssumptionKind.SQUARE: 4,
        AssumptionKind.INVERTIBLE: 5,
        AssumptionKind.COMMUTING: 6,
    }
    for assumption in sorted(assumptions, key=lambda x: priority[x.kind]):
        if assumption.kind != AssumptionKind.COMMUTING:
            target = assumption.targets[0]
            environment[target] = _enforce_single(
                environment[target], assumption.kind, rng, scalar_system
            )
    for assumption in assumptions:
        if assumption.kind == AssumptionKind.COMMUTING:
            left, right = assumption.targets
            q = _unitary(dimension, scalar_system == "complex", rng)
            first = rng.normal(size=dimension)
            second = rng.normal(size=dimension)
            if scalar_system == "complex":
                first = first + 1j * rng.normal(size=dimension)
                second = second + 1j * rng.normal(size=dimension)
            environment[left] = q @ np.diag(first) @ q.conj().T
            environment[right] = q @ np.diag(second) @ q.conj().T
    return environment


def _serialize_matrix(matrix: np.ndarray) -> tuple[tuple[dict[str, float], ...], ...]:
    return tuple(
        tuple({"real": float(value.real), "imag": float(value.imag)} for value in row)
        for row in matrix
    )


def _counterexample_id(schema_id: str, environment: Mapping[str, np.ndarray], residual: float) -> str:
    payload = [schema_id, f"{residual:.17g}"]
    for name in sorted(environment):
        payload.append(name)
        payload.append(np.asarray(environment[name]).tobytes().hex())
    return "mminus-" + sha256("|".join(payload).encode()).hexdigest()[:24]


def _minimize(
    schema: IdentitySchema,
    assumptions: tuple[Assumption, ...],
    environment: dict[str, np.ndarray],
    threshold: float,
) -> tuple[dict[str, np.ndarray], int, float, float]:
    current = {name: value.copy() for name, value in environment.items()}
    steps = 0
    absolute, relative = relative_residual(schema.lhs, schema.rhs, current)
    for name in sorted(current):
        rows, columns = current[name].shape
        for row in range(rows):
            for column in range(columns):
                old = current[name][row, column]
                if old == 0:
                    continue
                current[name][row, column] = 0.0
                assumptions_ok, _ = audit_assumptions(assumptions, current)
                try:
                    candidate_abs, candidate_rel = relative_residual(schema.lhs, schema.rhs, current)
                except ExprError:
                    assumptions_ok = False
                    candidate_abs, candidate_rel = absolute, relative
                if assumptions_ok and candidate_rel > threshold:
                    absolute, relative = candidate_abs, candidate_rel
                    steps += 1
                else:
                    current[name][row, column] = old
    return current, steps, absolute, relative


def test_identity(
    schema: IdentitySchema,
    instance: IdentityInstance,
    *,
    seed: int = 0,
    trials: int | None = None,
    tolerance: float = 1e-8,
    minimize: bool = True,
) -> IdentityTestReport:
    profile = instance.address.trial_profile
    requested = TRIAL_COUNTS[profile] if trials is None else int(trials)
    if requested < 1 or tolerance <= 0:
        raise ValueError("trials and tolerance must be positive")
    maximum_absolute = 0.0
    maximum_relative = 0.0
    errors: list[str] = []
    completed = 0

    for trial in range(requested):
        trial_seed = seed + trial * 104729
        environment = generate_environment(
            schema,
            instance.assumptions,
            dimension=instance.address.dimension,
            scalar_system=instance.address.scalar_system,
            matrix_family=instance.address.matrix_family,
            seed=trial_seed,
        )
        assumptions_ok, audit = audit_assumptions(instance.assumptions, environment)
        if not assumptions_ok:
            errors.append(f"trial {trial}: generated fixture failed assumptions")
            continue
        try:
            absolute, relative = relative_residual(schema.lhs, schema.rhs, environment)
        except ExprError as exc:
            errors.append(f"trial {trial}: {exc}")
            continue
        completed += 1
        maximum_absolute = max(maximum_absolute, absolute)
        maximum_relative = max(maximum_relative, relative)
        if relative > tolerance:
            minimized = environment
            steps = 0
            if minimize:
                minimized, steps, absolute, relative = _minimize(
                    schema, instance.assumptions, environment, tolerance
                )
                _, audit = audit_assumptions(instance.assumptions, minimized)
            counterexample = Counterexample(
                counterexample_id=_counterexample_id(schema.schema_id, minimized, relative),
                schema_id=schema.schema_id,
                dimension=instance.address.dimension,
                scalar_system=instance.address.scalar_system,
                environment={name: _serialize_matrix(value) for name, value in sorted(minimized.items())},
                absolute_residual=absolute,
                relative_residual=relative,
                assumption_audit=audit,
                seed=trial_seed,
                trial=trial,
                minimization_steps=steps,
            )
            return IdentityTestReport(
                schema_id=schema.schema_id,
                passed=False,
                trials_requested=requested,
                trials_completed=completed,
                maximum_absolute_residual=max(maximum_absolute, absolute),
                maximum_relative_residual=max(maximum_relative, relative),
                counterexample=counterexample,
                state=EvidenceState.FALSIFIED,
                errors=tuple(errors),
            )

    passed = completed == requested and maximum_relative <= tolerance
    return IdentityTestReport(
        schema_id=schema.schema_id,
        passed=passed,
        trials_requested=requested,
        trials_completed=completed,
        maximum_absolute_residual=maximum_absolute,
        maximum_relative_residual=maximum_relative,
        state=EvidenceState.NUMERICALLY_SUPPORTED if passed else EvidenceState.TYPE_CHECKED,
        errors=tuple(errors),
    )


# Prevent pytest from collecting this library function when imported into tests.
test_identity.__test__ = False
