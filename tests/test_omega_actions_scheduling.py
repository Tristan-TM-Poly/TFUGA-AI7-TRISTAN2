from __future__ import annotations

from omega_actions_t.digital_twin import (
    derive_worker_sweep,
    limited_worker_simulation,
    simulate_workflow,
    unlimited_parallel_simulation,
)
from omega_actions_t.sharding import shard_tests


def test_historical_sharding_balances_work_and_prioritizes_failure_value() -> None:
    payload = {
        "tests": [
            {"nodeid": "t1", "duration_seconds": 10, "runs": 10, "failures": 0},
            {"nodeid": "t2", "duration_seconds": 9, "runs": 10, "failures": 4},
            {"nodeid": "t3", "duration_seconds": 6, "runs": 10, "failures": 1},
            {"nodeid": "t4", "duration_seconds": 5, "runs": 10, "failures": 0},
        ]
    }
    report = shard_tests(payload, shards=2)
    assert report["aggregate"]["shard_count"] == 2
    assert report["aggregate"]["estimated_total_seconds"] == 30.0
    assert report["aggregate"]["estimated_parallel_wall_seconds"] <= 16.0
    all_nodeids = [nodeid for shard in report["shards"] for nodeid in shard["nodeids"]]
    assert sorted(all_nodeids) == ["t1", "t2", "t3", "t4"]
    t2 = next(test for shard in report["shards"] for test in shard["tests"] if test["nodeid"] == "t2")
    t1 = next(test for shard in report["shards"] for test in shard["tests"] if test["nodeid"] == "t1")
    assert t2["posterior_failure_probability"] > t1["posterior_failure_probability"]


def test_digital_twin_finds_critical_path_and_worker_speedup() -> None:
    workflow = {
        "path": ".github/workflows/ci.yml",
        "jobs": [
            {"name": "lint", "needs": []},
            {"name": "unit", "needs": []},
            {"name": "integration", "needs": ["unit"]},
            {"name": "package", "needs": ["lint", "integration"]},
        ],
    }
    durations = {"lint": 2.0, "unit": 5.0, "integration": 7.0, "package": 3.0}
    unlimited = unlimited_parallel_simulation(workflow, durations)
    assert unlimited["wall_seconds"] == 15.0
    assert unlimited["critical_path"] == ["unit", "integration", "package"]
    serial = limited_worker_simulation(workflow, 1, durations)
    assert serial["wall_seconds"] == 17.0
    twin = simulate_workflow(workflow, durations)
    assert twin["worker_sweep"][0]["workers"] == 1
    assert abs(twin["unlimited"]["max_theoretical_speedup"] - (17.0 / 15.0)) < 1e-6
    assert derive_worker_sweep(5) == [1, 2, 4, 5]
