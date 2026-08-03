"""Declarative identity catalog for Ω-VLA Wave 3."""
from __future__ import annotations

from dataclasses import replace

from .assumptions import Assumption, AssumptionKind
from .expressions import ExprKind, MatrixExpr
from .models import IdentitySchema

A = MatrixExpr.variable("A")
B = MatrixExpr.variable("B")
C = MatrixExpr.variable("C")
D = MatrixExpr.variable("D")
I = MatrixExpr.identity(1)
Z = MatrixExpr.zero(1)


def _a(kind: AssumptionKind, *targets: str) -> Assumption:
    return Assumption(kind, tuple(targets))


def _schema(
    schema_id: str,
    title: str,
    variables: tuple[str, ...],
    lhs: MatrixExpr,
    rhs: MatrixExpr,
    *,
    assumptions: tuple[Assumption, ...] = (),
    tags: tuple[str, ...] = (),
    parents: tuple[str, ...] = (),
    description: str = "",
) -> IdentitySchema:
    return IdentitySchema(
        schema_id=schema_id,
        title=title,
        variables=variables,
        lhs=lhs,
        rhs=rhs,
        assumptions=assumptions,
        tags=tags,
        parent_ids=parents,
        description=description,
    )


SCHEMAS: tuple[IdentitySchema, ...] = (
    _schema("adjoint.involution", "Adjoint involution", ("A",), A.adjoint().adjoint(), A, tags=("adjoint", "involution")),
    _schema("adjoint.sum", "Adjoint distributes over sums", ("A", "B"), (A + B).adjoint(), A.adjoint() + B.adjoint(), tags=("adjoint", "linearity"), parents=("adjoint.involution",)),
    _schema("adjoint.product", "Adjoint reverses products", ("A", "B"), (A @ B).adjoint(), B.adjoint() @ A.adjoint(), tags=("adjoint", "composition"), parents=("adjoint.involution",)),
    _schema("transpose.involution", "Transpose involution", ("A",), A.transpose().transpose(), A, tags=("transpose", "involution")),
    _schema("transpose.sum", "Transpose distributes over sums", ("A", "B"), (A + B).transpose(), A.transpose() + B.transpose(), tags=("transpose", "linearity"), parents=("transpose.involution",)),
    _schema("transpose.product", "Transpose reverses products", ("A", "B"), (A @ B).transpose(), B.transpose() @ A.transpose(), tags=("transpose", "composition"), parents=("transpose.involution",)),
    _schema("inverse.product", "Inverse reverses products", ("A", "B"), (A @ B).inverse(), B.inverse() @ A.inverse(), assumptions=(_a(AssumptionKind.INVERTIBLE, "A"), _a(AssumptionKind.INVERTIBLE, "B")), tags=("inverse", "composition")),
    _schema("inverse.involution", "Double inverse", ("A",), A.inverse().inverse(), A, assumptions=(_a(AssumptionKind.INVERTIBLE, "A"),), tags=("inverse", "involution")),
    _schema("commutator.antisymmetry", "Commutator antisymmetry", ("A", "B"), A.commutator(B), B.commutator(A).scale(-1), tags=("commutator", "lie")),
    _schema("commutator.self_zero", "Self commutator vanishes", ("A",), A.commutator(A), Z, tags=("commutator", "zero"), parents=("commutator.antisymmetry",)),
    _schema("commutator.identity_zero", "Identity commutes with every matrix", ("A",), A.commutator(I), Z, tags=("commutator", "identity")),
    _schema("anticommutator.symmetry", "Anticommutator symmetry", ("A", "B"), A.anticommutator(B), B.anticommutator(A), tags=("anticommutator",)),
    _schema("algebra.left_distributivity", "Left distributivity", ("A", "B", "C"), A @ (B + C), (A @ B) + (A @ C), tags=("algebra", "distributivity")),
    _schema("algebra.right_distributivity", "Right distributivity", ("A", "B", "C"), (A + B) @ C, (A @ C) + (B @ C), tags=("algebra", "distributivity")),
    _schema("algebra.associativity", "Matrix multiplication associativity", ("A", "B", "C"), (A @ B) @ C, A @ (B @ C), tags=("algebra", "associativity")),
    _schema("projection.idempotence", "Projection idempotence", ("A",), A.power(2), A, assumptions=(_a(AssumptionKind.PROJECTION, "A"),), tags=("projection", "conditional")),
    _schema("unitary.inverse_adjoint", "Unitary inverse equals adjoint", ("A",), A.inverse(), A.adjoint(), assumptions=(_a(AssumptionKind.UNITARY, "A"),), tags=("unitary", "inverse", "conditional")),
    _schema("involution.square_identity", "Involution squares to identity", ("A",), A.power(2), I, assumptions=(_a(AssumptionKind.INVOLUTION, "A"),), tags=("involution", "conditional")),
    _schema("commuting.binomial_square", "Commuting matrix binomial square", ("A", "B"), (A + B).power(2), A.power(2) + (A @ B).scale(2) + B.power(2), assumptions=(_a(AssumptionKind.COMMUTING, "A", "B"),), tags=("commuting", "polynomial", "conditional")),
    _schema("commutator.leibniz_right", "Commutator Leibniz rule", ("A", "B", "C"), A.commutator(B @ C), (A.commutator(B) @ C) + (B @ A.commutator(C)), tags=("commutator", "derivation"), parents=("commutator.antisymmetry", "algebra.left_distributivity")),
    _schema("tensor.adjoint", "Tensor-product adjoint", ("A", "B"), A.tensor(B).adjoint(), A.adjoint().tensor(B.adjoint()), tags=("tensor", "adjoint"), parents=("adjoint.product",)),
    _schema("tensor.mixed_product", "Tensor mixed-product identity", ("A", "B", "C", "D"), A.tensor(B) @ C.tensor(D), (A @ C).tensor(B @ D), tags=("tensor", "composition")),
    _schema("normal.commutator_adjoint_zero", "Normality via adjoint commutator", ("A",), A.commutator(A.adjoint()), Z, assumptions=(_a(AssumptionKind.NORMAL, "A"),), tags=("normal", "commutator", "conditional")),
    _schema("orthogonal.inverse_transpose", "Orthogonal inverse equals transpose", ("A",), A.inverse(), A.transpose(), assumptions=(_a(AssumptionKind.ORTHOGONAL, "A"),), tags=("orthogonal", "inverse", "conditional")),
)

_SCHEMA_MAP = {schema.schema_id: schema for schema in SCHEMAS}
if len(_SCHEMA_MAP) != len(SCHEMAS):
    raise RuntimeError("duplicate identity schema id")


def schema_by_id(schema_id: str) -> IdentitySchema:
    try:
        return _SCHEMA_MAP[schema_id]
    except KeyError as exc:
        raise KeyError(f"unknown identity schema {schema_id!r}") from exc


def resize_expr(expression: MatrixExpr, dimension: int) -> MatrixExpr:
    if expression.kind == ExprKind.IDENTITY:
        return MatrixExpr.identity(dimension)
    if expression.kind == ExprKind.ZERO:
        return MatrixExpr.zero(dimension)
    return MatrixExpr(
        kind=expression.kind,
        operands=tuple(resize_expr(x, dimension) for x in expression.operands),
        name=expression.name,
        dimension=expression.dimension,
        scalar=expression.scalar,
        exponent=expression.exponent,
    )


def schema_at_dimension(schema: IdentitySchema, dimension: int) -> IdentitySchema:
    if dimension < 1:
        raise ValueError("dimension must be positive")
    return replace(schema, lhs=resize_expr(schema.lhs, dimension), rhs=resize_expr(schema.rhs, dimension))


def catalog_manifest() -> dict[str, object]:
    return {
        "schemas": len(SCHEMAS),
        "schema_ids": [schema.schema_id for schema in SCHEMAS],
        "digests": {schema.schema_id: schema.digest() for schema in SCHEMAS},
        "theorem_claimed": False,
        "formal_proof_claimed": False,
        "scientific_validation_claimed": False,
    }
