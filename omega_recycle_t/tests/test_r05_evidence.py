import math

from omega_recycle.campaign import PredictionCase, evaluate_prediction_campaign
from omega_recycle.epa import parse_epa_smm_normalized_csv, short_tons_to_metric_tonnes
from omega_recycle.eurostat import adapt_env_wasmun_tsv
from omega_recycle.general_network import BalanceNode, DirectedArc, min_cost_general_flow
from omega_recycle.r05_evidence import run_r05_evidence
from omega_recycle.revision import compare_record_snapshots
from omega_recycle.temporal_calibration import TimedProbabilisticObservation, temporal_calibration_report
from omega_recycle.temporal_network import TemporalArc, TemporalBalance, solve_time_expanded_flow


def test_eurostat_env_wasmun_schema_units_and_status_flags() -> None:
    text = "freq,unit,wst_oper,geo\\TIME_PERIOD\t2023 \t2024 \nA,KG_HAB,GEN,EU27_2020\t511.0 \t517.0 p\n"
    observations = adapt_env_wasmun_tsv(text)
    assert len(observations) == 2
    assert observations[1].value == 517.0
    assert observations[1].status == "p"
    assert observations[1].normalized_unit == "kg_per_capita"


def test_epa_bridge_normalizes_short_tons_without_claiming_layout_magic() -> None:
    observation = parse_epa_smm_normalized_csv(
        "year,material,management_pathway,short_tons\n2018,paper,recycling,46000000\n"
    )[0]
    assert observation.year == 2018
    assert math.isclose(observation.metric_tonnes, short_tons_to_metric_tonnes(46_000_000))
    assert "normalized_bridge" in observation.claim_boundary


def test_revision_detector_keeps_added_and_modified_records() -> None:
    previous = ({"geo": "EU", "year": "2024", "value": "10"},)
    current = (
        {"geo": "EU", "year": "2024", "value": "11"},
        {"geo": "CA", "year": "2024", "value": "3"},
    )
    report = compare_record_snapshots(previous, current, key_fields=("geo", "year"))
    assert report.changed is True
    assert len(report.modified) == 1
    assert len(report.added) == 1


def test_temporal_calibration_detects_deliberate_deterioration() -> None:
    report = temporal_calibration_report(
        (
            TimedProbabilisticObservation("2024-01-01", 0.9, 1),
            TimedProbabilisticObservation("2024-02-01", 0.1, 0),
            TimedProbabilisticObservation("2025-01-01", 0.9, 0),
            TimedProbabilisticObservation("2025-02-01", 0.1, 1),
        ),
        bins=2,
    )
    assert report.deterioration_detected is True
    assert report.brier_delta_first_to_last > 0


def test_empirical_campaign_preserves_case_where_omega_loses() -> None:
    report = evaluate_prediction_campaign(
        (
            PredictionCase("a", 10, {"omega": 11, "baseline": 10}),
            PredictionCase("b", 20, {"omega": 19, "baseline": 20}),
        ),
        canonical_method="omega",
    )
    assert report.best_method_by_rmse == "baseline"
    assert report.canonical_rmse_regret > 0
    assert report.canonical_is_best is False


def test_general_network_supports_multi_hop_flow() -> None:
    result = min_cost_general_flow(
        (BalanceNode("source", 2), BalanceNode("hub", 0), BalanceNode("sink", -2)),
        (DirectedArc("source", "hub", 2, 1), DirectedArc("hub", "sink", 2, 2)),
    )
    assert result.total_flow == 2
    assert result.total_cost == 6
    assert result.unmet_demand == 0
    assert result.optimality_certified is True


def test_time_expanded_network_uses_holdover_instead_of_backward_time() -> None:
    result = solve_time_expanded_flow(
        (TemporalBalance("source", 0, 1), TemporalBalance("sink", 1, -1)),
        (TemporalArc("source", "hub", 0, 0, 1, 1), TemporalArc("hub", "sink", 1, 1, 1, 2)),
        holdover_nodes=("hub",),
        periods=(0, 1),
    )
    assert result.total_flow == 1
    assert result.total_cost == 3


def test_r05_evidence_court_keeps_negative_controls_and_boundaries() -> None:
    report = run_r05_evidence()
    assert report["bench_version"] == "0.5.0"
    assert report["eurostat"]["latest_status"] == "p"
    assert report["revision"]["changed"] is True
    assert report["calibration_drift"]["deterioration_detected"] is True
    assert report["negative_control_campaign"]["canonical_is_best"] is False
    assert report["multi_hop_flow"]["total_flow"] == 2
    assert report["time_expanded_flow"]["total_flow"] == 1
