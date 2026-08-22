import contextlib
import io
import json
import unittest

from omega_zeta_square_t.cli import main


class TestTensorConstraintCli(unittest.TestCase):
    def test_tensor_constraint_cli_is_exact_and_non_promoting(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = main(["tensor-constraint", "--size", "2", "--shift", "0"])
        self.assertEqual(code, 0)
        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["schema"], "omega-zeta-square-tensor-constraint/1")
        self.assertFalse(payload["proves_rh"])
        self.assertFalse(payload["constraint"]["proves_rh"])
        self.assertEqual(payload["constraint"]["term_count"], 3) if "term_count" in payload["constraint"] else None
        terms = {
            item["monomial"] if "monomial" in item else self._monomial(item["exponents"]): item["coefficient"]["exact"]
            for item in payload["constraint"]["terms"]
        }
        self.assertEqual(terms, {"a2^2": "-4", "a1*a3": "3", "a1^2*a2": "1"})
        self.assertTrue(payload["oak"]["all_orders_required_for_r10"])

    @staticmethod
    def _monomial(exponents):
        factors = []
        for index, power in enumerate(exponents, start=1):
            if power == 1:
                factors.append(f"a{index}")
            elif power > 1:
                factors.append(f"a{index}^{power}")
        return "*".join(factors) if factors else "1"


if __name__ == "__main__":
    unittest.main()
