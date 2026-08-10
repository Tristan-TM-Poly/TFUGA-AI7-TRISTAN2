from omega_recycle import Component, MaterialPassport, ResourceGraph


def sample_component(component_id: str) -> Component:
    return Component(component_id=component_id, name="assembly", mass_kg=1.5, material_fractions={"steel": 1.0}, reuse_value=25.0)


def test_material_passport_roundtrip() -> None:
    passport = MaterialPassport(product_id="p1", schema_version="0.1", components=(sample_component("a"),), provenance="synthetic-test")
    restored = MaterialPassport.from_json(passport.to_json())
    assert restored == passport


def test_resource_graph_hyperedge_and_mass() -> None:
    graph = ResourceGraph()
    graph.add_component(sample_component("a"))
    graph.add_component(sample_component("b"))
    graph.add_hyperedge("fastened_to", ("a", "b"))
    assert graph.total_mass_kg() == 3.0
    assert graph.hyperedges[0].relation == "fastened_to"
