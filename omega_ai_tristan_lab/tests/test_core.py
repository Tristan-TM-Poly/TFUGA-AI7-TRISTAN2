from omega_ai_tristan_lab import AgentHarness, MiniRAG, OAKEvaluator, TheoryPrototypeFactory
from omega_ai_tristan_lab.models import OAKStatus


def test_theory_factory_includes_oak_fields():
    card = TheoryPrototypeFactory().from_idea(
        "Agent IA qui transforme un PDF scientifique en LaTeX, code et rapport OAK"
    )
    assert card.name
    assert card.inputs
    assert card.outputs
    assert card.tests
    assert card.risks
    assert "PDF" in " ".join(card.inputs) or "paper" in " ".join(card.inputs).lower()


def test_oak_evaluator_is_conservative_but_actionable():
    card = TheoryPrototypeFactory().from_idea("RAG privé pour documents de recherche")
    report = OAKEvaluator().evaluate_theory(card)
    assert 0 <= report.score <= 1
    assert report.status in {OAKStatus.MODEL, OAKStatus.TESTED, OAKStatus.OAK_PASS, OAKStatus.IP_LOCK}
    assert report.next_action
    assert report.negative_memory


def test_agent_harness_runs_full_pipeline():
    report = AgentHarness().run("GitHub open-source digestion engine with license checks")
    assert report["theory_card"]
    assert report["oak_report"]
    assert report["bayes_score"]
    assert report["ip_classification"]
    assert report["revenue_paths"]
    assert all(step.done for step in report["steps"])


def test_minirag_retrieves_relevant_context():
    rag = MiniRAG()
    rag.add_text("OAK checks tests, risks, missing evidence, and negative memory.", source="oak")
    rag.add_text("Revenue mapping requires customer validation and no guaranteed income.", source="revenue")
    results = rag.search("What checks risks and missing evidence?", top_k=1)
    assert results
    chunk, score = results[0]
    assert chunk.source == "oak"
    assert score > 0
