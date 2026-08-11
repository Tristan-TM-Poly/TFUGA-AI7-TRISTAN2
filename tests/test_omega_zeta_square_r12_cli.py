import contextlib
import io
import json
import unittest

from omega_zeta_square_t.r12_cli import main


class TestR12Cli(unittest.TestCase):
    def test_size_two_atlas_cli(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = main(["--max-size", "2", "--shifts", "0", "1"])
        self.assertEqual(code, 0)
        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["raw_occurrence_count"], 8)
        self.assertEqual(payload["unique_polynomial_count"], 6)
        self.assertFalse(payload["proves_rh"])
        self.assertTrue(payload["oak"]["structural_cvcd_only"])


if __name__ == "__main__":
    unittest.main()
