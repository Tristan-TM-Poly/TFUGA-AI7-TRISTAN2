import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from omega_zeta_square_t.materialize import materialize_from_files


GRAPH = "specs/omega_zeta_square_t/proof_graph.json"
BIB = "specs/omega_zeta_square_t/bibliography_ledger.json"


class TestResearchBundleMaterializer(unittest.TestCase):
    def test_bundle_is_deterministic_and_oak_safe(self):
        with TemporaryDirectory() as a, TemporaryDirectory() as b:
            first = materialize_from_files(GRAPH, BIB, a)
            second = materialize_from_files(GRAPH, BIB, b)
            self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])
            self.assertFalse(first["proves_rh"])
            manifest = json.loads((Path(a) / "manifest.json").read_text(encoding="utf-8"))
            oak = json.loads((Path(a) / "oak_receipt.json").read_text(encoding="utf-8"))
            obligations = json.loads((Path(a) / "proof_obligations.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["oak_promotion"], "RESEARCH_BUNDLE_VALID")
            self.assertFalse(manifest["solution_claimed"])
            self.assertFalse(oak["solution_claimed"])
            self.assertTrue(oak["proof_graph_valid"])
            self.assertTrue(oak["bibliography_valid"])
            self.assertGreater(obligations["obligation_count"], 0)

    def test_bundle_hashes_match_files(self):
        import hashlib
        with TemporaryDirectory() as output:
            result = materialize_from_files(GRAPH, BIB, output)
            manifest = result["manifest"]
            for name, expected in manifest["artifact_sha256"].items():
                observed = hashlib.sha256((Path(output) / name).read_bytes()).hexdigest()
                self.assertEqual(observed, expected)


if __name__ == "__main__":
    unittest.main()
