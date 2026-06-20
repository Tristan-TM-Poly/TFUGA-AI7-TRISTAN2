import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "omega_tristan_publication_atlas.py"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_tristan_publication_atlas", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class OmegaTristanPublicationAtlasTests(unittest.TestCase):
    def test_safe_slug(self):
        mod = load_module()
        self.assertEqual(mod.safe_slug("Université de Montréal!"), "universit-de-montr-al")
        self.assertEqual(mod.safe_slug(""), "item")

    def test_score_match(self):
        mod = load_module()
        work = mod.Work(
            openalex_id="W1",
            title="Raman spectroscopy for crystal materials",
            cited_by_count=10,
            concepts=["Spectroscopy", "Materials science"],
        )
        score, terms = mod.score_match(["spectroscopy", "Raman", "crystal"], None, [work])
        self.assertGreater(score, 0)
        self.assertIn("spectroscopy", terms)

    def test_offline_atlas_writes_outputs(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "atlas"
            code = mod.main([
                "--scope", "quebec",
                "--offline",
                "--max-institutions", "2",
                "--top-k", "5",
                "--out-dir", str(out_dir),
            ])
            self.assertEqual(code, 0)
            manifest = out_dir / "publication_atlas_manifest.json"
            self.assertTrue(manifest.exists())
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertTrue(data["oak_boundary"]["no_email_automation"])
            self.assertGreaterEqual(data["institution_count"], 1)


if __name__ == "__main__":
    unittest.main()
