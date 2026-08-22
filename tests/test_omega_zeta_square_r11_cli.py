import contextlib
import io
import json
import unittest

from omega_zeta_square_t.r11_cli import main


class TestR11Cli(unittest.TestCase):
    def _run(self, argv):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = main(argv)
        self.assertEqual(code, 0)
        return json.loads(stream.getvalue())

    def test_principal_size_two_outputs_three_constraints(self):
        payload = self._run(["principal", "--size", "2"])
        self.assertEqual(payload["constraint_count"], 3)
        self.assertTrue(payload["oak"]["finite_psd_requires_all_principal_minors"])
        self.assertFalse(payload["proves_rh"])

    def test_xi_size_two_matches_r11_numerator(self):
        payload = self._run(["xi", "--size", "2"])
        constraint = payload["constraint"]
        self.assertEqual(constraint["common_integer_scale"], 1440)
        terms = {
            self._monomial(term["exponents"]): term["coefficient"]
            for term in constraint["terms"]
        }
        self.assertEqual(
            terms,
            {"d0*d4^2": -10, "d0*d2*d6": 3, "d2^2*d4": 15},
        )
        self.assertFalse(payload["proves_rh"])

    @staticmethod
    def _monomial(exponents):
        names = ["d0"] + [f"d{2*j}" for j in range(1, len(exponents))]
        parts = []
        for name, power in zip(names, exponents):
            if power == 1:
                parts.append(name)
            elif power > 1:
                parts.append(f"{name}^{power}")
        return "*".join(parts) if parts else "1"


if __name__ == "__main__":
    unittest.main()
