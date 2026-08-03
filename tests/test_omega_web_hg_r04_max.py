from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_web_hg_t.r04.max_adapters import (
    MAX_ADAPTERS,
    adapter_by_id,
    parse_crossref,
    parse_pmc_oai,
    parse_usgs,
)
from omega_web_hg_t.r04.max_campaign import HttpResponse, run_max_campaign
from omega_web_hg_t.r04.max_cli import _write_shard_config
from omega_web_hg_t.r04.max_models import digest_object
from omega_web_hg_t.r04.max_sharding import (
    aggregate_shards,
    build_shard_matrix,
    select_adapter_shard,
)


def test_crossref_parser_strips_abstracts_and_authors():
    body = json.dumps(
        {
            "message": {
                "items": [
                    {
                        "DOI": "10.1/x",
                        "title": ["A title"],
                        "URL": "https://doi.org/10.1/x",
                        "type": "article",
                        "abstract": "copyrighted text",
                        "author": [{"family": "Person"}],
                    }
                ]
            }
        }
    ).encode()
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
    body = json.dumps(
        {
            "features": [
                {
                    "id": "us1",
                    "properties": {
                        "title": "M 1.0",
                        "url": "https://example/us1",
                        "type": "earthquake",
                        "time": 1,
                    },
                }
            ]
        }
    ).encode()
    records = parse_usgs(body, "receipt")
    assert records[0].record_id == "us1"
    assert records[0].topics == ("earthquake",)


def test_key_required_adapter_is_skipped(tmp_path: Path):
    adapter = adapter_by_id("openalex")
    root = run_max_campaign(
        tmp_path,
        adapters=(adapter,),
        env={},
        item_budget=5,
        page_size=5,
        max_pages_per_source=1,
        transport=lambda *args: (_ for _ in ()).throw(
            AssertionError("network should not run")
        ),
    )
    report = json.loads((root / "campaign-report.json").read_text())
    assert report["record_count"] == 0
    assert report["skipped"][0]["source_id"] == "openalex"


def test_campaign_is_deduplicated_checkpointed_and_claim_safe(tmp_path: Path):
    adapter = adapter_by_id("crossref")
    body = json.dumps(
        {
            "message": {
                "items": [
                    {
                        "DOI": "10.1/x",
                        "title": ["A"],
                        "URL": "https://doi.org/10.1/x",
                        "type": "article",
                    },
                    {
                        "DOI": "10.1/x",
                        "title": ["A"],
                        "URL": "https://doi.org/10.1/x",
                        "type": "article",
                    },
                ]
            }
        }
    ).encode()
    calls = []

    def transport(url, headers, timeout, max_bytes):
        calls.append(url)
        return HttpResponse(
            200,
            {"Content-Type": "application/json", "X-RateLimit-Remaining": "9"},
            body,
            url,
        )

    root = run_max_campaign(
        tmp_path,
        adapters=(adapter,),
        env={},
        item_budget=10,
        page_size=10,
        max_pages_per_source=1,
        transport=transport,
        sleep=lambda _: None,
    )
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

    root = run_max_campaign(
        tmp_path,
        adapters=(adapter,),
        env={},
        item_budget=5,
        page_size=5,
        max_pages_per_source=1,
        retries=2,
        transport=transport,
        sleep=lambda _: None,
    )
    report = json.loads((root / "campaign-report.json").read_text())
    assert report["mminus_count"] == 1
    assert report["record_count"] == 0


def test_resume_does_not_replay_completed_adapter(tmp_path: Path):
    adapter = adapter_by_id("crossref")
    body = json.dumps(
        {"message": {"items": [{"DOI": "10.1/x", "title": ["A"]}]}}
    ).encode()
    calls = []

    def transport(url, headers, timeout, max_bytes):
        calls.append(url)
        return HttpResponse(200, {"Content-Type": "application/json"}, body, url)

    run_max_campaign(
        tmp_path,
        adapters=(adapter,),
        env={},
        item_budget=10,
        page_size=10,
        max_pages_per_source=1,
        transport=transport,
        sleep=lambda _: None,
    )
    run_max_campaign(
        tmp_path,
        adapters=(adapter,),
        env={},
        item_budget=10,
        page_size=10,
        max_pages_per_source=1,
        transport=transport,
        sleep=lambda _: None,
        resume=True,
    )
    assert len(calls) == 1


def test_shard_partition_is_complete_and_disjoint():
    matrix = build_shard_matrix(4)
    assert len(matrix["include"]) == 4
    selected_ids: list[str] = []
    for shard_index in range(4):
        selected_ids.extend(
            adapter.source_id
            for adapter in select_adapter_shard(
                MAX_ADAPTERS,
                shard_index=shard_index,
                shard_count=4,
            )
        )
    expected = sorted(adapter.source_id for adapter in MAX_ADAPTERS)
    assert sorted(selected_ids) == expected
    assert len(selected_ids) == len(set(selected_ids))


def test_resume_rejects_changed_shard_configuration(tmp_path: Path):
    _write_shard_config(
        tmp_path,
        shard_index=0,
        shard_count=4,
        query="hypergraph",
        selected_sources=["wikimedia"],
        resume=False,
    )
    with pytest.raises(ValueError, match="configuration mismatch"):
        _write_shard_config(
            tmp_path,
            shard_index=0,
            shard_count=4,
            query="different-query",
            selected_sources=["wikimedia"],
            resume=True,
        )


def _write_fake_shard(
    root: Path,
    *,
    shard_index: int,
    shard_count: int,
    record: dict[str, object],
) -> None:
    root.mkdir(parents=True)
    record = dict(record)
    record["digest"] = record.get("digest") or digest_object(record)
    (root / "records.jsonl").write_text(
        json.dumps(record, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (root / "receipts.jsonl").write_text("", encoding="utf-8")
    (root / "mminus.jsonl").write_text("", encoding="utf-8")
    report = {
        "metadata_only": True,
        "raw_bodies_persisted": False,
        "full_text_collected": False,
        "record_count": 1,
        "request_count": 0,
        "mminus_count": 0,
        "report_sha256": digest_object({"shard": shard_index}),
        "shard": {
            "index": shard_index,
            "count": shard_count,
            "selected_sources": [record["source_id"]],
        },
    }
    (root / "campaign-report.json").write_text(
        json.dumps(report, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_aggregate_shards_deduplicates_and_reports_missing(tmp_path: Path):
    source = tmp_path / "source"
    duplicate = {
        "source_id": "crossref",
        "record_id": "10.1/x",
        "title": "A",
    }
    _write_fake_shard(
        source / "shard-0",
        shard_index=0,
        shard_count=3,
        record=duplicate,
    )
    _write_fake_shard(
        source / "shard-1",
        shard_index=1,
        shard_count=3,
        record=duplicate,
    )
    output = aggregate_shards(
        source,
        tmp_path / "aggregate",
        expected_shards=3,
    )
    report = json.loads((output / "aggregate-report.json").read_text())
    assert report["record_count"] == 1
    assert report["discovered_shards"] == [0, 1]
    assert report["missing_shards"] == [2]
    assert report["complete"] is False
