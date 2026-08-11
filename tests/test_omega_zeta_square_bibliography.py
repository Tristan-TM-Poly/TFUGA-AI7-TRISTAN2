import json
from pathlib import Path
import unittest

from omega_zeta_square_t import validate_bibliography_ledger


GRAPH = Path("specs/omega_zeta_square_t/proof_graph.json")
LEDGER = Path("specs/omega_zeta_square_t/bibliography_ledger.json")


class TestBibliographyGate(unittest.TestCase):
    def test_current_ledger_binds_all_known_theorem_nodes(self):
        graph = json.loads(GRAPH.read_text(encoding="utf-8"))
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        self.assertEqual(validate_bibliography_ledger(graph, ledger), [])

    def test_missing_binding_is_rejected(self):
        graph = {
            "nodes": [{"id": "known", "status": "KNOWN_THEOREM"}],
            "hyperedges": [],
        }
        ledger = {"sources": [], "claim_bindings": []}
        errors = validate_bibliography_ledger(graph, ledger)
        self.assertEqual(errors, ["KNOWN_THEOREM node lacks bibliography binding: known"])

    def test_non_primary_binding_is_rejected(self):
        graph = {
            "nodes": [{"id": "known", "status": "KNOWN_THEOREM"}],
            "hyperedges": [],
        }
        ledger = {
            "sources": [{"id": "blog", "status": "SECONDARY_SUMMARY"}],
            "claim_bindings": [{"graph_node": "known", "source_id": "blog"}],
        }
        errors = validate_bibliography_ledger(graph, ledger)
        self.assertTrue(any("primary-source-verified" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
