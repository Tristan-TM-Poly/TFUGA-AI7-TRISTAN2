from __future__ import annotations

import json

from omega_game.__main__ import main
from omega_game.engines.scale_bench import (
    ScaleScenario,
    run_scale_bench,
    run_scale_scenario,
)


def _tiny(name: str = "tiny", seed: int = 1801, workers: int = 1) -> ScaleScenario:
    return ScaleScenario(
        name,
        seed=seed,
        population_size=3,
        seed_count=1,
        max_steps=4,
        shard_count=1,
        repetitions=2,
        process_workers=workers,
    )


def test_scale_scenario_job_formula_and_campaign_invariants() -> None:
    scenario = ScaleScenario(
        "formula",
        seed=1810,
        population_size=4,
        seed_count=2,
        max_steps=4,
        shard_count=2,
        repetitions=1,
        process_workers=1,
    )
    result = run_scale_scenario(scenario)
    assert scenario.expected_job_count == 24
    assert result.job_count == 24
    assert result.accepted
    assert all(result.invariant_checks.values())
    assert result.match_ticks_work_units > 0
    assert result.event_work_units > 0


def test_scale_scenario_deterministic_receipt_repeats() -> None:
    scenario = _tiny(seed=1820)
    first = run_scale_scenario(scenario)
    second = run_scale_scenario(scenario)
    assert first.deterministic_payload() == second.deterministic_payload()
    assert first.deterministic_receipt == second.deterministic_receipt


def test_empirical_measurements_are_excluded_from_deterministic_payload() -> None:
    result = run_scale_scenario(_tiny(seed=1830))
    payload = result.deterministic_payload()
    assert "empirical_wall_clock_seconds" not in payload
    assert "empirical_median_repetition_seconds" not in payload
    assert "empirical_peak_tracemalloc_bytes" not in payload
    assert "observed_process_speedup" not in payload
    assert result.empirical_wall_clock_seconds >= 0
    assert result.empirical_median_repetition_seconds >= 0
    assert result.empirical_peak_tracemalloc_bytes >= 0


def test_small_process_comparison_keeps_checkpoint_equivalence() -> None:
    result = run_scale_scenario(_tiny(name="process", seed=1840, workers=2))
    assert result.accepted
    assert result.invariant_checks["process_checkpoint_equivalent"] is True
    if result.observed_process_speedup is not None:
        assert result.observed_process_speedup >= 0


def test_scale_bench_multi_scenario_receipt_is_deterministic() -> None:
    scenarios = (
        _tiny(name="a", seed=1850),
        ScaleScenario(
            "b",
            seed=1851,
            population_size=4,
            seed_count=1,
            max_steps=4,
            shard_count=2,
            repetitions=1,
            process_workers=1,
        ),
    )
    first = run_scale_bench(scenarios)
    second = run_scale_bench(scenarios)
    assert first.accepted and second.accepted
    assert first.deterministic_payload() == second.deterministic_payload()
    assert first.deterministic_receipt == second.deterministic_receipt
    assert [row.job_count for row in first.scenarios] == [6, 12]


def test_scale_bench_cli_runs_bounded_single_scenario(capsys) -> None:
    code = main(
        [
            "scale-bench",
            "--seed", "1870",
            "--population", "3",
            "--seed-count", "1",
            "--max-steps", "4",
            "--shards", "1",
            "--repetitions", "1",
            "--workers", "1",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["accepted"] is True
    assert payload["scenarios"][0]["job_count"] == 6
    assert len(payload["deterministic_receipt"]) == 64


def test_scale_bench_invalid_contracts_fail_closed() -> None:
    invalid = (
        ScaleScenario("", population_size=3),
        ScaleScenario("bad-pop", population_size=1),
        ScaleScenario("bad-seeds", seed_count=0),
        ScaleScenario("bad-steps", max_steps=0),
        ScaleScenario("bad-shards", shard_count=0),
        ScaleScenario("bad-reps", repetitions=0),
        ScaleScenario("bad-workers", process_workers=0),
    )
    for scenario in invalid:
        try:
            run_scale_scenario(scenario)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid scenario should fail: {scenario}")

    try:
        run_scale_bench(())
    except ValueError:
        pass
    else:
        raise AssertionError("empty ScaleBench should fail")

    duplicate = (_tiny("same", 1860), _tiny("same", 1861))
    try:
        run_scale_bench(duplicate)
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate ScaleBench scenario names should fail")
