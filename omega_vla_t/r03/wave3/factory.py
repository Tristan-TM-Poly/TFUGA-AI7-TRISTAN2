"""Assumption and expression mutation plus identity-instance construction."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

from .assumptions import Assumption, AssumptionKind
from .catalog import schema_at_dimension, schema_by_id
from .expressions import ExprKind, MatrixExpr
from .models import EvidenceState, IdentityAddress, IdentityInstance, IdentitySchema


_STRENGTHEN = {
    "strengthen_normal": AssumptionKind.NORMAL,
    "strengthen_invertible": AssumptionKind.INVERTIBLE,
    "strengthen_hermitian": AssumptionKind.HERMITIAN,
}


def mutate_assumptions(
    schema: IdentitySchema,
    policy: str,
) -> tuple[tuple[Assumption, ...], tuple[str, ...]]:
    assumptions = list(schema.assumptions)
    notes: list[str] = []
    if policy == "none":
        return tuple(assumptions), ()
    if policy == "drop_one":
        if assumptions:
            removed = assumptions.pop(0)
            notes.append(f"dropped:{removed.kind.value}:{','.join(removed.targets)}")
        else:
            notes.append("drop_one:no_assumption_available")
    elif policy == "drop_all":
        notes.extend(
            f"dropped:{value.kind.value}:{','.join(value.targets)}"
            for value in assumptions
        )
        assumptions = []
    elif policy in _STRENGTHEN:
        kind = _STRENGTHEN[policy]
        for variable in schema.variables:
            candidate = Assumption(kind, (variable,))
            if candidate not in assumptions:
                assumptions.append(candidate)
        notes.append(f"strengthened:{kind.value}:all_variables")
    elif policy == "swap_adjoint_transpose":
        notes.append("expression_mutation:swap_adjoint_transpose")
    elif policy == "reverse_operands":
        notes.append("expression_mutation:reverse_lhs_operands")
    else:
        raise ValueError(f"unknown mutation policy {policy!r}")
    return tuple(sorted(assumptions)), tuple(notes)


def _map_expr(expression: MatrixExpr, *, swap: bool = False) -> MatrixExpr:
    kind = expression.kind
    if swap and kind == ExprKind.ADJOINT:
        kind = ExprKind.TRANSPOSE
    elif swap and kind == ExprKind.TRANSPOSE:
        kind = ExprKind.ADJOINT
    return MatrixExpr(
        kind=kind,
        operands=tuple(_map_expr(x, swap=swap) for x in expression.operands),
        name=expression.name,
        dimension=expression.dimension,
        scalar=expression.scalar,
        exponent=expression.exponent,
    )


def _reverse_lhs(expression: MatrixExpr) -> MatrixExpr:
    operands = tuple(_reverse_lhs(x) for x in expression.operands)
    if expression.kind in {
        ExprKind.MATMUL, ExprKind.COMMUTATOR, ExprKind.ANTICOMMUTATOR,
    }:
        operands = tuple(reversed(operands))
    return MatrixExpr(
        kind=expression.kind,
        operands=operands,
        name=expression.name,
        dimension=expression.dimension,
        scalar=expression.scalar,
        exponent=expression.exponent,
    )


def mutate_schema(schema: IdentitySchema, policy: str) -> IdentitySchema:
    if policy == "swap_adjoint_transpose":
        return replace(
            schema,
            lhs=_map_expr(schema.lhs, swap=True),
            rhs=_map_expr(schema.rhs, swap=True),
            tags=tuple(sorted(set(schema.tags + ("mutated",)))),
        )
    if policy == "reverse_operands":
        return replace(
            schema,
            lhs=_reverse_lhs(schema.lhs),
            tags=tuple(sorted(set(schema.tags + ("mutated",)))),
        )
    return schema


def instantiate(address: IdentityAddress) -> tuple[IdentitySchema, IdentityInstance]:
    schema = schema_at_dimension(schema_by_id(address.schema_id), address.dimension)
    schema = mutate_schema(schema, address.mutation_policy)
    assumptions, notes = mutate_assumptions(schema, address.mutation_policy)
    identity_payload = (
        address.canonical(),
        schema.digest(),
        tuple(value.to_dict()["kind"] for value in assumptions),
        notes,
    )
    instance_id = "identity-" + sha256(repr(identity_payload).encode()).hexdigest()[:24]
    instance = IdentityInstance(
        instance_id=instance_id,
        address=address,
        schema_digest=schema.digest(),
        assumptions=assumptions,
        mutation_notes=notes,
        evidence_state=EvidenceState.TYPE_CHECKED,
    )
    return schema, instance
