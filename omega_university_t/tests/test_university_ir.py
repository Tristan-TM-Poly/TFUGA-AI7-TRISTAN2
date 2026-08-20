import unittest

from omega_university_t import CurriculumError, compile_curriculum, make_receipt


GRAPH = {
    "algebra": (),
    "calculus": ("algebra",),
    "linear_algebra": ("algebra",),
    "physics_modeling": ("calculus", "linear_algebra"),
    "simulation": ("physics_modeling",),
}


class CurriculumCompilerTests(unittest.TestCase):
    def test_compiles_prerequisites_before_target(self) -> None:
        plan = compile_curriculum(GRAPH, ["simulation"])
        self.assertEqual(
            plan.ordered,
            ("algebra", "calculus", "linear_algebra", "physics_modeling", "simulation"),
        )

    def test_verified_capability_cuts_dependency_expansion(self) -> None:
        plan = compile_curriculum(GRAPH, ["simulation"], verified=["physics_modeling"])
        self.assertEqual(plan.ordered, ("simulation",))
        self.assertEqual(plan.already_verified, ("physics_modeling",))

    def test_multiple_targets_are_deduplicated_deterministically(self) -> None:
        plan = compile_curriculum(GRAPH, ["simulation", "calculus", "simulation"])
        self.assertEqual(plan.targets, ("calculus", "simulation"))
        self.assertEqual(len(plan.ordered), len(set(plan.ordered)))

    def test_unknown_target_fails_closed(self) -> None:
        with self.assertRaises(CurriculumError):
            compile_curriculum(GRAPH, ["unknown"])

    def test_unresolved_prerequisite_fails_closed(self) -> None:
        graph = {"target": ("missing",)}
        with self.assertRaises(CurriculumError):
            compile_curriculum(graph, ["target"])

    def test_verified_external_prerequisite_is_allowed_as_explicit_input(self) -> None:
        graph = {"target": ("external_verified",)}
        plan = compile_curriculum(graph, ["target"], verified=["external_verified"])
        self.assertEqual(plan.ordered, ("target",))
        self.assertEqual(plan.already_verified, ("external_verified",))

    def test_reachable_cycle_fails_closed(self) -> None:
        graph = {"a": ("b",), "b": ("c",), "c": ("a",)}
        with self.assertRaises(CurriculumError):
            compile_curriculum(graph, ["a"])

    def test_receipt_is_stable_and_never_grants_authority(self) -> None:
        plan = compile_curriculum(GRAPH, ["simulation"], verified=["algebra"])
        left = make_receipt(plan, graph_version="fixture-v1")
        right = make_receipt(plan, graph_version="fixture-v1")
        self.assertEqual(left["sha256"], right["sha256"])
        self.assertFalse(left["boundaries"]["external_action_authorized"])
        self.assertFalse(plan.credential_awarded)
        self.assertFalse(plan.scientific_claim_proven)
        self.assertEqual(plan.authority, "PLAN_ONLY")

    def test_empty_targets_fail_closed(self) -> None:
        with self.assertRaises(CurriculumError):
            compile_curriculum(GRAPH, [])


if __name__ == "__main__":
    unittest.main()
