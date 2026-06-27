from omega_game import ProductBenchMetrics, TheorySpec, default_product_bench, default_productizer, default_theory_compiler


def _product_for(theory_name: str):
    world = default_theory_compiler().compile(TheorySpec(theory_name))
    return default_productizer().productize(world)


def test_product_bench_scores_are_bounded():
    product = _product_for("Ω-CIRCUITS-T")
    result = default_product_bench().evaluate(product)

    assert 0.0 <= result.score <= 1.0
    assert result.level in {"needs_work", "prototype", "priority", "excellent", "plus_ultra"}
    assert result.product_name == product.product_name


def test_product_bench_metrics_reject_out_of_range_value():
    try:
        ProductBenchMetrics(value=1.5)
    except ValueError as exc:
        assert "value" in str(exc)
    else:
        raise AssertionError("ProductBenchMetrics accepted value outside [0, 1]")


def test_product_bench_to_dict_has_contract_keys():
    payload = default_product_bench().evaluate(_product_for("Ω-ENERGY-T")).to_dict()

    assert set(payload) == {"product_name", "target_engine", "score", "level", "metrics", "notes"}
    assert payload["metrics"]
    assert payload["notes"]


def test_product_bench_many_preserves_count():
    bench = default_product_bench()
    products = [_product_for("Ω-CIRCUITS-T"), _product_for("Ω-ENERGY-T")]
    results = bench.evaluate_many([(product, None) for product in products])

    assert len(results) == 2
