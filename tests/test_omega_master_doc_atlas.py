import tempfile
import unittest
from pathlib import Path
from omega_latex_t.master_doc_atlas import build_atlas, load_registry, write_bundle

class MasterAtlasTests(unittest.TestCase):
    def setUp(self):
        self.registry = Path("docs/generated/omega_master_doc_atlas/source-registry.json")

    def test_build_preserves_boundaries(self):
        atlas=build_atlas(load_registry(self.registry))
        self.assertEqual(atlas["repository_count"],6)
        self.assertIn("REPOSITORY_OVERLAP != SUPERSESSION",atlas["oak_boundaries"])
        self.assertIn("REVIEW_BINDING_VOLUME != EVIDENCE_STRENGTH",atlas["oak_boundaries"])
        self.assertEqual(atlas["totals"]["module_observations"],5206)
        self.assertEqual(atlas["totals"]["public_symbol_observations"],26262)
        self.assertEqual(atlas["totals"]["claim_candidates"],33)
        self.assertEqual(atlas["totals"]["cross_repository_identical_module_hash_groups"],5)

    def test_review_links_are_not_promoted(self):
        atlas=build_atlas(load_registry(self.registry))
        self.assertEqual(atlas["totals"]["review_only_claim_evidence_bindings"],54318)
        self.assertNotIn("supported_claims",atlas["totals"])

    def test_bundle_is_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            aa=write_bundle(self.registry,Path(a)); bb=write_bundle(self.registry,Path(b))
            self.assertEqual(aa["atlas_fingerprint"],bb["atlas_fingerprint"])
            self.assertEqual((Path(a)/"MANIFEST.json").read_bytes(),(Path(b)/"MANIFEST.json").read_bytes())

    def test_source_artifact_digests_are_retained(self):
        atlas=build_atlas(load_registry(self.registry))
        self.assertTrue(all(len(x["artifact_sha256"])==64 for x in atlas["source_snapshots"]))

if __name__ == "__main__": unittest.main()
