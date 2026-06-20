import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "omega_open_data_harvester.py"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_open_data_harvester", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class OmegaOpenDataHarvesterTests(unittest.TestCase):
    def test_license_allowlist(self):
        mod = load_module()
        self.assertTrue(mod.license_allowed("CC-BY-4.0", ["cc-by"]))
        self.assertFalse(mod.license_allowed("unknown", ["cc-by"]))

    def test_manifest_boundary(self):
        mod = load_module()
        trace = mod.HarvestTrace(mode="search", theory="omega_math_universe")
        payload = trace.to_jsonable()
        self.assertTrue(payload["oak_boundary"]["metadata_is_not_validation"])
        self.assertEqual(payload["result_count"], 0)

    def test_download_item_skips_without_url(self):
        mod = load_module()
        item = mod.DataItem(source="test", query="q", title="No URL", url="")
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.download_item(item, Path(tmp), ["cc0"], 1024, dry_run=True)
        self.assertEqual(result["status"], "skipped")
        self.assertIn("missing_download_url", result["residues"])

    def test_download_item_dry_run(self):
        mod = load_module()
        item = mod.DataItem(
            source="test",
            query="q",
            title="Dataset",
            url="https://example.org/landing",
            download_url="https://example.org/file.csv",
            license_hint="CC0",
            size_bytes=12,
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.download_item(item, Path(tmp), ["cc0"], 1024, dry_run=True)
        self.assertEqual(result["status"], "dry_run")
        self.assertTrue(result["path"].endswith(".csv"))


if __name__ == "__main__":
    unittest.main()
