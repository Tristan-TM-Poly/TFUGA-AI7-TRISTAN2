"""Deterministic demonstration fixtures for Ω-VLA R0.3."""

from __future__ import annotations

import numpy as np

from .ir import EdgeKind, IREdge, IRNode, NodeKind, Provenance, VLAProgram
from .operators import OperatorExpr
from .types import MathType, ScalarSystem, UnitDimension


def finite_operator_fixture() -> tuple[OperatorExpr, dict[str, np.ndarray]]:
    operator_type = MathType.linear_operator(
        3,
        3,
        scalar_system=ScalarSystem.COMPLEX,
        domain_id="V",
        codomain_id="V",
    )
    a = OperatorExpr.symbol("A", operator_type, properties=("normal",))
    b = OperatorExpr.symbol("B", operator_type)
    expression = (a.adjoint() @ b + b.adjoint() @ a).commutator(
        OperatorExpr.identity(operator_type)
    )
    environment = {
        "A": np.array(
            [
                [1.0 + 1.0j, 0.0, 0.0],
                [0.0, 2.0 - 0.5j, 0.0],
                [0.0, 0.0, -1.0 + 2.0j],
            ],
            dtype=np.complex128,
        ),
        "B": np.array(
            [
                [0.0, 1.0, 0.0],
                [-1.0, 0.0, 2.0],
                [0.0, -2.0, 0.5],
            ],
            dtype=np.complex128,
        ),
    }
    return expression, environment


def typed_equation_program() -> VLAProgram:
    provenance = Provenance(
        source="Ω-VLA-T∞³ R0.3 deterministic fixture",
        locator="fixtures.typed_equation_program",
        method="handwritten",
        confidence=1.0,
    )
    velocity_units = UnitDimension.from_mapping({"L": 1, "T": -1})
    operator_type = MathType.linear_operator(
        3,
        3,
        scalar_system=ScalarSystem.REAL,
        units=UnitDimension.dimensionless(),
        domain_id="V",
        codomain_id="V",
    )
    vector_type = MathType.vector(
        3,
        scalar_system=ScalarSystem.REAL,
        units=velocity_units,
        space_id="V",
    )
    program = VLAProgram(
        program_id="linear-system-fixture",
        title="Typed finite linear system A x = b",
        metadata={
            "epistemic_status": "software_fixture",
            "theorem_claimed": False,
        },
    )
    nodes = (
        IRNode.build("V", NodeKind.SPACE, "Finite vector space V", attributes={"dimension": 3}, provenance=provenance),
        IRNode.build("A", NodeKind.OPERATOR, "Linear operator A", math_type=operator_type, provenance=provenance),
        IRNode.build("x", NodeKind.VECTOR, "Unknown state x", math_type=vector_type, provenance=provenance),
        IRNode.build("b", NodeKind.VECTOR, "Observed target b", math_type=vector_type, provenance=provenance),
        IRNode.build(
            "eq",
            NodeKind.EQUATION,
            "A x = b",
            attributes={
                "questions": [
                    "existence",
                    "uniqueness",
                    "conditioning",
                    "residual",
                ]
            },
            provenance=provenance,
        ),
        IRNode.build("assumption", NodeKind.ASSUMPTION, "A is invertible for this fixture", provenance=provenance),
        IRNode.build("residual", NodeKind.RESIDUAL, "r = b - A x", math_type=vector_type, provenance=provenance),
    )
    for node in nodes:
        program.add_node(node)
    for edge in (
        IREdge.build("A", "V", EdgeKind.DOMAIN_OF),
        IREdge.build("A", "V", EdgeKind.CODOMAIN_OF),
        IREdge.build("x", "V", EdgeKind.BELONGS_TO),
        IREdge.build("b", "V", EdgeKind.BELONGS_TO),
        IREdge.build("eq", "A", EdgeKind.DEPENDS_ON),
        IREdge.build("eq", "x", EdgeKind.DEPENDS_ON),
        IREdge.build("eq", "b", EdgeKind.DEPENDS_ON),
        IREdge.build("eq", "assumption", EdgeKind.HAS_ASSUMPTION),
        IREdge.build("eq", "residual", EdgeKind.HAS_RESIDUAL),
    ):
        program.add_edge(edge)
    return program
