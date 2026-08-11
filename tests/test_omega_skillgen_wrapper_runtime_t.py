import subprocess
import sys
import unittest
from pathlib import Path

from omega_skillgen_t.package import DEFAULT_WRAPPERS

ROOT = Path(__file__).resolve().parents[1]


class WrapperRuntimeTests(unittest.TestCase):
    def test_every_packaged_wrapper_executes_help_from_repository_root(self):
        self.assertGreaterEqual(len(DEFAULT_WRAPPERS), 8)
        for wrapper in DEFAULT_WRAPPERS:
            with self.subTest(wrapper=wrapper):
                path = ROOT / "scripts" / wrapper
                self.assertTrue(path.is_file(), f"missing wrapper {path}")
                result = subprocess.run(
                    [sys.executable, str(path), "--help"],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    f"wrapper failed: {wrapper}\nstdout={result.stdout}\nstderr={result.stderr}",
                )
                self.assertIn("usage:", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
