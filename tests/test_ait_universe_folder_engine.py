import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ait_universe_folder_engine.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ait_universe_folder_engine", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AITUniverseFolderEngineTests(unittest.TestCase):
    def test_generation_creates_meta_trace_and_local_node_files(self):
        engine = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "AIT-Universe"
            code = engine.main([
                "--root", str(root),
                "--max-depth", "1",
                "--branching", "2",
                "--node-limit", "12",
                "--force",
            ])
            self.assertEqual(code, 0)
            self.assertTrue((root / "Meta-Hypergraph" / "meta.json").exists())
            self.assertTrue((root / "ait_universe_trace.json").exists())

            trace = json.loads((root / "ait_universe_trace.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(trace["node_count"], 2)
            self.assertTrue(trace["oak_boundary"]["expansion_is_bounded"])

    def test_dry_run_does_not_write_files(self):
        engine = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "DryRun-Universe"
            code = engine.main([
                "--root", str(root),
                "--max-depth", "1",
                "--branching", "2",
                "--node-limit", "8",
                "--dry-run",
            ])
            self.assertEqual(code, 0)
            self.assertFalse((root / "Meta-Hypergraph" / "meta.json").exists())

    def test_stable_hash_is_deterministic(self):
        engine = load_module()
        self.assertEqual(engine.stable_hash("a", "b"), engine.stable_hash("a", "b"))
        self.assertNotEqual(engine.stable_hash("a", "b"), engine.stable_hash("a", "c"))


if __name__ == "__main__":
    unittest.main()
