import json
from fractions import Fraction

import pytest

from omega_vla_t.r03 import (
    EdgeKind,
    IREdge,
    IRError,
    IRNode,
    MathType,
    NodeKind,
    Provenance,
    Regularity,
    ScalarSystem,
    Shape,
    StructureKind,
    TypeSystemError,
    UnitDimension,
    VLAProgram,
    Variance,
    audit_program,
    common_scalar_system,
    compile_graphml,
    math_type_from_dict,
    merge_programs,
    typed_equation_program,
)


def test_unit_dimension_exact_arithmetic_and_round_trip() -> None:
    length = UnitDimension.base("L")
    time = UnitDimension.base("T")
    velocity = length / time
    acceleration = velocity / time
    area = length.power(2)
    square_root_area = area.power(Fraction(1, 2))
    assert velocity.to_dict() == {"L": "1", "T": "-1"}
    assert acceleration.to_dict() == {"L": "1", "T": "-2"}
    assert square_root_area == length
    assert UnitDimension.from_mapping(velocity.to_dict()) == velocity
    assert not velocity.is_dimensionless
    assert UnitDimension.dimensionless().is_dimensionless


def test_unknown_unit_symbol_is_rejected() -> None:
    with pytest.raises(TypeSystemError):
        UnitDimension.base("currency")
    with pytest.raises(TypeSystemError):
        UnitDimension.from_mapping({"L": 1, "bad": 2})


def test_shape_supports_concrete_and_symbolic_dimensions() -> None:
    concrete = Shape.of(2, 3, 4)
    symbolic = Shape.of("n", "m")
    assert concrete.rank == 3
    assert concrete.concrete_size == 24
    assert symbolic.concrete_size is None
    assert concrete.tensor(symbolic).rank == 5
    assert Shape.of(2).dimensions[0].multiply(Shape.of(3).dimensions[0]).value == 6
    assert Shape.of("n").dimensions[0].multiply(Shape.of(3).dimensions[0]).value == "(n*3)"


def test_scalar_embedding_ladder_is_conservative() -> None:
    assert common_scalar_system(ScalarSystem.INTEGER, ScalarSystem.REAL) == ScalarSystem.REAL
    assert common_scalar_system(ScalarSystem.REAL, ScalarSystem.COMPLEX) == ScalarSystem.COMPLEX
    with pytest.raises(TypeSystemError):
        common_scalar_system(ScalarSystem.QUATERNION, ScalarSystem.COMPLEX)
    with pytest.raises(TypeSystemError):
        common_scalar_system(ScalarSystem.FINITE_FIELD, ScalarSystem.REAL)


def test_math_type_rejects_invalid_rank_contracts() -> None:
    with pytest.raises(TypeSystemError):
        MathType(structure=StructureKind.SCALAR, shape=Shape.of(1))
    with pytest.raises(TypeSystemError):
        MathType(structure=StructureKind.VECTOR, shape=Shape.of(2, 2))
    with pytest.raises(TypeSystemError):
        MathType(structure=StructureKind.LINEAR_OPERATOR, shape=Shape.of(3))
    with pytest.raises(TypeSystemError):
        MathType(
            structure=StructureKind.TENSOR,
            shape=Shape.of(2, 3),
            variance=(Variance.COVARIANT,),
        )


def test_addition_checks_shape_units_and_named_spaces() -> None:
    length = UnitDimension.base("L")
    velocity = length / UnitDimension.base("T")
    vector = MathType.vector(3, units=velocity, space_id="V")
    compatible = MathType.vector(3, units=velocity, space_id="V")
    assert vector.additive_result(compatible) == vector

    with pytest.raises(TypeSystemError):
        vector.additive_result(MathType.vector(4, units=velocity, space_id="V"))
    with pytest.raises(TypeSystemError):
        vector.additive_result(MathType.vector(3, units=length, space_id="V"))
    with pytest.raises(TypeSystemError):
        vector.additive_result(MathType.vector(3, units=velocity, space_id="W"))


def test_operator_composition_tracks_shape_spaces_and_units() -> None:
    inverse_time = UnitDimension.base("T").power(-1)
    acceleration_per_velocity = UnitDimension.base("T").power(-1)
    outer = MathType.linear_operator(
        4,
        3,
        units=inverse_time,
        domain_id="V",
        codomain_id="W",
    )
    inner = MathType.linear_operator(
        3,
        2,
        units=acceleration_per_velocity,
        domain_id="U",
        codomain_id="V",
    )
    result = outer.compose_result(inner)
    assert result.shape.to_dict() == [4, 2]
    assert result.domain_id == "U"
    assert result.codomain_id == "W"
    assert result.units == UnitDimension.base("T").power(-2)

    incompatible = MathType.linear_operator(5, 2, domain_id="U", codomain_id="X")
    with pytest.raises(TypeSystemError):
        outer.compose_result(incompatible)


def test_adjoint_swaps_domain_and_codomain() -> None:
    operator = MathType.linear_operator(5, 3, domain_id="U", codomain_id="V")
    adjoint = operator.adjoint_result()
    assert adjoint.shape.to_dict() == [3, 5]
    assert adjoint.domain_id == "V"
    assert adjoint.codomain_id == "U"


def test_tensor_product_tracks_operator_dimensions() -> None:
    left = MathType.linear_operator(2, 3, domain_id="U", codomain_id="V")
    right = MathType.linear_operator(5, 7, domain_id="X", codomain_id="Y")
    result = left.tensor_result(right)
    assert result.shape.to_dict() == [10, 21]
    assert result.domain_id == "tensor(U,X)"
    assert result.codomain_id == "tensor(V,Y)"


def test_math_type_json_round_trip_and_digest() -> None:
    original = MathType(
        structure=StructureKind.FIELD,
        scalar_system=ScalarSystem.REAL,
        shape=Shape.of("n", 3),
        units=UnitDimension.from_mapping({"L": 1, "T": -1}),
        variance=(Variance.NOT_APPLICABLE, Variance.CONTRAVARIANT),
        regularity=Regularity.C1,
        support="domain-Omega",
        domain_id="Omega",
        codomain_id="T-Omega",
        tags=("velocity", "physical"),
    )
    reconstructed = math_type_from_dict(original.to_dict())
    assert reconstructed == original
    assert reconstructed.digest() == original.digest()
    assert len(original.digest()) == 64


def test_typed_equation_program_is_valid_and_reproducible() -> None:
    program = typed_equation_program()
    report = program.validate()
    assert report.passed
    assert not report.issues
    payload = program.canonical_json()
    reconstructed = VLAProgram.from_json(payload)
    assert reconstructed.digest() == program.digest()
    assert reconstructed.canonical_json() == payload
    assert program.dependency_order().index("A") < program.dependency_order().index("eq")
    assert set(program.neighbors("eq")) == {"A", "assumption", "b", "residual", "x"}


def test_ir_rejects_duplicate_nodes_and_dangling_edges() -> None:
    program = VLAProgram("fixture", "Fixture")
    node = IRNode.build("x", NodeKind.SYMBOL, "x")
    program.add_node(node)
    with pytest.raises(IRError):
        program.add_node(node)
    with pytest.raises(IRError):
        program.add_edge(IREdge.build("x", "missing", EdgeKind.DEPENDS_ON))


def test_dependency_cycles_are_detected() -> None:
    provenance = Provenance("test")
    program = VLAProgram("cycle", "Cycle")
    for name in ("a", "b", "c"):
        program.add_node(IRNode.build(name, NodeKind.SYMBOL, name, provenance=provenance))
    program.add_edge(IREdge.build("a", "b", EdgeKind.DEPENDS_ON))
    program.add_edge(IREdge.build("b", "c", EdgeKind.DEPENDS_ON))
    program.add_edge(IREdge.build("c", "a", EdgeKind.DEPENDS_ON))
    with pytest.raises(IRError):
        program.dependency_order()
    report = program.validate()
    assert not report.passed
    assert any(issue.code == "DEPENDENCY_CYCLE" for issue in report.issues)


def test_untyped_operator_node_is_rejected_by_validation() -> None:
    provenance = Provenance("test")
    program = VLAProgram("bad", "Untyped operator")
    program.add_node(IRNode.build("A", NodeKind.OPERATOR, "A", provenance=provenance))
    report = program.validate()
    assert not report.passed
    assert any(issue.code == "UNTYPED_MATH_NODE" for issue in report.issues)


def test_adjoint_relation_checks_types() -> None:
    provenance = Provenance("test")
    operator = MathType.linear_operator(3, 2, domain_id="U", codomain_id="V")
    adjoint = operator.adjoint_result()
    program = VLAProgram("adjoint", "Adjoint")
    program.add_node(IRNode.build("A", NodeKind.OPERATOR, "A", math_type=operator, provenance=provenance))
    program.add_node(IRNode.build("Ah", NodeKind.OPERATOR, "A*", math_type=adjoint, provenance=provenance))
    program.add_edge(IREdge.build("Ah", "A", EdgeKind.ADJOINT_OF))
    assert program.validate().passed

    wrong = MathType.linear_operator(2, 3, domain_id="wrong", codomain_id="wrong")
    bad = VLAProgram("bad-adjoint", "Bad adjoint")
    bad.add_node(IRNode.build("A", NodeKind.OPERATOR, "A", math_type=operator, provenance=provenance))
    bad.add_node(IRNode.build("Ah", NodeKind.OPERATOR, "A*", math_type=wrong, provenance=provenance))
    bad.add_edge(IREdge.build("Ah", "A", EdgeKind.ADJOINT_OF))
    assert not bad.validate().passed


def test_merge_programs_namespaces_nodes_and_preserves_validity() -> None:
    left = typed_equation_program()
    right = typed_equation_program().clone(program_id="linear-system-copy")
    merged = merge_programs(
        (left, right),
        program_id="merged",
        title="Merged systems",
    )
    assert len(merged.nodes) == 2 * len(left.nodes)
    assert len(merged.edges) == 2 * len(left.edges)
    assert merged.validate().passed
    assert merged.metadata["merged_programs"] == ["linear-system-fixture", "linear-system-copy"]


def test_graphml_compiler_is_deterministic() -> None:
    program = typed_equation_program()
    first = compile_graphml(program)
    second = compile_graphml(program)
    assert first.content == second.content
    assert first.source_digest == program.digest()
    assert '<graph id="linear-system-fixture"' in first.content
    assert "theorem" not in first.content.lower()


def test_oak_program_report_passes_fixture_without_claims() -> None:
    report = audit_program(typed_equation_program())
    assert report.passed
    payload = report.to_dict()
    assert payload["status"] == "OAK_PASS_VLA_IR_FIXTURE_R0_3"
    assert payload["theorem_claimed"] is False
    assert payload["formal_proof_claimed"] is False
    assert payload["scientific_validation_claimed"] is False
    assert len(payload["gates"]) == 12
