"""Deterministic, bounded and claim-safe Counterexample Superfactory."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import prod
from pathlib import Path
import sqlite3
import tempfile
from typing import Callable, Iterator, Mapping

import numpy as np

from .models import (
    CounterexampleRecord,
    MatrixWitness,
    MinimizationTrace,
    RepairProposal,
    SearchPlan,
    SearchReport,
    SearchState,
    make_record_id,
    matrix_to_payload,
)


FAMILIES = (
    "dense", "diagonal", "symmetric", "skew_symmetric", "hermitian",
    "unitary", "orthogonal", "projection", "involution", "singular",
    "rank_one", "ill_conditioned", "nilpotent", "jordan", "toeplitz",
    "circulant", "permutation", "sparse_event",
)
STRATEGIES = (
    "random", "small_integer", "spectral", "sparse", "ill_conditioned",
    "non_normal", "boundary", "mutation_guided",
)
MINIMIZERS = ("none", "zero", "principal", "quantize", "principal_zero", "full_pipeline")
TRIAL_PROFILES = (4, 8, 16, 32, 64, 96)
CONJECTURES = tuple(f"identity-{index:03d}" for index in range(1, 65))
DIMENSIONS = tuple(range(1, 33))
SCALAR_SYSTEMS = ("real", "complex")
SEEDS = tuple(range(128))


def _dense(n: int, complex_mode: bool, rng: np.random.Generator) -> np.ndarray:
    value = rng.normal(size=(n, n))
    if complex_mode:
        value = value + 1j * rng.normal(size=(n, n))
    return value.astype(np.complex128)


def _unitary(n: int, complex_mode: bool, rng: np.random.Generator) -> np.ndarray:
    raw = _dense(n, complex_mode, rng)
    if not complex_mode:
        raw = raw.real
    q, r = np.linalg.qr(raw)
    diagonal = np.diag(r)
    phase = np.ones_like(diagonal, dtype=np.complex128)
    mask = np.abs(diagonal) > np.finfo(float).eps
    phase[mask] = diagonal[mask] / np.abs(diagonal[mask])
    return (q @ np.diag(np.conj(phase))).astype(np.complex128)


def generate_matrix(dimension: int, scalar_system: str, family: str, seed: int) -> np.ndarray:
    if dimension < 1:
        raise ValueError("dimension must be positive")
    if scalar_system not in SCALAR_SYSTEMS:
        raise ValueError("scalar_system must be real or complex")
    if family not in FAMILIES:
        raise ValueError(f"unknown family {family!r}")
    complex_mode = scalar_system == "complex"
    rng = np.random.default_rng(seed)
    if family == "dense":
        return _dense(dimension, complex_mode, rng)
    if family == "diagonal":
        values = rng.normal(size=dimension)
        if complex_mode:
            values = values + 1j * rng.normal(size=dimension)
        return np.diag(values).astype(np.complex128)
    if family == "symmetric":
        value = _dense(dimension, False, rng).real
        return (value + value.T).astype(np.complex128) / 2
    if family == "skew_symmetric":
        value = _dense(dimension, False, rng).real
        return (value - value.T).astype(np.complex128) / 2
    if family == "hermitian":
        value = _dense(dimension, complex_mode, rng)
        return (value + value.conj().T) / 2
    if family in {"unitary", "orthogonal"}:
        return _unitary(dimension, family == "unitary" and complex_mode, rng)
    if family == "projection":
        q = _unitary(dimension, complex_mode, rng)
        basis = q[:, : max(1, dimension // 2)]
        return basis @ basis.conj().T
    if family == "involution":
        q = _unitary(dimension, complex_mode, rng)
        signs = np.where(np.arange(dimension) % 2 == 0, 1.0, -1.0)
        return q @ np.diag(signs) @ q.conj().T
    if family == "singular":
        value = _dense(dimension, complex_mode, rng)
        if dimension == 1:
            return np.zeros((1, 1), dtype=np.complex128)
        value[-1] = value[0]
        return value
    if family == "rank_one":
        left = rng.normal(size=dimension)
        right = rng.normal(size=dimension)
        if complex_mode:
            left = left + 1j * rng.normal(size=dimension)
            right = right + 1j * rng.normal(size=dimension)
        return np.outer(left, np.conj(right)).astype(np.complex128)
    if family == "ill_conditioned":
        q = _unitary(dimension, complex_mode, rng)
        return q @ np.diag(np.logspace(0.0, -14.0, dimension)) @ q.conj().T
    if family == "nilpotent":
        value = np.zeros((dimension, dimension), dtype=np.complex128)
        for index in range(dimension - 1):
            value[index, index + 1] = 1
        return value
    if family == "jordan":
        value = np.eye(dimension, dtype=np.complex128)
        for index in range(dimension - 1):
            value[index, index + 1] = 1
        return value
    if family == "toeplitz":
        column = rng.normal(size=dimension)
        row = rng.normal(size=dimension)
        row[0] = column[0]
        if complex_mode:
            column = column + 1j * rng.normal(size=dimension)
            row = row + 1j * rng.normal(size=dimension)
            row[0] = column[0]
        return np.asarray(
            [[column[i-j] if i >= j else row[j-i] for j in range(dimension)] for i in range(dimension)],
            dtype=np.complex128,
        )
    if family == "circulant":
        first = rng.normal(size=dimension)
        if complex_mode:
            first = first + 1j * rng.normal(size=dimension)
        return np.asarray([np.roll(first, index) for index in range(dimension)], dtype=np.complex128)
    if family == "permutation":
        value = np.zeros((dimension, dimension), dtype=np.complex128)
        value[np.arange(dimension), rng.permutation(dimension)] = 1
        return value
    if family == "sparse_event":
        value = np.zeros((dimension, dimension), dtype=np.complex128)
        count = max(1, dimension // 3)
        rows = rng.integers(0, dimension, size=count)
        columns = rng.integers(0, dimension, size=count)
        amplitudes = rng.normal(size=count)
        if complex_mode:
            amplitudes = amplitudes + 1j * rng.normal(size=count)
        value[rows, columns] = amplitudes
        return value
    raise AssertionError("unreachable")


def generate_environment(
    variables: tuple[str, ...], dimension: int, scalar_system: str, family: str, seed: int
) -> dict[str, np.ndarray]:
    return {
        name: generate_matrix(dimension, scalar_system, family, seed + offset * 104729)
        for offset, name in enumerate(variables)
    }


def _nonzeros(environment: Mapping[str, np.ndarray]) -> int:
    return sum(int(np.count_nonzero(value)) for value in environment.values())


def _copy(environment: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    return {name: np.asarray(value, dtype=np.complex128).copy() for name, value in environment.items()}


def minimize_counterexample(
    environment: Mapping[str, np.ndarray],
    predicate: Callable[[Mapping[str, np.ndarray]], bool],
) -> tuple[dict[str, np.ndarray], MinimizationTrace]:
    current = _copy(environment)
    before_dimension = next(iter(current.values())).shape[0]
    before_nonzeros = _nonzeros(current)
    accepted: list[dict[str, object]] = []
    rejected = 0

    changed = True
    while changed and next(iter(current.values())).shape[0] > 1:
        changed = False
        n = next(iter(current.values())).shape[0]
        for index in range(n - 1, -1, -1):
            keep = [value for value in range(n) if value != index]
            candidate = {name: matrix[np.ix_(keep, keep)] for name, matrix in current.items()}
            if predicate(candidate):
                current = candidate
                accepted.append({"operation": "drop_principal_index", "index": index})
                changed = True
                break
            rejected += 1

    for name in sorted(current):
        rows, columns = current[name].shape
        for row in range(rows):
            for column in range(columns):
                old = current[name][row, column]
                if old == 0:
                    continue
                current[name][row, column] = 0
                if predicate(current):
                    accepted.append({"operation": "zero_entry", "matrix": name, "row": row, "column": column})
                else:
                    current[name][row, column] = old
                    rejected += 1

    simple_values = (0, 1, -1, 1j, -1j, 0.5, -0.5)
    for name in sorted(current):
        rows, columns = current[name].shape
        for row in range(rows):
            for column in range(columns):
                old = current[name][row, column]
                replaced = False
                for candidate_value in sorted(simple_values, key=lambda value: (abs(old-value), abs(value))):
                    if candidate_value == old:
                        continue
                    current[name][row, column] = candidate_value
                    if predicate(current):
                        accepted.append({
                            "operation": "quantize", "matrix": name, "row": row, "column": column,
                            "real": float(complex(candidate_value).real), "imag": float(complex(candidate_value).imag),
                        })
                        replaced = True
                        break
                if not replaced:
                    current[name][row, column] = old
                    rejected += 1

    after_dimension = next(iter(current.values())).shape[0]
    return current, MinimizationTrace(
        method="principal_zero_quantize",
        before_nonzeros=before_nonzeros,
        after_nonzeros=_nonzeros(current),
        before_dimension=before_dimension,
        after_dimension=after_dimension,
        accepted_steps=tuple(accepted),
        rejected_steps=rejected,
    )


def _relative(matrix: np.ndarray, target: np.ndarray) -> float:
    return float(np.linalg.norm(matrix-target)) / max(float(np.linalg.norm(matrix)), float(np.linalg.norm(target)), 1.0)


def propose_repairs(conjecture_id: str, environment: Mapping[str, np.ndarray]) -> tuple[RepairProposal, ...]:
    candidates: list[tuple[str, float, str]] = []
    for name, matrix in sorted(environment.items()):
        n, m = matrix.shape
        if n != m:
            continue
        identity = np.eye(n, dtype=np.complex128)
        properties = {
            "symmetric": _relative(matrix, matrix.T),
            "hermitian": _relative(matrix, matrix.conj().T),
            "normal": _relative(matrix @ matrix.conj().T, matrix.conj().T @ matrix),
            "projection": _relative(matrix @ matrix, matrix),
            "involution": _relative(matrix @ matrix, identity),
            "unitary": _relative(matrix.conj().T @ matrix, identity),
        }
        singular = np.linalg.svd(matrix, compute_uv=False)
        properties["invertible"] = 0.0 if singular.size and singular[-1] > 1e-10 else 1.0
        for property_name, residual in properties.items():
            if residual <= 1e-8:
                candidates.append((f"{property_name}({name})", residual, f"finite residual {residual:.3e}"))
    names = sorted(environment)
    for index, left_name in enumerate(names):
        for right_name in names[index+1:]:
            left, right = environment[left_name], environment[right_name]
            residual = _relative(left @ right, right @ left)
            if residual <= 1e-8:
                candidates.append((f"commuting({left_name},{right_name})", residual, f"commutator residual {residual:.3e}"))
    proposals = []
    for hypothesis, residual, rationale in sorted(candidates, key=lambda item: (item[1], item[0]))[:8]:
        proposal_id = "repair-" + sha256(f"{conjecture_id}|{hypothesis}|{residual:.17g}".encode()).hexdigest()[:20]
        proposals.append(RepairProposal(
            proposal_id=proposal_id,
            conjecture_id=conjecture_id,
            added_hypotheses=(hypothesis,),
            rationale=(rationale, "candidate repair requires independent re-testing"),
            confidence_label="medium" if residual <= 1e-12 else "low",
        ))
    return tuple(proposals)


ResidualFunction = Callable[[Mapping[str, np.ndarray]], tuple[float, float]]
AssumptionFunction = Callable[[Mapping[str, np.ndarray]], tuple[bool, tuple[Mapping[str, object], ...]]]


def search_counterexample(
    plan: SearchPlan,
    *,
    variables: tuple[str, ...],
    residual_fn: ResidualFunction,
    assumptions_fn: AssumptionFunction | None = None,
    minimize: bool = True,
) -> SearchReport:
    assumptions = assumptions_fn or (lambda environment: (True, ()))
    maximum = 0.0
    errors: list[str] = []

    def predicate(environment: Mapping[str, np.ndarray]) -> bool:
        try:
            assumptions_ok, _ = assumptions(environment)
            if not assumptions_ok:
                return False
            _, relative = residual_fn(environment)
            return bool(np.isfinite(relative) and relative > plan.tolerance)
        except Exception:
            return False

    for trial in range(plan.trials):
        seed = plan.seed + trial * 104729
        environment = generate_environment(variables, plan.dimension, plan.scalar_system, plan.family, seed)
        try:
            assumptions_ok, audit = assumptions(environment)
            if not assumptions_ok:
                errors.append(f"trial {trial}: fixture rejected by assumptions")
                continue
            absolute, relative = residual_fn(environment)
        except Exception as exc:
            errors.append(f"trial {trial}: {type(exc).__name__}: {exc}")
            continue
        if not np.isfinite(absolute) or not np.isfinite(relative):
            errors.append(f"trial {trial}: non-finite residual")
            continue
        maximum = max(maximum, float(relative))
        if relative <= plan.tolerance:
            continue
        trace = None
        minimized = environment
        if minimize:
            minimized, trace = minimize_counterexample(environment, predicate)
            absolute, relative = residual_fn(minimized)
            assumptions_ok, audit = assumptions(minimized)
        witness = MatrixWitness(
            matrices={name: matrix_to_payload(value) for name, value in sorted(minimized.items())},
            absolute_residual=float(absolute),
            relative_residual=float(relative),
            assumptions_passed=bool(assumptions_ok),
            assumption_audit=tuple(audit),
            provenance={"family": plan.family, "seed": seed, "trial": trial, "strategy": plan.strategy},
        )
        repairs = propose_repairs(plan.conjecture_id, minimized)
        state = SearchState.REPAIR_PROPOSED if repairs else (SearchState.MINIMIZED if trace else SearchState.COUNTEREXAMPLE_FOUND)
        record = CounterexampleRecord(
            record_id=make_record_id(plan.conjecture_id, plan.digest(), witness.digest()),
            conjecture_id=plan.conjecture_id,
            plan_digest=plan.digest(),
            state=state,
            witness=witness,
            minimization=trace,
            repairs=repairs,
            tags=(plan.family, plan.scalar_system, plan.strategy),
        )
        return SearchReport(plan, state, trial+1, max(maximum, float(relative)), record, tuple(errors))
    return SearchReport(plan, SearchState.SEARCHED_NO_WITNESS, plan.trials, maximum, None, tuple(errors))


def search_matrix_identity(
    plan: SearchPlan,
    *,
    variables: tuple[str, ...],
    lhs: Callable[[Mapping[str, np.ndarray]], np.ndarray],
    rhs: Callable[[Mapping[str, np.ndarray]], np.ndarray],
    assumptions_fn: AssumptionFunction | None = None,
    minimize: bool = True,
) -> SearchReport:
    def residual(environment: Mapping[str, np.ndarray]) -> tuple[float, float]:
        left = np.asarray(lhs(environment), dtype=np.complex128)
        right = np.asarray(rhs(environment), dtype=np.complex128)
        absolute = float(np.linalg.norm(left-right))
        return absolute, absolute / max(float(np.linalg.norm(left)), float(np.linalg.norm(right)), 1.0)
    return search_counterexample(
        plan, variables=variables, residual_fn=residual,
        assumptions_fn=assumptions_fn, minimize=minimize,
    )


def no_assumptions(environment: Mapping[str, np.ndarray]) -> tuple[bool, tuple[Mapping[str, object], ...]]:
    return True, ()


def projection_assumption(environment: Mapping[str, np.ndarray]) -> tuple[bool, tuple[Mapping[str, object], ...]]:
    matrix = environment["A"]
    residual = _relative(matrix @ matrix, matrix)
    return residual <= 1e-8, ({"kind": "projection", "targets": ["A"], "residual": residual},)


def invertible_assumption(environment: Mapping[str, np.ndarray]) -> tuple[bool, tuple[Mapping[str, object], ...]]:
    audit = []
    passed = True
    for name, matrix in sorted(environment.items()):
        singular = np.linalg.svd(matrix, compute_uv=False)
        ok = bool(singular.size and singular[-1] > 1e-10)
        audit.append({"kind": "invertible", "targets": [name], "residual": 0.0 if ok else 1.0})
        passed = passed and ok
    return passed, tuple(audit)


@dataclass(frozen=True)
class MatrixConjecture:
    conjecture_id: str
    variables: tuple[str, ...]
    lhs: Callable[[Mapping[str, np.ndarray]], np.ndarray]
    rhs: Callable[[Mapping[str, np.ndarray]], np.ndarray]
    assumptions: AssumptionFunction


BUILTINS = {
    "unconditional_commutativity": MatrixConjecture(
        "unconditional_commutativity", ("A", "B"),
        lambda env: env["A"] @ env["B"], lambda env: env["B"] @ env["A"], no_assumptions,
    ),
    "projection_idempotence": MatrixConjecture(
        "projection_idempotence", ("A",),
        lambda env: env["A"] @ env["A"], lambda env: env["A"], projection_assumption,
    ),
    "transpose_product": MatrixConjecture(
        "transpose_product", ("A", "B"),
        lambda env: (env["A"] @ env["B"]).T,
        lambda env: env["B"].T @ env["A"].T, no_assumptions,
    ),
    "adjoint_product": MatrixConjecture(
        "adjoint_product", ("A", "B"),
        lambda env: (env["A"] @ env["B"]).conj().T,
        lambda env: env["B"].conj().T @ env["A"].conj().T, no_assumptions,
    ),
    "inverse_product_reverse": MatrixConjecture(
        "inverse_product_reverse", ("A", "B"),
        lambda env: np.linalg.inv(env["A"] @ env["B"]),
        lambda env: np.linalg.inv(env["B"]) @ np.linalg.inv(env["A"]), invertible_assumption,
    ),
}


@dataclass(frozen=True)
class FrontierAddress:
    conjecture_id: str
    dimension: int
    scalar_system: str
    family: str
    strategy: str
    minimizer: str
    trials: int
    seed: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_plan(self) -> SearchPlan:
        return SearchPlan(
            self.conjecture_id, self.dimension, self.scalar_system, self.family,
            self.strategy, self.minimizer, self.seed, self.trials,
        )


class CounterexampleFrontier:
    axes = (CONJECTURES, DIMENSIONS, SCALAR_SYSTEMS, FAMILIES, STRATEGIES, MINIMIZERS, TRIAL_PROFILES, SEEDS)

    @property
    def size(self) -> int:
        return prod(len(axis) for axis in self.axes)

    def decode(self, index: int) -> FrontierAddress:
        if not 0 <= index < self.size:
            raise IndexError("frontier index out of range")
        coordinates = []
        value = index
        for axis in reversed(self.axes):
            coordinates.append(value % len(axis))
            value //= len(axis)
        coordinates.reverse()
        return FrontierAddress(*(axis[position] for axis, position in zip(self.axes, coordinates)))

    def encode(self, address: FrontierAddress) -> int:
        values = (
            address.conjecture_id, address.dimension, address.scalar_system,
            address.family, address.strategy, address.minimizer, address.trials, address.seed,
        )
        index = 0
        for axis, value in zip(self.axes, values):
            index = index * len(axis) + axis.index(value)
        return index

    def iter_window(self, start: int, count: int) -> Iterator[tuple[int, FrontierAddress]]:
        if start < 0 or count < 0:
            raise ValueError("start and count must be non-negative")
        for index in range(start, min(self.size, start+count)):
            yield index, self.decode(index)

    def manifest(self) -> dict[str, object]:
        return {
            "logical_frontier_size": self.size,
            "axes": {
                "conjectures": len(CONJECTURES), "dimensions": len(DIMENSIONS),
                "scalar_systems": len(SCALAR_SYSTEMS), "families": len(FAMILIES),
                "strategies": len(STRATEGIES), "minimizers": len(MINIMIZERS),
                "trial_profiles": len(TRIAL_PROFILES), "seeds": len(SEEDS),
            },
            "permanent_total_cap": None,
            "theorem_claimed": False,
            "formal_proof_claimed": False,
            "scientific_validation_claimed": False,
        }


def plan_campaign(start_offset: int, count: int) -> dict[str, object]:
    frontier = CounterexampleFrontier()
    items = [
        {"logical_index": index, "address": address.to_dict(), "plan": address.to_plan().to_dict()}
        for index, address in frontier.iter_window(start_offset, count)
    ]
    canonical = json.dumps(items, sort_keys=True, separators=(",", ":"))
    return {
        "start_offset": start_offset, "requested": count, "generated": len(items),
        "next_offset": start_offset + len(items), "logical_frontier_size": frontier.size,
        "aggregate_sha256": sha256(canonical.encode()).hexdigest(), "items": items,
        "permanent_total_cap": None, "theorem_claimed": False,
        "formal_proof_claimed": False, "scientific_validation_claimed": False,
    }


def execute_builtin_campaign(
    conjecture_id: str, *, dimension: int, scalar_system: str, family: str,
    seed: int, trials: int, tolerance: float = 1e-8, minimize: bool = True,
) -> dict[str, object]:
    conjecture = BUILTINS[conjecture_id]
    plan = SearchPlan(
        conjecture_id, dimension, scalar_system, family, "builtin_campaign",
        "full_pipeline" if minimize else "none", seed, trials, tolerance,
    )
    return search_matrix_identity(
        plan, variables=conjecture.variables, lhs=conjecture.lhs, rhs=conjecture.rhs,
        assumptions_fn=conjecture.assumptions, minimize=minimize,
    ).to_dict()


_SCHEMA = """
CREATE TABLE IF NOT EXISTS counterexamples (
    record_id TEXT PRIMARY KEY,
    conjecture_id TEXT NOT NULL,
    digest TEXT NOT NULL UNIQUE,
    state TEXT NOT NULL,
    relative_residual REAL NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_counterexamples_conjecture
ON counterexamples(conjecture_id, relative_residual DESC);
"""


class CounterexampleRegistry:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(_SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def put(self, record: CounterexampleRecord) -> bool:
        payload = json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":"))
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO counterexamples "
                "(record_id, conjecture_id, digest, state, relative_residual, payload) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (record.record_id, record.conjecture_id, record.digest(), record.state.value,
                 record.witness.relative_residual, payload),
            )
            return cursor.rowcount == 1

    def count(self) -> int:
        with self.connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM counterexamples").fetchone()[0])

    def export_jsonl(self, path: str | Path) -> int:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with self.connect() as connection, output.open("w", encoding="utf-8") as handle:
            for (payload,) in connection.execute("SELECT payload FROM counterexamples ORDER BY conjecture_id, record_id"):
                handle.write(payload + "\n")
                count += 1
        return count


def run_oakbench() -> dict[str, object]:
    checks: list[dict[str, object]] = []
    frontier = CounterexampleFrontier()
    indices = (0, 1, 17, frontier.size//2, frontier.size-1)
    checks.append({"name": "frontier_roundtrip", "passed": all(frontier.encode(frontier.decode(i)) == i for i in indices), "value": frontier.size})
    checks.append({"name": "frontier_scale", "passed": frontier.size > 10**9, "value": frontier.size})
    checks.append({"name": "family_count", "passed": len(FAMILIES) >= 18, "value": len(FAMILIES)})
    first = plan_campaign(4096, 128)
    second = plan_campaign(4096, 128)
    checks.append({"name": "campaign_determinism", "passed": first["aggregate_sha256"] == second["aggregate_sha256"], "value": first["aggregate_sha256"]})
    false_report = execute_builtin_campaign(
        "unconditional_commutativity", dimension=2, scalar_system="real",
        family="dense", seed=2026, trials=16,
    )
    checks.append({"name": "find_false_commutativity", "passed": false_report["record"] is not None, "value": false_report["state"]})
    true_report = execute_builtin_campaign(
        "transpose_product", dimension=4, scalar_system="real",
        family="dense", seed=2026, trials=16,
    )
    checks.append({"name": "finite_true_fixture_no_witness", "passed": true_report["state"] == "SEARCHED_NO_WITNESS", "value": true_report["maximum_relative_residual"]})
    projection = execute_builtin_campaign(
        "projection_idempotence", dimension=4, scalar_system="complex",
        family="projection", seed=17, trials=8,
    )
    checks.append({"name": "conditional_projection_fixture", "passed": projection["state"] == "SEARCHED_NO_WITNESS", "value": projection["state"]})
    registry_passed = False
    if false_report["record"]:
        payload = false_report["record"]
        witness_payload = payload["witness"]
        witness = MatrixWitness(
            matrices=witness_payload["matrices"], absolute_residual=witness_payload["absolute_residual"],
            relative_residual=witness_payload["relative_residual"], assumptions_passed=True,
            assumption_audit=tuple(witness_payload.get("assumption_audit", [])),
            provenance=witness_payload.get("provenance", {}),
        )
        record = CounterexampleRecord(
            payload["record_id"], payload["conjecture_id"], payload["plan_digest"],
            SearchState(payload["state"]), witness,
        )
        with tempfile.TemporaryDirectory() as directory:
            registry = CounterexampleRegistry(Path(directory)/"mminus.sqlite3")
            registry_passed = registry.put(record) and not registry.put(record) and registry.count() == 1
    checks.append({"name": "registry_deduplication", "passed": registry_passed, "value": 1 if registry_passed else 0})
    passed = all(bool(check["passed"]) for check in checks)
    return {
        "status": "OAK_PASS_SOFTWARE_RESEARCH_FIXTURES_R0_3_WAVE_4" if passed else "OAK_FAIL_R0_3_WAVE_4",
        "passed": passed, "checks": checks, "logical_frontier_size": frontier.size,
        "theorem_claimed": False, "formal_proof_claimed": False,
        "scientific_validation_claimed": False,
    }
