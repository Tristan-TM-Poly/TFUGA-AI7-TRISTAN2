from __future__ import annotations

import math
import unittest

from omega_compute_physics_t import ComplexityAtlas, ResourceSample, profile_call, profile_pipeline


class ComplexityAtlasTests(unittest.TestCase):
    def test_multivariate_polynomial_fit_recovers_surface(self) -> None:
        atlas = ComplexityAtlas(name="poly-surface")
        for a in range(1, 5):
            for b in range(1, 5):
                y = 2.0 + 3.0 * a + 4.0 * b + 5.0 * a * b
                atlas.add_sample(
                    ResourceSample(
                        variables={"a": float(a), "b": float(b)},
                        resources={"wall_time_s": y},
                    )
                )
        model = atlas.fit(
            "wall_time_s",
            max_total_degree=2,
            include_logs=False,
            include_xlogx=False,
            ridge=1e-14,
        )
        prediction = model.predict({"a": 5.0, "b": 3.0})
        expected = 2.0 + 3.0 * 5.0 + 4.0 * 3.0 + 5.0 * 5.0 * 3.0
        self.assertAlmostEqual(prediction, expected, places=6)
        self.assertGreater(model.r2, 0.999999)
        self.assertEqual(model.status, "empirical-fit")
        self.assertIn("does not establish asymptotic", model.certificate()["oak_warning"])

    def test_local_elasticity_recovers_quadratic_exponent(self) -> None:
        atlas = ComplexityAtlas(name="quadratic")
        for n in range(1, 9):
            atlas.add_sample(
                ResourceSample(
                    variables={"n": float(n)},
                    resources={"time": float(n * n)},
                )
            )
        atlas.fit(
            "time",
            max_total_degree=2,
            include_logs=False,
            include_xlogx=False,
            ridge=1e-14,
        )
        exponent = atlas.elasticity("time", {"n": 4.5})["n"]
        self.assertAlmostEqual(exponent, 2.0, places=4)
        directional = atlas.path_scaling_exponent("time", {"n": 4.5}, {"n": 1.0})
        self.assertAlmostEqual(directional, 2.0, places=4)

    def test_phase_boundary_detects_slope_jump(self) -> None:
        atlas = ComplexityAtlas(name="phase")
        for n in (1.0, 2.0, 4.0, 8.0, 16.0, 32.0):
            if n <= 8.0:
                value = n
            else:
                value = 8.0 * (n / 8.0) ** 3
            atlas.add_sample(ResourceSample(variables={"n": n}, resources={"time": value}))
        boundaries = atlas.phase_boundaries("n", "time", jump_threshold=1.0)
        self.assertTrue(boundaries)
        self.assertEqual(boundaries[0]["status"], "empirical-regime-candidate")
        self.assertTrue(8.0 < boundaries[0]["location"] < 16.0)
        self.assertAlmostEqual(boundaries[0]["slope_before"], 1.0, places=7)
        self.assertAlmostEqual(boundaries[0]["slope_after"], 3.0, places=7)

    def test_interaction_hessian_is_small_for_pure_power_law(self) -> None:
        atlas = ComplexityAtlas(name="power")
        # a*b is degree two and has constant log-elasticities (1, 1), so the
        # log-space Hessian should be approximately zero away from numerical noise.
        for a in (1.0, 2.0, 3.0, 4.0):
            for b in (1.0, 2.0, 3.0, 4.0):
                atlas.add_sample(ResourceSample(variables={"a": a, "b": b}, resources={"r": a * b}))
        atlas.fit(
            "r",
            max_total_degree=2,
            include_logs=False,
            include_xlogx=False,
            ridge=1e-14,
        )
        hessian = atlas.interaction_hessian("r", {"a": 2.5, "b": 2.5})
        self.assertLess(abs(hessian["a"]["a"]), 1e-3)
        self.assertLess(abs(hessian["a"]["b"]), 1e-3)
        self.assertLess(abs(hessian["b"]["a"]), 1e-3)
        self.assertLess(abs(hessian["b"]["b"]), 1e-3)


class ProfilerTests(unittest.TestCase):
    def test_profile_call_emits_resource_sample(self) -> None:
        result = profile_call(
            lambda n: sum(i * i for i in range(n)),
            1000,
            variables={"n": 1000.0},
            repeats=2,
            warmups=0,
        )
        self.assertEqual(result.sample.variables["n"], 1000.0)
        self.assertGreaterEqual(result.resources["wall_time_s"], 0.0)
        self.assertGreaterEqual(result.resources["cpu_time_s"], 0.0)
        self.assertGreaterEqual(result.resources["peak_python_bytes"], 0.0)
        self.assertEqual(len(result.repetitions), 2)
        self.assertIn("measurement_semantics", result.sample.metadata)

    def test_sequential_pipeline_composition(self) -> None:
        pipeline = profile_pipeline(
            [
                ("plus_one", lambda x: x + 1),
                ("square", lambda x: x * x),
            ],
            3,
            variables={"n": 1.0},
            repeats_per_stage=1,
            warmups_per_stage=0,
        )
        self.assertEqual(pipeline.output, 16)
        self.assertEqual([name for name, _ in pipeline.stages], ["plus_one", "square"])
        self.assertGreaterEqual(pipeline.resources["wall_time_s"], 0.0)


if __name__ == "__main__":
    unittest.main()
