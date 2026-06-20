import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "omega_publication_package_factory.py"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_publication_package_factory", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class OmegaPublicationPackageFactoryTests(unittest.TestCase):
    def test_classify_readiness(self):
        mod = load_module()
        thresholds = {"weak": 2.0, "promising": 5.0, "strong": 8.0}
        self.assertEqual(mod.classify_readiness(0.5, thresholds), "needs_more_evidence")
        self.assertEqual(mod.classify_readiness(3.0, thresholds), "weak_candidate")
        self.assertEqual(mod.classify_readiness(6.0, thresholds), "promising_candidate")
        self.assertEqual(mod.classify_readiness(9.0, thresholds), "strong_candidate")

    def test_build_packages_from_minimal_manifest(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = {
                "version": "omega.tristan_publication_atlas.v1",
                "matches": [
                    {
                        "institution": {"display_name": "Test University"},
                        "author": {"display_name": "Ada Researcher"},
                        "project_key": "omega_spectro_universe",
                        "project_title": "Omega Spectro Universe",
                        "score": 6.5,
                        "matched_terms": ["spectroscopy", "Raman"],
                        "works": [
                            {"publication_year": 2024, "title": "Raman spectroscopy benchmark", "landing_url": "https://example.org/work"}
                        ],
                        "residues": []
                    }
                ]
            }
            atlas_path = tmp_path / "atlas.json"
            atlas_path.write_text(json.dumps(manifest), encoding="utf-8")
            out_dir = tmp_path / "packages"
            records = mod.build_packages(atlas_path, None, out_dir, 0.0, 10)
            self.assertEqual(len(records), 1)
            self.assertTrue((out_dir / "publication_package_manifest.json").exists())
            self.assertTrue((out_dir / "PUBLICATION_PACKAGE_DASHBOARD.md").exists())
            self.assertTrue(any(path.endswith("05_OAK_VALIDATION_PLAN.md") for path in records[0].files))


if __name__ == "__main__":
    unittest.main()
