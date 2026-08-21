import unittest

from omega_capability_os_t.core import Capability
from omega_capability_os_t.cross_skill_transplant import (
    SkillContext,
    evaluate_capability_transplant,
)
from omega_generative_closure_t.reprovenance_replay import FrozenSlice


class CapabilityOSCrossSkillTransplantR01Tests(unittest.TestCase):
    def capability(self, authority="read"):
        return Capability(
            capability_id="verified-transform",
            domains=("github", "research", "document"),
            consumes=("intent", "evidence"),
            produces=("receipt", "residual"),
            authority=authority,
            quality=0.9,
            information_gain=0.9,
            verifiability=0.9,
            reuse=0.9,
            cost=0.2,
            latency=0.2,
            risk=0.1,
        )

    def contexts(self):
        return (
            SkillContext.make("github", "github", ["intent"], ["receipt"], "read"),
            SkillContext.make("research", "research", ["evidence"], ["residual"], "read"),
            SkillContext.make("document", "document", ["intent"], ["receipt"], "read"),
        )

    def common_kwargs(self):
        return dict(
            frozen_slices=(
                FrozenSlice.make("github", ["src-git"], ["bench-git"]),
                FrozenSlice.make("research", ["src-research"], ["bench-research"]),
                FrozenSlice.make("document", ["src-doc"], ["bench-doc"]),
            ),
            training_provenance_ids=("train-a",),
            runs={
                "run-a": {"git": "PASS", "research": "PASS", "doc": "PASS"},
                "run-b": {"git": "PASS", "research": "PASS", "doc": "PASS"},
            },
            historical_expected={"git": "PASS", "research": "PASS", "doc": "PASS"},
            historical_candidate={"git": "PASS", "research": "PASS", "doc": "PASS"},
            counterfactual_observations=((0.4, 0.6), (0.5, 0.7), (0.7, 0.7)),
        )

    def test_promotes_only_after_cross_skill_and_replay_courts_pass(self):
        report = evaluate_capability_transplant(
            self.capability(), self.contexts(), **self.common_kwargs()
        )
        self.assertEqual(report.decision, "PROMOTE")
        self.assertEqual(report.transfer_ratio, 1.0)
        self.assertEqual(report.blockers, ())

    def test_authority_widening_blocks_transplant(self):
        report = evaluate_capability_transplant(
            self.capability(authority="write"), self.contexts(), **self.common_kwargs()
        )
        self.assertEqual(report.decision, "HOLD")
        self.assertIn("cross_skill_transfer_below_threshold", report.blockers)
        self.assertTrue(any("authority_widening_required" in x.blockers for x in report.contexts))

    def test_missing_output_contract_blocks_transplant(self):
        contexts = self.contexts() + (
            SkillContext.make("calendar", "calendar", ["intent"], ["schedule"], "read"),
        )
        report = evaluate_capability_transplant(
            self.capability(), contexts, **self.common_kwargs()
        )
        self.assertEqual(report.decision, "HOLD")
        self.assertLess(report.transfer_ratio, 1.0)

    def test_shared_provenance_blocks_false_independence(self):
        kwargs = self.common_kwargs()
        kwargs["frozen_slices"] = (
            FrozenSlice.make("github", ["shared"], ["bench-git"]),
            FrozenSlice.make("research", ["shared"], ["bench-research"]),
        )
        report = evaluate_capability_transplant(
            self.capability(), self.contexts(), **kwargs
        )
        self.assertEqual(report.decision, "HOLD")
        self.assertIn("provenance:shared_provenance_detected", report.blockers)

    def test_cross_run_instability_blocks_promotion(self):
        kwargs = self.common_kwargs()
        kwargs["runs"] = {
            "run-a": {"git": "PASS", "research": "PASS"},
            "run-b": {"git": "HOLD", "research": "PASS"},
        }
        report = evaluate_capability_transplant(
            self.capability(), self.contexts(), **kwargs
        )
        self.assertEqual(report.decision, "HOLD")
        self.assertIn("reproducibility:cross_run_decision_instability", report.blockers)


if __name__ == "__main__":
    unittest.main()
