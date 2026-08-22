import pytest

from omega_hyperphase_mat_t import (
    CLAIMS,
    ExactHypergraphEnsemble,
    Hyperedge,
    HypergraphState,
    PhaseHypergraphAtlas,
    PhaseNode,
    TransitionHyperedge,
    finite_size_crossover,
    four_site_topology_ensemble,
)


def pair_model(*, coupling=1.0):
    graph = HypergraphState("fixed", (Hyperedge((0, 1), coupling, "pair"),))
    return ExactHypergraphEnsemble(2, (graph,))


def test_probabilities_normalize_and_partition_identity_holds():
    model = pair_model()
    state = model.evaluate(2.0)
    assert sum(m.probability for m in state.microstates) == pytest.approx(1.0)
    assert state.free_energy == pytest.approx(-2.0 * state.log_partition)


def test_thermodynamic_entropy_identity_holds():
    model = pair_model()
    state = model.evaluate(1.7)
    assert state.entropy == pytest.approx((state.internal_energy - state.free_energy) / 1.7)
    assert state.entropy >= 0.0


def test_fixed_hypergraph_has_zero_topology_entropy():
    state = pair_model().evaluate(1.0)
    assert state.topology_entropy == pytest.approx(0.0, abs=1e-12)
    assert state.conditional_configuration_entropy == pytest.approx(state.entropy)


def test_dynamic_hypergraph_satisfies_entropy_chain_rule():
    state = four_site_topology_ensemble().evaluate(2.0)
    assert state.topology_entropy > 0.0
    assert state.entropy == pytest.approx(
        state.topology_entropy + state.conditional_configuration_entropy, abs=1e-12
    )
    assert state.entropy_chain_residual == pytest.approx(0.0, abs=1e-12)


def test_arbitrary_k_body_interaction_is_exactly_supported():
    graph = HypergraphState("three-body", (Hyperedge((0, 1, 2), 2.5, "triple"),))
    assert graph.total_energy((1, 1, 1)) == pytest.approx(-2.5)
    assert graph.total_energy((1, 1, -1)) == pytest.approx(2.5)
    model = ExactHypergraphEnsemble(3, (graph,))
    assert len(model.evaluate(1.0).microstates) == 8


def test_dynamic_ensemble_reduces_to_fixed_case_when_second_topology_is_penalized():
    base = HypergraphState("base", (Hyperedge((0, 1), 1.0),))
    suppressed = HypergraphState(
        "suppressed", (Hyperedge((0, 1), 1.0),), structural_energy=100.0
    )
    fixed = ExactHypergraphEnsemble(2, (base,)).evaluate(1.0)
    dynamic = ExactHypergraphEnsemble(2, (base, suppressed)).evaluate(1.0)
    assert dynamic.hypergraph_probabilities[0] > 1.0 - 1e-12
    assert dynamic.internal_energy == pytest.approx(fixed.internal_energy, abs=1e-12)


def test_field_breaks_spin_flip_symmetry():
    model = ExactHypergraphEnsemble(1, (HypergraphState("single"),), fields=(0.8,))
    assert model.evaluate(1.0).mean_magnetization > 0.0


def test_covariance_api_matches_zero_variance_constant_observable():
    model = pair_model()
    cov = model.covariance(
        1.0,
        lambda spins, graph: 1.0,
        lambda spins, graph: float(sum(spins)),
    )
    assert cov == pytest.approx(0.0, abs=1e-12)


def test_response_peak_is_explicitly_classified_as_finite_size_crossover():
    states = pair_model().sweep((0.5, 1.0, 2.0, 4.0))
    marker = finite_size_crossover(states, observable="heat_capacity")
    assert marker.classification == "FINITE_SIZE_CROSSOVER"
    assert marker.temperature in {0.5, 1.0, 2.0, 4.0}
    assert all(state.finite_size_only for state in states)


def test_structural_penalty_controls_topology_probability():
    low = four_site_topology_ensemble(structural_penalty=0.0).evaluate(1.0)
    high = four_site_topology_ensemble(structural_penalty=5.0).evaluate(1.0)
    assert low.hypergraph_probabilities[1] > high.hypergraph_probabilities[1]


def test_phase_atlas_validates_transition_references():
    atlas = PhaseHypergraphAtlas()
    atlas.add_phase(PhaseNode("alpha", "alpha phase", {"q": 0.1}))
    atlas.add_phase(PhaseNode("beta", "beta phase", {"q": 0.9}))
    atlas.add_transition(
        TransitionHyperedge("alpha-beta", ("alpha",), ("beta",), "model transition")
    )
    payload = atlas.to_dict()
    assert len(payload["phases"]) == 2
    assert len(payload["transitions"]) == 1
    with pytest.raises(ValueError):
        atlas.add_transition(
            TransitionHyperedge("bad", ("missing",), ("beta",), "invalid")
        )


def test_claim_registry_separates_established_model_and_hypothesis_statuses():
    statuses = {claim.status for claim in CLAIMS}
    assert {"ESTABLISHED", "DEFINITION", "MODEL", "HYPOTHESIS"} <= statuses
    finite_guardrail = next(c for c in CLAIMS if c.claim_id == "HPM-006")
    assert "finite" in finite_guardrail.statement.lower()


def test_invalid_temperature_and_out_of_bounds_edges_are_rejected():
    with pytest.raises(ValueError):
        pair_model().evaluate(0.0)
    with pytest.raises(ValueError):
        ExactHypergraphEnsemble(
            2,
            (HypergraphState("bad", (Hyperedge((0, 2), 1.0),)),),
        )
