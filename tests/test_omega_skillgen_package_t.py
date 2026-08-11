import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path

from omega_skillgen_t.package import ENTRYPOINTS, build_standalone_bundle

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_standalone_bundle_has_one_manifest_runtime_and_install_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "skill.zip"
            result = build_standalone_bundle(ROOT, out)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["skill_manifests"], 1)
            self.assertEqual(result["pyproject_manifests"], 1)
            self.assertEqual(len(result["entrypoints"]), 9)
            self.assertGreaterEqual(len(result["wrappers"]), 9)
            with zipfile.ZipFile(out) as archive:
                names = archive.namelist()
                self.assertTrue(any(name.endswith("/SKILL.md") for name in names))
                self.assertTrue(any("/omega_skillgen_t/core.py" in name for name in names))
                self.assertTrue(any("/scripts/omega-skillgen" in name for name in names))
                pyproject_name = next(name for name in names if name.endswith("/pyproject.toml"))
                metadata = tomllib.loads(archive.read(pyproject_name).decode("utf-8"))
                self.assertEqual(metadata["project"]["scripts"], ENTRYPOINTS)
                self.assertEqual(metadata["build-system"]["build-backend"], "setuptools.build_meta")


if __name__ == "__main__":
    unittest.main()
