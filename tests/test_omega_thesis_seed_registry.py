from omega_thesis_factory_t.core import build_page_tree, oak_report
from omega_thesis_factory_t.seed_registry import CANONICAL_SEED_IDS, canonical_seed, canonical_seeds


def test_registry_contains_first_five_canonical_seeds():
    seeds = canonical_seeds()
    assert tuple(seeds) == CANONICAL_SEED_IDS
    assert len(seeds) == 5


def test_all_registry_seeds_validate_and_expand():
    for seed in canonical_seeds().values():
        seed.validate()
        nodes = build_page_tree(seed, depth=2)
        report = oak_report(seed, nodes)
        assert report["total_nodes"] == 7
        assert report["frontier_pages"] == 4
        assert report["oak_risks"]
        assert report["blocked_promotions"]


def test_canonical_seed_lookup_by_id():
    seed = canonical_seed("OMEGA_TRANSFORM_T")
    assert seed.id == "OMEGA_TRANSFORM_T"
    assert "compression" in seed.domain
