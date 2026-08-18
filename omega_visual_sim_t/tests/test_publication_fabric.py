import unittest

from omega_visual.publication import (
    PUBLICATION_PROTOCOL,
    PublicationSpecError,
    compile_publication_bundle,
    validate_publication_bundle,
)
from omega_visual.world import compile_sim_capsule, visual_spec_to_world


VISUAL_SPEC = {
    "model": {
        "type": "damped_harmonic_oscillator",
        "units": {
            "mass": "kg",
            "stiffness": "N/m",
            "damping": "N*s/m",
            "displacement": "m",
        },
        "parameters": {
            "mass_kg": 1.0,
            "stiffness_n_m": 4.0,
            "damping_n_s_m": 0.5,
            "initial_displacement_m": 1.0,
            "initial_velocity_m_s": 0.0,
        },
    },
    "visual": {"title": "Publication fabric oscillator"},
}


def capsule():
    return compile_sim_capsule(visual_spec_to_world(VISUAL_SPEC), seed=7)


class PublicationFabricTests(unittest.TestCase):
    def test_compiles_three_surface_bundle_without_status_inflation(self):
        source = capsule()
        bundle = compile_publication_bundle(
            source,
            title="Executable oscillator",
            summary="A proof-carrying publication candidate derived from one SimCapsule.",
            claim_ids=["claim:oscillator-dynamics"],
            evidence_refs=["github:example/reference"],
            website_path="/lab/oscillator",
            github_repo="Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
            youtube_channels=["Tristan Science"],
        )
        self.assertEqual(bundle["protocol"], PUBLICATION_PROTOCOL)
        self.assertEqual(bundle["oak"]["scientific_status"], source["oak"]["scientific_status"])
        self.assertFalse(bundle["oak"]["popularity_is_evidence"])
        self.assertEqual(bundle["surfaces"]["youtube"]["mode"], "draft_export_only")
        self.assertFalse(bundle["surfaces"]["youtube"]["publication_authorized"])
        self.assertTrue(bundle["surfaces"]["web"]["enabled"])
        self.assertTrue(bundle["surfaces"]["github"]["enabled"])

    def test_explicit_authority_only_creates_publish_candidate(self):
        bundle = compile_publication_bundle(
            capsule(),
            title="Authorized candidate",
            summary="Still not proof and still not evidence merely because publication was authorized.",
            youtube_channels=["Owned Channel"],
            rights_mode="owned",
            publication_authorized=True,
        )
        self.assertEqual(bundle["surfaces"]["youtube"]["mode"], "publish_candidate")
        self.assertFalse(bundle["oak"]["publication_is_validation"])
        self.assertFalse(bundle["oak"]["simulation_is_proof"])

    def test_authority_without_channel_fails_closed(self):
        with self.assertRaises(PublicationSpecError):
            compile_publication_bundle(
                capsule(),
                title="No channel",
                summary="Explicit authority has no target and must fail closed.",
                publication_authorized=True,
            )

    def test_wrong_capsule_protocol_is_rejected(self):
        bad = capsule()
        bad["protocol"] = "OTHER/9.9"
        with self.assertRaises(PublicationSpecError):
            compile_publication_bundle(
                bad,
                title="Bad source",
                summary="The compiler must reject an incompatible attachment protocol.",
            )

    def test_validator_rejects_epistemic_promotion(self):
        bundle = compile_publication_bundle(
            capsule(),
            title="No promotion",
            summary="Publishing cannot upgrade SIMULATED to VERIFIED.",
        )
        bundle["oak"]["scientific_status"] = "VERIFIED"
        with self.assertRaises(PublicationSpecError):
            validate_publication_bundle(bundle)

    def test_bundle_hash_is_deterministic(self):
        kwargs = dict(
            title="Deterministic bundle",
            summary="Equivalent inputs produce an equivalent publication identity.",
            website_path="/lab/demo",
            rights_mode="semantic_original",
        )
        first = compile_publication_bundle(capsule(), **kwargs)
        second = compile_publication_bundle(capsule(), **kwargs)
        self.assertEqual(first["bundle_sha256"], second["bundle_sha256"])
        self.assertEqual(first["bundle_id"], second["bundle_id"])


if __name__ == "__main__":
    unittest.main()
