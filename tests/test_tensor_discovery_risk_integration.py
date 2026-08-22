from sage_tristan.tensor_discovery_bench import compile_report


def test_r07_meta_routing_declares_r061_cumulative_risk_dependency():
    report = compile_report()
    assert report["release"] == "R0.7"
    assert report["meta_routing_uses_cumulative_risk_gate"] is True
    assert report["meta_llmt_automatically_superior"] is False
    assert report["benchmark_proxy_only"] is True
