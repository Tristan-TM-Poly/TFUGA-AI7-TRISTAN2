import unittest

from omega_sensorium import (
    ActiveObservationEngine,
    MetaSensorium,
    MinimalWitnessCompiler,
    Observable,
    ObservationCandidate,
    ObservationCourt,
    ObservationReceipt,
    ScienceQuestion,
    ScienceToSensorCompiler,
    SensorCapability,
)


class SensoriumTests(unittest.TestCase):
    def setUp(self):
        self.question = ScienceQuestion("Q1", "separate H1/H2", ("H1", "H2"), 0.8)
        self.observables = (
            Observable("O1", "color", "photometry", 0.5, 0.5, 0.7),
            Observable("O2", "line", "spectroscopy", 0.7, 0.7, 0.9),
        )
        self.sensors = (
            SensorCapability("S1", ("O1",), 0.8, 0.8, 0.95, 1.0, provenance=("p",)),
            SensorCapability("S2", ("O2",), 0.9, 0.9, 0.94, 2.0, provenance=("p",)),
            SensorCapability("S3", ("O1", "O2"), 0.9, 0.9, 0.90, 5.0, provenance=("p",)),
        )

    def test_science_to_sensor_prefers_minimum_sensor_count_then_cost(self):
        genome = ScienceToSensorCompiler().compile(self.question, self.observables, self.sensors)
        self.assertEqual(genome.sensor_ids, ("S3",))

    def test_no_feasible_sensor_returns_none(self):
        impossible = (Observable("OX", "x", "gamma", 10, 10, 1),)
        self.assertIsNone(ScienceToSensorCompiler().compile(self.question, impossible, self.sensors))

    def test_empty_requirement_is_explicit_no_action(self):
        genome = ScienceToSensorCompiler().compile(self.question, (), self.sensors)
        self.assertEqual(genome.sensor_ids, ())
        self.assertIn("no-action", genome.genome_id)

    def test_minimal_witness_uses_threshold_then_resource_cost(self):
        candidates = (
            ObservationCandidate("cheap-weak", ("O1",), ("S1",), 1, 0.7, 1, 1, resource_cost=0.2),
            ObservationCandidate("valid", ("O2",), ("S2",), 1, 0.85, 0.9, 0.9, resource_cost=1.0),
            ObservationCandidate("expensive", ("O2",), ("S3",), 2, 0.95, 0.95, 0.95, resource_cost=4.0),
        )
        selected = MinimalWitnessCompiler().select(candidates, min_discrimination=0.8, min_calibration=0.8)
        self.assertEqual(selected.candidate_id, "valid")

    def test_no_action_wins_when_candidate_does_not_beat_baseline(self):
        candidate = ObservationCandidate("C", ("O1",), ("S1",), 0.1, 0.8, 0.8, 0.8)
        self.assertIsNone(MinimalWitnessCompiler().select((candidate,), min_discrimination=0.8, baseline_value=1.0))

    def test_active_observation_ranks_information_value(self):
        low = ObservationCandidate("low", ("O1",), ("S1",), 0.5, 0.8, 0.8, 0.8, resource_cost=1)
        high = ObservationCandidate("high", ("O2",), ("S2",), 1.0, 0.9, 0.9, 0.9, resource_cost=1)
        ranked = ActiveObservationEngine().rank((low, high))
        self.assertEqual([c.candidate_id for c in ranked], ["high", "low"])

    def test_receipt_requires_independent_verifier_and_calibration(self):
        receipt = ObservationReceipt(
            "R1", "E1", ("S1",), {}, ("hash",), "pipeline-v1", 0.1,
            "agent-A", "agent-A", ("source",),
        )
        result = ObservationCourt().verify_receipt(receipt)
        self.assertFalse(result.passed)
        self.assertTrue(any("Generator" in r for r in result.reasons))
        self.assertTrue(any("calibration" in r for r in result.reasons))

    def test_valid_receipt_passes(self):
        receipt = ObservationReceipt(
            "R2", "E2", ("S1",), {"S1": "cal-v1"}, ("hash",), "pipeline-v1", 0.1,
            "agent-A", "verifier-B", ("source",),
        )
        self.assertTrue(ObservationCourt().verify_receipt(receipt).passed)

    def test_meta_stop_reuses_existing_kernel(self):
        sensorium = MetaSensorium()
        self.assertFalse(sensorium.should_create_new_meta_layer(
            verified_out_of_sample_gain=100,
            meta_complexity_cost=0.1,
            expressible_by_current_kernel=True,
        ))


if __name__ == "__main__":
    unittest.main()
