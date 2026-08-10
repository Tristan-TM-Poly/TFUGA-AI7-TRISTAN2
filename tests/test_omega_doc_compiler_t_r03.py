from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from omega_latex_t.doc_universe import discover_systems, scan_repository, render_depth, write_bundle


class DocUniverseR03Tests(unittest.TestCase):
    def _repo(self, root: Path) -> None:
        (root / "omega_alpha_t").mkdir()
        (root / "omega_alpha_t" / "__init__.py").write_text(
            '"""alpha"""\n\ndef public_api(x):\n    """Public entry."""\n    return x\n\ndef _private():\n    return 0\n',
            encoding="utf-8",
        )
        (root / "omega_alpha_t" / "core.py").write_text("class Engine:\n    pass\n", encoding="utf-8")
        (root / "omega_alpha").mkdir()
        (root / "omega_alpha" / "__init__.py").write_text("", encoding="utf-8")
        (root / "tests").mkdir()
        (root / "tests" / "test_omega_alpha_t.py").write_text(
            "from omega_alpha_t import public_api\n\ndef test_public_api(): assert public_api(1) == 1\n",
            encoding="utf-8",
        )
        (root / ".github" / "workflows").mkdir(parents=True)
        (root / ".github" / "workflows" / "omega-alpha.yml").write_text("name: omega_alpha_t\non: [push]\n", encoding="utf-8")
        (root / "schemas").mkdir()
        (root / "schemas" / "omega_alpha_t.schema.json").write_text('{"type":"object"}', encoding="utf-8")
        (root / "docs").mkdir()
        (root / "docs" / "OMEGA_ALPHA_T.md").write_text("# omega_alpha_t\n", encoding="utf-8")

    def test_scan_extracts_facts_without_truth_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root)
            self.assertEqual(discover_systems(root), ["omega_alpha", "omega_alpha_t"])
            report = scan_repository(root, source_commit="abc123", declared_statuses={"omega_alpha_t": "D"})
            target = next(x for x in report["systems"] if x["id"] == "omega_alpha_t")
            self.assertEqual(target["statuses"]["declared_system_status"], "D")
            self.assertEqual(target["statuses"]["oak_review_status"], "review")
            self.assertGreaterEqual(target["metrics"]["public_symbol_count"], 2)
            self.assertEqual(target["metrics"]["test_candidate_count"], 1)
            self.assertEqual(target["metrics"]["workflow_candidate_count"], 1)
            self.assertEqual(target["metrics"]["schema_candidate_count"], 1)
            self.assertIn("TEST_PRESENT != TEST_GREEN", target["oak_boundaries"])

    def test_family_candidates_are_candidates_not_equivalence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root)
            report = scan_repository(root)
            self.assertIn("omega_alpha", report["family_candidates"])
            self.assertEqual(sorted(report["family_candidates"]["omega_alpha"]), ["omega_alpha", "omega_alpha_t"])

    def test_depths_and_bundle_are_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            out = Path(tmp) / "out"
            root.mkdir()
            self._repo(root)
            report = scan_repository(root, source_commit="deadbeef")
            target = next(x for x in report["systems"] if x["id"] == "omega_alpha_t")
            for depth in range(6):
                self.assertTrue(render_depth(target, depth).startswith(f"# D{depth}"))
            first = write_bundle(report, out)
            first_text = (out / "manifest.json").read_text(encoding="utf-8")
            second = write_bundle(report, out)
            second_text = (out / "manifest.json").read_text(encoding="utf-8")
            self.assertEqual(first, second)
            self.assertEqual(first_text, second_text)
            self.assertTrue((out / "systems" / "omega_alpha_t" / "D4.md").exists())
            data = json.loads((out / "doc-universe.json").read_text(encoding="utf-8"))
            self.assertEqual(data["source_commit"], "deadbeef")

    def test_invalid_depth_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root)
            target = scan_repository(root)["systems"][0]
            with self.assertRaises(ValueError):
                render_depth(target, 6)


if __name__ == "__main__":
    unittest.main()
