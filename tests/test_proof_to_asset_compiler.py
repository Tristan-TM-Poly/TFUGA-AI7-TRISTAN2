from tools.proof_to_asset_compiler import compile_proof_to_asset


def test_compiler_creates_review_paths():
    plan = compile_proof_to_asset("Research Factory", slug="research_factory")
    assert plan.technical_note == "docs/technical_notes/research_factory.md"
    assert plan.demo == "examples/research_factory_demo.md"
    assert plan.benchmark == "benchmarks/research_factory_benchmark.md"
    assert plan.review_packet == "docs/review_packets/research_factory_review.md"


def test_ready_for_review_changes_next_action():
    plan = compile_proof_to_asset("Result", slug="result", ready_for_public_review=True)
    assert "reviewed" in plan.safe_next_action
