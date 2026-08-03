from __future__ import annotations

import json
from pathlib import Path

from omega_web_hg_t.r04.max_adapters import adapter_by_id, parse_crossref, parse_pmc_oai, parse_usgs
from omega_web_hg_t.r04.max_campaign import HttpResponse, run_max_campaign


def test_crossref_parser_strips_abstracts_and_authors():
    body = json.dumps({"message": {"items": [{"DOI": "10.1/x", "title": ["A title"], "URL": "https://doi.org/10.1/x", "type": "article", "abstract": "copyrighted text", "author": [{"family": "Person"}]}]}}).encode()
    records = parse_crossref(body, "receipt")
    assert len(records) == 1
    payload = records[0].to_dict()
    assert payload["title"] == "A title"
    assert "abstract" not in payload
    assert "author" not in payload


def test_pmc_oai_parser_metadata_only():
    body = b'''<?xml version="1.0"?><OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:dc="http://purl.org/dc/elements/1.1/"><ListRecords><record><header><identifier>oai:pmc:PMC1</identifier><datestamp>2026-01-01</datestamp></header><metadata><dc:dc><dc:title>Open record</dc:title><dc:identifier>https://pmc.ncbi.nlm.nih.gov/articles/PMC1/</dc:identifier><dc:rights>CC BY</dc:rights></dc:dc></metadata></record></ListRecords></OAI-PMH>'''
    records = parse_pmc_oai(body, "receipt")
    assert records[0].title == "Open record"
    assert records[0].license == "CC BY"


def test_usgs_parser():
    body = json.dumps({"features": [{"id": "us1", "properties": {"title": "M 1.0", "url": "https://example/us1", "type": "earthquake", "time": 1}}]}).encode()
    records = parse_usgs(body, "receipt")
    assert records[0].record_id == "us1"
    assert records[0].topics == ("earthquake",)


def test_key_required_adapter_is_skipped(tmp_path: Path):
    adapter = adapter_by_id("openalex")
    root = run_max_campaign(tmp_path, adapters=(adapter,), env={}, item_budget=5, page_size=5, max_pages_per_source=1, transport=lambda *args: (_ for _ in ()).throw(AssertionError("network should not run")))
    report = json.loads((root / "campaign-report.json").read_text())
    assert report["record_count"] == 0
    assert report["skipped"][0]["source_id"] == "openalex"


def test_campaign_is_deduplicated_checkpointed_and_claim_safe(tmp_path: Path):
    adapter = adapter_by_id("crossref")
    body = json.dumps({"message": {"items": [{"DOI": "10.1/x", "title": ["A"], "URL": "https://doi.org/10.1/x", "type": "article"}, {"DOI": "10.1/x", "title": ["A"], "URL": "https://doi.org/10.1/x", "type": "article"}]}}).encode()
    calls = []
    def transport(url, headers, timeout, max_bytes):
        calls.append(url)
        return HttpResponse(200, {"Content-Type": "application/json", "X-RateLimit-Remaining": "9"}, body, url)
    root = run_max_campaign(tmp_path, adapters=(adapter,), env={}, item_budget=10, page_size=10, max_pages_per_source=1, transport=transport, sleep=lambda _: None)
    report = json.loads((root / "campaign-report.json").read_text())
    assert report["record_count"] == 1
    assert report["raw_bodies_persisted"] is False
    assert report["full_text_collected"] is False
    assert report["permanent_total_cap"] is None
    assert (root / "checkpoint.json").exists()
    assert (root / "campaign.sqlite3").exists()


def test_failure_becomes_negative_memory(tmp_path: Path):
    adapter = adapter_by_id("wikimedia")
    def transport(url, headers, timeout, max_bytes):
        return HttpResponse(503, {"Retry-After": "0"}, b"unavailable", url)
    root = run_max_campaign(tmp_path, adapters=(adapter,), env={}, item_budget=5, page_size=5, max_pages_per_source=1, retries=2, transport=transport, sleep=lambda _: None)
    report = json.loads((root / "campaign-report.json").read_text())
    assert report["mminus_count"] == 1
    assert report["record_count"] == 0


def test_resume_does_not_replay_completed_adapter(tmp_path: Path):
    adapter = adapter_by_id("crossref")
    body = json.dumps({"message": {"items": [{"DOI": "10.1/x", "title": ["A"]}]}}).encode()
    calls = []
    def transport(url, headers, timeout, max_bytes):
        calls.append(url)
        return HttpResponse(200, {"Content-Type": "application/json"}, body, url)
    run_max_campaign(tmp_path, adapters=(adapter,), env={}, item_budget=10, page_size=10, max_pages_per_source=1, transport=transport, sleep=lambda _: None)
    run_max_campaign(tmp_path, adapters=(adapter,), env={}, item_budget=10, page_size=10, max_pages_per_source=1, transport=transport, sleep=lambda _: None, resume=True)
    assert len(calls) == 1
