import unittest

from omega_value_os import (
    AutomationCandidate,
    AutomationLevel,
    AuthorityEnvelope,
    GeneratorGenome,
    ProofOfBetterReceipt,
    decide_automation,
    mutate_generator,
    proof_of_better,
    should_create_meta_layer,
)


class OmegaValueOSTest(unittest.TestCase):
    def candidate(self, action="analytics_refresh", **overrides):
        values = dict(
            action=action,
            repeatability=1.0,
            observability=1.0,
            reversibility=1.0,
            auditability=1.0,
            verified_benefit=1.0,
            downside=0.2,
            irreversibility=0.1,
            permission_sensitivity=0.1,
            compliance_risk=0.1,
            model_uncertainty=0.1,
            estimated_cost=0.0,
        )
        values.update(overrides)
        return AutomationCandidate(**values)

    def test_low_risk_observable_task_can_be_zero_touch(self):
        envelope = AuthorityEnvelope(
            allowed_actions=frozenset({"analytics_refresh"}),
            max_budget=10.0,
            max_irreversibility=0.2,
        )
        decision = decide_automation(self.candidate(), envelope)
        self.assertTrue(decision.permitted)
        self.assertEqual(decision.level, AutomationLevel.ZERO_TOUCH)

    def test_sensitive_financial_action_never_becomes_zero_touch(self):
        envelope = AuthorityEnvelope(
            allowed_actions=frozenset({"payment_send"}),
            max_budget=1000.0,
            max_irreversibility=1.0,
        )
        decision = decide_automation(
            self.candidate(action="payment_send", estimated_cost=1.0), envelope
        )
        self.assertFalse(decision.permitted)
        self.assertEqual(decision.level, AutomationLevel.HUMAN_APPROVED)
        self.assertTrue(any("sensitive" in reason for reason in decision.reasons))

    def test_explicit_approval_requirement_blocks_autonomy(self):
        envelope = AuthorityEnvelope(
            allowed_actions=frozenset({"publish_campaign"}),
            requires_human_approval=frozenset({"publish_campaign"}),
            max_irreversibility=0.5,
        )
        decision = decide_automation(
            self.candidate(action="publish_campaign"), envelope
        )
        self.assertFalse(decision.permitted)

    def test_prohibited_manipulation_is_blocked(self):
        action = "growth_fake_engagement_batch"
        envelope = AuthorityEnvelope(
            allowed_actions=frozenset({action}),
            max_irreversibility=0.5,
        )
        decision = decide_automation(self.candidate(action=action), envelope)
        self.assertFalse(decision.permitted)

    def test_proof_of_better_requires_no_regression_on_required_metrics(self):
        receipt = ProofOfBetterReceipt(
            candidate="candidate",
            baseline="baseline",
            metrics_candidate={"verified_value": 11, "trust": 9, "resilience": 11},
            metrics_baseline={"verified_value": 10, "trust": 10, "resilience": 10},
            hard_gate_passed=True,
            uncertainty=0.1,
            rollback="git revert",
        )
        passed, deltas = proof_of_better(receipt)
        self.assertFalse(passed)
        self.assertEqual(deltas["trust"], -1)

    def test_meta_layer_requires_gain_above_debt(self):
        self.assertFalse(should_create_meta_layer(0.2, 0.15, 0.1))
        self.assertTrue(should_create_meta_layer(0.4, 0.15, 0.1))

    def test_meta_generator_never_self_approves(self):
        parent = GeneratorGenome(
            name="offer-generator",
            objective="verified value",
            operators=("specialize",),
            constraints=("generator!=judge",),
        )
        child = mutate_generator(parent, "counterfactual-test")
        self.assertTrue(child.requires_independent_evaluation)
        self.assertEqual(child.child.version, parent.version + 1)


if __name__ == "__main__":
    unittest.main()
