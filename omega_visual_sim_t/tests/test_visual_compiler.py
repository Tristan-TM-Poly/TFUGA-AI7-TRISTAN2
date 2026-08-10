import json
import tempfile
import unittest
from pathlib import Path

from omega_visual.core import SpecError, compile_visual, load_spec, render_svg, simulate, verify_manifest


ROOT = Path(__file__).parents[1]


class VisualCompilerTests(unittest.TestCase):
    def test_end_to_end_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = compile_visual(ROOT / "examples/oscillator.json", root / "a")
            second = compile_visual(ROOT / "examples/oscillator.json", root / "b")
            self.assertEqual(first["spec_sha256"], second["spec_sha256"])
            self.assertEqual(first["artifacts"], second["artifacts"])
            self.assertEqual(verify_manifest(root / "a/manifest.json"), [])

    def test_initial_conditions_are_preserved(self) -> None:
        spec = load_spec(ROOT / "examples/oscillator.json")
        initial = simulate(spec)[0]
        self.assertEqual(initial.t_s, 0.0)
        self.assertAlmostEqual(initial.displacement_m, 0.1)
        self.assertAlmostEqual(initial.velocity_m_s, 0.0)

    def test_units_are_a_truth_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            spec = json.loads((ROOT / "examples/oscillator.json").read_text())
            del spec["model"]["units"]["mass"]
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps(spec))
            with self.assertRaisesRegex(SpecError, "units"):
                load_spec(path)

    def test_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            compile_visual(ROOT / "examples/oscillator.json", root)
            (root / "states.json").write_text("[]")
            self.assertEqual(verify_manifest(root / "manifest.json"), ["hash mismatch: states.json"])

    def test_svg_title_is_escaped(self) -> None:
        spec = load_spec(ROOT / "examples/oscillator.json")
        spec["visual"]["title"] = "<script>alert('x')</script>"
        svg = render_svg(spec, simulate(spec)[0])
        self.assertNotIn("<script>", svg)
        self.assertIn("&lt;script&gt;", svg)

    def test_unbounded_images_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            spec = json.loads((ROOT / "examples/oscillator.json").read_text())
            spec["output"]["width"] = 100_000
            path = Path(directory) / "oversized.json"
            path.write_text(json.dumps(spec))
            with self.assertRaisesRegex(SpecError, "dimensions"):
                load_spec(path)


if __name__ == "__main__":
    unittest.main()
