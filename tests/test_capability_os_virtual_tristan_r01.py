import unittest

from omega_capability_os_t.core import Capability, Intent
from omega_capability_os_t.virtual_tristan import (
    apoptosis_candidates,
    compile_virtual_tristans,
    separation_gate,
)


class VirtualTristanR01Tests(unittest.TestCase):
    def registry(self):
        return (
            Capability("scan", ("repo",), ("repo",), ("residuals",), authority="read"),
            Capability("design", ("repo",), ("residuals",), ("plan",), authority="draft"),
            Capability("patch", ("repo",), ("plan",), ("candidate",), authority="write"),
            Capability("verify", ("repo",), ("candidate",), ("evidence",), authority="read"),
        )

    def test_compiles_minimal_role_population_under_authority(self):
        intent = Intent("x", ("repo",), ("evidence",), ("repo",), allow_mutation=False)
        population = compile_virtual_tristans(
            self.registry(), intent,
            required_roles=("mycelium", "oak"),
            role_capabilities={"mycelium": ("scan",), "oak": ("verify",)},
        )
        self.assertEqual(population.decision, "READY")
        self.assertEqual(tuple(x.role for x in population.members), ("mycelium", "oak"))

    def test_write_capability_does_not_gain_authority_implicitly(self):
        intent = Intent("x", ("repo",), ("candidate",), ("repo",), allow_mutation=False)
        population = compile_virtual_tristans(
            self.registry(), intent,
            required_roles=("engineer",),
            role_capabilities={"engineer": ("patch",)},
        )
        self.assertEqual(population.decision, "HOLD")
        self.assertIn("engineer", population.unresolved_roles)

    def test_population_budget_fails_closed(self):
        intent = Intent("x", ("repo",), ("evidence",), ("repo",))
        population = compile_virtual_tristans(
            self.registry(), intent,
            required_roles=("mycelium", "oak"),
            role_capabilities={"mycelium": ("scan",), "oak": ("verify",)},
            max_population=1,
        )
        self.assertEqual(population.decision, "HOLD")
        self.assertIn("population_budget_exceeded", population.blockers)

    def test_generator_falsifier_verifier_promotion_must_be_distinct(self):
        self.assertEqual(
            separation_gate(
                generator_id="g", falsifier_id="f", verifier_id="v", promotion_authority_id="p"
            )["decision"],
            "PASS",
        )
        report = separation_gate(
            generator_id="g", falsifier_id="g", verifier_id="v", promotion_authority_id="p"
        )
        self.assertEqual(report["decision"], "HOLD")
        self.assertIn("role_authority_collapse", report["blockers"])

    def test_apoptosis_is_measured_not_popularity_based(self):
        self.assertEqual(apoptosis_candidates({"vt:a": 0.0, "vt:b": 0.2, "vt:c": -0.1}), ("vt:a", "vt:c"))


if __name__ == "__main__":
    unittest.main()
