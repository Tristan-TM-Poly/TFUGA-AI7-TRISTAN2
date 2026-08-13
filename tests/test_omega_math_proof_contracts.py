from omega_math_proof_research_os.contracts import MathArtifact, ProofGenome, SourceAnchor


def test_math_artifact_preserves_formal_and_oak_boundaries():
    artifact = MathArtifact(
        artifact_id="example.theorem",
        kind="theorem",
        natural_text="If n is even, n^2 is even.",
        normalized_statement="forall n in Z, even(n) -> even(n^2)",
        formal_statement="candidate-only",
        proof_genome=ProofGenome(operators=("INTRO", "REWRITE")),
        source_anchors=(SourceAnchor(source_id="book:p1", source_url="https://example.invalid/book"),),
        formal_status="candidate",
        oak_status="hold",
    )
    assert not artifact.is_formally_verified()
    assert not artifact.is_oak_verified()


def test_kernel_acceptance_does_not_imply_oak_verification():
    artifact = MathArtifact(
        artifact_id="example.formal",
        kind="theorem",
        natural_text="Source wording",
        formal_statement="formalized statement",
        formal_status="kernel_accepted",
        oak_status="hold",
    )
    assert artifact.is_formally_verified()
    assert not artifact.is_oak_verified()


def test_source_anchor_defaults_to_unknown_license():
    anchor = SourceAnchor(source_id="source", source_url="https://example.invalid")
    assert anchor.license_status == "unknown"
