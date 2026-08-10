from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from omega_latex_t.doc_factory import (
    build_factory_report,
    compare_reports,
    extract_claims,
    normalize_execution_receipts,
    write_factory_bundle,
)


class DocFactoryR10Tests(unittest.TestCase):
    def _repo(self, root: Path) -> None:
        (root / "omega_alpha_t").mkdir()
        (root / "omega_alpha_t" / "__init__.py").write_text(
            '"""alpha"""\nfrom .core import Engine\n\ndef public_api(x):\n    """Public entry."""\n    return x\n',
            encoding="utf-8",
        )
        (root / "omega_alpha_t" / "core.py").write_text(
            'import json\n\nclass Engine:\n    """Engine docs."""\n    pass\n', encoding="utf-8"
        )
        (root / "omega_alpha").mkdir()
        (root / "omega_alpha" / "__init__.py").write_text("", encoding="utf-8")
        (root / "tests").mkdir()
        (root / "tests" / "test_omega_alpha_t.py").write_text(
            "from omega_alpha_t import public_api\n\ndef test_public_api(): assert public_api(1) == 1\n",
            encoding="utf-8",
        )
        (root / ".github" / "workflows").mkdir(parents=True)
        (root / ".github" / "workflows" / "omega-alpha.yml").write_text(
            "name: omega_alpha_t\non: [push]\n", encoding="utf-8"
        )
        (root / "schemas").mkdir()
        (root / "schemas" / "omega_alpha_t.schema.json").write_text('{"type":"object"}', encoding="utf-8")
        (root / "docs").mkdir()
        (root / "docs" / "OMEGA_ALPHA_T.md").write_text(
            "# Alpha\n\nClaim: omega_alpha_t produces a deterministic structural report.\n"
            "Hypothesis: omega_alpha_t may scale to larger repositories.\n"
            "Status: unresolved\n",
            encoding="utf-8",
        )

    def test_factory_compiles_claims_receipts_graph_and_status_tensor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self._repo(root)
            artifact = root / "omega_alpha_t" / "core.py"
            receipts = {"receipts": [{
                "kind": "test-run", "system_id": "omega_alpha_t",
                "artifact_path": "omega_alpha_t/core.py",
                "source_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "status": "passed", "observed_at": "2026-08-10T17:00:00Z",
                "environment": {"python": "3.12"}, "details": {"tests": 1},
            }]}
            report = build_factory_report(root, source_commit="abc123", declared_statuses={"omega_alpha_t": "D"}, execution_receipts_payload=receipts, cache_dir=root / ".cache")
            target = next(s for s in report["systems"] if s["id"] == "omega_alpha_t")
            self.assertEqual(report["factory_version"], "1.0.0")
            self.assertEqual(target["statuses"]["declared_system_status"], "D")
            self.assertEqual(target["statuses"]["reproducibility_status"], "fresh-execution-observations")
            self.assertEqual(len(report["claims"]), 2)
            self.assertTrue(report["claim_evidence_bindings"])
            self.assertTrue(any(e["relation"] == "imports" for e in report["graph"]["edges"]))
            self.assertTrue(target["fingerprint"])
            self.assertIn("CI_GREEN != SCIENTIFIC_TRUTH", report["oak_boundaries"])
            q = next(r for r in report["quality"]["systems"] if r["system_id"] == "omega_alpha_t")
            self.assertEqual(q["execution_receipt_count"], 1)
            self.assertEqual(q["stale_execution_receipt_count"], 0)
            self.assertGreaterEqual(q["placeholder_count"], 1)

    def test_stale_execution_receipt_is_not_silently_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self._repo(root)
            path = root / "omega_alpha_t" / "core.py"
            old = hashlib.sha256(path.read_bytes()).hexdigest()
            path.write_text("class Engine:\n    version = 2\n", encoding="utf-8")
            rows = normalize_execution_receipts(root, [{
                "kind": "benchmark-run", "system_id": "omega_alpha_t",
                "artifact_path": "omega_alpha_t/core.py", "source_sha256": old,
                "status": "passed", "observed_at": "", "environment": {}, "details": {},
            }], ["omega_alpha_t"])
            self.assertTrue(rows[0]["stale"])
            self.assertEqual(rows[0]["stale_reason"], "source-hash-mismatch")
            self.assertEqual(rows[0]["authority"], "observation-only")

    def test_claim_extractor_does_not_promote_arbitrary_prose(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self._repo(root)
            (root / "docs" / "noise.md").write_text("# Not a claim\nomega_alpha_t is wonderful.\n", encoding="utf-8")
            claims = extract_claims(root, ["omega_alpha_t", "omega_alpha"])
            self.assertEqual(len(claims), 2)
            self.assertTrue(all(c["status"] == "candidate-unverified" for c in claims))

    def test_delta_invalidates_previous_docs_for_changed_system_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self._repo(root)
            before = build_factory_report(root, source_commit="a", cache_dir=root / ".cache")
            (root / "omega_alpha_t" / "core.py").write_text("class Engine:\n    version = 2\n", encoding="utf-8")
            after = build_factory_report(root, source_commit="b", cache_dir=root / ".cache")
            delta = compare_reports(before, after)
            self.assertIn("omega_alpha_t", delta["changed_systems"])
            self.assertIn("omega_alpha_t", delta["invalidated_previous_documentation"])

    def test_bundle_is_deterministic_and_has_all_projection_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"; out = Path(tmp) / "out"; root.mkdir(); self._repo(root)
            report = build_factory_report(root, source_commit="deadbeef", cache_dir=root / ".cache")
            first = write_factory_bundle(report, out); first_text = (out / "MANIFEST.json").read_text(encoding="utf-8")
            second = write_factory_bundle(report, out); second_text = (out / "MANIFEST.json").read_text(encoding="utf-8")
            self.assertEqual(first, second); self.assertEqual(first_text, second_text)
            for rel in [
                "MASTER_DOC_ATLAS.md", "factory-report.json", "claims.jsonl", "quality.csv",
                "graph/evidence-graph.dot", "graph/evidence-graph.graphml",
                "latex/MASTER_DOC_ATLAS.tex", "depths/systems/omega_alpha_t/D5.md",
            ]:
                self.assertTrue((out / rel).is_file(), rel)

    def test_bad_receipt_kind_and_unknown_system_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self._repo(root)
            with self.assertRaises(ValueError):
                normalize_execution_receipts(root, [{"kind": "magic-proof", "system_id": "omega_alpha_t"}], ["omega_alpha_t"])
            with self.assertRaises(ValueError):
                normalize_execution_receipts(root, [{"kind": "test-run", "system_id": "omega_missing"}], ["omega_alpha_t"])

    def test_content_addressed_import_cache_is_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self._repo(root); cache = root / ".cache"
            build_factory_report(root, cache_dir=cache)
            entries = list((cache / "imports-v1").glob("*.json"))
            self.assertGreaterEqual(len(entries), 2)
            payload = json.loads(entries[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "imports-v1")


if __name__ == "__main__":
    unittest.main()
