import unittest

from omega_skillgen_t.discovery_bridge import record_to_skill_spec
from omega_skillgen_t.benchmark_bridge import benchmark_to_eval_cases, enrich_spec_with_benchmarks
from omega_skillgen_t.core import validate_spec


class BenchmarkBridgeTests(unittest.TestCase):
    def test_benchmark_becomes_positive_and_negative_control(self):
        record = {
            "id":"BEN-1",
            "generator_id":"GEN-1",
            "variant":0,
            "parameters":{"scale":0.5},
            "expected":{"finite":True,"reconstruction_error_max":1e-6,"preserve":"charge"},
            "negative_control":"wrong_family",
            "oak_status":"synthetic_template_not_empirical_evidence"
        }
        cases = benchmark_to_eval_cases(record)
        self.assertEqual([case["class"] for case in cases], ["positive", "edge"])
        self.assertTrue(all(case["oak_status"] == "synthetic_template_not_empirical_evidence" for case in cases))

    def test_enrichment_preserves_epistemic_boundary(self):
        generator = {
            "id":"GEN-1","domain":"spectral","family":"translation","scale":"atomic",
            "representation":"operator","status":"prototype","invariant":"charge","risk":"none",
            "oak_gate":"baseline+negative_control","benchmark_ids":["BEN-1"]
        }
        benchmark = {
            "id":"BEN-1","generator_id":"GEN-1","variant":0,"parameters":{"scale":0.5},
            "expected":{"finite":True,"reconstruction_error_max":1e-6,"preserve":"charge"},
            "negative_control":"wrong_family","oak_status":"synthetic_template_not_empirical_evidence"
        }
        spec = enrich_spec_with_benchmarks(record_to_skill_spec(generator), [benchmark])
        self.assertEqual(validate_spec(spec), [])
        self.assertEqual(len(spec["benchmark_contracts"]), 1)
        self.assertTrue(any("empirical evidence" in invariant for invariant in spec["invariants"]))


if __name__ == "__main__":
    unittest.main()
