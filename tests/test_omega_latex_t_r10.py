import tempfile
import unittest
from pathlib import Path

from omega_latex_t.cache_index import build_cache_index, write_sharded_index
from omega_latex_t.covariance import CovarianceError, propagate_jacobian, propagate_linear
from omega_latex_t.figure_backends import render_svg, svg_receipt
from omega_latex_t.metadata_receipts import metadata_receipt, metadata_receipt_report, normalize_doi
from omega_latex_t.proof_lineage import proof_lineage
from omega_latex_t.repo_universe import RepoUniverseError, repository_inventory_to_universe
from omega_latex_t.review_queue import metadocument_review_queue
from omega_latex_t.source_fragments import extract_text_fragment, source_fragment_report, validate_receipt


class FakeSource:
    def __init__(self, source_id, digest=""):
        self.id = source_id
        self.sha256 = digest


class FakeDoc:
    def __init__(self, provenance=None, nodes=(), sources=()):
        self.provenance = provenance or {}
        self.nodes = nodes
        self.sources = sources

    def semantic_hash(self):
        return "a" * 64


class R10Tests(unittest.TestCase):
    def test_source_fragment_receipt_roundtrip_and_registered_source(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.txt"
            p.write_text("a\nb\nc\n", encoding="utf-8")
            fragment, receipt = extract_text_fragment(p, "s1", start_line=2, end_line=3)
            self.assertEqual(fragment, "b\nc\n")
            self.assertFalse(validate_receipt(receipt.to_mapping(), fragment_text=fragment))
            self.assertTrue(validate_receipt(receipt.to_mapping(), fragment_text="tampered"))
            report = source_fragment_report(FakeDoc({"source_fragments": [receipt.to_mapping()]}, sources=[FakeSource("s1", receipt.source_sha256)]))
            self.assertFalse(report["entries"][0]["findings"])

    def test_metadata_receipt(self):
        self.assertEqual(normalize_doi("https://doi.org/10.1000/ABC"), "10.1000/abc")
        receipt = metadata_receipt({"DOI": "10.1000/ABC", "title": ["T"]})
        self.assertEqual(receipt["doi"], "10.1000/abc")
        self.assertEqual(len(receipt["normalized_metadata_sha256"]), 64)
        report = metadata_receipt_report(FakeDoc({"metadata_receipts": [receipt]}))
        self.assertEqual(report["valid_count"], 1)

    def test_covariance_linear_and_jacobian(self):
        result = propagate_linear([2, 3], [1, 2], [[1, .5], [.5, 4]], unit="m")
        self.assertAlmostEqual(result["value"], 8)
        self.assertAlmostEqual(result["variance"], 19)
        out = propagate_jacobian([[1, 0], [0, 2]], [[1, 0], [0, 4]])
        self.assertEqual(out, [[1.0, 0.0], [0.0, 16.0]])
        with self.assertRaises(CovarianceError):
            propagate_linear([1], [1], [[1, 2], [0, 1]])

    def test_svg_is_deterministic(self):
        spec = {"kind": "plot", "caption": "demo", "series": [{"x": [0, 1], "y": [1, 3], "mode": "line+markers"}]}
        a = render_svg(spec)
        b = render_svg(spec)
        self.assertEqual(a, b)
        self.assertIn("<svg", a)
        self.assertEqual(svg_receipt(spec, a), svg_receipt(spec, b))

    def test_proof_lineage(self):
        doc = FakeDoc({"verifier_receipts": [{"receipt_id": "r1", "theorem_id": "t1", "system": "lean", "status": "passed", "artifact_sha256": "b" * 64}, {"receipt_id": "r2", "theorem_id": "t1", "system": "lean", "status": "passed", "parent_receipt_id": "r1"}]})
        graph = proof_lineage(doc)
        self.assertFalse(graph["findings"])
        self.assertTrue(any(edge["kind"] == "derives_receipt" for edge in graph["edges"]))

    def test_repo_universe_requires_explicit_source_and_schema_compatible_entries(self):
        payload = {"repositories": [{"id": 1, "full_name": "o/a", "document_source": {"kind": "summary", "path": "a.json"}}, {"id": 2, "full_name": "o/b"}]}
        result = repository_inventory_to_universe(payload, depths=[0, 2])
        self.assertEqual(result["repository_count"], 2)
        self.assertEqual(result["admitted_count"], 1)
        self.assertEqual(result["universe_manifest"]["depths"], [0, 2])
        self.assertNotIn("repository", result["universe_manifest"]["entries"][0])
        with self.assertRaises(RepoUniverseError):
            repository_inventory_to_universe(payload, depths=[])

    def test_cache_index_and_shards(self):
        digest = "a" * 64
        index = build_cache_index([{"key": "k", "content_sha256": digest, "path": "p", "size": 1}])
        self.assertEqual(index["entries"][0]["shard"], "aa")
        with tempfile.TemporaryDirectory() as td:
            paths = write_sharded_index(index, td)
            self.assertEqual(len(paths), 2)
            self.assertTrue(Path(paths[-1]).exists())

    def test_review_queue_priority_and_string_orphan(self):
        queue = metadocument_review_queue({"conflict_candidates": [{"canonical_key": "k"}], "duplicate_candidates": [{"content_fingerprint": "h"}], "orphan_candidates": ["doc:n"]})
        self.assertEqual([item["priority"] for item in queue["items"]], [100, 60, 20])
        self.assertEqual(queue["items"][-1]["subject"], "doc:n")


if __name__ == "__main__":
    unittest.main()
