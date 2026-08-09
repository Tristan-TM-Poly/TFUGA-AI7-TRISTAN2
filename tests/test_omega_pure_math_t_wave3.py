import operator

import pytest

from omega_pure_math_t.defect_hierarchy import (
    associator,
    commutator,
    nested_commutator,
    sampled_defect_signature,
)
from omega_pure_math_t.local_global import (
    Section,
    compatibility_obstructions,
    cover_is_complete,
    glue_sections,
)
from omega_pure_math_t.multigraded import (
    GradedElement,
    OutputChannel,
    graded_associativity_defect,
    multiply_multigraded,
    standard_graded_rule,
)
from omega_pure_math_t.proof_compression import ProofSupport, minimum_proof_library


def test_defect_hierarchy_separates_associativity_and_commutativity():
    assert commutator(2, 3, operator.mul) == 0
    assert associator(2, 3, 4, operator.mul) == 0
    assert nested_commutator([2, 3, 4], operator.mul) == 0
    signature = sampled_defect_signature([-1, 0, 1], operator.sub)
    assert signature["max_commutator"] > 0
    assert signature["max_associator"] > 0


def test_standard_multigraded_product_is_associative_on_basis_elements():
    x = GradedElement.basis(1)
    y = GradedElement.basis(2)
    z = GradedElement.basis(3)
    product = multiply_multigraded(x, y, standard_graded_rule)
    assert product.as_dict() == {3: 1.0}
    assert graded_associativity_defect(x, y, z, standard_graded_rule).norm() == 0


def test_multigraded_rule_can_expose_nonassociativity():
    def asymmetric_rule(p: int, q: int):
        return (OutputChannel(p + q, p + 1.0),)

    x = GradedElement.basis(1)
    defect = graded_associativity_defect(x, x, x, asymmetric_rule)
    assert defect.as_dict() == {3: 2.0}
    assert defect.norm() == 2.0


def test_finite_local_sections_glue_when_overlaps_agree():
    left = Section.from_mapping("U", {"a": 1, "b": 2})
    right = Section.from_mapping("V", {"b": 2, "c": 3})
    assert not compatibility_obstructions([left, right])
    assert cover_is_complete([left, right], {"a", "b", "c"})
    global_section = glue_sections([left, right])
    assert global_section.as_dict() == {"a": 1, "b": 2, "c": 3}


def test_finite_local_sections_return_overlap_obstruction():
    left = Section.from_mapping("U", {"x": 1})
    right = Section.from_mapping("V", {"x": 2})
    obstruction = compatibility_obstructions([left, right])
    assert len(obstruction) == 1
    assert obstruction[0].point == "x"
    with pytest.raises(ValueError, match="gluing obstruction"):
        glue_sections([left, right])


def test_exact_proof_library_compression_finds_shared_minimum():
    supports = [
        ProofSupport("T1", frozenset({"A", "B"})),
        ProofSupport("T1", frozenset({"C"})),
        ProofSupport("T2", frozenset({"B", "C"})),
        ProofSupport("T2", frozenset({"D"})),
    ]
    result = minimum_proof_library(supports)
    assert result is not None
    assert result.cost == 2.0
    assert len(result.lemmas) == 2
    assert {support.theorem for support in result.selected_supports} == {"T1", "T2"}
