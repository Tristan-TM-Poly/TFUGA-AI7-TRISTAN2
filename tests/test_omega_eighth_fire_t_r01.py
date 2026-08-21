import unittest

from omega_capability_os_t.core import Capability
from omega_eighth_fire_t.capability_bridge import capability_to_fire_packet
from omega_eighth_fire_t.core import HARD_GATES, FireMetrics, FireProposal, GateResult, evaluate
from omega_eighth_fire_t.generator import Residual, generate_candidates
from omega_eighth_fire_t.worldstate import ActorState, WorldState


def proposal(*, pass_all=True, capture=0.1, exit_path="export", rollback="revert"):
    gates = {name: GateResult(pass_all, "fixture") for name in HARD_GATES}
    return FireProposal(
        proposal_id="8f-test",
        purpose="Increase independent capability",
        beneficiaries=("learner",),
        capability="reproduce a bounded workflow",
        method="training + benchmark + export",
        metrics=FireMetrics(
            verified_capability_gain=0.8,
            transfer=0.8,
            autonomy=0.8,
            regeneration=0.7,
            reciprocity=0.6,
            reach=0.6,
            cost=0.2,
            risk=0.1,
            complexity=0.1,
            debt=0.05,
            capture=capture,
            dependency_half_life_days=30,
            capability_half_life_days=365,
            forkability=0.8,
            local_ownership=0.8,
            future_optionality=0.8,
        ),
        gates=gates,
        provenance=("fixture",),
        falsifiers=("cannot reproduce independently",),
        exit_path=exit_path,
        rollback=rollback,
    )


class EighthFireR01Tests(unittest.TestCase):
    def test_hard_gate_failure_suppresses_score(self):
        p = proposal()
        gates = dict(p.gates)
        gates["safety"] = GateResult(False, "failed fixture")
        p = FireProposal(**{**p.__dict__, "gates": gates})
        receipt = evaluate(p)
        self.assertEqual(receipt.decision, "HOLD")
        self.assertIsNone(receipt.operational_score)
        self.assertIn("safety", receipt.failed_gates)

    def test_clean_proposal_is_eligible_and_has_n_plus_1(self):
        receipt = evaluate(proposal())
        self.assertEqual(receipt.decision, "ELIGIBLE")
        self.assertGreater(receipt.operational_score, 0)
        self.assertIn("vanishing_system_test", receipt.n_plus_1_probes)

    def test_capture_requires_review(self):
        receipt = evaluate(proposal(capture=0.9))
        self.assertEqual(receipt.decision, "REVIEW")
        self.assertIn("high_capture_risk", receipt.anti_capture_flags)

    def test_residual_generator_prefers_by_priority(self):
        candidates = generate_candidates(Residual("education", "lab gap", ("learner",), 0.9, 0.2))
        self.assertEqual(len(candidates), 5)
        self.assertGreaterEqual(candidates[0].priority, candidates[-1].priority)

    def test_worldstate_measures_distributed_capability_minus_burdens(self):
        before = WorldState({"learner": ActorState(0.2, 0.1, 0.05, 0.0)})
        after = WorldState({"learner": ActorState(0.8, 0.1, 0.05, 0.0)})
        self.assertGreater(after.delta(before), 0)

    def test_capability_bridge_does_not_upgrade_declaration_to_evidence(self):
        cap = Capability("teach", ("education",), ("need",), ("lesson",), authority="draft")
        packet = capability_to_fire_packet(cap)
        self.assertEqual(packet.evidence_status, "DECLARED_NOT_MEASURED")
        self.assertIn("not proof", packet.oak_boundary)


if __name__ == "__main__":
    unittest.main()
