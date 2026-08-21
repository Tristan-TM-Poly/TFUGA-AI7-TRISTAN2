import json
import unittest
from dataclasses import replace
from pathlib import Path

from omega_capability_os_t.pilot_preregistration import (
    QuebecPilotPreregistration,
    evaluate_preregistration,
)


class QuebecPilotPreregistrationR01Tests(unittest.TestCase):
    def protocol(self, **overrides):
        payload = dict(
            protocol_id="qc-pilot-test-001",
            jurisdiction="Québec, Canada",
            context="bounded educational capability-transfer test fixture",
            affected_groups=("participating learners", "teaching staff"),
            beneficiary_groups=("participating learners",),
            system_version="capability-os-test-v1",
            consent_version="consent-test-v1",
            generator_id="intervention-designer",
            evaluator_id="independent-evaluator",
            baseline="same task without the intervention",
            intervention="bounded assistance plus explicit verification procedure",
            alternatives=("no intervention", "checklist-only intervention"),
            transfer_observable="independent task performance after system withdrawal",
            withdrawal_condition="system unavailable during independent task",
            delayed_replay_window="one predeclared delayed session",
            dependency_measurement="post-withdrawal assistance requests per task",
            min_withdrawal_retention=0.70,
            min_delayed_retention=0.60,
            max_dependency_after_withdrawal=0.0,
            min_understanding=0.70,
            min_agency=0.70,
            max_acceptance_debt=0.50,
            opt_out_mechanism="participant can decline without penalty",
            contestation_mechanism="documented channel for objections and corrections",
            rollback_mechanism="stop intervention and revert to baseline procedure",
            evidence_disclosure="share protocol, uncertainty, null and negative results",
            stakeholder_representation="affected roles represented before criteria freeze",
            minority_residual_policy="preserve unresolved objections in the final receipt",
            material_change_reconsultation=True,
            personalized_psychological_targeting=False,
            acceptance_rate_is_success_gate=False,
            outcomes_observed=False,
            authority_status="UNRESOLVED",
            decision_criteria=("HOLD", "REVISE", "NO_ACTION", "PILOT_ELIGIBLE"),
            require_delayed_above_baseline=True,
            require_evaluator_separation=True,
        )
        payload.update(overrides)
        return QuebecPilotPreregistration(**payload)

    def test_repository_template_cannot_freeze_with_placeholders(self):
        path = Path("pilots/quebec/8f_capability_transfer_preregistration.template.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        protocol = QuebecPilotPreregistration.from_dict(payload)
        receipt = evaluate_preregistration(protocol)
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("unresolved_placeholder", receipt.blockers)
        self.assertFalse(receipt.execution_eligible)

    def test_complete_pre_outcome_protocol_can_freeze_without_execution_authority(self):
        receipt = evaluate_preregistration(self.protocol())
        self.assertEqual(receipt.decision, "FROZEN")
        self.assertEqual(receipt.blockers, ())
        self.assertIsNotNone(receipt.protocol_digest)
        self.assertIsNotNone(receipt.legitimacy_criteria_digest)
        self.assertIsNotNone(receipt.transfer_criteria_digest)
        self.assertFalse(receipt.execution_eligible)

    def test_outcomes_cannot_be_observed_before_freeze(self):
        receipt = evaluate_preregistration(self.protocol(outcomes_observed=True))
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("outcomes_already_observed", receipt.blockers)

    def test_acceptance_rate_cannot_be_success_gate(self):
        receipt = evaluate_preregistration(self.protocol(acceptance_rate_is_success_gate=True))
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("acceptance_rate_cannot_be_success_gate", receipt.blockers)

    def test_personalized_psychological_targeting_is_denied(self):
        receipt = evaluate_preregistration(self.protocol(personalized_psychological_targeting=True))
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("personalized_psychological_targeting_denied", receipt.blockers)

    def test_generator_and_evaluator_separation_is_required(self):
        receipt = evaluate_preregistration(
            self.protocol(generator_id="same-actor", evaluator_id="same-actor")
        )
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("generator_evaluator_not_separated", receipt.blockers)

    def test_alternative_or_no_intervention_baseline_is_required(self):
        receipt = evaluate_preregistration(self.protocol(alternatives=()))
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("alternatives_missing", receipt.blockers)

    def test_any_material_protocol_mutation_changes_frozen_digest(self):
        original = self.protocol()
        mutated = replace(original, min_agency=0.80)
        first = evaluate_preregistration(original)
        second = evaluate_preregistration(mutated)
        self.assertEqual(first.decision, "FROZEN")
        self.assertEqual(second.decision, "FROZEN")
        self.assertNotEqual(first.protocol_digest, second.protocol_digest)
        self.assertNotEqual(first.legitimacy_criteria_digest, second.legitimacy_criteria_digest)


if __name__ == "__main__":
    unittest.main()
