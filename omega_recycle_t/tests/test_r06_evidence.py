from __future__ import annotations

from io import BytesIO
import pytest

from omega_recycle.general_network import BalanceNode, DirectedArc
from omega_recycle.holdout import TemporalPredictionCase, evaluate_temporal_holdout
from omega_recycle.lcia_governance import GovernedFactor, GovernedMethod, MethodDescriptor, validate_governed_method
from omega_recycle.live_sources import LiveSnapshot, LiveSourceSpec, compare_live_snapshots, fetch_live_snapshot, render_manifest
from omega_recycle.multi_commodity import Commodity, SharedArc, solve_fractional_multi_commodity
from omega_recycle.r06_evidence import run_r06_evidence
from omega_recycle.solver_crosscheck import crosscheck_general_flow, crosscheck_time_expanded_flow
from omega_recycle.source_anchors import EPA_SMM_ANCHOR, EUROSTAT_ENV_WASMUN_ANCHOR
from omega_recycle.temporal_network import TemporalArc, TemporalBalance
from omega_recycle.unit_ontology import compatible_units, convert_value


def test_internal_directed_solver_matches_scipy_highs() -> None:
    report = crosscheck_general_flow(
        (BalanceNode("source", 2), BalanceNode("hub", 0), BalanceNode("sink", -2)),
        (DirectedArc("source", "hub", 2, 1), DirectedArc("hub", "sink", 2, 2), DirectedArc("source", "sink", 1, 10)),
    )
    assert report.flow_agreement is True
    assert report.cost_agreement is True
    assert report.internal_flow == 2
    assert report.external_flow == pytest.approx(2)
    assert report.internal_cost == pytest.approx(6)
    assert report.external_cost == pytest.approx(6)
    assert "formal_proof" in report.claim_boundary


def test_time_expanded_solver_matches_scipy_highs() -> None:
    report = crosscheck_time_expanded_flow(
        (TemporalBalance("source", 0, 1), TemporalBalance("sink", 2, -1)),
        (TemporalArc("source", "hub", 0, 1, 1, 1), TemporalArc("hub", "sink", 1, 2, 1, 2)),
        holdover_nodes=("hub",), periods=(0, 1, 2),
    )
    assert report.flow_agreement is True
    assert report.cost_agreement is True
    assert report.internal_cost == pytest.approx(3)


def test_multi_commodity_shared_capacity_is_not_double_counted() -> None:
    result = solve_fractional_multi_commodity(
        (Commodity("copper", "cu_source", "cu_sink", 1), Commodity("aluminium", "al_source", "al_sink", 1)),
        (
            SharedArc("cu_in", "cu_source", "hub", 1, 0), SharedArc("al_in", "al_source", "hub", 1, 0),
            SharedArc("shared", "hub", "split", 1.5, 1), SharedArc("cu_out", "split", "cu_sink", 1, 0),
            SharedArc("al_out", "split", "al_sink", 1, 0),
        ),
    )
    assert result.total_flow == pytest.approx(1.5)
    assert result.total_cost == pytest.approx(1.5)
    assert sum(dict(result.delivered).values()) == pytest.approx(1.5)
    assert result.optimality_certified is True
    assert "fractional_multi_commodity_lp" in result.claim_boundary


def test_temporal_holdout_allows_baseline_to_beat_omega() -> None:
    report = evaluate_temporal_holdout(
        (
            TemporalPredictionCase("2021", 2021, 500, {"omega": 501, "persistence": 499}),
            TemporalPredictionCase("2022", 2022, 510, {"omega": 514, "persistence": 509}),
            TemporalPredictionCase("2023", 2023, 511, {"omega": 518, "persistence": 510}),
            TemporalPredictionCase("2024", 2024, 517, {"omega": 525, "persistence": 512}),
        ), holdout_start=2023, canonical_method="omega",
    )
    assert report.train_count == 2
    assert report.test_count == 2
    assert report.campaign.canonical_is_best is False
    assert report.campaign.best_method_by_rmse == "persistence"


def test_unit_ontology_converts_only_compatible_dimensions() -> None:
    assert convert_value(1, "metric_tonne", "kg") == pytest.approx(1000)
    assert convert_value(3.6, "MJ", "kWh") == pytest.approx(1)
    assert compatible_units("g", "kg") is True
    with pytest.raises(ValueError): convert_value(1, "kg", "kWh")


def test_lcia_method_governance_requires_versioned_hash_and_known_input_units() -> None:
    descriptor = MethodDescriptor("test-method", "1", "external", "https://example.org/method", "0" * 64)
    method = GovernedMethod(descriptor, (GovernedFactor("electricity", "kWh", "climate", 0.5, "kgCO2e"),))
    validate_governed_method(method)
    bad = GovernedMethod(descriptor, (GovernedFactor("mystery", "widgets", "climate", 1.0, "kgCO2e"),))
    with pytest.raises(KeyError): validate_governed_method(bad)


class _Headers(dict):
    def get(self, key: str, default=None): return super().get(key, default)

class _Response:
    status = 200
    headers = _Headers({"Content-Type": "application/json", "ETag": '"fixture"'})
    def __init__(self, data: bytes) -> None: self._buffer = BytesIO(data)
    def read(self, size: int = -1) -> bytes: return self._buffer.read(size)
    def getcode(self) -> int: return 200
    def __enter__(self): return self
    def __exit__(self, *args) -> None: return None


def test_live_snapshot_fetcher_is_allowlisted_hashing_and_revision_aware() -> None:
    spec = LiveSourceSpec("fixture", "https://ec.europa.eu/test", max_bytes=100)
    def opener(request, timeout):
        assert request.full_url == spec.url
        assert timeout > 0
        return _Response(b'{"value":517}')
    _, first = fetch_live_snapshot(spec, retrieved_at="2026-08-10T12:57:00-04:00", opener=opener)
    assert first.http_status == 200
    assert first.etag == '"fixture"'
    assert "omega-recycle-live-manifest-v1" in render_manifest((first,))
    second = LiveSnapshot(first.source_id, first.url, "2026-08-11T12:57:00-04:00", "f" * 64, first.byte_count, first.content_type, first.etag, first.last_modified, 200)
    assert compare_live_snapshots((first,), (second,)).changed == ("fixture",)
    with pytest.raises(ValueError): LiveSourceSpec("bad", "https://example.com/not-allowlisted")


def test_current_source_anchors_remain_explicitly_non_raw() -> None:
    eurostat = dict(EUROSTAT_ENV_WASMUN_ANCHOR.facts)
    epa = dict(EPA_SMM_ANCHOR.facts)
    assert eurostat["last_data_update"] == "2026-03-30T21:00"
    assert eurostat["eu_2024_generated_kg_per_capita"] == "517"
    assert epa["latest_national_facts_figures_data_year"] == "2018"
    assert "not_raw_http_snapshot" in EUROSTAT_ENV_WASMUN_ANCHOR.evidence_kind


def test_r06_evidence_report_preserves_all_boundaries() -> None:
    report = run_r06_evidence()
    assert report["bench_version"] == "0.6.0"
    assert report["solver_crosscheck"]["flow_agreement"] is True
    assert report["solver_crosscheck"]["cost_agreement"] is True
    assert report["time_expanded_crosscheck"]["flow_agreement"] is True
    assert report["time_expanded_crosscheck"]["cost_agreement"] is True
    assert report["multi_commodity"]["shared_capacity_binding"] is True
    assert report["multi_commodity"]["optimality_certified"] is True
    assert report["temporal_holdout"]["canonical_is_best"] is False
    assert report["lcia_governance"]["bundled_recognized_factor_set"] is False
