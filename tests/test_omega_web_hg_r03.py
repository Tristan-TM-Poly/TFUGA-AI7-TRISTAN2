from __future__ import annotations

import json
from pathlib import Path

from omega_web_hg_t.r03.compiler import audit_absorption, compile_absorption
from omega_web_hg_t.r03.extract import detect_duplicates, sentence_candidates, simhash64
from omega_web_hg_t.r03.models import ClaimCandidate
from omega_web_hg_t.r03.search import SearchIndex


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _source_run(root: Path) -> Path:
    root.mkdir(parents=True)
    pages = [
        {
            "page_id": "page_a", "requested_url": "https://example.org/a", "final_url": "https://example.org/a",
            "canonical_url": "https://example.org/a", "title": "Alpha", "language": "fr",
            "evidence_id": "evidence_a", "content_sha256": "a" * 64,
            "fetched_at": "2026-08-03T16:00:00Z", "status": 200, "content_type": "text/html", "byte_length": 100,
        },
        {
            "page_id": "page_b", "requested_url": "https://example.org/b", "final_url": "https://example.org/b",
            "canonical_url": "https://example.org/b", "title": "Beta", "language": "fr",
            "evidence_id": "evidence_b", "content_sha256": "b" * 64,
            "fetched_at": "2026-08-03T16:00:01Z", "status": 200, "content_type": "text/html", "byte_length": 100,
        },
    ]
    sections = [
        {
            "section_id": "section_a", "page_id": "page_a", "index": 0, "level": 1, "heading": "Résultat",
            "text": "Cette méthode conserve chaque preuve et relie précisément la phrase à sa section d'origine. Elle permet ensuite une recherche reproductible dans le corpus capturé.",
            "locator": "section:0",
        },
        {
            "section_id": "section_b", "page_id": "page_b", "index": 0, "level": 1, "heading": "Résultat répété",
            "text": "Cette méthode conserve chaque preuve et relie précisément la phrase à sa section d'origine.",
            "locator": "section:0",
        },
    ]
    evidence = [
        {
            "evidence_id": "evidence_a", "requested_url": "https://example.org/a", "final_url": "https://example.org/a",
            "fetched_at": "2026-08-03T16:00:00Z", "http_status": 200, "content_type": "text/html",
            "content_sha256": "a" * 64, "byte_length": 100, "headers": {}, "extractor": "fixture",
            "policy_code": "ALLOW", "raw_blob": None,
        },
        {
            "evidence_id": "evidence_b", "requested_url": "https://example.org/b", "final_url": "https://example.org/b",
            "fetched_at": "2026-08-03T16:00:01Z", "http_status": 200, "content_type": "text/html",
            "content_sha256": "b" * 64, "byte_length": 100, "headers": {}, "extractor": "fixture",
            "policy_code": "ALLOW", "raw_blob": None,
        },
    ]
    _write_jsonl(root / "pages.jsonl", pages)
    _write_jsonl(root / "sections.jsonl", sections)
    _write_jsonl(root / "evidence.jsonl", evidence)
    return root


def test_sentence_candidates_filter_and_split():
    text = "Phrase courte. Cette phrase suffisamment longue contient une proposition structurée et vérifiable dans sa source. Une autre phrase documente clairement le résultat obtenu par le système."
    candidates = sentence_candidates(text)
    assert len(candidates) == 2
    assert candidates[0].startswith("Cette phrase")


def test_simhash_and_duplicate_detection():
    base = ClaimCandidate("c1", "p1", "s1", "e1", "https://example.org/1", "x", "La méthode relie chaque phrase à une preuve précise et reproductible dans le corpus.", "1", 13)
    exact = ClaimCandidate("c2", "p2", "s2", "e2", "https://example.org/2", "y", base.text, "2", 13)
    near = ClaimCandidate("c3", "p3", "s3", "e3", "https://example.org/3", "z", "La méthode relie chaque phrase à une preuve précise et traçable dans le corpus.", "3", 13)
    assert simhash64(base.text) == simhash64(base.text)
    duplicates = detect_duplicates([base, exact, near], near_distance=12)
    assert any(item.kind == "exact" and item.member_id == "c2" for item in duplicates)
    assert any(item.kind == "near" and item.member_id == "c3" for item in duplicates)


def test_compile_absorption_search_and_audit(tmp_path: Path):
    source = _source_run(tmp_path / "source")
    output = tmp_path / "absorption"
    bundle = compile_absorption(source, output)
    assert bundle.report["status"] == "PASS_R0_3"
    assert len(bundle.claims) == 3
    assert any(item.kind == "exact" for item in bundle.duplicates)
    assert (output / "search.sqlite3").is_file()
    graph = json.loads((output / "absorption-hypergraph.json").read_text(encoding="utf-8"))
    node_ids = {item["id"] for item in graph["nodes"]}
    assert all(edge["source_id"] in node_ids and edge["target_id"] in node_ids for edge in graph["hyperedges"])
    with SearchIndex(output / "search.sqlite3") as index:
        results = index.query("preuve", kinds=("claim_candidate",))
    assert results
    assert results[0]["evidence_id"] in {"evidence_a", "evidence_b"}
    assert audit_absorption(output)["status"] == "PASS_R0_3"


def test_search_metadata_and_limit(tmp_path: Path):
    path = tmp_path / "search.sqlite3"
    with SearchIndex(path) as index:
        index.add_document(document_id="d1", kind="section", title="Test", text="hypergraphe probatoire vérifiable", url="https://example.org", locator="section:0", evidence_id="e1", metadata={"x": 1})
        index.connection.commit()
        if index.fts_enabled:
            index.connection.execute("INSERT INTO documents_fts(documents_fts) VALUES('rebuild')")
            index.connection.commit()
        results = index.query("hypergraphe", limit=1)
        assert results[0]["metadata"] == {"x": 1}
