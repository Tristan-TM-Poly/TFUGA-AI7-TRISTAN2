import pytest

from omega_game.bench import OAKBenchMetrics, OAKBenchRunner, default_engine_benchmarks


def test_oakbench_metrics_quality_is_bounded():
    metrics = OAKBenchMetrics(
        fun=1.0,
        agency=1.0,
        coherence=1.0,
        learning=1.0,
        safety=1.0,
        novelty=1.0,
        fairness=1.0,
        replayability=1.0,
        compression_gain=1.0,
        m_minus_reduction=1.0,
    )

    assert 0.0 <= metrics.quality() <= 1.0
    assert metrics.level() == "plus_ultra"


def test_oakbench_metrics_rejects_out_of_range_values():
    with pytest.raises(ValueError):
        OAKBenchMetrics(fun=1.5)


def test_oakbench_runner_runs_registered_benchmark():
    runner = OAKBenchRunner()
    runner.register("demo", lambda: default_engine_benchmarks().run_one("TextWorld-T"))

    result = runner.run_one("demo")

    assert result.engine == "TextWorld-T"
    assert 0.0 <= result.quality <= 1.0
    assert result.level in {"needs_work", "prototype", "good", "excellent", "plus_ultra"}


def test_default_oakbench_runs_all_current_engines():
    runner = default_engine_benchmarks()
    report = runner.report()

    assert report["benchmark"] == "OAKBench-GAME-T"
    assert report["engine_count"] == 5
    assert 0.0 <= report["average_quality"] <= 1.0
    assert {result["engine"] for result in report["results"]} == {
        "TextWorld-T",
        "BoardGame-T",
        "ScienceSandbox-T",
        "CircuitDungeon-T",
        "EnergyCivilization-T",
    }


def test_oakbench_result_to_dict_contains_metrics_and_notes():
    result = default_engine_benchmarks().run_one("CircuitDungeon-T")
    payload = result.to_dict()

    assert payload["engine"] == "CircuitDungeon-T"
    assert "metrics" in payload
    assert "notes" in payload
    assert 0.0 <= payload["quality"] <= 1.0
