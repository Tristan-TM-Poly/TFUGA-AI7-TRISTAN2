import unittest

from omega_capability_os_t.social_legitimacy_profile import (
    FrozenLegitimacyCriteria,
    SocialLegitimacyObservation,
    evaluate_social_legitimacy,
)


class CapabilityOsSocialLegitimacyR05Tests(unittest.TestCase):
    def criteria(self, **overrides):
        payload = dict(
            initiative_id="qc-social-pilot-001",
            system_version="v1",
            consent_version="consent-v1",
            evaluator_id="independent-evaluator",
            min_understanding=0.70,
            min_agency=0.70,
            max_acceptance_debt=0.50,
            require_evaluator_separation=True,
            require_opt_out=True,
            require_contestability=True,
            require_reversibility=True,
            require_evidence_transparency=True,
            require_stakeholder_representation=True,
            forbid_personalized_manipulation=True,
        )
        payload.update(overrides)
        return FrozenLegitimacyCriteria(**payload)

    def observation(self, criteria, **overrides):
        payload = dict(
            criteria_digest=criteria.digest(),
            generator_id="proposal-generator",
            evaluator_id="independent-evaluator",
            system_version="v1",
            consent_version="consent-v1",
            understanding=0.90,
            agency=0.90,
            acceptance_rate=0.60,
            non_coercion=True,
            opt_out_available=True,
            contestability_available=True,
            reversibility_available=True,
            evidence_transparent=True,
            stakeholder_representation_present=True,
            minority_residuals=("privacy concern remains open",),
            minority_residuals_preserved=True,
            unresolved_concerns=0.10,
            information_asymmetry=0.05,
            hidden_dependency=0.0,
            unmeasured_harm=0.0,
            unrepresented_stakeholders=0.0,
            personalized_manipulation_used=False,
            material_change_since_consent=False,
        )
        payload.update(overrides)
        return SocialLegitimacyObservation(**payload)

    def test_zero_adoption_can_pass_a_legitimate_process(self):
        criteria = self.criteria()
        receipt = evaluate_social_legitimacy(
            criteria,
            self.observation(criteria, acceptance_rate=0.0),
        )
        self.assertEqual(receipt.decision, "PASS")
        self.assertEqual(receipt.acceptance_rate, 0.0)

    def test_high_acceptance_cannot_compensate_for_coercion(self):
        criteria = self.criteria()
        receipt = evaluate_social_legitimacy(
            criteria,
            self.observation(criteria, acceptance_rate=1.0, non_coercion=False),
        )
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("coercion_or_undue_pressure_detected", receipt.blockers)

    def test_personalized_manipulation_is_hard_denied(self):
        criteria = self.criteria()
        receipt = evaluate_social_legitimacy(
            criteria,
            self.observation(criteria, personalized_manipulation_used=True),
        )
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("personalized_manipulation_denied", receipt.blockers)

    def test_material_change_requires_reconsultation(self):
        criteria = self.criteria()
        receipt = evaluate_social_legitimacy(
            criteria,
            self.observation(criteria, material_change_since_consent=True),
        )
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("reconsultation_required", receipt.blockers)

    def test_consent_version_mismatch_blocks(self):
        criteria = self.criteria()
        receipt = evaluate_social_legitimacy(
            criteria,
            self.observation(criteria, consent_version="consent-v0"),
        )
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("consent_version_mismatch", receipt.blockers)

    def test_minority_residual_must_not_be_erased(self):
        criteria = self.criteria()
        receipt = evaluate_social_legitimacy(
            criteria,
            self.observation(criteria, minority_residuals_preserved=False),
        )
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("minority_residual_erased", receipt.blockers)

    def test_acceptance_debt_is_non_compensatory(self):
        criteria = self.criteria(max_acceptance_debt=0.50)
        receipt = evaluate_social_legitimacy(
            criteria,
            self.observation(
                criteria,
                acceptance_rate=1.0,
                unresolved_concerns=0.30,
                information_asymmetry=0.20,
                hidden_dependency=0.20,
            ),
        )
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("acceptance_debt_exceeds_threshold", receipt.blockers)

    def test_generator_cannot_be_own_evaluator(self):
        criteria = self.criteria(evaluator_id="same-actor")
        receipt = evaluate_social_legitimacy(
            criteria,
            self.observation(criteria, generator_id="same-actor", evaluator_id="same-actor"),
        )
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("generator_evaluator_not_separated", receipt.blockers)


if __name__ == "__main__":
    unittest.main()
