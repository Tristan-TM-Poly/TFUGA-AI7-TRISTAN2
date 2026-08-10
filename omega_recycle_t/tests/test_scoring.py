from omega_recycle import Component, Material, RecoveryMode, RecoveryRoute, circularity_score, evaluate_route, material_entropy

MATERIALS = {"copper": Material("copper", 8.0), "polymer": Material("polymer", 0.5)}


def component(functional_probability: float = 0.9) -> Component:
    return Component(component_id="c1", name="motor", mass_kg=5.0, material_fractions={"copper": 0.4, "polymer": 0.6}, reuse_value=120.0, functional_probability=functional_probability)


def test_structure_preservation_can_beat_material_recycling() -> None:
    c = component()
    reuse = evaluate_route(c, MATERIALS, RecoveryRoute(RecoveryMode.REUSE))
    recycle = evaluate_route(c, MATERIALS, RecoveryRoute(RecoveryMode.MATERIAL_RECYCLE, process_cost=2.0, retained_mass_fraction=0.9))
    assert reuse.score > recycle.score


def test_material_entropy_is_normalized() -> None:
    h = material_entropy(component())
    assert 0.0 < h <= 1.0


def test_single_material_has_zero_entropy() -> None:
    c = Component(component_id="pure", name="pure copper", mass_kg=1.0, material_fractions={"copper": 1.0}, reuse_value=0.0)
    assert material_entropy(c) == 0.0


def test_circularity_score_is_bounded() -> None:
    score = circularity_score(recovered_value_value=150, input_value=100, retained_mass_kg=12, input_mass_kg=10, output_quality=1.0, expected_future_cycles=5)
    assert score == 1.0
