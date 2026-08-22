import unittest

from omega_tristan_meta.skill_civilization import (
    SkillGenome,
    ablation_report,
    compile_counterfactual_plans,
    crystallize_skill_plan,
    evaluate_meta_improvement,
    generate_residual_skill_candidates,
    meta_depth_decision,
    meta_generalize,
    regeneration_closure,
    regeneration_seed,
    select_minimum_sufficient_plan,
)


def skill(
    name,
    caps,
    *,
    verified=True,
    evidence=("E1",),
    cost=1.0,
    risk=0.1,
    complexity=0.1,
    transfer=0.8,
    regenerability=0.8,
):
    return SkillGenome(
        name=name,
        capabilities=frozenset(caps),
        verified=verified,
        evidence_refs=tuple(evidence),
        cost=cost,
        risk=risk,
        complexity=complexity,
        transfer=transfer,
        regenerability=regenerability,
    )


class MetaSkillCivilizationTests(unittest.TestCase):
    def test_meta_generalization_is_candidate_not_truth(self):
        a = skill("a", {"verify", "route"}, evidence=("EA",))
        b = skill("b", {"verify", "generate"}, evidence=("EB",))
        result = meta_generalize([a, b])
        self.assertEqual(result["candidate_invariants"], ["verify"])
        self.assertEqual(result["status"], "CANDIDATE")
        self.assertIn("not a universal law", result["note"])

    def test_counterfactuals_include_no_action_reuse_compose_and_generate(self):
        a = skill("a", {"route"})
        b = skill("b", {"verify"})
        plans = compile_counterfactual_plans({"route", "verify", "regenerate"}, [a, b])
        modes = {plan.mode for plan in plans}
        self.assertTrue({"NO_ACTION", "REUSE", "COMPOSE", "GENERATE_RESIDUAL"} <= modes)

    def test_minimum_sufficient_prefers_smaller_verified_plan(self):
        all_in_one = skill("all", {"route", "verify"}, cost=1.0, risk=0.0, complexity=0.0)
        a = skill("a", {"route"}, cost=1.0)
        b = skill("b", {"verify"}, cost=1.0)
        plans = compile_counterfactual_plans({"route", "verify"}, [all_in_one, a, b])
        chosen = select_minimum_sufficient_plan(plans)
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.skills, ("all",))

    def test_unverified_skill_cannot_be_selected_as_verified_sufficient(self):
        candidate = skill("candidate", {"route", "verify"}, verified=False, evidence=())
        plans = compile_counterfactual_plans({"route", "verify"}, [candidate])
        self.assertIsNone(select_minimum_sufficient_plan(plans))

    def test_residual_generation_never_auto_promotes(self):
        a = skill("a", {"route"})
        generated = generate_residual_skill_candidates({"route", "verify"}, [a])
        self.assertEqual(len(generated), 1)
        self.assertEqual(generated[0]["capability"], "verify")
        self.assertFalse(generated[0]["auto_promote"])

    def test_ablation_identifies_redundant_skill_without_deleting(self):
        a = skill("a", {"route", "verify"}, evidence=("EA",))
        b = skill("b", {"verify"}, evidence=("EB",))
        plans = compile_counterfactual_plans({"route", "verify"}, [a, b])
        composed = next(plan for plan in plans if plan.mode == "COMPOSE" and plan.skills == ("a", "b"))
        report = ablation_report(composed, {"a": a, "b": b}, {"route", "verify"})
        self.assertEqual(report["redundant_candidates"], ["b"])
        self.assertFalse(report["automatic_deletion_authorized"])

    def test_meta_improvement_requires_independent_judge_and_pays_rent(self):
        blocked = evaluate_meta_improvement(
            generator="same",
            judge="same",
            verified_gain=1.0,
            complexity_debt=0.1,
            risk_debt=0.1,
            meta_debt=0.1,
            independent_evidence=True,
        )
        self.assertFalse(blocked.accepted)
        accepted = evaluate_meta_improvement(
            generator="g",
            judge="j",
            verified_gain=1.0,
            complexity_debt=0.1,
            risk_debt=0.1,
            meta_debt=0.1,
            independent_evidence=True,
        )
        self.assertTrue(accepted.accepted)
        self.assertFalse(accepted.auto_promoted)

    def test_meta_depth_can_stop(self):
        decision = meta_depth_decision(
            verified_gain=0.2,
            extra_complexity=0.2,
            compute_cost=0.2,
            risk=0.1,
            meta_debt=0.1,
        )
        self.assertFalse(decision["continue"])

    def test_crystal_and_regeneration_seed_are_deterministic(self):
        a = skill("a", {"route", "verify"}, evidence=("EA",), cost=1.0, risk=0.0, complexity=0.0)
        plan = select_minimum_sufficient_plan(
            compile_counterfactual_plans({"route", "verify"}, [a])
        )
        receipt1 = crystallize_skill_plan(
            name="kernel",
            plan=plan,
            skill_index={"a": a},
            generator="g",
            judge="j",
            independent_evidence=True,
            tests_passed=True,
        )
        receipt2 = crystallize_skill_plan(
            name="kernel",
            plan=plan,
            skill_index={"a": a},
            generator="g",
            judge="j",
            independent_evidence=True,
            tests_passed=True,
        )
        self.assertEqual(receipt1.status, "CANDIDATE_CRYSTAL")
        self.assertEqual(receipt1.crystal.digest, receipt2.crystal.digest)
        self.assertEqual(
            regeneration_seed(receipt1.crystal).seed_digest,
            regeneration_seed(receipt2.crystal).seed_digest,
        )

    def test_crystal_fails_closed_without_independent_evidence(self):
        a = skill("a", {"route"}, evidence=("EA",), cost=0.1, risk=0.0, complexity=0.0)
        plan = select_minimum_sufficient_plan(compile_counterfactual_plans({"route"}, [a]))
        receipt = crystallize_skill_plan(
            name="kernel",
            plan=plan,
            skill_index={"a": a},
            generator="g",
            judge="j",
            independent_evidence=False,
            tests_passed=True,
        )
        self.assertEqual(receipt.status, "HOLD")
        self.assertIsNone(receipt.crystal)

    def test_regeneration_closure_is_explicit(self):
        self.assertEqual(regeneration_closure({"a", "b"}, {"a"}), 0.5)
        self.assertEqual(regeneration_closure(set(), set()), 1.0)


if __name__ == "__main__":
    unittest.main()
