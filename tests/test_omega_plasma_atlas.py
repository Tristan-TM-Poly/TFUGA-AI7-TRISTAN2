from omega_plasma_t.atlas import *

def test_atlas_is_large_sharded_and_queryable():
    manifest=regime_lattice_manifest()
    rows=list(iter_regime_lattice())
    assert manifest["permanent_cap"] is False
    assert len(rows)==manifest["total_cells"]
    assert len(rows)>10000
    assert search_atlas("tearing")

def test_benchmark_model_matrix_is_cross_product():
    rows=list(iter_benchmark_model_matrix())
    assert len(rows)==len(benchmarks())*len(models())
