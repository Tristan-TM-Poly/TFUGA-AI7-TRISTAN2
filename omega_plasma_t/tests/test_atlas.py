from omega_plasma_t.atlas import *
def test_atlas_is_large_and_queryable():
    m=regime_lattice_manifest(); rows=list(iter_regime_lattice())
    assert m["permanent_cap"] is False and len(rows)==m["total_cells"] and len(rows)>10000
    assert search_atlas("tearing")
def test_benchmark_model_matrix(): assert len(list(iter_benchmark_model_matrix()))==len(benchmarks())*len(models())
