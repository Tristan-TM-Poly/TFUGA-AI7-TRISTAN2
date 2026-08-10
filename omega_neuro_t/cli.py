from __future__ import annotations

import argparse
import json

from .dendrite import BranchIntegrator, SomaIntegrator, address_aware_response
from .models import DendriticBranchState, HyperEdge, SynapseState
from .hypergraph import MultiscaleNeuroHypergraph
from .oakbench import ModelScore, OAKBench
from .synapse import effective_synaptic_weight, scalar_weight_baseline


def build_demo() -> dict:
    proximal = BranchIntegrator(DendriticBranchState("proximal", threshold=0.2, gain=1.3))
    distal = BranchIntegrator(DendriticBranchState("distal", threshold=0.5, gain=2.0, local_calcium=0.2))
    response = address_aware_response([proximal, distal], [[0.4, 0.3], [0.2, 0.7]], soma=SomaIntegrator())

    synapse = SynapseState(
        "s1", "n1", "n2",
        release_probability=0.6,
        quantal_scale=1.2,
        short_term_gain=0.9,
        long_term_gain=1.1,
        dendritic_address="distal",
        astrocytic_context=1.05,
        neuromodulatory_context=1.10,
        metabolic_context=0.95,
        uncertainty=0.1,
    )

    graph = MultiscaleNeuroHypergraph()
    for node in ("n1", "n2", "branch:distal", "astro:local"):
        graph.add_node(node)
    graph.add_edge(HyperEdge("e_pair", frozenset({"n1", "n2"}), layer="structural"))
    graph.add_edge(HyperEdge("e_triplet", frozenset({"n1", "branch:distal", "astro:local"}), layer="effective"))

    oak = OAKBench(complexity_penalty=0.02, uncertainty_penalty=0.1)
    baseline = ModelScore("scalar_synapse", predictive_loss=0.30, complexity=1.0, uncertainty=0.05)
    candidate = ModelScore("state_tensor", predictive_loss=0.20, complexity=4.0, uncertainty=0.08)

    return {
        "address_aware_response": response,
        "scalar_synaptic_weight": scalar_weight_baseline(synapse),
        "contextual_synaptic_weight": effective_synaptic_weight(synapse),
        "higher_order_fraction": graph.higher_order_fraction(),
        "active_projection": graph.contextual_projection({"structural": 0.25, "effective": 1.0}),
        "oak": {
            "baseline_score": oak.score(baseline),
            "candidate_score": oak.score(candidate),
            "candidate_justified": oak.justified(baseline, candidate),
        },
        "epistemic_notice": "synthetic executable model; not biological validation or clinical inference",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ω-NEURO-CELL-SYN-NET-T∞ reference lab")
    parser.add_argument("--pretty", action="store_true", help="pretty-print the deterministic demo JSON")
    args = parser.parse_args()
    print(json.dumps(build_demo(), indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
