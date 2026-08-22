import unittest

from omega_morphogenesis import EpistemicStatus, TransformationMetrics
from omega_tristan_meta.morphogenesis import (
    CausalMemory,
    MemoryEntry,
    MetaMorphogenesisEngine,
    MorphGenome,
)


class MetaMorphogenesisTests(unittest.TestCase):
    def setUp(self):
        self.engine = MetaMorphogenesisEngine()
        self.before = MorphGenome(id="G0", purpose="baseline", operators=("OBSERVE",))
        self.after = MorphGenome(
            id="G1",
            purpose="improved",
            operators=("OBSERVE", "VERIFY"),
            evidence_contracts=("independent verification",),
            regeneration_rules=("rebuild from BOOK0",),
            parent_ids=("G0",),
        )

    def _valid_receipt(self):
        return self.engine.evaluate_transition(
            self.before,
            self.after,
            transformation="add-verification",
            generator_id="generator",
            verifier_id="verifier",
            action="write",
            authority_actions=("write",),
            input_status=EpistemicStatus.HYPOTHESIS,
            output_status=EpistemicStatus.SIMULATED,
            evidence_status=EpistemicStatus.SIMULATED,
            provenance=("fixture:meta-morphogenesis",),
            tests=("test_meta_morphogenesis",),
            evidence_refs=("E1",),
            rollback="git revert",
            metrics=TransformationMetrics(
                verified_gain=2.0,
                information_gain=0.5,
                transfer=1.0,
                regenerability=1.0,
                optionality=1.0,
                future_work_eliminated=1.0,
                complexity=0.2,
                risk=0.1,
                complexity_rent=0.5,
            ),
        )

    def test_morph_genome_digest_is_deterministic(self):
        self.assertEqual(self.after.digest(), self.after.digest())
        self.assertNotEqual(self.before.digest(), self.after.digest())

    def test_generator_cannot_judge_its_own_transition(self):
        receipt = self.engine.evaluate_transition(
            self.before,
            self.after,
            transformation="bad-self-approval",
            generator_id="same",
            verifier_id="same",
            action="write",
            authority_actions=("write",),
            input_status=EpistemicStatus.HYPOTHESIS,
            output_status=EpistemicStatus.SIMULATED,
            evidence_status=EpistemicStatus.SIMULATED,
            provenance=("fixture",),
            tests=("fixture",),
            rollback="revert",
        )
        self.assertFalse(receipt.accepted)
        self.assertTrue(any("Generator != Judge" in reason for reason in receipt.reasons))

    def test_genome_permission_does_not_grant_execution_authority(self):
        genome_claiming_write = MorphGenome(
            id="G-permission",
            purpose="declared capability only",
            permissions=("write",),
        )
        receipt = self.engine.evaluate_transition(
            self.before,
            genome_claiming_write,
            transformation="genome-does-not-authorize",
            generator_id="generator",
            verifier_id="verifier",
            action="write",
            authority_actions=(),
            input_status=EpistemicStatus.HYPOTHESIS,
            output_status=EpistemicStatus.HYPOTHESIS,
            evidence_status=EpistemicStatus.HYPOTHESIS,
            provenance=("fixture",),
            tests=("genome-authority-separation",),
            rollback="revert",
        )
        self.assertFalse(receipt.accepted)
        self.assertTrue(any("authority does not allow action" in reason for reason in receipt.reasons))

    def test_epistemic_inflation_is_rejected(self):
        receipt = self.engine.evaluate_transition(
            self.before,
            self.after,
            transformation="inflate",
            generator_id="generator",
            verifier_id="verifier",
            action="write",
            authority_actions=("write",),
            input_status=EpistemicStatus.HYPOTHESIS,
            output_status=EpistemicStatus.OBSERVED,
            evidence_status=EpistemicStatus.SIMULATED,
            provenance=("fixture",),
            tests=("fixture",),
            rollback="revert",
        )
        self.assertFalse(receipt.accepted)
        self.assertTrue(any("epistemic inflation" in reason for reason in receipt.reasons))

    def test_valid_transition_can_pay_complexity_rent(self):
        receipt = self._valid_receipt()
        self.assertTrue(receipt.accepted)
        self.assertTrue(receipt.persist)
        self.assertFalse(receipt.external_action_performed)
        self.assertFalse(receipt.auto_promoted)

    def test_crystal_requires_accepted_persistent_evidence(self):
        receipt = self._valid_receipt()
        crystal = self.engine.crystallize(
            receipt,
            name="Verified Morphogenesis",
            contract="Evaluate a proof-carrying genome transition",
            inputs=("MorphGenome",),
            outputs=("MorphogenesisReceipt",),
            dependencies=("omega_morphogenesis",),
            provenance=("PR#534",),
        )
        self.assertEqual(crystal.generator, "generator")
        self.assertEqual(crystal.evidence, ("E1",))
        self.assertTrue(crystal.digest())

    def test_m_plus_m_minus_and_unknown_are_distinct(self):
        memory = CausalMemory()
        memory.record(MemoryEntry("p", "M+", "ctx", "keep", "worked", "pass"))
        memory.record(
            MemoryEntry(
                "n",
                "M-",
                "ctx",
                "reject",
                "self-approval",
                "fail",
                generalization="Never promote when Generator == Judge",
            )
        )
        memory.record(MemoryEntry("u", "M?", "ctx", "hold", "insufficient evidence", "unknown"))
        self.assertEqual(len(memory.by_kind("M+")), 1)
        self.assertEqual(len(memory.by_kind("M-")), 1)
        self.assertEqual(len(memory.by_kind("M?")), 1)
        self.assertEqual(memory.negative_invariants(), ("Never promote when Generator == Judge",))

    def test_apoptosis_is_review_only(self):
        decision = self.engine.apoptosis_review(
            component="redundant-layer",
            marginal_verified_capability=0.0,
            maintenance=1.0,
            complexity=1.0,
            risk=0.5,
            regeneration_closure=1.0,
            preserves_evidence=True,
            preserves_provenance=True,
        )
        self.assertEqual(decision.disposition, "ELIGIBLE_FOR_REVIEW")
        self.assertFalse(decision.automatic_delete)

    def test_apoptosis_fails_closed_when_regeneration_is_incomplete(self):
        decision = self.engine.apoptosis_review(
            component="unique-evidence-layer",
            marginal_verified_capability=0.0,
            maintenance=10.0,
            complexity=10.0,
            risk=1.0,
            regeneration_closure=0.8,
            preserves_evidence=True,
            preserves_provenance=True,
        )
        self.assertEqual(decision.disposition, "KEEP")

    def test_forget_plus_only_marks_regenerate_on_demand(self):
        decision = self.engine.forget_plus_review(
            component="reconstructible-cache",
            regeneration_closure=1.0,
            preserves_evidence=True,
            preserves_provenance=True,
        )
        self.assertEqual(decision.disposition, "REGENERATE_ON_DEMAND")
        self.assertFalse(decision.automatic_delete)

    def test_evidence_invalidation_has_dependency_blast_radius(self):
        graph = {"E1": ("C1", "C2"), "C1": ("CrystalA",), "C2": ("CrystalB",)}
        radius = self.engine.evidence_blast_radius(graph, "E1")
        self.assertEqual(radius, ("C1", "C2", "CrystalA", "CrystalB"))


if __name__ == "__main__":
    unittest.main()
