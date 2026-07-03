from pathlib import Path

from omega_ai_tristan_lab import (
    AgentHarness,
    DocumentIngestor,
    LexicalSearchBackend,
    MiniRAG,
    OAKEvaluator,
    ReportRenderer,
    TheoryPrototypeFactory,
    Workspace,
)
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


def test_v02_ingests_markdown_and_chunks(tmp_path: Path):
    path = tmp_path / "theory.md"
    path.write_text("# Theory\n\nOAK transforms ideas into tested prototypes with negative memory.", encoding="utf-8")
    ingestor = DocumentIngestor()
    doc = ingestor.ingest_path(path)
    chunks = ingestor.chunk_document(doc, chunk_size=40, overlap=5)
    assert doc.media_type == "text/markdown"
    assert "OAK transforms" in doc.text
    assert chunks
    assert chunks[0].source_path == str(path)


def test_v02_pdf_without_optional_dependency_is_oak_safe(tmp_path: Path):
    path = tmp_path / "empty.pdf"
    path.write_bytes(b"%PDF-1.4\n% placeholder")
    doc = DocumentIngestor().ingest_path(path)
    assert doc.media_type == "application/pdf"
    assert doc.warnings or doc.text


def test_v02_report_renderer_outputs_json_and_markdown():
    report = AgentHarness().run("Agent OAK-safe pour revenus et IP")
    renderer = ReportRenderer()
    json_text = renderer.to_json_text(report)
    markdown = renderer.to_markdown(report)
    assert "theory_card" in json_text
    assert "Ω-AI-TRISTAN-LAB Report" in markdown
    assert "OAK Report" in markdown


def test_v02_workspace_persists_reports(tmp_path: Path):
    workspace = Workspace(tmp_path)
    run = workspace.run_idea("Mini RAG OAK-safe pour notes de recherche")
    assert run.json_report.exists()
    assert run.markdown_report.exists()
    assert run.manifest.exists()
    assert "oak_rule" in run.manifest.read_text(encoding="utf-8")


def test_v02_workspace_ingests_documents(tmp_path: Path):
    doc_path = tmp_path / "note.md"
    doc_path.write_text("Bayes-Tristan scores truth, utility, safety, and testability.", encoding="utf-8")
    workspace = Workspace(tmp_path / "runs")
    run = workspace.run_with_documents(
        idea="Utiliser Bayes-Tristan pour décider quoi prototyper",
        document_paths=[doc_path],
        context_query="truth safety testability",
    )
    markdown = run.markdown_report.read_text(encoding="utf-8")
    assert run.json_report.exists()
    assert "Bayes-Tristan" in markdown


def test_v02_lexical_backend_contract():
    backend = LexicalSearchBackend()
    backend.add("HGFM and CVCD create compressed fertile prototypes.", source="canon")
    results = backend.search("compressed prototypes", top_k=1)
    assert results
    assert results[0].source == "canon"
