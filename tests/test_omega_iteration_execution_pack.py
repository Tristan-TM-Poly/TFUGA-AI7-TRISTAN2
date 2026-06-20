import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "omega_iteration_execution_pack.py"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_iteration_execution_pack", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class IterationExecutionPackTests(unittest.TestCase):
    def sample_selected(self):
        return {
            "summary": {"count": 2},
            "selected": [
                {"id": "a", "title": "Add validator", "action": "add_validator", "module": "m", "layer": "oak", "files": ["scripts/a.py"], "tests": ["unit"], "oak_gates": ["bounded_generation"], "residues": []},
                {"id": "b", "title": "Add workflow", "action": "add_workflow", "module": "m", "layer": "workflow", "files": [".github/workflows/b.yml"], "tests": ["yaml_present"], "oak_gates": ["prototype_is_not_proof"], "residues": ["review_required"]}
            ]
        }

    def test_build_pack(self):
        mod = load_module()
        pack = mod.build_pack(self.sample_selected(), mod.DEFAULT_CONFIG, "owner/repo")
        self.assertEqual(pack["count"], 2)
        self.assertIn("execution_prompt", pack)
        self.assertEqual(len(pack["file_plan"]), 2)
        self.assertTrue(pack["oak_boundary"]["bounded_batch"])
        self.assertIn(".github/workflows/b.yml", pack["impact_input"]["artifacts"])

    def test_write_outputs(self):
        mod = load_module()
        pack = mod.build_pack(self.sample_selected(), mod.DEFAULT_CONFIG, "owner/repo")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pack"
            mod.write_outputs(pack, out)
            self.assertTrue((out / "execution_pack.json").exists())
            self.assertTrue((out / "execution_prompt.md").exists())
            self.assertTrue((out / "impact_input.json").exists())


if __name__ == "__main__":
    unittest.main()
