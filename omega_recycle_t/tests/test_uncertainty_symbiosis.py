from omega_recycle import Component, Material, MaterialNeed, MaterialOffer, RecoveryMode, RecoveryRoute, functional_probability_sweep, match_material_flows, switching_thresholds


def test_probability_sweep_detects_regimes() -> None:
    materials = {"copper": Material("copper", 50.0)}
    component = Component("x", "assembly", 2.0, {"copper": 1.0}, reuse_value=120.0)
    routes = (RecoveryRoute(RecoveryMode.REUSE), RecoveryRoute(RecoveryMode.MATERIAL_RECYCLE))
    sweep = functional_probability_sweep(component, materials, routes, steps=11)
    thresholds = switching_thresholds(sweep)
    assert len(sweep) == 11
    assert thresholds[0].probability == 0.0
    assert len({point.winning_mode for point in sweep}) >= 2


def test_symbiosis_match_respects_purity_and_price() -> None:
    offers = (MaterialOffer("plant-a", "copper", 100.0, purity=0.95, unit_price=4.0, distance_km=10), MaterialOffer("plant-b", "copper", 50.0, purity=0.70, unit_price=2.0, distance_km=1))
    needs = (MaterialNeed("plant-c", "copper", 80.0, min_purity=0.90, max_unit_price=5.0),)
    matches = match_material_flows(offers, needs, transport_cost_per_kg_km=0.01)
    assert len(matches) == 1
    assert matches[0].seller == "plant-a"
    assert matches[0].quantity_kg == 80.0
