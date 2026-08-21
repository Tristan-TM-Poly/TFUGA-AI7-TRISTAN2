import unittest

from omega_capability_os_t.virtual_tristan_8f import (
    BeneficiaryFlow,
    ConstitutionalGates,
    FrozenTransferCriteria,
    TransferObservation,
    evaluate_constitutional_beneficiary_flow,
    evaluate_prospective_transfer,
)


class VirtualTristanEighthFireR04Tests(unittest.TestCase):
    def flow(self, **overrides):
        payload = dict(
            beneficiary_id="beneficiary-qc-1",
            capability_left_behind=0.85,
            autonomy_gain=0.40,
            forkability_gain=0.30,
            reciprocity=0.35,
            dependency_created=0.0,
            capture_risk=0.05,
            irreversible_harm=0.0,
            dependency_half_life=0.0,
            consent_present=True,
            attribution_present=True,
        )
        payload.update(overrides)
        return BeneficiaryFlow(**payload)

    def gates(self, **overrides):
        payload = dict(
            evidence=True,
            safety=True,
            non_domination=True,
            regeneration=True,
            rollback_contestability=True,
        )
        payload.update(overrides)
        return ConstitutionalGates(**payload)

    def criteria(self, **overrides):
        payload = dict(
            experiment_id="qc-transfer-pilot-001",
            evaluator_id="independent-evaluator",
            min_withdrawal_retention=0.70,
            min_delayed_retention=0.60,
            max_dependency_after_withdrawal=0.0,
            require_delayed_above_baseline=True,
            require_evaluator_separation=True,
        )
        payload.update(overrides)
        return FrozenTransferCriteria(**payload)

    def observation(self, criteria, **overrides):
        payload = dict(
            beneficiary_id="beneficiary-qc-1",
            criteria_digest=criteria.digest(),
            generator_id="capability-generator",
            evaluator_id="independent-evaluator",
            baseline_capability=0.30,
            assisted_capability=0.90,
            withdrawal_capability=0.75,
            delayed_capability=0.70,
            dependency_after_withdrawal=0.0,
            system_available_during_withdrawal=False,
        )
        payload.update(overrides)
        return TransferObservation(**payload)

    def test_constitutional_pass_requires_all_explicit_gates(self):
        result = evaluate_constitutional_beneficiary_flow(self.flow(), self.gates())
        self.assertEqual(result.decision, "PASS")
        self.assertEqual(result.blockers, ())
        self.assertTrue(result.apoptosis_ready)

    def test_non_compensatory_constitutional_gate_blocks(self):
        result = evaluate_constitutional_beneficiary_flow(
            self.flow(capability_left_behind=100.0, autonomy_gain=100.0),
            self.gates(safety=False),
        )
        self.assertEqual(result.decision, "HOLD")
        self.assertIn("safety_gate_failed", result.blockers)

    def test_prospective_transfer_passes_after_actual_withdrawal(self):
        criteria = self.criteria()
        receipt = evaluate_prospective_transfer(criteria, self.observation(criteria))
        self.assertEqual(receipt.decision, "PASS")
        self.assertGreaterEqual(receipt.withdrawal_retention, 0.70)
        self.assertGreaterEqual(receipt.delayed_retention, 0.60)
        self.assertGreater(receipt.delayed_gain_over_baseline, 0.0)

    def test_generator_cannot_be_its_own_evaluator(self):
        criteria = self.criteria(evaluator_id="same-actor")
        receipt = evaluate_prospective_transfer(
            criteria,
            self.observation(criteria, generator_id="same-actor", evaluator_id="same-actor"),
        )
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("generator_evaluator_not_separated", receipt.blockers)

    def test_metric_mutation_after_freeze_is_detected(self):
        frozen = self.criteria(min_delayed_retention=0.60)
        mutated = self.criteria(min_delayed_retention=0.10)
        observation = self.observation(frozen)
        receipt = evaluate_prospective_transfer(mutated, observation)
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("criteria_digest_mismatch", receipt.blockers)

    def test_system_must_really_be_withdrawn(self):
        criteria = self.criteria()
        receipt = evaluate_prospective_transfer(
            criteria,
            self.observation(criteria, system_available_during_withdrawal=True),
        )
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("system_not_withdrawn", receipt.blockers)

    def test_delayed_replay_must_beat_baseline_when_required(self):
        criteria = self.criteria()
        receipt = evaluate_prospective_transfer(
            criteria,
            self.observation(
                criteria,
                baseline_capability=0.50,
                assisted_capability=0.90,
                withdrawal_capability=0.75,
                delayed_capability=0.50,
            ),
        )
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("no_delayed_gain_over_baseline", receipt.blockers)

    def test_post_withdrawal_dependency_is_a_hard_blocker(self):
        criteria = self.criteria(max_dependency_after_withdrawal=0.0)
        receipt = evaluate_prospective_transfer(
            criteria,
            self.observation(criteria, dependency_after_withdrawal=0.2),
        )
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIn("dependency_after_withdrawal_exceeds_threshold", receipt.blockers)


if __name__ == "__main__":
    unittest.main()
