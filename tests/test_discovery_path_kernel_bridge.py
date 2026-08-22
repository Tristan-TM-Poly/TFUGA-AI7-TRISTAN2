from sage_tristan.discovery_path_ir import gauss_ceres_reconstruction
from sage_tristan.discovery_path_kernel_bridge import (
    path_to_kernel_events,
    validate_bridge_events,
)


def test_bridge_emits_existing_discovery_kernel_event_contracts():
    path = gauss_ceres_reconstruction()
    events = path_to_kernel_events(path)
    assert tuple(event.event_type for event in events) == (
        "ObservationEvent",
        "ClaimEvent",
        "GeneratorCandidate",
        "GeneratorCandidate",
        "GeneratorCandidate",
        "ExperimentSpec",
        "ResultPacket",
        "OAKTransition",
    )


def test_bridge_contracts_and_parentage_validate():
    receipt = validate_bridge_events(gauss_ceres_reconstruction())
    assert receipt.contracts_valid is True
    assert receipt.parentage_valid is True
    assert receipt.validation_issues == ()
    assert receipt.historical_causation_certified is False


def test_bridge_preserves_oak_boundary_in_claim_and_result():
    events = path_to_kernel_events(gauss_ceres_reconstruction())
    claim = events[1]
    result = events[-2]
    oak = events[-1]
    assert claim.payload["historical_causation_claim"] is False
    assert result.payload["historical_truth_certified"] is False
    assert oak.payload["to_status"] == "IMPLEMENTED"
    assert "no historical/scientific certification" in oak.payload["cause"]


def test_bridge_result_has_units_and_uncertainty():
    result = path_to_kernel_events(gauss_ceres_reconstruction())[-2]
    assert result.event_type == "ResultPacket"
    assert result.units["path_cost"] == "1"
    assert result.units["residual_budget"] == "1"
    assert result.uncertainty["terminal_model_uncertainty"] >= 0
