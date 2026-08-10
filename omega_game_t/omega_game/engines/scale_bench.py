from __future__ import annotations

import hashlib
import json
import math
import time
import tracemalloc
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .campaign import benchmark_campaign, plan_campaign, run_campaign_slice
from .campaign_runtime import compare_process_execution
from .evolution import seed_population
from .simulation import ArenaConfig


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class ScaleScenario:
    name: str
    seed: int = 1801
    population_size: int = 4
    seed_count: int = 2
    max_steps: int = 8
    shard_count: int = 2
    repetitions: int = 2
    process_workers: int = 1

    def validate(self) -> None:
        if not self.name:
            raise ValueError("scenario name cannot be empty")
        if self.population_size < 2:
            raise ValueError("population_size must be >= 2")
        if self.seed_count < 1:
            raise ValueError("seed_count must be >= 1")
        if self.max_steps < 1:
            raise ValueError("max_steps must be >= 1")
        if self.shard_count < 1:
            raise ValueError("shard_count must be >= 1")
        if self.repetitions < 1:
            raise ValueError("repetitions must be >= 1")
        if self.process_workers < 1:
            raise ValueError("process_workers must be >= 1")

    @property
    def expected_job_count(self) -> int:
        # No explicit layout set in R1.0.5 ScaleBench: one implicit arena per job.
        # Mirrored round-robin gives two orientations per unordered pair.
        return math.comb(self.population_size, 2) * self.seed_count * 2


@dataclass(frozen=True)
class ScaleScenarioResult:
    scenario: ScaleScenario
    accepted: bool
    invariant_checks: dict[str, bool]
    job_count: int
    match_ticks_work_units: int
    event_work_units: int
    checkpoint_receipt: str
    benchmark_receipt: str
    deterministic_receipt: str
    empirical_wall_clock_seconds: float
    empirical_median_repetition_seconds: float
    empirical_peak_tracemalloc_bytes: int
    observed_process_speedup: float | None

    def deterministic_payload(self) -> dict[str, Any]:
        return {
            "scenario": asdict(self.scenario),
            "accepted": self.accepted,
            "invariant_checks": {
                key: self.invariant_checks[key] for key in sorted(self.invariant_checks)
            },
            "job_count": self.job_count,
            "match_ticks_work_units": self.match_ticks_work_units,
            "event_work_units": self.event_work_units,
            "checkpoint_receipt": self.checkpoint_receipt,
            "benchmark_receipt": self.benchmark_receipt,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.deterministic_payload(),
            "deterministic_receipt": self.deterministic_receipt,
            "empirical_wall_clock_seconds": self.empirical_wall_clock_seconds,
            "empirical_median_repetition_seconds": self.empirical_median_repetition_seconds,
            "empirical_peak_tracemalloc_bytes": self.empirical_peak_tracemalloc_bytes,
            "observed_process_speedup": self.observed_process_speedup,
        }


@dataclass(frozen=True)
class ScaleBenchReport:
    accepted: bool
    scenarios: tuple[ScaleScenarioResult, ...]
    deterministic_receipt: str

    def deterministic_payload(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "scenarios": [result.deterministic_payload() for result in self.scenarios],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "scenarios": [result.to_dict() for result in self.scenarios],
            "deterministic_receipt": self.deterministic_receipt,
            "boundaries": [
                "wall clock is empirical and excluded from deterministic receipts",
                "tracemalloc peak is a local Python-allocation observation, not total process RSS",
                "observed process speedup is not guaranteed speedup",
                "larger tested workload does not prove unbounded scalability",
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def run_scale_scenario(scenario: ScaleScenario) -> ScaleScenarioResult:
    scenario.validate()
    population = seed_population(
        scenario.population_size,
        seed=scenario.seed,
        prefix=f"scale-{scenario.name}",
    )
    seeds = tuple(scenario.seed + index for index in range(scenario.seed_count))
    manifest = plan_campaign(
        population,
        seeds=seeds,
        arena_template=ArenaConfig(max_steps=scenario.max_steps),
        mirrored=True,
        shard_count=scenario.shard_count,
    )

    tracemalloc.start()
    start = time.perf_counter()
    checkpoint, slice_report = run_campaign_slice(manifest)
    empirical_wall = time.perf_counter() - start
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    benchmark = benchmark_campaign(manifest, repetitions=scenario.repetitions)
    process_equivalent = True
    observed_speedup: float | None = None
    if scenario.process_workers > 1:
        comparison = compare_process_execution(
            manifest,
            workers=scenario.process_workers,
        )
        process_equivalent = comparison.deterministic_equivalence
        observed_speedup = comparison.observed_speedup

    invariant_checks = {
        "job_count_matches_formula": manifest.job_count == scenario.expected_job_count,
        "campaign_complete": slice_report.complete_campaign,
        "checkpoint_covers_all_jobs": len(checkpoint.completed) == manifest.job_count,
        "benchmark_job_count_matches": benchmark.job_count == manifest.job_count,
        "ticks_repeat_deterministically": len(set(benchmark.deterministic_ticks_per_run)) == 1,
        "events_repeat_deterministically": len(set(benchmark.deterministic_events_per_run)) == 1,
        "process_checkpoint_equivalent": process_equivalent,
    }
    accepted = all(invariant_checks.values())
    deterministic_payload = {
        "scenario": asdict(scenario),
        "accepted": accepted,
        "invariant_checks": {
            key: invariant_checks[key] for key in sorted(invariant_checks)
        },
        "job_count": manifest.job_count,
        "match_ticks_work_units": slice_report.match_ticks_work_units,
        "event_work_units": slice_report.event_work_units,
        "checkpoint_receipt": checkpoint.checkpoint_receipt,
        "benchmark_receipt": benchmark.result_receipt,
    }
    return ScaleScenarioResult(
        scenario=scenario,
        accepted=accepted,
        invariant_checks=invariant_checks,
        job_count=manifest.job_count,
        match_ticks_work_units=slice_report.match_ticks_work_units,
        event_work_units=slice_report.event_work_units,
        checkpoint_receipt=checkpoint.checkpoint_receipt,
        benchmark_receipt=benchmark.result_receipt,
        deterministic_receipt=_canonical_hash(deterministic_payload),
        empirical_wall_clock_seconds=round(empirical_wall, 9),
        empirical_median_repetition_seconds=benchmark.median_wall_clock_seconds,
        empirical_peak_tracemalloc_bytes=int(peak_bytes),
        observed_process_speedup=observed_speedup,
    )


def default_scale_scenarios(*, seed: int = 1801) -> tuple[ScaleScenario, ...]:
    return (
        ScaleScenario(
            "tiny",
            seed=seed,
            population_size=3,
            seed_count=1,
            max_steps=4,
            shard_count=1,
            repetitions=2,
            process_workers=1,
        ),
        ScaleScenario(
            "small",
            seed=seed + 100,
            population_size=4,
            seed_count=2,
            max_steps=6,
            shard_count=2,
            repetitions=2,
            process_workers=2,
        ),
        ScaleScenario(
            "medium",
            seed=seed + 200,
            population_size=6,
            seed_count=2,
            max_steps=8,
            shard_count=3,
            repetitions=1,
            process_workers=2,
        ),
    )


def run_scale_bench(
    scenarios: Iterable[ScaleScenario] | None = None,
    *,
    seed: int = 1801,
) -> ScaleBenchReport:
    selected = tuple(default_scale_scenarios(seed=seed) if scenarios is None else scenarios)
    if not selected:
        raise ValueError("ScaleBench requires at least one scenario")
    names = [scenario.name for scenario in selected]
    if len(set(names)) != len(names):
        raise ValueError("ScaleBench scenario names must be unique")
    results = tuple(run_scale_scenario(scenario) for scenario in selected)
    accepted = all(result.accepted for result in results)
    deterministic_payload = {
        "accepted": accepted,
        "scenarios": [result.deterministic_payload() for result in results],
    }
    return ScaleBenchReport(
        accepted=accepted,
        scenarios=results,
        deterministic_receipt=_canonical_hash(deterministic_payload),
    )
