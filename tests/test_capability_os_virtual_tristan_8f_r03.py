import unittest

from omega_capability_os_t.virtual_tristan_8f import (
    BeneficiaryFlow,
    EighthFireThresholds,
    eighth_fire_swarm_court,
    evaluate_beneficiary_flow,
)


class VirtualTristanEighthFireR03Tests(unittest.TestCase):
    def good(self, beneficiary_id="b1", **overrides):
        payload = dict(
            beneficiary_id=beneficiary_id,
            capability_left_behind=0.8,
            autonomy_gain=0.4,
            forkability_gain=0.3,
            reciprocity=0.4,
            dependency_created=0.1,
            capture_risk=0.1,
            irreversible_harm=0.0,
            dependency_half_life=0.5,
            consent_present=True,
            attribution_present=True,
        )
        payload.update(overrides)
        return BeneficiaryFlow(**payload)

    def test_passes_noncompensatory_flow(self):
        result = evaluate_beneficiary_flow(self.good())
        self.assertEqual(result.decision, "PASS")
        self.assertEqual(result.blockers, ())

    def test_missing_consent_blocks_even_with_high_positive_score(self):
        result = evaluate_beneficiary_flow(
            self.good(
                capability_left_behind=10.0,
                autonomy_gain=10.0,
                forkability_gain=10.0,
                reciprocity=10.0,
                consent_present=False,
            )
        )
        self.assertEqual(result.decision, "HOLD")
        self.assertIn("consent_missing", result.blockers)

    def test_capture_and_dependency_are_hard_gates(self):
        result = evaluate_beneficiary_flow(
            self.good(dependency_created=0.9, capture_risk=0.8)
        )
        self.assertEqual(result.decision, "HOLD")
        self.assertIn("dependency_exceeds_threshold", result.blockers)
        self.assertIn("capture_risk_exceeds_threshold", result.blockers)

    def test_beneficiary_n_plus_one_blocks_forgotten_person(self):
        report = eighth_fire_swarm_court(
            (self.good("known"),),
            expected_beneficiaries=("known", "forgotten"),
        )
        self.assertEqual(report.decision, "HOLD")
        self.assertEqual(report.forgotten_beneficiaries, ("forgotten",))
        self.assertIn("beneficiary_n_plus_one_failure", report.blockers)

    def test_all_expected_beneficiaries_can_pass(self):
        report = eighth_fire_swarm_court(
            (self.good("a"), self.good("b")),
            expected_beneficiaries=("a", "b"),
        )
        self.assertEqual(report.decision, "PASS")
        self.assertEqual(report.blockers, ())

    def test_apoptosis_ready_requires_zero_dependency(self):
        ready = evaluate_beneficiary_flow(
            self.good(dependency_created=0.0, dependency_half_life=0.0)
        )
        dependent = evaluate_beneficiary_flow(self.good(dependency_created=0.1))
        self.assertTrue(ready.apoptosis_ready)
        self.assertFalse(dependent.apoptosis_ready)

    def test_thresholds_are_explicit_and_finite(self):
        with self.assertRaises(ValueError):
            EighthFireThresholds(max_capture_risk=float("inf"))


if __name__ == "__main__":
    unittest.main()
