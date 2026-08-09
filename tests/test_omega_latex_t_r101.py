import json
import tempfile
import unittest
from pathlib import Path

from omega_latex_t.audit import audit_document
from omega_latex_t.covariance import CovarianceError, covariance_diagnostics, covariance_ledger, propagate_linear
from omega_latex_t.metadata_receipts import metadata_receipt, metadata_receipt_report
from omega_latex_t.models import DocumentIR, DocumentMeta
from omega_latex_t.proof_lineage import proof_lineage
from omega_latex_t.universe import UniverseManifestError, build_universe, normalize_universe_manifest


class R101HardeningTests(unittest.TestCase):
    def _doc(self, provenance=None):
        return DocumentIR(meta=DocumentMeta(title="R1.0.1 hardening fixture"), nodes=(), provenance=provenance or {})

    def test_metadata_receipt_is_self_verifying(self):
        receipt = metadata_receipt({"DOI": "10.1000/ABC", "title": ["T"]})
        report = metadata_receipt_report(self._doc({"metadata_receipts": [receipt]}))
        self.assertEqual(report["verified_count"], 1)

        tampered = dict(receipt)
        tampered["normalized_metadata_sha256"] = "0" * 64
        bad = metadata_receipt_report(self._doc({"metadata_receipts": [tampered]}))
        self.assertFalse(bad["entries"][0]["valid"])
        self.assertIn("normalized_metadata_hash_mismatch", bad["entries"][0]["reasons"])

        malformed = dict(receipt)
        malformed["raw_metadata_sha256"] = "banana"
        bad_format = metadata_receipt_report(self._doc({"metadata_receipts": [malformed]}))
        self.assertIn("invalid_raw_metadata_sha256", bad_format["entries"][0]["reasons"])

    def test_legacy_metadata_receipt_is_explicitly_unverified(self):
        receipt = metadata_receipt({"DOI": "10.1000/ABC", "title": ["T"]})
        receipt.pop("raw_metadata")
        report = metadata_receipt_report(self._doc({"metadata_receipts": [receipt]}))
        self.assertTrue(report["entries"][0]["valid"])
        self.assertFalse(report["entries"][0]["verified"])
        self.assertIn("raw_metadata_unavailable_for_verification", report["entries"][0]["reasons"])

    def test_covariance_requires_positive_semidefinite_structure(self):
        diagnostics = covariance_diagnostics([[1.0, 0.5], [0.5, 1.0]])
        self.assertTrue(diagnostics["positive_semidefinite"])
        self.assertAlmostEqual(propagate_linear([2, 3], [1, 2], [[1, 0.5], [0.5, 4]])["variance"], 19.0)
        with self.assertRaises(CovarianceError):
            covariance_diagnostics([[1.0, 2.0], [2.0, 1.0]])

        ledger = covariance_ledger(self._doc({"covariance_models": {"bad": {"variables": ["x", "y"], "covariance": [[1.0, 2.0], [2.0, 1.0]]}}}))
        self.assertEqual(ledger["entries"][0]["findings"][0]["code"], "COVARIANCE_MODEL_INVALID")

    def test_proof_lineage_malformed_input_becomes_findings(self):
        graph = proof_lineage(self._doc({"verifier_receipts": [
            {"receipt_id": "r1", "theorem_id": "t", "parent_receipt_id": "r2"},
            {"receipt_id": "r1", "theorem_id": "t"},
            {"receipt_id": "r2", "theorem_id": "t", "parent_receipt_id": "r1"},
            "not-an-object",
        ]}))
        codes = {item["code"] for item in graph["findings"]}
        self.assertIn("PROOF_LINEAGE_DUPLICATE_RECEIPT_ID", codes)
        self.assertIn("PROOF_LINEAGE_CYCLE", codes)
        self.assertIn("PROOF_LINEAGE_RECEIPT_INVALID", codes)

    def test_audit_totalizes_duplicate_receipts_and_bad_metadata(self):
        valid = metadata_receipt({"DOI": "10.1000/ABC", "title": ["T"]})
        valid["normalized_metadata_sha256"] = "0" * 64
        doc = self._doc({"verifier_receipts": [
            {"receipt_id": "r1", "theorem_id": "t"},
            {"receipt_id": "r1", "theorem_id": "t"},
        ], "metadata_receipts": [valid]})
        report = audit_document(doc)
        codes = {finding.code for finding in report.findings}
        self.assertIn("PROOF_LINEAGE_DUPLICATE_RECEIPT_ID", codes)
        self.assertIn("METADATA_RECEIPT_INVALID", codes)
        self.assertFalse(report.passed)

    def test_universe_manifest_defaults_to_manifest_directory(self):
        normalized = normalize_universe_manifest({"entries": [{"id": "x", "kind": "docir", "path": "x.json"}]})
        self.assertEqual(normalized["allowed_roots"], ["."])

    def test_universe_blocks_path_escape_and_streams_checkpoint(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "campaign"
            root.mkdir()
            outside = Path(td) / "outside.json"
            outside.write_text(json.dumps({"meta": {"title": "outside"}, "nodes": []}), encoding="utf-8")
            source = root / "inside.json"
            source.write_text(json.dumps({"meta": {"title": "inside"}, "nodes": []}), encoding="utf-8")

            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "entries": [{"id": "inside", "kind": "docir", "path": "inside.json"}],
                "depths": [0, 1],
                "allowed_roots": ["."],
            }), encoding="utf-8")
            report = build_universe(manifest, root / "out", root / "cache")
            self.assertEqual(report["job_count"], 2)
            self.assertEqual(report["executed_job_count"], 2)
            self.assertEqual(report["streaming"]["resident_document_count_max"], 1)
            self.assertNotIn("completed_job_ids", report["checkpoint"])
            self.assertTrue(report["checkpoint"]["complete"])

            resumed = build_universe(manifest, root / "out", root / "cache")
            self.assertEqual(resumed["executed_job_count"], 0)

            escaped = root / "escaped.json"
            escaped.write_text(json.dumps({
                "entries": [{"id": "outside", "kind": "docir", "path": "../outside.json"}],
                "depths": [0],
                "allowed_roots": ["."],
            }), encoding="utf-8")
            with self.assertRaises(UniverseManifestError):
                build_universe(escaped, root / "bad-out", root / "bad-cache")


if __name__ == "__main__":
    unittest.main()
