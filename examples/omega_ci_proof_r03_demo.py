from omega_ci_proof_t.r03.debt import ProofDebtEngine
from omega_ci_proof_t.r03.graph import EpistemicGraphEngine


def main() -> None:
    graph = EpistemicGraphEngine.from_mapping({
        "nodes": [
            {"node_id": "CLAIM-A", "kind": "claim", "label": "A", "criticality": 4},
            {"node_id": "EVID-A", "kind": "evidence", "label": "Evidence A"},
        ],
        "edges": [{"source": "CLAIM-A", "target": "EVID-A", "relation": "supported_by"}],
    })
    state = {"claims": {"CLAIM-A": {"coverage_score": 1.0, "required_tests": 0, "observed_tests": 0, "evidence_statuses": ["CURRENT"], "provenance_complete": True}}}
    print(graph.stats())
    print(ProofDebtEngine().evaluate(graph, state).to_dict())


if __name__ == "__main__":
    main()
