from omega_math_proof_research_os.extractor import classify_block
from omega_math_proof_research_os.proof_isa import ProofOp, normalize_ops


def test_explicit_markers_form_reproducible_extraction_baseline():
    assert classify_block("Definition 1. A graph is ...").kind == "definition"
    assert classify_block("Theorem 2. Every ...").kind == "theorem"
    assert classify_block("Proof. Suppose ...").kind == "proof"
    assert classify_block("Counterexample. Take ...").kind == "counterexample"


def test_unmarked_prose_is_not_promoted_to_theorem_by_baseline():
    result = classify_block("This paragraph discusses a mathematical idea.")
    assert result.kind is None
    assert result.confidence == 0.0


def test_proof_isa_normalization_is_stable():
    assert normalize_ops(["assume", "rewrite", "close"]) == (
        ProofOp.ASSUME,
        ProofOp.REWRITE,
        ProofOp.CLOSE,
    )
