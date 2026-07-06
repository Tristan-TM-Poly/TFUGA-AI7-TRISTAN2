from omega_thesis_factory_t.company_map import company_map
from omega_thesis_factory_t.pack import make_pack
from omega_thesis_factory_t.seed_registry import canonical_seed, canonical_seeds


def test_make_pack_contains_seed_nodes_and_report():
    seed = canonical_seed("OMEGA_TRANSFORM_T")
    pack = make_pack(seed, depth=2)
    assert pack["seed"]["id"] == "OMEGA_TRANSFORM_T"
    assert len(pack["nodes"]) == 7
    assert pack["report"]["frontier_pages"] == 4


def test_company_map_is_cautious_for_all_seeds():
    for seed in canonical_seeds().values():
        mapping = company_map(seed)
        assert mapping["seed_id"] == seed.id
        assert mapping["product_hypotheses"]
        assert "guaranteed revenue" in mapping["blocked_claims"]
        assert "risk controls" in mapping["must_validate"]
