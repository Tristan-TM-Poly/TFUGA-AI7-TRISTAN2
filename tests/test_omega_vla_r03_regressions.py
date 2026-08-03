import pytest

from omega_vla_t.r03 import (
    MathType,
    OperatorError,
    OperatorExpr,
    OperatorKind,
    UnitDimension,
    evaluate_operator,
)


def test_kronecker_sum_preserves_common_units() -> None:
    inverse_time = UnitDimension.base("T").power(-1)
    left_type = MathType.linear_operator(
        2,
        2,
        units=inverse_time,
        domain_id="U",
        codomain_id="U",
    )
    right_type = MathType.linear_operator(
        3,
        3,
        units=inverse_time,
        domain_id="V",
        codomain_id="V",
    )
    left = OperatorExpr.symbol("A", left_type)
    right = OperatorExpr.symbol("B", right_type)
    expression = OperatorExpr.binary(OperatorKind.KRONECKER_SUM, left, right)
    inferred = expression.infer_type()
    assert inferred.shape.to_dict() == [6, 6]
    assert inferred.units == inverse_time
    assert inferred.domain_id == "tensor(U,V)"
    assert inferred.codomain_id == "tensor(U,V)"


def test_kronecker_sum_rejects_different_units() -> None:
    left = OperatorExpr.symbol(
        "A",
        MathType.linear_operator(
            2,
            2,
            units=UnitDimension.base("T").power(-1),
        ),
    )
    right = OperatorExpr.symbol(
        "B",
        MathType.linear_operator(3, 3),
    )
    expression = OperatorExpr.binary(OperatorKind.KRONECKER_SUM, left, right)
    with pytest.raises(ValueError):
        expression.infer_type()


def test_symbolic_dimensions_are_rejected_as_operator_errors() -> None:
    symbolic = OperatorExpr.symbol(
        "A",
        MathType.linear_operator("n", "n", domain_id="V", codomain_id="V"),
    )
    with pytest.raises(OperatorError, match="concrete dimensions"):
        evaluate_operator(symbolic, {"A": [[1.0]]})
