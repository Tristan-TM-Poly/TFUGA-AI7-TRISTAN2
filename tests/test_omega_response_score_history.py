import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "omega_response_score_history.py"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_response_score_history", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ResponseScoreHistoryTests(unittest.TestCase):
    def test_collect_and_summary(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.json").write_text(json.dumps({"summary": "a", "artifacts": ["scripts/a.py"], "tests": ["unit"], "workflows": []}), encoding="utf-8")
            (root / "b.json").write_text(json.dumps({"summary": "b", "score": 84, "rating": "plus_ultra"}), encoding="utf-8")
            records = mod.collect(root)
            summary = mod.summarize(records)
            self.assertEqual(summary["count"], 2)
            self.assertEqual(summary["best_score"], 84)
            self.assertEqual(records[-1]["rating"], "plus_ultra")

    def test_write_outputs(self):
        mod = load_module()
        records = [{"source": "x", "summary": "x", "score": 70, "rating": "very_strong", "artifact_count": 1, "tests_count": 1, "workflow_count": 0, "residue_count": 0}]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            mod.write_outputs(records, out)
            self.assertTrue((out / "response_score_history.json").exists())
            self.assertTrue((out / "RESPONSE_SCORE_HISTORY.md").exists())


if __name__ == "__main__":
    unittest.main()
