from __future__ import annotations

import json

from omega_web_hg_t.r04 import BEST_SITES_V1, PlannerOptions, audit_profiles, build_plan, materialize_plan


def test_catalog_is_valid_and_unique() -> None:
    report = audit_profiles(BEST_SITES_V1)
    assert report["status"] == "PASS"
    assert report["sources"] == 12
    assert report["duplicates"] == []


def test_default_plan_is_metadata_only_and_fail_closed(monkeypatch) -> None:
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.delenv("NASA_API_KEY", raising=False)
    plan = build_plan()
    selected = {item.source_id for item in plan.sources}
    assert "openalex" not in selected
    assert "nasa_open" not in selected
    assert "arxiv" not in selected
    assert {"wikimedia", "crossref", "pubmed", "pmc_open", "nist_pdr", "cern_open_data", "usgs", "esa_cci", "canada_open"} <= selected
    assert all(item.full_text_policy == "metadata_only" for item in plan.sources)
    assert plan.execute_network is False


def test_keyed_sources_require_explicit_route(monkeypatch) -> None:
    monkeypatch.setenv("OPENALEX_API_KEY", "fixture")
    monkeypatch.setenv("NASA_API_KEY", "fixture")
    plan = build_plan(options=PlannerOptions(include_key_required=True))
    selected = {item.source_id for item in plan.sources}
    assert "openalex" in selected
    assert "nasa_open" in selected


def test_review_required_source_is_opt_in() -> None:
    default = build_plan()
    opted = build_plan(options=PlannerOptions(include_review_required=True))
    assert "arxiv" not in {item.source_id for item in default.sources}
    assert "arxiv" in {item.source_id for item in opted.sources}


def test_plan_is_deterministic() -> None:
    left = build_plan()
    right = build_plan()
    assert left.digest == right.digest
    assert left.to_dict() == right.to_dict()
    boundaries = left.to_dict()["claim_boundaries"]
    assert boundaries["source_is_best_proven"] is False
    assert boundaries["content_truth_certified"] is False
    assert boundaries["license_clearance_automated"] is False


def test_materialized_plan_is_parseable(tmp_path) -> None:
    plan = build_plan()
    root = materialize_plan(plan, tmp_path / "campaign")
    payload = json.loads((root / "campaign-plan.json").read_text(encoding="utf-8"))
    assert payload["digest"] == plan.digest
    assert payload["source_count"] == len(plan.sources)
    assert (root / "README.md").is_file()
