import copy
import unittest
from pathlib import Path

from omega_visual.core import load_spec
from omega_visual.world import (
    ATTACHMENT_PROTOCOL,
    WorldSpecError,
    compile_sim_capsule,
    validate_executable_world,
    visual_spec_to_world,
)


ROOT = Path(__file__).parents[1]


class ExecutableWorldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.visual_spec = load_spec(ROOT / "examples/oscillator.json")
        self.world = visual_spec_to_world(self.visual_spec)

    def test_visual_spec_is_lifted_without_claim_inflation(self) -> None:
        self.assertEqual(self.world["world"]["scientific_status"], "SIMULATED")
        self.assertEqual(self.world["source"]["kind"], "VisualSpec")
        self.assertEqual(self.world["engines"][0]["execution"]["target"], "client")
        self.assertIn("no experimental calibration", self.world["known_limits"])

    def test_capsule_is_deterministic_and_web_attachable(self) -> None:
        first = compile_sim_capsule(self.world, seed=7)
        second = compile_sim_capsule(self.world, seed=7)
        self.assertEqual(first["protocol"], ATTACHMENT_PROTOCOL)
        self.assertEqual(first["world_sha256"], second["world_sha256"])
        self.assertEqual(first["run_sha256"], second["run_sha256"])
        self.assertEqual(first["capsule_id"], second["capsule_id"])
        self.assertEqual(first["attachment"]["slot"], "SimSlot")
        self.assertTrue(first["execution"]["streaming"]["state_stream"])
        self.assertFalse(first["oak"]["simulation_is_proof"])
        self.assertFalse(first["oak"]["visualization_is_truth"])

    def test_seed_changes_run_identity_not_world_identity(self) -> None:
        first = compile_sim_capsule(self.world, seed=1)
        second = compile_sim_capsule(self.world, seed=2)
        self.assertEqual(first["world_sha256"], second["world_sha256"])
        self.assertEqual(first["capsule_id"], second["capsule_id"])
        self.assertNotEqual(first["run_sha256"], second["run_sha256"])

    def test_missing_unit_is_rejected(self) -> None:
        bad = copy.deepcopy(self.world)
        bad["observables"][0]["unit"] = ""
        with self.assertRaisesRegex(WorldSpecError, "unit"):
            validate_executable_world(bad)

    def test_unknown_view_quantity_is_rejected(self) -> None:
        bad = copy.deepcopy(self.world)
        bad["views"][0]["observables"] = ["nonexistent_quantity"]
        with self.assertRaisesRegex(WorldSpecError, "unknown quantities"):
            validate_executable_world(bad)

    def test_verified_status_requires_evidence(self) -> None:
        bad = copy.deepcopy(self.world)
        bad["world"]["scientific_status"] = "VERIFIED"
        bad["evidence"] = []
        with self.assertRaisesRegex(WorldSpecError, "requires at least one evidence"):
            validate_executable_world(bad)

    def test_unquantified_uncertainty_remains_visible_as_residue(self) -> None:
        capsule = compile_sim_capsule(self.world)
        self.assertTrue(any("unquantified uncertainty" in residue for residue in capsule["oak"]["residues"]))


if __name__ == "__main__":
    unittest.main()
