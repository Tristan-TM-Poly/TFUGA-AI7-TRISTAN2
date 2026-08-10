from omega_recycle.calibration import ProbabilisticObservation, calibration_report
from omega_recycle.datasets import EUROSTAT_ENV_WASMUN, ingest_delimited_snapshot, public_dataset_catalog
from omega_recycle.lca import InventoryFlow, LCAInventory
from omega_recycle.lcia import CharacterizationFactor, CharacterizationSet, characterize_inventory
from omega_recycle.network import DemandNode, SupplyNode, TransferArc, min_cost_transport
from omega_recycle.provenance import ProvenanceRecord, canonical_dataset_hash
from omega_recycle.symbiosis import MaterialNeed, MaterialOffer, match_material_flows
from omega_recycle.symbiosis_court import exact_match_material_flows, symbiosis_regret


def test_transport_maximizes_flow_before_minimizing_cost() -> None:
    result = min_cost_transport(
        (SupplyNode("s1", 1), SupplyNode("s2", 1)),
        (DemandNode("d1", 1), DemandNode("d2", 1)),
        (
            TransferArc("s1", "d1", 1, 1),
            TransferArc("s1", "d2", 1, 1),
            TransferArc("s2", "d1", 1, 2),
        ),
    )
    assert result.total_flow == 2
    assert result.total_cost == 3
    assert {(a.source_id, a.target_id) for a in result.allocations} == {("s1", "d2"), ("s2", "d1")}
    assert result.optimality_certified is True


def test_symbiosis_court_keeps_a_counterexample_to_greedy() -> None:
    offers = (
        MaterialOffer("A1", "copper", 1, 1.0, 1.0),
        MaterialOffer("A2", "copper", 1, 1.0, 2.0),
    )
    needs = (
        MaterialNeed("B1", "copper", 1, 1.0, 2.0),
        MaterialNeed("B2", "copper", 1, 1.0, 1.5),
    )
    greedy = match_material_flows(offers, needs)
    exact = exact_match_material_flows(offers, needs)
    court = symbiosis_regret(offers, needs)
    assert sum(match.quantity_kg for match in greedy) == 1
    assert exact.total_quantity_kg == 2
    assert court.quantity_regret_kg == 1
    assert court.greedy_is_flow_optimal is False
    assert court.comparable_cost_regret is None


def test_calibration_metrics_reward_perfect_predictions() -> None:
    perfect = calibration_report(
        (ProbabilisticObservation(0.0, 0), ProbabilisticObservation(1.0, 1)),
        bins=2,
    )
    wrong = calibration_report(
        (ProbabilisticObservation(0.9, 0), ProbabilisticObservation(0.1, 1)),
        bins=2,
    )
    assert perfect.brier_score == 0
    assert perfect.expected_calibration_error == 0
    assert perfect.log_loss < 1e-12
    assert wrong.brier_score > perfect.brier_score
    assert "not_causal" in perfect.claim_boundary


def test_public_snapshot_hash_is_reproducible_and_bound_to_source() -> None:
    text = "geo,year,value\nEU,2024,517\n"
    first = ingest_delimited_snapshot(EUROSTAT_ENV_WASMUN, text, retrieved_at="2026-08-10T12:00:00-04:00")
    second = ingest_delimited_snapshot(EUROSTAT_ENV_WASMUN, text, retrieved_at="2026-08-10T12:00:00-04:00")
    assert first.provenance.sha256 == second.provenance.sha256
    assert first.provenance.sha256 == canonical_dataset_hash(first.records)
    assert first.provenance.source_id == "eurostat-env-wasmun"
    assert len(public_dataset_catalog()) >= 2


def test_lcia_adapter_requires_external_provenance_and_keeps_claim_boundary() -> None:
    inventory = LCAInventory(
        "c1",
        "reuse",
        (
            InventoryFlow("electricity", 2.0, "kWh", "input"),
            InventoryFlow("component_mass", 1.0, "kg", "input"),
        ),
    )
    provenance = ProvenanceRecord("synthetic-factors", "https://example.invalid/factors", "2026-08-10", "0" * 64)
    factor_set = CharacterizationSet(
        name="synthetic-test-only",
        version="1",
        methodology="synthetic-test",
        provenance=provenance,
        factors=(CharacterizationFactor("electricity", "kWh", "climate", 0.5, "kgCO2e", "input"),),
    )
    result = characterize_inventory(inventory, factor_set)
    assert result.impacts[0].value == 1.0
    assert result.matched_flows == 1
    assert "input:component_mass[kg]" in result.unmatched_flows
    assert "not_certified" in result.claim_boundary
