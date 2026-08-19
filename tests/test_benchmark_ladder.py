from tools.benchmark_ladder import BenchmarkLevel, assess_benchmark_level


def test_no_benchmark_is_b0():
    assessment = assess_benchmark_level()
    assert assessment.level == BenchmarkLevel.B0_NONE


def test_simple_baseline_is_b3():
    assessment = assess_benchmark_level(simple_baseline=True)
    assert assessment.level == BenchmarkLevel.B3_SIMPLE_BASELINE


def test_reproducible_is_b7():
    assessment = assess_benchmark_level(reproducible=True)
    assert assessment.level == BenchmarkLevel.B7_REPRODUCIBLE_BENCHMARK
