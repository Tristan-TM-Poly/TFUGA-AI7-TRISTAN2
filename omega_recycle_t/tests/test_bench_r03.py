from omega_recycle.bench import run_oakbench


def test_r03_contract_survives_later_bench_versions() -> None:
    bench = run_oakbench()
    assert bench["compatibility"]["r03_contract_preserved"] is True
    assert bench["solver_crosscheck"]["score_equal"] is True
    assert bench["solver_crosscheck"]["modes_equal"] is True
    assert bench["solver_crosscheck"]["optimality_certified"] is True
    assert bench["lca_inventory"]["claim_boundary"] == "inventory_only_no_lifecycle_impact_claim"
