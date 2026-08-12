from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from omega_compute_physics_t.call_graph import build_call_graph
from omega_compute_physics_t.complexity_diff import ComplexityDiffReport, PointDelta
from omega_compute_physics_t.complexity_ir import compile_source_ir
from omega_compute_physics_t.contract_planner import plan_contract
from omega_compute_physics_t.fixture_registry import conservative_default_registry
from omega_compute_physics_t.fleet_stage_a import StageABenchmarkSeed
from omega_compute_physics_t.language_adapters import default_language_registry
from omega_compute_physics_t.regression_ledger import RegressionLedger, event_from_diff
from omega_compute_physics_t.risk_preflight import scan_source_risk
from omega_compute_physics_t.snapshot_ledger import compare_snapshots, snapshot_from_records
from omega_compute_physics_t.universal_fleet import scan_universal_fleet


class TestSnapshotLedger(unittest.TestCase):
    def test_snapshot_diff_is_content_addressed(self) -> None:
        old = snapshot_from_records("org/repo", "a" * 40, [
            {"path": "a.py", "size": 10, "sha": "blob-a"},
            {"path": "old.txt", "size": 3, "sha": "blob-old"},
        ])
        new = snapshot_from_records("org/repo", "b" * 40, [
            {"path": "a.py", "size": 11, "sha": "blob-b"},
            {"path": "new.txt", "size": 4, "sha": "blob-new"},
        ])
        diff = compare_snapshots(old, new)
        self.assertEqual(diff.changed, ("a.py",))
        self.assertEqual(diff.added, ("new.txt",))
        self.assertEqual(diff.removed, ("old.txt",))


class TestCallGraph(unittest.TestCase):
    def test_resolves_local_calls_and_recursion(self) -> None:
        rows = compile_source_ir(
            """
def a(n):
    return b(n)

def b(n):
    if n <= 0:
        return 0
    return a(n - 1)
""",
            module="m.py",
        )
        graph = build_call_graph(rows)
        pairs = {(edge.caller, edge.callee) for edge in graph.edges}
        self.assertIn(("m.py:a", "m.py:b"), pairs)
        self.assertIn(("m.py:b", "m.py:a"), pairs)
        self.assertEqual(len(graph.recursive_components), 1)
        self.assertEqual(set(graph.recursive_components[0]), {"m.py:a", "m.py:b"})


class TestFixturesAndContracts(unittest.TestCase):
    def test_planned_contract_remains_untrusted(self) -> None:
        fixture = conservative_default_registry().get("scalar-n")
        seed = StageABenchmarkSeed(
            repository="org/repo",
            module="pkg/core.py",
            function="work",
            priority_score=12.0,
            structural_scaling_candidate="O(n) loop-depth candidate",
        )
        plan = plan_contract(
            seed,
            commit_sha="c" * 40,
            fixture=fixture,
            axis_values={"n": [8, 32, 128]},
        )
        self.assertFalse(plan.contract.trusted_checkout)
        self.assertFalse(plan.contract.executable)
        self.assertIn("trusted_checkout", " ".join(plan.contract.validate()))


class TestRiskPreflight(unittest.TestCase):
    def test_detects_network_and_mutating_io(self) -> None:
        report = scan_source_risk(
            """
import requests

def f(path):
    open(path, 'w').write('x')
    return requests.get('https://example.invalid')
""",
            module="danger.py",
        )
        self.assertTrue(report.risk.network)
        self.assertTrue(report.risk.destructive_io)
        self.assertGreaterEqual(len(report.findings), 2)

    def test_clean_report_is_not_a_safety_claim(self) -> None:
        report = scan_source_risk("def add(a, b): return a + b", module="pure.py")
        self.assertFalse(any(report.risk.blocked_reasons()))
        self.assertIn("not a sandbox", report.oak_warning.lower())


class TestMultiLanguageAdapters(unittest.TestCase):
    def test_python_and_c_are_visible(self) -> None:
        registry = default_language_registry()
        py = registry.scan("def f(n):\n    for i in range(n):\n        pass\n", path="a.py")
        c = registry.scan("int f(int n){for(int i=0;i<n;i++){} return n;}", path="a.c")
        self.assertEqual(py.language, "python")
        self.assertEqual(py.confidence, "syntax-aware")
        self.assertEqual(c.language, "c")
        self.assertEqual(c.confidence, "heuristic")
        self.assertGreaterEqual(c.loop_tokens, 1)


class TestUniversalFleet(unittest.TestCase):
    def test_static_scan_multiple_languages_and_repos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            r1 = root / "r1"
            r2 = root / "r2"
            r1.mkdir()
            r2.mkdir()
            (r1 / "a.py").write_text("def a(n):\n    return n + 1\n", encoding="utf-8")
            (r1 / "b.c").write_text("int b(int n){ return n+1; }\n", encoding="utf-8")
            (r2 / "c.rs").write_text("fn c(n:i32)->i32 { n+1 }\n", encoding="utf-8")
            report = scan_universal_fleet({
                "org/r1": (r1, "1" * 40),
                "org/r2": (r2, "2" * 40),
            })
            self.assertEqual(len(report.repositories), 2)
            self.assertEqual(report.total_source_files, 3)
            self.assertEqual(report.language_counts["python"], 1)
            self.assertEqual(report.language_counts["c"], 1)
            self.assertEqual(report.language_counts["rust"], 1)
            self.assertGreaterEqual(report.total_python_functions_ir, 1)


class TestRegressionLedger(unittest.TestCase):
    def test_warning_event_requires_rebenchmark(self) -> None:
        report = ComplexityDiffReport(
            target="wall_time_s",
            direction="lower-is-better",
            n_points=2,
            mean_relative_change=0.15,
            median_relative_change=0.15,
            max_relative_increase=0.25,
            max_relative_decrease=0.0,
            regression_fraction=0.5,
            improvement_fraction=0.0,
            neutral_fraction=0.5,
            domain_overlap={"n": 1.0},
            elasticity_delta=None,
            crossover_candidates=(),
            point_deltas=(
                PointDelta({"n": 1.0}, 1.0, 1.25, 0.25, 0.25, "regression"),
                PointDelta({"n": 2.0}, 2.0, 2.1, 0.1, 0.05, "neutral"),
            ),
        )
        event = event_from_diff(
            report,
            repository="org/repo",
            old_commit="a" * 40,
            new_commit="b" * 40,
        )
        self.assertEqual(event.severity, "warning")
        self.assertTrue(event.requires_rebenchmark)
        ledger = RegressionLedger()
        ledger.append(event)
        self.assertEqual(len(ledger.by_severity("warning")), 1)


if __name__ == "__main__":
    unittest.main()
