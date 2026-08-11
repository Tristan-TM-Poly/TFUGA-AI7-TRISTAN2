import tempfile
import unittest
import zipfile
from pathlib import Path

from omega_skillgen_t.package import build_standalone_bundle

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_standalone_bundle_has_one_manifest_and_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "skill.zip"
            result = build_standalone_bundle(ROOT, out)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["skill_manifests"], 1)
            self.assertGreaterEqual(len(result["wrappers"]), 5)
            with zipfile.ZipFile(out) as archive:
                names = archive.namelist()
                self.assertTrue(any(name.endswith("/SKILL.md") for name in names))
                self.assertTrue(any("/omega_skillgen_t/core.py" in name for name in names))
                self.assertTrue(any("/scripts/omega-skillgen" in name for name in names))


if __name__ == "__main__":
    unittest.main()
