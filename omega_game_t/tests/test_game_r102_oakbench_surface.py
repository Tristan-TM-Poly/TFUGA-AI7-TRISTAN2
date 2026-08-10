from __future__ import annotations

import json

from omega_game import (
    CapabilityRecord,
    FaultInjectionResult,
    IntegratedOAKBenchConfig,
    IntegratedOAKBenchReport,
    run_integrated_oakbench,
)
from omega_game.__main__ import main


def test_integrated_oakbench_is_exported_from_package_root() -> None:
    config = IntegratedOAKBenchConfig(
        seed=1601,
        max_steps=4,
        layout_count=3,
        campaign_shards=2,
        process_workers=1,
        fairness_threshold=0.50,
    )
    report = run_integrated_oakbench(config)
    assert isinstance(report, IntegratedOAKBenchReport)
    assert report.accepted
    assert all(isinstance(row, FaultInjectionResult) for row in report.fault_matrix)
    assert all(isinstance(row, CapabilityRecord) for row in report.capabilities)


def test_oakbench_cli_runs_same_integrated_gate(capsys) -> None:
    code = main(
        [
            "oakbench",
            "--seed", "1602",
            "--max-steps", "4",
            "--layouts", "3",
            "--shards", "2",
            "--workers", "1",
            "--fairness-threshold", "0.5",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert code == 0
    assert payload["accepted"] is True
    assert payload["invariant_checks"]["all_faults_detected"] is True
    assert len(payload["deterministic_receipt"]) == 64
