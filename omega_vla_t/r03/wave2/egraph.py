"""Bounded equality-saturation style rewriting for OperatorExpr.

This is a compact deterministic saturation engine, not a complete e-graph
implementation. It preserves type checks, records every accepted rewrite and
stops under explicit node, expression and round budgets.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Iterable

from ..operators import OperatorExpr, OperatorKind


class EGraphError(ValueError):
    pass


RewriteFunction = Callable[[OperatorExpr], Iterable[OperatorExpr]]


@dataclass(frozen=True)
class RewriteRule:
    name: str
    function: RewriteFunction
    soundness_status: str = "software_fixture"
    assumptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise EGraphError("rewrite rules require a name")
        if self.soundness_status not in {
            "software_fixture",
            "classical_identity",
            "conditional",
            "experimental",
        }:
            raise EGraphError("invalid rewrite soundness status")


@dataclass(frozen=True)
class EGraphBudget:
    max_rounds: int = 12
    max_expressions: int = 20_000
    max_total_nodes: int = 1_000_000
    max_expression_nodes: int = 10_000

    def __post_init__(self) -> None:
        if min(
            self.max_rounds,
            self.max_expressions,
            self.max_total_nodes,
            self.max_expression_nodes,
        ) <= 0:
            raise EGraphError("all saturation budgets must be positive")


@dataclass(frozen=True)
class RewriteEvent:
    rule: str
    source_digest: str
    target_digest: str
    source_nodes: int
    target_nodes: int


@dataclass(frozen=True)
class EGraphReport:
    input_digest: str
    expressions_discovered: int
    total_nodes_seen: int
    rounds_completed: int
    saturated: bool
    stopped_reason: str
    best_expression: OperatorExpr
    best_cost: tuple[int, int, str]
    events: tuple[RewriteEvent, ...]
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["best_expression"] = self.best_expression.to_dict()
        return payload


def expression_cost(expression: OperatorExpr) -> tuple[int, int, str]:
    """Prefer fewer nodes, lower depth, then canonical digest."""

    return (expression.node_count(), expression.depth(), expression.digest())


def _rebuild(expression: OperatorExpr, operands: tuple[OperatorExpr, ...]) -> OperatorExpr:
    return OperatorExpr(
        kind=expression.kind,
        operands=operands,
        name=expression.name,
        declared_type=expression.declared_type,
        scalar_value=expression.scalar_value,
        matrix_value=expression.matrix_value,
        exponent=expression.exponent,
        attributes=expression.attributes,
        properties=expression.properties,
    )


def _rewrite_children(expression: OperatorExpr, rule: RewriteRule) -> Iterable[OperatorExpr]:
    for index, child in enumerate(expression.operands):
        for replacement in rule.function(child):
            operands = list(expression.operands)
            operands[index] = replacement
            yield _rebuild(expression, tuple(operands))


def _default_local_rewrites(expression: OperatorExpr) -> Iterable[OperatorExpr]:
    kind = expression.kind
    operands = expression.operands

    simplified = expression.simplify()
    if simplified != expression:
        yield simplified

    if kind == OperatorKind.COMMUTATOR:
        left, right = operands
        yield (left @ right) - (right @ left)
        yield right.commutator(left).scale(-1)

    if kind == OperatorKind.ANTICOMMUTATOR:
        left, right = operands
        yield (left @ right) + (right @ left)
        yield right.anticommutator(left)

    if kind == OperatorKind.ADJOINT:
        child = operands[0]
        if child.kind == OperatorKind.COMMUTATOR:
            left, right = child.operands
            yield right.adjoint().commutator(left.adjoint())
        if child.kind == OperatorKind.ANTICOMMUTATOR:
            left, right = child.operands
            yield left.adjoint().anticommutator(right.adjoint())
        if child.kind == OperatorKind.TENSOR_PRODUCT:
            yield OperatorExpr.nary(
                OperatorKind.TENSOR_PRODUCT,
                tuple(value.adjoint() for value in child.operands),
            )

    if kind == OperatorKind.POWER:
        child = operands[0]
        exponent = expression.exponent
        if exponent == 0:
            yield OperatorExpr.identity(child.infer_type())
        elif exponent == 1:
            yield child
        elif exponent == 2:
            yield child @ child

    if kind == OperatorKind.INVERSE:
        child = operands[0]
        if child.kind == OperatorKind.INVERSE:
            yield child.operands[0]
        if child.kind == OperatorKind.COMPOSE:
            yield OperatorExpr.nary(
                OperatorKind.COMPOSE,
                tuple(
                    OperatorExpr.unary(OperatorKind.INVERSE, value)
                    for value in reversed(child.operands)
                ),
            )

    if kind == OperatorKind.COMPOSE and len(operands) == 2:
        left, right = operands
        if left.kind == OperatorKind.SUM:
            yield OperatorExpr.nary(
                OperatorKind.SUM,
                tuple(value @ right for value in left.operands),
            )
        if right.kind == OperatorKind.SUM:
            yield OperatorExpr.nary(
                OperatorKind.SUM,
                tuple(left @ value for value in right.operands),
            )

    if kind == OperatorKind.TENSOR_PRODUCT and len(operands) == 2:
        left, right = operands
        if left.kind == OperatorKind.SUM:
            yield OperatorExpr.nary(
                OperatorKind.SUM,
                tuple(value.tensor(right) for value in left.operands),
            )
        if right.kind == OperatorKind.SUM:
            yield OperatorExpr.nary(
                OperatorKind.SUM,
                tuple(left.tensor(value) for value in right.operands),
            )


def default_rules() -> tuple[RewriteRule, ...]:
    return (
        RewriteRule(
            "operator_classical_local",
            _default_local_rewrites,
            soundness_status="classical_identity",
        ),
    )


def saturate(
    expression: OperatorExpr,
    *,
    rules: Iterable[RewriteRule] | None = None,
    budget: EGraphBudget | None = None,
) -> EGraphReport:
    """Discover equivalent typed expressions under bounded rewrite search."""

    selected_rules = tuple(rules or default_rules())
    envelope = budget or EGraphBudget()
    expression.infer_type()

    known: dict[str, OperatorExpr] = {expression.digest(): expression}
    frontier = [expression]
    events: list[RewriteEvent] = []
    total_nodes = expression.node_count()
    rounds = 0
    stopped_reason = "saturated"

    for round_index in range(envelope.max_rounds):
        rounds = round_index + 1
        next_frontier: list[OperatorExpr] = []
        for source in frontier:
            for rule in selected_rules:
                candidates = list(rule.function(source))
                candidates.extend(_rewrite_children(source, rule))
                for target in candidates:
                    try:
                        target.infer_type()
                    except Exception:
                        continue
                    nodes = target.node_count()
                    if nodes > envelope.max_expression_nodes:
                        continue
                    digest = target.digest()
                    if digest in known:
                        continue
                    if len(known) >= envelope.max_expressions:
                        stopped_reason = "max_expressions"
                        return _report(
                            expression,
                            known,
                            total_nodes,
                            rounds,
                            False,
                            stopped_reason,
                            events,
                        )
                    if total_nodes + nodes > envelope.max_total_nodes:
                        stopped_reason = "max_total_nodes"
                        return _report(
                            expression,
                            known,
                            total_nodes,
                            rounds,
                            False,
                            stopped_reason,
                            events,
                        )
                    known[digest] = target
                    next_frontier.append(target)
                    total_nodes += nodes
                    events.append(
                        RewriteEvent(
                            rule=rule.name,
                            source_digest=source.digest(),
                            target_digest=digest,
                            source_nodes=source.node_count(),
                            target_nodes=nodes,
                        )
                    )
        if not next_frontier:
            return _report(
                expression,
                known,
                total_nodes,
                rounds,
                True,
                "saturated",
                events,
            )
        frontier = next_frontier

    return _report(
        expression,
        known,
        total_nodes,
        rounds,
        False,
        "max_rounds",
        events,
    )


def _report(
    original: OperatorExpr,
    known: dict[str, OperatorExpr],
    total_nodes: int,
    rounds: int,
    saturated_flag: bool,
    reason: str,
    events: list[RewriteEvent],
) -> EGraphReport:
    best = min(known.values(), key=expression_cost)
    return EGraphReport(
        input_digest=original.digest(),
        expressions_discovered=len(known),
        total_nodes_seen=total_nodes,
        rounds_completed=rounds,
        saturated=saturated_flag,
        stopped_reason=reason,
        best_expression=best,
        best_cost=expression_cost(best),
        events=tuple(events),
    )
