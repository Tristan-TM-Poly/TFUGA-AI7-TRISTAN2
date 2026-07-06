from omega_thesis_factory_t.core import build_page_tree, example_seed, oak_report


def test_example_seed_is_valid():
    seed = example_seed()
    seed.validate()
    assert seed.id == "OMEGA_THESIS_2N_GIT_T"
    assert seed.status == "C"
    assert seed.cvcd_invariants


def test_page_tree_depth_counts_are_binary():
    seed = example_seed()
    nodes = build_page_tree(seed, depth=3)
    assert len(nodes) == 15
    assert sum(1 for node in nodes if node.depth == 3) == 8
    assert {node.kind for node in nodes} == {"ROOT", "LOG", "EXP"}


def test_page_tree_depth_zero_returns_root_only():
    seed = example_seed()
    nodes = build_page_tree(seed, depth=0)
    assert len(nodes) == 1
    assert nodes[0].kind == "ROOT"
    assert nodes[0].parent_id is None


def test_oak_report_caps_claims_for_early_statuses():
    seed = example_seed()
    nodes = build_page_tree(seed, depth=2)
    report = oak_report(seed, nodes)
    assert report["total_nodes"] == 7
    assert report["frontier_pages"] == 4
    assert report["expected_total_nodes"] == 7
    assert report["blocked_promotions"]
    assert "pull_request" in report["git_targets"]
