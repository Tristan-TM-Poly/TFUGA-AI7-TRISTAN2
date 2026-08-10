import math

import pytest

from omega_neuro_t.dendrite import BranchIntegrator, SomaIntegrator, address_aware_response
from omega_neuro_t.hypergraph import MultiscaleNeuroHypergraph
from omega_neuro_t.models import DendriticBranchState, HyperEdge, SynapseState
from omega_neuro_t.networks import reference_archetypes
from omega_neuro_t.oakbench import ModelScore, OAKBench
from omega_neuro_t.synapse import effective_synaptic_weight, log_plasticity_update, scalar_weight_baseline


def test_synapse_probability_validation():
    with pytest.raises(ValueError):
        SynapseState("s", "a", "b", release_probability=1.1)


def test_context_changes_effective_weight_without_changing_scalar_baseline():
    base = SynapseState("s1", "a", "b", release_probability=0.5, quantal_scale=2.0)
    rich = SynapseState(
        "s2", "a", "b",
        release_probability=0.5,
        quantal_scale=2.0,
        astrocytic_context=1.2,
        neuromodulatory_context=1.1,
        metabolic_context=0.8,
    )
    assert scalar_weight_baseline(base) == scalar_weight_baseline(rich) == 1.0
    assert effective_synaptic_weight(base) != effective_synaptic_weight(rich)


def test_log_plasticity_is_multiplicative():
    updated = log_plasticity_update(2.0, math.log(2.0), 1.0)
    assert updated == pytest.approx(4.0)


def test_dendritic_address_model_is_order_sensitive_to_branch_properties():
    b1 = BranchIntegrator(DendriticBranchState("b1", threshold=0.0, gain=0.5))
    b2 = BranchIntegrator(DendriticBranchState("b2", threshold=0.6, gain=3.0))
    soma = SomaIntegrator()
    r1 = address_aware_response([b1, b2], [[1.0], [0.2]], soma=soma)
    r2 = address_aware_response([b1, b2], [[0.2], [1.0]], soma=soma)
    assert r1 != pytest.approx(r2)


def test_hypergraph_supports_higher_order_relations_and_layer_projection():
    graph = MultiscaleNeuroHypergraph()
    for node in ("pre", "post", "branch", "astro"):
        graph.add_node(node)
    graph.add_edge(HyperEdge("pair", frozenset({"pre", "post"}), layer="structural"))
    graph.add_edge(HyperEdge("higher", frozenset({"pre", "branch", "astro"}), layer="effective", weight=2.0))
    assert graph.edges["higher"].order == 3
    assert graph.higher_order_fraction() == pytest.approx(0.5)
    assert graph.contextual_projection({"structural": 0.0, "effective": 0.5}) == {"higher": 1.0}


def test_oak_prefers_simplicity_when_predictive_loss_is_equal():
    oak = OAKBench(complexity_penalty=0.1)
    simple = ModelScore("simple", predictive_loss=0.2, complexity=1.0)
    complex_model = ModelScore("complex", predictive_loss=0.2, complexity=5.0)
    assert oak.rank([complex_model, simple])[0] == simple


def test_oak_accepts_complexity_when_prediction_gain_pays_penalty():
    oak = OAKBench(complexity_penalty=0.02)
    baseline = ModelScore("baseline", predictive_loss=0.4, complexity=1.0)
    candidate = ModelScore("candidate", predictive_loss=0.1, complexity=5.0)
    assert oak.justified(baseline, candidate)


def test_network_atlas_returns_a_reference_archetype():
    atlas = reference_archetypes()
    assert atlas.nearest(atlas.entries["recurrent"]) == "recurrent"
