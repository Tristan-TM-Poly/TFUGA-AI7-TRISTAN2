from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools.production_quality_observatory import (
    ObservatoryError,
    evaluate,
    load_json,
    render_markdown,
    validate_snapshot,
)


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "reports" / "production_quality_snapshot_2026-08-02.json"
POLICY_PATH = ROOT / "policies" / "omega_production_quality_observatory_r0_1.json"


def snapshot() -> dict:
    return load_json(SNAPSHOT_PATH)


def policy() -> dict:
    return load_json(POLICY_PATH)


def test_current_snapshot_routes_to_wip_reduction_and_externalization() -> None:
    report = evaluate(snapshot(), policy())

    assert report["decision"] == "REDUCE_WIP_AND_EXTERNALIZE"
    assert report["gates"]["volume"]["status"] == "GREEN"
    assert report["gates"]["integration"]["status"] == "GREEN"
    assert report["gates"]["wip"]["status"] == "RED"
    assert report["gates"]["external_science"]["status"] == "RED"
    assert report["gates"]["external_product"]["status"] == "RED"
    assert report["scalar_score_has_final_authority"] is False


def test_quadrillion_virtual_plan_cannot_satisfy_execution_gate() -> None:
    payload = snapshot()
    payload["volume_classes"]["actual_materialized_or_executed_minimum"]["value"] = 1
    payload["volume_classes"]["largest_virtual_plan"]["value"] = 10**15

    report = evaluate(payload, policy())

    assert report["gates"]["volume"]["status"] == "RED"
    assert report["gates"]["volume"]["actual_minimum"] == 1
    assert report["gates"]["volume"]["largest_virtual_plan"] == 10**15
    assert report["gates"]["volume"]["virtual_plan_excluded"] is True


def test_selective_expansion_requires_low_wip_and_external_signals() -> None:
    payload = snapshot()
    payload["repository_state"]["open_pull_requests"] = 3
    payload["repository_state"]["open_pr_commit_associations"] = 30
    external = payload["external_evidence_observed_in_scope"]
    external["real_instrument_datasets_with_provenance"] = 1
    external["external_pilots"] = 1

    report = evaluate(payload, policy())

    assert report["decision"] == "SELECTIVE_EXPANSION_ALLOWED"
    assert report["gates"]["wip"]["status"] == "GREEN"
    assert report["gates"]["external_science"]["status"] == "GREEN"
    assert report["gates"]["external_product"]["status"] == "GREEN"


def test_virtual_plan_must_be_explicitly_non_materialized() -> None:
    payload = snapshot()
    payload["volume_classes"]["largest_virtual_plan"]["materialized"] = True

    with pytest.raises(ObservatoryError, match="non-materialized"):
        validate_snapshot(payload)


def test_negative_metrics_are_rejected() -> None:
    payload = snapshot()
    payload["repository_state"]["open_pull_requests"] = -1

    with pytest.raises(ObservatoryError, match="Negative values"):
        validate_snapshot(payload)


def test_markdown_report_is_deterministic_and_contains_oak_boundary() -> None:
    report = evaluate(snapshot(), policy())
    first = render_markdown(report)
    second = render_markdown(copy.deepcopy(report))

    assert first == second
    assert "REDUCE_WIP_AND_EXTERNALIZE" in first
    assert "A virtual plan is not execution" in first
    assert "scalar score has no final authority" in first


def test_snapshot_and_policy_are_valid_json_objects() -> None:
    assert isinstance(json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8")), dict)
    assert isinstance(json.loads(POLICY_PATH.read_text(encoding="utf-8")), dict)
