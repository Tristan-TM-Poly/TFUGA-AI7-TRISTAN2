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
            r10 = json.loads((Path(a) / "theorems" / "r10_theorem.json").read_text(encoding="utf-8"))
            r11 = json.loads((Path(a) / "theorems" / "r11_compiler_theorem.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["oak_promotion"], "RESEARCH_BUNDLE_VALID")
            self.assertFalse(manifest["solution_claimed"])
            self.assertEqual(
                manifest["theorem_specs"],
                ["r10_theorem.json", "r11_compiler_theorem.json"],
            )
            self.assertFalse(oak["solution_claimed"])
            self.assertTrue(oak["proof_graph_valid"])
            self.assertTrue(oak["bibliography_valid"])
            self.assertTrue(oak["theorem_specs_valid"])
            self.assertEqual(oak["theorem_spec_count"], 2)
            self.assertEqual(r10["status"], "PROVED_DERIVED_EQUIVALENCE")
            self.assertEqual(r11["status"], "PROVED_TRANSFORM_IDENTITY")
            self.assertFalse(r10["solution_claimed"])
            self.assertFalse(r11["solution_claimed"])
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
