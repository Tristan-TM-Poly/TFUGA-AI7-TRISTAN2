"""Property-test and bounded SMT-LIB target compilers."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from typing import Any

from .assumptions import AssumptionKind
from .expressions import ExprKind, MatrixExpr
from .models import IdentityInstance, IdentitySchema


@dataclass(frozen=True)
class CompiledTarget:
    target_id: str
    backend: str
    status: str
    source: str
    source_sha256: str
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    formally_verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compile_property_test(
    schema: IdentitySchema,
    instance: IdentityInstance,
    *,
    trials: int = 32,
    seed: int = 2026,
) -> CompiledTarget:
    source = f'''"""Generated finite property test for {schema.schema_id}.

Numerical support is not proof.
"""
from omega_vla_t.r03.wave3.factory import instantiate
from omega_vla_t.r03.wave3.falsify import test_identity
from omega_vla_t.r03.wave3.models import IdentityAddress

address = IdentityAddress(**{instance.address.__dict__!r})
schema, instance = instantiate(address)
report = test_identity(schema, instance, seed={seed}, trials={trials})
assert report.passed, report.to_dict()
assert report.theorem_claimed is False
assert report.formal_proof_claimed is False
'''
    return _target("python-property-test", "GENERATED_UNEXECUTED", source)


def _target(backend: str, status: str, source: str) -> CompiledTarget:
    digest = sha256(source.encode()).hexdigest()
    return CompiledTarget(
        target_id=f"{backend}-{digest[:20]}",
        backend=backend,
        status=status,
        source=source,
        source_sha256=digest,
    )


def _matrix_symbol(name: str, dimension: int) -> list[list[str]]:
    return [[f"{name}_{i}_{j}" for j in range(dimension)] for i in range(dimension)]


def _add(a: list[list[str]], b: list[list[str]], op: str = "+") -> list[list[str]]:
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        raise ValueError("SMT matrix shape mismatch")
    return [[f"({op} {a[i][j]} {b[i][j]})" for j in range(len(a[0]))] for i in range(len(a))]


def _mul(a: list[list[str]], b: list[list[str]]) -> list[list[str]]:
    if len(a[0]) != len(b):
        raise ValueError("SMT matrix multiplication mismatch")
    result: list[list[str]] = []
    for i in range(len(a)):
        row: list[str] = []
        for j in range(len(b[0])):
            terms = [f"(* {a[i][k]} {b[k][j]})" for k in range(len(b))]
            row.append(terms[0] if len(terms) == 1 else f"(+ {' '.join(terms)})")
        result.append(row)
    return result


def _transpose(a: list[list[str]]) -> list[list[str]]:
    return [list(row) for row in zip(*a)]


def _expr_smt(expr: MatrixExpr, dimension: int) -> list[list[str]]:
    if expr.kind == ExprKind.VARIABLE:
        return _matrix_symbol(expr.name, dimension)
    if expr.kind == ExprKind.IDENTITY:
        return [["1" if i == j else "0" for j in range(dimension)] for i in range(dimension)]
    if expr.kind == ExprKind.ZERO:
        return [["0" for _ in range(dimension)] for _ in range(dimension)]
    values = [_expr_smt(value, dimension) for value in expr.operands]
    if expr.kind == ExprKind.ADD:
        result = values[0]
        for value in values[1:]:
            result = _add(result, value)
        return result
    if expr.kind == ExprKind.SUBTRACT:
        return _add(values[0], values[1], "-")
    if expr.kind == ExprKind.MATMUL:
        result = values[0]
        for value in values[1:]:
            result = _mul(result, value)
        return result
    if expr.kind in {ExprKind.TRANSPOSE, ExprKind.ADJOINT}:
        return _transpose(values[0])
    if expr.kind == ExprKind.POWER:
        assert expr.exponent is not None
        if expr.exponent < 0:
            raise ValueError("negative powers unsupported by finite SMT target")
        result = _expr_smt(MatrixExpr.identity(dimension), dimension)
        for _ in range(expr.exponent):
            result = _mul(result, values[0])
        return result
    if expr.kind == ExprKind.COMMUTATOR:
        return _add(_mul(values[0], values[1]), _mul(values[1], values[0]), "-")
    if expr.kind == ExprKind.ANTICOMMUTATOR:
        return _add(_mul(values[0], values[1]), _mul(values[1], values[0]))
    if expr.kind == ExprKind.SCALAR_MULTIPLY:
        scalar = expr.scalar
        if isinstance(scalar, complex) and scalar.imag:
            raise ValueError("complex scalar unsupported by real SMT target")
        number = float(scalar.real if isinstance(scalar, complex) else scalar)
        return [[f"(* {number:.17g} {entry})" for entry in row] for row in values[0]]
    raise ValueError(f"{expr.kind.value} unsupported by finite SMT target")


def compile_smtlib_counterexample(
    schema: IdentitySchema,
    instance: IdentityInstance,
) -> CompiledTarget:
    """Compile a finite real counterexample query, never a proof certificate."""
    dimension = instance.address.dimension
    if instance.address.scalar_system != "real":
        return _target(
            "smtlib2-qf_nra",
            "UNSUPPORTED_COMPLEX",
            "; Complex matrices are not encoded by this bounded target.\n",
        )
    try:
        lhs = _expr_smt(schema.lhs, dimension)
        rhs = _expr_smt(schema.rhs, dimension)
    except ValueError as exc:
        return _target("smtlib2-qf_nra", "UNSUPPORTED_EXPRESSION", f"; {exc}\n")

    lines = [
        "; Ω-VLA Wave 3 finite counterexample target",
        "; sat => finite counterexample under encoded assumptions",
        "; unsat => only this bounded formula is unsatisfiable; not a universal proof",
        "(set-logic QF_NRA)",
    ]
    for variable in schema.variables:
        for i in range(dimension):
            for j in range(dimension):
                lines.append(f"(declare-fun {variable}_{i}_{j} () Real)")

    def equality(left: list[list[str]], right: list[list[str]]) -> str:
        clauses = [
            f"(= {left[i][j]} {right[i][j]})"
            for i in range(len(left)) for j in range(len(left[0]))
        ]
        return clauses[0] if len(clauses) == 1 else f"(and {' '.join(clauses)})"

    for assumption in instance.assumptions:
        name = assumption.targets[0]
        matrix = _matrix_symbol(name, dimension)
        if assumption.kind in {AssumptionKind.SYMMETRIC, AssumptionKind.HERMITIAN}:
            lines.append(f"(assert {equality(matrix, _transpose(matrix))})")
        elif assumption.kind == AssumptionKind.SKEW_SYMMETRIC:
            neg_t = [[f"(- {x})" for x in row] for row in _transpose(matrix)]
            lines.append(f"(assert {equality(matrix, neg_t)})")
        elif assumption.kind == AssumptionKind.PROJECTION:
            lines.append(f"(assert {equality(_mul(matrix, matrix), matrix)})")
        elif assumption.kind == AssumptionKind.INVOLUTION:
            identity = _expr_smt(MatrixExpr.identity(dimension), dimension)
            lines.append(f"(assert {equality(_mul(matrix, matrix), identity)})")
        elif assumption.kind == AssumptionKind.COMMUTING:
            second = _matrix_symbol(assumption.targets[1], dimension)
            lines.append(f"(assert {equality(_mul(matrix, second), _mul(second, matrix))})")
        elif assumption.kind in {
            AssumptionKind.SQUARE, AssumptionKind.NORMAL,
            AssumptionKind.INVERTIBLE, AssumptionKind.UNITARY,
            AssumptionKind.ORTHOGONAL, AssumptionKind.POSITIVE_SEMIDEFINITE,
        }:
            lines.append(f"; assumption {assumption.kind.value} omitted or partially encoded")
    lines.append(f"(assert (not {equality(lhs, rhs)}))")
    lines.extend(("(check-sat)", "(get-model)"))
    return _target("smtlib2-qf_nra", "FORMAL_TARGET_UNCHECKED", "\n".join(lines) + "\n")
