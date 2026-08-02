from pathlib import Path
from omega_pct_t.core import DimensionVector, ModelRegistry, ParticleFieldHypergraph

CATALOG = Path(__file__).parents[1] / "data" / "omega_pct_catalog.json"

def test_catalog_loads_and_validates():
    registry = ModelRegistry.from_catalog(CATALOG)
    assert len(registry.fields) >= 20
    assert len(registry.particles) >= 40
    errors = [issue for issue in registry.validate() if issue.severity == "error"]
    assert errors == []

def test_qed_charge_and_lepton_numbers_are_conserved():
    registry = ModelRegistry.from_catalog(CATALOG)
    assert registry.interaction_balance("interaction.qed.emu_elastic") == {}

def test_hypergraph_is_deterministic():
    registry = ModelRegistry.from_catalog(CATALOG)
    left = registry.build_hypergraph()
    right = registry.build_hypergraph()
    assert left.digest() == right.digest()
    assert len(left.nodes) == len(registry.fields) + len(registry.particles)
    assert "particle.electron" in left.nodes
    assert left.neighborhood("particle.electron")["incoming"]

def test_dimension_vector_arithmetic():
    energy = DimensionVector(mass=1)
    inverse_energy = DimensionVector(mass=-1)
    assert (energy + inverse_energy).dimensionless
    assert energy.scaled(4) == DimensionVector(mass=4)
