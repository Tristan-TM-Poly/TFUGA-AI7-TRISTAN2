from omega_recycle.adapters import adapt_asset_records, battery_mine_record, building_mine_record, electronics_mine_record
from omega_recycle.provenance import canonical_dataset_hash, sha256_bytes
from omega_recycle.urban_mine import aggregate_recoverable_stock


def test_domain_adapters_feed_urban_mine_without_claim_inflation() -> None:
    records = (
        electronics_mine_record(zone="Mtl", year=2026, material="copper", stock_mass_kg=100.0, accessible_fraction=0.8, recovery_yield=0.9),
        battery_mine_record(zone="Mtl", year=2026, material="copper", stock_mass_kg=50.0, accessible_fraction=0.5, recovery_yield=0.8),
        building_mine_record(zone="Mtl", year=2026, material="steel", stock_mass_kg=200.0, accessible_fraction=0.6, recovery_yield=0.95),
    )
    adapted = adapt_asset_records(records)
    aggregated = aggregate_recoverable_stock(adapted)
    assert abs(aggregated[("Mtl", 2026, "copper")] - 92.0) < 1e-12
    assert abs(aggregated[("Mtl", 2026, "steel")] - 114.0) < 1e-12


def test_provenance_hashes_are_deterministic() -> None:
    assert sha256_bytes(b"omega") == sha256_bytes(b"omega")
    a = canonical_dataset_hash([{"b": 2, "a": 1}])
    b = canonical_dataset_hash([{"a": 1, "b": 2}])
    assert a == b
    assert len(a) == 64
