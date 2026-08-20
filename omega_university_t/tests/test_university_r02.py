import unittest

from omega_university_t.curriculum_court import (
    CurriculumOption,
    compare_curriculum_options,
)
from omega_university_t.evidence_ir import (
    EvidenceError,
    EvidencePolicy,
    EvidenceRecord,
    assess_capability,
    make_evidence_receipt,
)
from omega_university_t.frontier_ir import FrontierItem, map_frontier


GRAPH = {
    "algebra": (),
    "calculus": ("algebra",),
    "linear_algebra": ("algebra",),
    "physics_modeling": ("calculus", "linear_algebra"),
    "simulation": ("physics_modeling",),
}


class EvidenceCourtTests(unittest.TestCase):
    def test_policy_sufficiency_requires_all_constraints(self) -> None:
        policy = EvidencePolicy(
            min_records=2,
            min_distinct_methods=2,
            min_independent_sources=1,
            min_reality_level=2,
        )
        rows = [
            EvidenceRecord("simulation", "e1", "artifact", "self", reality_level=1),
            EvidenceRecord(
                "simulation", "e2", "replication", "lab-b", reality_level=2, independent=True
            ),
        ]
        assessment = assess_capability(rows, policy)
        self.assertTrue(assessment.evidence_sufficient)
        self.assertEqual(assessment.decision, "EVIDENCE_SUFFICIENT_UNDER_POLICY")
        self.assertFalse(assessment.credential_awarded)
        self.assertFalse(assessment.scientific_claim_proven)
        self.assertFalse(assessment.external_action_authorized)

    def test_invalid_evidence_does_not_count(self) -> None:
        policy = EvidencePolicy(min_records=2)
        rows = [
            EvidenceRecord("simulation", "e1", "artifact", "self"),
            EvidenceRecord("simulation", "e2", "artifact", "self", valid=False),
        ]
        assessment = assess_capability(rows, policy)
        self.assertEqual(assessment.decision, "INSUFFICIENT_EVIDENCE")
        self.assertIn("records<2", assessment.unmet_requirements)

    def test_duplicate_evidence_ids_fail_closed(self) -> None:
        rows = [
            EvidenceRecord("simulation", "dup", "artifact", "a"),
            EvidenceRecord("simulation", "dup", "replication", "b"),
        ]
        with self.assertRaises(EvidenceError):
            assess_capability(rows, EvidencePolicy())

    def test_mixed_capabilities_fail_closed(self) -> None:
        rows = [
            EvidenceRecord("simulation", "e1", "artifact", "a"),
            EvidenceRecord("calculus", "e2", "artifact", "b"),
        ]
        with self.assertRaises(EvidenceError):
            assess_capability(rows, EvidencePolicy())

    def test_independence_counts_distinct_sources_not_records(self) -> None:
        policy = EvidencePolicy(min_records=2, min_independent_sources=2)
        rows = [
            EvidenceRecord("simulation", "e1", "replication", "lab", independent=True),
            EvidenceRecord("simulation", "e2", "measurement", "lab", independent=True),
        ]
        assessment = assess_capability(rows, policy)
        self.assertEqual(assessment.decision, "INSUFFICIENT_EVIDENCE")
        self.assertIn("independent_sources<2", assessment.unmet_requirements)

    def test_evidence_receipt_is_stable_and_non_authorizing(self) -> None:
        assessment = assess_capability(
            [EvidenceRecord("simulation", "e1", "artifact", "self")],
            EvidencePolicy(),
        )
        left = make_evidence_receipt(assessment, policy_version="p1")
        right = make_evidence_receipt(assessment, policy_version="p1")
        self.assertEqual(left["sha256"], right["sha256"])
        self.assertFalse(left["boundaries"]["external_action_authorized"])
        self.assertFalse(left["boundaries"]["policy_sufficiency_is_external_truth"])


class CurriculumCourtTests(unittest.TestCase):
    def test_none_is_always_present(self) -> None:
        rows = compare_curriculum_options(GRAPH, ["simulation"])
        self.assertEqual({row.option for row in rows}, {"NONE"})

    def test_declared_verified_option_can_reduce_structural_plan(self) -> None:
        rows = compare_curriculum_options(
            GRAPH,
            ["simulation"],
            options=[CurriculumOption("REUSE_MODELING", ("physics_modeling",), 1.0)],
        )
        by_name = {row.option: row for row in rows}
        self.assertLess(
            by_name["REUSE_MODELING"].missing_count,
            by_name["NONE"].missing_count,
        )
        self.assertFalse(by_name["REUSE_MODELING"].external_action_authorized)

    def test_none_wins_when_option_changes_nothing_and_costs_more(self) -> None:
        rows = compare_curriculum_options(
            GRAPH,
            ["simulation"],
            options=[CurriculumOption("NO_GAIN", (), 5.0)],
        )
        selected = [row.option for row in rows if row.selected]
        self.assertEqual(selected, ["NONE"])

    def test_reserved_none_name_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CurriculumOption("NONE")

    def test_duplicate_option_names_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            compare_curriculum_options(
                GRAPH,
                ["simulation"],
                options=[CurriculumOption("X"), CurriculumOption("X")],
            )


class FrontierBridgeTests(unittest.TestCase):
    def test_reachable_means_only_declared_requirements_present(self) -> None:
        rows = map_frontier(
            [FrontierItem("f1", ("simulation", "physics_modeling"))],
            ["simulation", "physics_modeling"],
        )
        self.assertTrue(rows[0].reachable_under_declared_capabilities)
        self.assertFalse(rows[0].research_success_claimed)
        self.assertFalse(rows[0].scientific_novelty_claimed)
        self.assertFalse(rows[0].external_action_authorized)

    def test_frontier_distance_is_missing_capability_count(self) -> None:
        rows = map_frontier(
            [
                FrontierItem("far", ("a", "b", "c")),
                FrontierItem("near", ("a", "b")),
            ],
            ["a"],
        )
        self.assertEqual([row.frontier_id for row in rows], ["near", "far"])
        self.assertEqual(rows[0].distance, 1)
        self.assertEqual(rows[1].distance, 2)

    def test_duplicate_frontier_ids_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            map_frontier(
                [FrontierItem("x", ("a",)), FrontierItem("x", ("b",))],
                [],
            )

    def test_frontier_item_requires_capability(self) -> None:
        with self.assertRaises(ValueError):
            FrontierItem("empty", ())


if __name__ == "__main__":
    unittest.main()
