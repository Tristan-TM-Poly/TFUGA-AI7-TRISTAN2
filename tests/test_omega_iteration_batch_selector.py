import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "omega_iteration_batch_selector.py"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_iteration_batch_selector", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def candidate(i, layer, module, action, priority=50):
    return {
        "id": f"c{i}",
        "title": f"candidate {i}",
        "layer": layer,
        "module": module,
        "action": action,
        "priority": priority,
        "oak_gates": ["bounded_generation", "prototype_is_not_proof"],
        "files": [f"docs/{i}.md"],
        "residues": [],
    }


class IterationBatchSelectorTests(unittest.TestCase):
    def test_selects_requested_size(self):
        mod = load_module()
        candidates = [candidate(i, f"l{i%4}", f"m{i%3}", f"a{i%5}", 100-i) for i in range(20)]
        selected = mod.select_batch(candidates, 8, mod.DEFAULT_CONFIG)
        self.assertEqual(len(selected), 8)
        self.assertGreaterEqual(len({x["layer"] for x in selected}), 3)

    def test_write_outputs(self):
        mod = load_module()
        selected = [candidate(i, f"l{i}", f"m{i}", f"a{i}") for i in range(3)]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            mod.write_outputs(selected, out)
            self.assertTrue((out / "selected_batch.json").exists())
            self.assertTrue((out / "selected_batch_prompt.md").exists())


if __name__ == "__main__":
    unittest.main()
