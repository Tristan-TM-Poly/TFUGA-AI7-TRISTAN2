from omega_patent_thesis_t import claim_tree, example_seed, gitpack_paths, risk_level, value_map


def test_example_seed_validates():
    seed = example_seed()
    seed.validate()
    assert seed.patent_id == "EXAMPLE-PATENT-T"


def test_claim_tree_has_root_and_claims():
    tree = claim_tree(example_seed())
    assert tree["root"]
    assert len(tree["independent"]) == 1


def test_risk_level_defaults_to_review():
    assert risk_level(example_seed()) == "review"


def test_value_map_has_checks():
    got = value_map(example_seed())
    assert "checks" in got
    assert got["risk_level"] == "review"


def test_gitpack_paths_are_namespaced():
    paths = gitpack_paths(example_seed())
    assert paths["manifest"][0].startswith("patents/example-patent-t")
