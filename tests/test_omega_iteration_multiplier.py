import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "omega_iteration_multiplier.py"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_iteration_multiplier", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class OmegaIterationMultiplierTests(unittest.TestCase):
    def test_build_additions_count_and_batches(self):
        mod = load_module()
        additions = mod.build_additions(mod.DEFAULT_CONFIG, 64, 16)
        self.assertEqual(len(additions), 64)
        self.assertEqual(additions[0].batch, 1)
        self.assertEqual(additions[-1].batch, 4)
        self.assertTrue(additions[0].oak_gates)

    def test_bounds(self):
        mod = load_module()
        with self.assertRaises(ValueError):
            mod.build_additions(mod.DEFAULT_CONFIG, 0, 16)
        with self.assertRaises(ValueError):
            mod.build_additions(mod.DEFAULT_CONFIG, 8, 0)

    def test_write_outputs(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            additions = mod.build_additions(mod.DEFAULT_CONFIG, 12, 4, focus="chatgpt_tristan_v2")
            mod.write_outputs(additions, out, 4)
            manifest = out / "iteration_multiplier_manifest.json"
            dashboard = out / "ITERATION_MULTIPLIER_DASHBOARD.md"
            self.assertTrue(manifest.exists())
            self.assertTrue(dashboard.exists())
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["addition_count"], 12)
            self.assertTrue(data["oak_boundary"]["bounded_generation"])
            self.assertTrue((out / "batches" / "batch_001" / "prompt.md").exists())


if __name__ == "__main__":
    unittest.main()
