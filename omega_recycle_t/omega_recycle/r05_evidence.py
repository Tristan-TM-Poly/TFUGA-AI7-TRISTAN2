from __future__ import annotations

import json

from .campaign import PredictionCase, evaluate_prediction_campaign
from .epa import parse_epa_smm_normalized_csv
from .eurostat import adapt_env_wasmun_tsv
from .general_network import BalanceNode, DirectedArc, min_cost_general_flow
from .revision import compare_record_snapshots
from .temporal_calibration import TimedProbabilisticObservation, temporal_calibration_report
from .temporal_network import TemporalArc, TemporalBalance, solve_time_expanded_flow


def run_r05_evidence() -> dict:
    eurostat_fixture = (
        "freq,unit,wst_oper,geo\\TIME_PERIOD\t2023 \t2024 \n"
        "A,KG_HAB,GEN,EU27_2020\t511.0 \t517.0 p\n"
    )
    eurostat = adapt_env_wasmun_tsv(eurostat_fixture)
    epa = parse_epa_smm_normalized_csv(
        "year,material,management_pathway,short_tons\n"
        "2018,paper_and_paperboard,recycling,46000000\n"
    )
    previous = ({"geo": "EU27_2020", "year": "2024", "value": "516"},)
    current = (
        {"geo": "EU27_2020", "year": "2024", "value": "517"},
        {"geo": "CA", "year": "2024", "value": "3"},
    )
    revision = compare_record_snapshots(previous, current, key_fields=("geo", "year"))
    drift = temporal_calibration_report(
        (
            TimedProbabilisticObservation("2024-01-01", 0.9, 1),
            TimedProbabilisticObservation("2024-02-01", 0.1, 0),
            TimedProbabilisticObservation("2025-01-01", 0.9, 0),
            TimedProbabilisticObservation("2025-02-01", 0.1, 1),
        ),
        bins=2,
    )
    campaign = evaluate_prediction_campaign(
        (
            PredictionCase("a", 10, {"omega": 11, "baseline": 10}),
            PredictionCase("b", 20, {"omega": 19, "baseline": 20}),
        ),
        canonical_method="omega",
    )
    multi_hop = min_cost_general_flow(
        (BalanceNode("source", 2), BalanceNode("hub", 0), BalanceNode("sink", -2)),
        (DirectedArc("source", "hub", 2, 1, "collect"), DirectedArc("hub", "sink", 2, 2, "process")),
    )
    temporal = solve_time_expanded_flow(
        (TemporalBalance("source", 0, 1), TemporalBalance("sink", 1, -1)),
        (TemporalArc("source", "hub", 0, 0, 1, 1, "collect"), TemporalArc("hub", "sink", 1, 1, 1, 2, "process")),
        holdover_nodes=("hub",),
        periods=(0, 1),
    )
    return {
        "bench_version": "0.5.0",
        "deterministic": True,
        "fixture_boundary": "schema_and_negative_control_fixtures_not_claimed_as_live_empirical_downloads",
        "eurostat": {
            "count": len(eurostat),
            "unit": eurostat[-1].normalized_unit,
            "latest_value": eurostat[-1].value,
            "latest_status": eurostat[-1].status,
            "source_contract": "env_wasmun_required_dimensions_geo_unit_wst_oper",
        },
        "epa": {
            "count": len(epa),
            "unit": epa[0].unit,
            "metric_tonnes": round(epa[0].metric_tonnes, 6),
            "claim_boundary": epa[0].claim_boundary,
        },
        "revision": {
            "changed": revision.changed,
            "structure_changed": revision.structure_changed,
            "added": len(revision.added),
            "modified": len(revision.modified),
            "claim_boundary": revision.claim_boundary,
        },
        "calibration_drift": {
            "years": [window.year for window in drift.windows],
            "brier_delta": round(drift.brier_delta_first_to_last, 6),
            "ece_delta": round(drift.ece_delta_first_to_last, 6),
            "deterioration_detected": drift.deterioration_detected,
            "claim_boundary": drift.claim_boundary,
        },
        "negative_control_campaign": {
            "best_method": campaign.best_method_by_rmse,
            "canonical_method": campaign.canonical_method,
            "canonical_rmse_regret": round(campaign.canonical_rmse_regret, 6),
            "canonical_is_best": campaign.canonical_is_best,
            "claim_boundary": campaign.claim_boundary,
        },
        "multi_hop_flow": {
            "total_flow": multi_hop.total_flow,
            "total_cost": multi_hop.total_cost,
            "optimality_certified": multi_hop.optimality_certified,
            "claim_boundary": multi_hop.claim_boundary,
        },
        "time_expanded_flow": {
            "total_flow": temporal.total_flow,
            "total_cost": temporal.total_cost,
            "optimality_certified": temporal.optimality_certified,
            "claim_boundary": temporal.claim_boundary,
        },
        "limits": [
            "Eurostat and EPA fixtures exercise source contracts but are not live downloads",
            "EPA adapter accepts a normalized bridge table rather than arbitrary webpage or workbook layouts",
            "revision detection compares normalized records and cannot decide semantic comparability",
            "temporal drift metrics do not establish causality or future performance",
            "general and time-expanded solvers are finite single-commodity flow models",
            "shared-capacity multi-commodity optimization remains R0.6 work",
        ],
    }


def render_r05_evidence() -> str:
    return json.dumps(run_r05_evidence(), indent=2, sort_keys=True)
