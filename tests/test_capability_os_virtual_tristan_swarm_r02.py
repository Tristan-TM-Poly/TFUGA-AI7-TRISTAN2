import unittest

from omega_capability_os_t.core import Capability, Intent
from omega_capability_os_t.virtual_tristan import compile_virtual_tristans
from omega_capability_os_t.virtual_tristan_swarm import (
    SwarmProbeResult,
    marginal_contributions,
    minimum_sufficient_swarm,
)


class VirtualTristanMinimumSwarmR02Tests(unittest.TestCase):
    def population(self):
        registry = (
            Capability("gen", ("repo",), (), ("draft",), authority="draft"),
            Capability("falsify", ("repo",), (), ("residual",), authority="read"),
            Capability("verify", ("repo",), (), ("receipt",), authority="read"),
            Capability("extra", ("repo",), (), ("note",), authority="read"),
        )
        intent = Intent("swarm", (), (), domains=("repo",), allow_mutation=False)
        return compile_virtual_tristans(
            registry,
            intent,
            required_roles=("generator", "falsifier", "verifier", "historian"),
            role_capabilities={
                "generator": ("gen",),
                "falsifier": ("falsify",),
                "verifier": ("verify",),
                "historian": ("extra",),
            },
        )

    def results(self):
        return (
            SwarmProbeResult("vt:generator", ("r1",), ("draft",), 0.9, 1.0),
            SwarmProbeResult("vt:falsifier", ("r2",), (), 0.9, 1.0),
            SwarmProbeResult("vt:verifier", (), ("receipt",), 0.95, 1.0),
            SwarmProbeResult("vt:historian", ("r1",), (), 0.9, 0.2),
        )

    def test_selects_minimum_cardinality_swarm(self):
        report = minimum_sufficient_swarm(
            self.population(),
            self.results(),
            required_residuals=("r1", "r2"),
            required_outputs=("draft", "receipt"),
            min_evidence_score=0.8,
        )
        self.assertEqual(report.decision, "MINIMAL")
        self.assertEqual(set(report.selected_ids), {"vt:generator", "vt:falsifier", "vt:verifier"})
        self.assertEqual(report.removed_ids, ("vt:historian",))

    def test_contribution_marks_redundant_member(self):
        contributions = {x.tristan_id: x for x in marginal_contributions(self.population(), self.results())}
        self.assertEqual(contributions["vt:historian"].contribution_score, 0.0)
        self.assertGreater(contributions["vt:falsifier"].contribution_score, 0.0)

    def test_missing_probe_result_holds(self):
        report = minimum_sufficient_swarm(
            self.population(),
            self.results()[:-1],
            required_residuals=("r1", "r2"),
            required_outputs=("draft", "receipt"),
        )
        self.assertEqual(report.decision, "HOLD")
        self.assertIn("missing_member_probe_results", report.blockers)

    def test_impossible_requirements_hold(self):
        report = minimum_sufficient_swarm(
            self.population(),
            self.results(),
            required_residuals=("never-covered",),
            required_outputs=("draft",),
        )
        self.assertEqual(report.decision, "HOLD")
        self.assertIn("no_sufficient_swarm_in_supplied_population", report.blockers)

    def test_tie_uses_lower_cost_then_stable_identity(self):
        pop = self.population()
        rows = (
            SwarmProbeResult("vt:generator", ("r",), ("o",), 0.9, 2.0),
            SwarmProbeResult("vt:falsifier", ("r",), ("o",), 0.9, 1.0),
            SwarmProbeResult("vt:verifier", (), (), 0.9, 1.0),
            SwarmProbeResult("vt:historian", (), (), 0.9, 1.0),
        )
        report = minimum_sufficient_swarm(pop, rows, required_residuals=("r",), required_outputs=("o",), min_evidence_score=0.8)
        self.assertEqual(report.selected_ids, ("vt:falsifier",))

    def test_not_ready_population_fails_closed(self):
        registry = (Capability("read", ("repo",), (), ("x",), authority="read"),)
        intent = Intent("x", (), (), domains=("repo",))
        pop = compile_virtual_tristans(registry, intent, required_roles=("missing",), role_capabilities={})
        report = minimum_sufficient_swarm(pop, (), required_residuals=(), required_outputs=())
        self.assertEqual(report.decision, "HOLD")
        self.assertIn("population_not_ready", report.blockers)


if __name__ == "__main__":
    unittest.main()
