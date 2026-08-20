import unittest

from omega_university_t import (
    FrozenAssessment,
    LearningObservation,
    LearningRealityError,
    PrerequisiteAblationCase,
    PrerequisiteAblationError,
    evaluate_ood_probe,
    evaluate_prerequisite_ablation,
    make_learning_receipt,
    measure_learning_gain,
)


class LearningRealityTests(unittest.TestCase):
    def make_assessment(self, **overrides):
        data = {
            "assessment_id": "em-transfer-v1",
            "capability_id": "electromagnetism-modeling",
            "item_ids": ("q1", "q2", "q3"),
            "context": "novel-boundary-condition",
            "version": "1.0.0",
            "holdout": True,
            "generator_exposed": False,
        }
        data.update(overrides)
        return FrozenAssessment(**data)

    def test_frozen_assessment_digest_is_deterministic(self):
        self.assertEqual(self.make_assessment().digest(), self.make_assessment().digest())

    def test_frozen_assessment_digest_changes_when_manifest_changes(self):
        left = self.make_assessment()
        right = self.make_assessment(generator_exposed=True)
        self.assertNotEqual(left.digest(), right.digest())

    def test_duplicate_assessment_items_fail_closed(self):
        with self.assertRaises(LearningRealityError):
            self.make_assessment(item_ids=("q1", "q1"))

    def test_learning_gain_is_observed_only(self):
        assessment = self.make_assessment()
        observation = LearningObservation(
            observation_id="obs-1",
            intervention_id="module-maxwell-1",
            capability_id=assessment.capability_id,
            assessment_digest=assessment.digest(),
            pre_score=0.4,
            post_score=0.7,
            context=assessment.context,
        )
        result = measure_learning_gain(observation, assessment)
        self.assertAlmostEqual(result.observed_delta, 0.3)
        self.assertEqual(result.status, "OBSERVED_GAIN_ONLY")
        self.assertFalse(result.causal_claim_proven)
        self.assertFalse(result.credential_awarded)
        self.assertFalse(result.external_action_authorized)

    def test_learning_observation_must_bind_exact_frozen_manifest(self):
        assessment = self.make_assessment()
        observation = LearningObservation(
            observation_id="obs-2",
            intervention_id="module-maxwell-1",
            capability_id=assessment.capability_id,
            assessment_digest="wrong-digest",
            pre_score=0.2,
            post_score=0.8,
            context=assessment.context,
        )
        with self.assertRaises(LearningRealityError):
            measure_learning_gain(observation, assessment)

    def test_causal_review_requires_all_structural_gates(self):
        assessment = self.make_assessment()
        observation = LearningObservation(
            observation_id="obs-3",
            intervention_id="module-maxwell-1",
            capability_id=assessment.capability_id,
            assessment_digest=assessment.digest(),
            pre_score=0.3,
            post_score=0.8,
            context=assessment.context,
            randomized_assignment=True,
            concurrent_control=True,
            independent_evaluator=True,
        )
        result = measure_learning_gain(observation, assessment)
        self.assertTrue(result.causal_review_eligible)
        self.assertFalse(result.causal_claim_proven)

    def test_generator_exposure_blocks_causal_review_gate(self):
        assessment = self.make_assessment(generator_exposed=True)
        observation = LearningObservation(
            observation_id="obs-4",
            intervention_id="module-maxwell-1",
            capability_id=assessment.capability_id,
            assessment_digest=assessment.digest(),
            pre_score=0.3,
            post_score=0.8,
            context=assessment.context,
            randomized_assignment=True,
            concurrent_control=True,
            independent_evaluator=True,
        )
        self.assertFalse(measure_learning_gain(observation, assessment).causal_review_eligible)

    def test_ood_probe_separates_structural_ood_from_holdout_validity(self):
        assessment = self.make_assessment()
        result = evaluate_ood_probe(
            train_context="standard-boundary-condition",
            assessment=assessment,
            score=0.75,
            baseline_score=0.5,
        )
        self.assertTrue(result.structurally_ood)
        self.assertTrue(result.valid_holdout)
        self.assertAlmostEqual(result.observed_delta_over_baseline, 0.25)
        self.assertFalse(result.transfer_claim_proven)
        self.assertFalse(result.external_action_authorized)

    def test_same_context_is_not_structurally_ood(self):
        assessment = self.make_assessment()
        result = evaluate_ood_probe(
            train_context=assessment.context,
            assessment=assessment,
            score=0.6,
        )
        self.assertFalse(result.structurally_ood)

    def test_learning_receipt_is_stable_and_non_authorizing(self):
        assessment = self.make_assessment()
        observation = LearningObservation(
            observation_id="obs-5",
            intervention_id="module-maxwell-1",
            capability_id=assessment.capability_id,
            assessment_digest=assessment.digest(),
            pre_score=0.1,
            post_score=0.4,
            context=assessment.context,
        )
        result = measure_learning_gain(observation, assessment)
        left = make_learning_receipt(result, assessment)
        right = make_learning_receipt(result, assessment)
        self.assertEqual(left["sha256"], right["sha256"])
        self.assertFalse(left["boundaries"]["observed_gain_is_causal_proof"])
        self.assertFalse(left["boundaries"]["external_action_authorized"])


class PrerequisiteAblationTests(unittest.TestCase):
    def make_case(self, **overrides):
        data = {
            "case_id": "abl-1",
            "prerequisite_id": "vector-calculus",
            "target_id": "maxwell-modeling",
            "retained_scores": (0.78, 0.82, 0.80),
            "ablated_scores": (0.79, 0.81, 0.80),
            "assessment_digest": "frozen-digest-1",
            "same_frozen_assessment": True,
            "comparable_sampling": True,
            "randomized_assignment": True,
            "independent_evaluator": True,
        }
        data.update(overrides)
        return PrerequisiteAblationCase(**data)

    def test_candidate_redundant_does_not_prove_redundancy(self):
        result = evaluate_prerequisite_ablation(self.make_case())
        self.assertEqual(result.status, "CANDIDATE_REDUNDANT_UNDER_FIXTURE")
        self.assertTrue(result.causal_review_eligible)
        self.assertFalse(result.prerequisite_redundancy_proven)
        self.assertFalse(result.prerequisite_removal_authorized)

    def test_observed_drop_blocks_candidate_redundancy(self):
        case = self.make_case(ablated_scores=(0.50, 0.55, 0.52))
        result = evaluate_prerequisite_ablation(case, tolerance=0.02)
        self.assertEqual(result.status, "OBSERVED_PERFORMANCE_DROP")
        self.assertLess(result.observed_delta, -0.02)

    def test_incomparable_fixture_fails_closed(self):
        case = self.make_case(same_frozen_assessment=False)
        result = evaluate_prerequisite_ablation(case)
        self.assertEqual(result.status, "INCOMPARABLE_FIXTURE")
        self.assertFalse(result.causal_review_eligible)
        self.assertFalse(result.prerequisite_removal_authorized)

    def test_non_randomized_fixture_is_not_causal_review_eligible(self):
        case = self.make_case(randomized_assignment=False)
        result = evaluate_prerequisite_ablation(case)
        self.assertFalse(result.causal_review_eligible)

    def test_invalid_ablation_scores_fail_closed(self):
        with self.assertRaises(PrerequisiteAblationError):
            self.make_case(ablated_scores=(1.2,))

    def test_negative_tolerance_fails_closed(self):
        with self.assertRaises(PrerequisiteAblationError):
            evaluate_prerequisite_ablation(self.make_case(), tolerance=-0.1)


if __name__ == "__main__":
    unittest.main()
