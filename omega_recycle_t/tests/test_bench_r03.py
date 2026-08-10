from omega_recycle.bench import run_oakbench


def test_r03_bench_crosschecks_solver_and_claim_boundaries() -> None:
    bench = run_oakbench()
    assert bench["bench_version"] == "0.3.0"
    assert bench["solver_crosscheck"]["score_equal"] is True
    assert bench["solver_crosscheck"]["modes_equal"] is True
    assert bench["solver_crosscheck"]["optimality_certified"] is True
    assert bench["lca_inventory"]["claim_boundary"] == "inventory_only_no_lifecycle_impact_claim"
