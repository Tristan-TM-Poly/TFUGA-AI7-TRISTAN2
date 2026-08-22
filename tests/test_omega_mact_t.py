import unittest

from omega_mact_t import Decision, EpistemicType, EvidenceRef, MactCompiler, MemoryDecision, MemoryObject, ResourceVector, TransformationCandidate, VerificationContract, classify_memory, meta_stop_gate, pareto_front
from omega_mact_t.benchmark import run_benchmark


def evidence(scope="demo", independent=True):
    return [EvidenceRef("e1", EpistemicType.MEASURED, scope, independent)]


class MactTests(unittest.TestCase):
    def setUp(self):
        self.contract = VerificationContract(required_scope="demo", max_risk=1.0, max_irreversibility=1.0)

    def core_candidates(self):
        return [TransformationCandidate("none", "NO_ACTION", "same", ResourceVector(), evidence=evidence()), TransformationCandidate("wait", "WAIT", "same-later", ResourceVector(time=0.1), evidence=evidence()), TransformationCandidate("reuse", "REUSE", "same", ResourceVector(compute=0.2), evidence=evidence(), rollback="drop cache")]

    def test_pareto_dominance(self):
        a = TransformationCandidate("a", "NO_ACTION", "same", ResourceVector(compute=1))
        b = TransformationCandidate("b", "WAIT", "same", ResourceVector(compute=2))
        self.assertEqual([x.id for x in pareto_front([a, b])], ["a"])

    def test_anti_candidates_are_mandatory(self):
        with self.assertRaises(ValueError):
            MactCompiler().evaluate([TransformationCandidate("x", "COMPUTE", "x", ResourceVector())], self.contract)

    def test_selects_no_action_when_sufficient(self):
        selected = MactCompiler().select(self.core_candidates(), self.contract)
        self.assertIsNotNone(selected)
        self.assertEqual(selected.operation, "NO_ACTION")

    def test_no_action_rejected_when_target_not_met(self):
        contract = VerificationContract(required_scope="demo", required_semantic_effect="result")
        candidates = [TransformationCandidate("none", "NO_ACTION", "unchanged", ResourceVector(), evidence=evidence()), TransformationCandidate("wait", "WAIT", "unchanged", ResourceVector(time=.1), evidence=evidence()), TransformationCandidate("reuse", "REUSE", "result", ResourceVector(compute=.1), evidence=evidence(), rollback="drop cache")]
        selected = MactCompiler().select(candidates, contract)
        self.assertIsNotNone(selected)
        self.assertEqual(selected.id, "reuse")

    def test_external_action_without_authority_is_hold(self):
        candidates = self.core_candidates() + [TransformationCandidate("act", "ACT", "external-change", ResourceVector(action=0.1, irreversibility=0.2), evidence=evidence(), authority_granted=False, rollback="undo")]
        act_eval = next(x for x in MactCompiler().evaluate(candidates, self.contract) if x.candidate_id == "act")
        self.assertEqual(act_eval.decision, Decision.HOLD)

    def test_generator_cannot_judge(self):
        candidates = self.core_candidates() + [TransformationCandidate("bad", "COMPUTE", "same", ResourceVector(compute=0.01), evidence=evidence(), generator_role="same", judge_role="same", rollback="discard")]
        evaluation = next(x for x in MactCompiler().evaluate(candidates, self.contract) if x.candidate_id == "bad")
        self.assertEqual(evaluation.decision, Decision.REJECT)

    def test_independent_evidence_is_required(self):
        bad_ev = evidence(independent=False)
        candidates = [TransformationCandidate("none", "NO_ACTION", "same", ResourceVector(), evidence=bad_ev), TransformationCandidate("wait", "WAIT", "later", ResourceVector(time=.1), evidence=bad_ev), TransformationCandidate("reuse", "REUSE", "same", ResourceVector(compute=.1), evidence=bad_ev, rollback="discard")]
        self.assertTrue(all(x.decision == Decision.HOLD for x in MactCompiler().evaluate(candidates, self.contract)))

    def test_ineligible_candidate_cannot_pareto_dominate_valid_candidate(self):
        candidates = self.core_candidates() + [TransformationCandidate("unauthorized", "ACT", "external", ResourceVector(), evidence=evidence(), authority_granted=False)]
        selected = MactCompiler().select(candidates, self.contract)
        self.assertIsNotNone(selected)
        self.assertEqual(selected.operation, "NO_ACTION")

    def test_meta_stop_requires_net_positive_savings(self):
        self.assertFalse(meta_stop_gate(1.0, 1.0).passed)
        self.assertFalse(meta_stop_gate(2.0, 1.0, complexity_debt=1.1).passed)
        self.assertTrue(meta_stop_gate(3.0, 1.0, complexity_debt=0.5, risk_debt=0.5).passed)

    def test_oakbench_mact_toy_cases(self):
        results = run_benchmark()
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.passed for r in results))

    def test_memory_keeps_provenance(self):
        self.assertEqual(classify_memory(MemoryObject("m", 100, 1, reconstructible=True, regeneration_verified=True, provenance_critical=True)).decision, MemoryDecision.KEEP)

    def test_memory_regenerates_when_cheaper(self):
        self.assertEqual(classify_memory(MemoryObject("m", 10, 1, reconstructible=True, regeneration_verified=True)).decision, MemoryDecision.REGENERATE_ON_DEMAND)

    def test_unverified_deletion_is_held(self):
        self.assertEqual(classify_memory(MemoryObject("m", 10, 1, reconstructible=False, regeneration_verified=False)).decision, MemoryDecision.HOLD_DELETE)

    def test_receipt_never_claims_execution_or_auto_promotion(self):
        compiler = MactCompiler()
        candidates = self.core_candidates()
        evaluations = compiler.evaluate(candidates, self.contract)
        selected = compiler.select(candidates, self.contract)
        ev = next(e for e in evaluations if e.candidate_id == selected.id)
        receipt = compiler.receipt(selected, ev, "before", "after", "unit-test")
        self.assertFalse(receipt.external_action_performed)
        self.assertFalse(receipt.auto_promoted)


if __name__ == "__main__":
    unittest.main()
