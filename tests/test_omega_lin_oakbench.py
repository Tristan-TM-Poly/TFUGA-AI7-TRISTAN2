from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import omega_lin_oakbench as oakbench  # noqa: E402


class OmegaLinOakbenchTest(unittest.TestCase):
    def test_pendulum_jacobian_and_affine_offset_near_equilibrium(self) -> None:
        f = oakbench.pendulum_rhs({"g": 9.81, "length": 1.0, "damping": 0.05})
        x0 = [0.0, 0.0]
        u0 = [0.0]
        A = oakbench.finite_difference_jacobian_x(f, x0, u0, 1e-6)
        B = oakbench.finite_difference_jacobian_u(f, x0, u0, 1e-6)
        c = oakbench.affine_offset(f(x0, u0), A, B, x0, u0)
        self.assertAlmostEqual(A[0][1], 1.0, places=6)
        self.assertAlmostEqual(A[1][0], -9.81, places=5)
        self.assertAlmostEqual(A[1][1], -0.05, places=6)
        self.assertAlmostEqual(B[1][0], 1.0, places=6)
        self.assertEqual(c, [0.0, 0.0])

    def test_affine_offset_is_nonzero_away_from_equilibrium(self) -> None:
        f = oakbench.pendulum_rhs({"g": 9.81, "length": 1.0, "damping": 0.05})
        x0 = [0.4, 0.0]
        u0 = [0.0]
        A = oakbench.finite_difference_jacobian_x(f, x0, u0, 1e-6)
        B = oakbench.finite_difference_jacobian_u(f, x0, u0, 1e-6)
        c = oakbench.affine_offset(f(x0, u0), A, B, x0, u0)
        self.assertGreater(abs(c[1]), 0.01)

    def test_scaled_norm_respects_units(self) -> None:
        raw = oakbench.norm2([1.0, 10.0])
        scaled = oakbench.scaled_norm([1.0, 10.0], [1.0, 10.0])
        self.assertGreater(raw, scaled)
        self.assertAlmostEqual(scaled, math.sqrt(2.0), places=7)

    def test_pendulum_report_is_conservative_and_controllable(self) -> None:
        report = oakbench.run_oakbench(oakbench.default_config("pendulum"))
        self.assertEqual(report.model, "pendulum")
        self.assertGreater(report.valid_radius, 0.0)
        self.assertIs(report.stable_local_2d, True)
        self.assertIs(report.controllable_2d, True)
        self.assertIn("L4", report.oak_level)
        self.assertIn("Research/education prototype only: no physical control certification.", report.oak_warnings)
        self.assertIn("global periodicity", report.invariant_audit["lost_or_approximated"])
        self.assertGreaterEqual(report.residuals.curvature_index, 0.0)

    def test_vanderpol_warning_and_duffing_support(self) -> None:
        vdp = oakbench.run_oakbench(oakbench.default_config("vanderpol"))
        self.assertIn("limit-cycle global geometry", vdp.invariant_audit["lost_or_approximated"])
        self.assertTrue(any("affine" in item for item in vdp.m_minus))

        duffing = oakbench.run_oakbench(oakbench.default_config("duffing"))
        self.assertEqual(duffing.model, "duffing")
        self.assertIn("cubic stiffness far from x0", duffing.invariant_audit["lost_or_approximated"])

    def test_write_json_and_markdown_reports(self) -> None:
        report = oakbench.run_oakbench(oakbench.default_config("pendulum"))
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "pendulum.json"
            md_path = Path(tmpdir) / "pendulum.md"
            oakbench.write_json_report(report, json_path)
            oakbench.write_markdown_report(report, md_path)
            data = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(data["model"], "pendulum")
            self.assertIn("residuals", data)
            self.assertTrue(math.isfinite(data["valid_radius"]))
            self.assertIn("OAK boundary", md_path.read_text(encoding="utf-8"))

    def test_cli_system_outputs_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "duffing.json"
            out_md = Path(tmpdir) / "duffing.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "omega_lin_oakbench.py"),
                    "--system",
                    "duffing",
                    "--output",
                    str(out_json),
                    "--markdown-output",
                    str(out_md),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("duffing", result.stdout)
            self.assertTrue(out_json.exists())
            self.assertTrue(out_md.exists())
            self.assertEqual(json.loads(out_json.read_text(encoding="utf-8"))["model"], "duffing")


if __name__ == "__main__":
    unittest.main()
