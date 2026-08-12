from __future__ import annotations

import unittest

from omega_compute_physics_t.call_graph import build_call_graph
from omega_compute_physics_t.change_impact import propagate_change_impact
from omega_compute_physics_t.complexity_ir import compile_source_ir
from omega_compute_physics_t.confidence_debt import confidence_debt
from omega_compute_physics_t.snapshot_ledger import SnapshotDiff


class TestChangeImpact(unittest.TestCase):
    def test_propagates_to_callers_with_decay(self) -> None:
        ir = []
        ir.extend(compile_source_ir(
            """
def leaf(n):
    return n + 1

def middle(n):
    return leaf(n)

def top(n):
    return middle(n)
""",
            module="pkg/core.py",
        ))
        graph = build_call_graph(ir)
        diff = SnapshotDiff(
            repository="org/repo",
            old_commit="a" * 40,
            new_commit="b" * 40,
            added=(),
            removed=(),
            changed=("pkg/core.py",),
            unchanged=10,
        )
        report = propagate_change_impact(diff, graph, max_hops=3, decay=0.5)
        by_node = {row.node: row for row in report.impacted_nodes}
        self.assertIn("pkg/core.py:leaf", by_node)
        self.assertIn("pkg/core.py:middle", by_node)
        self.assertIn("pkg/core.py:top", by_node)
        self.assertEqual(by_node["pkg/core.py:leaf"].distance, 0)
        self.assertEqual(by_node["pkg/core.py:middle"].distance, 0)
        self.assertEqual(by_node["pkg/core.py:top"].distance, 0)

    def test_tracks_changed_files_outside_call_graph(self) -> None:
        graph = build_call_graph(compile_source_ir("def f(): return 1", module="a.py"))
        diff = SnapshotDiff(
            repository="org/repo",
            old_commit="a" * 40,
            new_commit="b" * 40,
            added=(),
            removed=(),
            changed=("config.yaml",),
            unchanged=1,
        )
        report = propagate_change_impact(diff, graph)
        self.assertEqual(report.unresolved_changed_files, ("config.yaml",))


class TestConfidenceDebt(unittest.TestCase):
    def test_old_changed_evidence_becomes_high_priority(self) -> None:
        report = confidence_debt(
            age_days=120,
            half_life_days=30,
            empirical_coverage=0.75,
            nominal_coverage=0.90,
            domain_overlap=0.6,
            code_changed=True,
            machine_changed=True,
        )
        self.assertGreaterEqual(report.debt, 0.7)
        self.assertEqual(report.priority, "critical-revalidate")

    def test_fresh_calibrated_evidence_has_low_debt(self) -> None:
        report = confidence_debt(
            age_days=0,
            empirical_coverage=0.90,
            nominal_coverage=0.90,
            domain_overlap=1.0,
        )
        self.assertAlmostEqual(report.debt, 0.0)
        self.assertEqual(report.priority, "fresh-enough")


if __name__ == "__main__":
    unittest.main()
