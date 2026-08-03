from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from omega_prototype_portfolio_t.core import (
    ClaimBoundary, Evidence, NextAction, Prototype, Relation, Snapshot,
    analyze, assess, audit, compare, compile_bundle, dependency_cycles,
    digest, graphml, load_snapshot, plan, snapshot_from_dict,
)
from omega_prototype_portfolio_t.seed import seed_snapshot


@pytest.fixture()
def snapshot() -> Snapshot:
    return seed_snapshot()


@pytest.mark.parametrize("value", [-2, -1, 6, 7, 100])
def test_dimension_bounds_reject(value):
    p = seed_snapshot().prototypes[0]
    bad = dict(p.dimensions); bad["truth"] = value
    with pytest.raises(ValueError): replace(p, dimensions=bad)


@pytest.mark.parametrize("strength", ["", "MODEL", "CERTAIN", "5", "external"])
def test_unknown_evidence_strength_rejects(strength):
    with pytest.raises(ValueError): Evidence("test", "fixture", strength)


def test_seed_has_23_unique_prototypes(snapshot):
    assert len(snapshot.prototypes) == 23
    assert len({p.prototype_id for p in snapshot.prototypes}) == 23


def test_seed_heads_are_exact(snapshot):
    assert all(len(sha) == 40 for sha in snapshot.source_heads.values())


def test_snapshot_digest_is_deterministic(snapshot):
    assert snapshot.sha256 == snapshot_from_dict(snapshot.to_dict()).sha256


def test_snapshot_forbids_external_action(snapshot):
    with pytest.raises(ValueError): replace(snapshot, external_action_performed=True)


def test_snapshot_forbids_truth_probability(snapshot):
    with pytest.raises(ValueError): replace(snapshot, truth_probability_claimed=True)


def test_duplicate_ids_reject(snapshot):
    with pytest.raises(ValueError): replace(snapshot, prototypes=snapshot.prototypes + (snapshot.prototypes[0],))


def test_payment_does_not_imply_retention(snapshot):
    p = snapshot.prototypes[0]
    signals = dict(p.signals); signals["payment_collected"] = True; signals["repeat_usage"] = True; signals["retention"] = False
    candidate = replace(p, prototype_id="paid-once", signals=signals)
    assert assess(candidate).stage != "P7_RETAINED"


def test_retention_requires_repeat_usage(snapshot):
    p = snapshot.prototypes[0]
    signals = dict(p.signals); signals["retention"] = True
    with pytest.raises(ValueError): replace(p, signals=signals)


def test_repeat_usage_requires_payment(snapshot):
    p = snapshot.prototypes[0]
    signals = dict(p.signals); signals["repeat_usage"] = True
    with pytest.raises(ValueError): replace(p, signals=signals)


def test_internal_strength_gap_enters_mminus(snapshot):
    item = next(p for p in snapshot.prototypes if p.prototype_id == "startup-foundry")
    assert "M-PROTOTYPE-INTERNAL-STRENGTH-EXTERNAL-GAP" in assess(item).m_minus


def test_scoring_is_not_truth_probability(snapshot):
    a = assess(snapshot.prototypes[0])
    assert 0 <= a.priority <= 100
    assert not hasattr(a, "truth_probability")


def test_rigid_body_is_benchmarked(snapshot):
    item = next(p for p in snapshot.prototypes if p.prototype_id == "rigid-body")
    assert assess(item).stage == "P4_BENCHMARKED"


def test_web_hg_reaches_external(snapshot):
    item = next(p for p in snapshot.prototypes if p.prototype_id == "web-hg")
    assert assess(item).stage == "P5_EXTERNAL"


def test_tfacc_stays_structured(snapshot):
    item = next(p for p in snapshot.prototypes if p.prototype_id == "tfacc")
    assert assess(item).stage == "P1_STRUCTURED"


def test_dependency_graph_has_no_cycles(snapshot):
    assert dependency_cycles(snapshot) == []


def test_dependency_cycle_detected(snapshot):
    a, b = snapshot.prototypes[:2]
    a2 = replace(a, relations=(Relation("depends_on", b.prototype_id),))
    b2 = replace(b, relations=(Relation("depends_on", a.prototype_id),))
    mini = replace(snapshot, snapshot_id="cycle", prototypes=(a2, b2))
    assert dependency_cycles(mini)
    assert audit(mini)["status"] == "FAIL"


def test_missing_relation_target_fails_audit(snapshot):
    p = replace(snapshot.prototypes[0], relations=(Relation("depends_on", "missing"),))
    mini = replace(snapshot, snapshot_id="missing", prototypes=(p,))
    assert audit(mini)["status"] == "FAIL"


def test_seed_audit_passes(snapshot):
    report = audit(snapshot)
    assert report["status"] == "PASS"
    assert report["external_action_performed"] is False


def test_analysis_is_deterministic(snapshot):
    assert analyze(snapshot) == analyze(snapshot)


def test_analysis_covers_every_prototype(snapshot):
    result = analyze(snapshot)
    assert len(result["assessments"]) == len(snapshot.prototypes)


def test_analysis_has_separate_score_axes(snapshot):
    row = analyze(snapshot)["assessments"][0]
    for key in ("science", "engineering", "product", "integration", "evidence_density", "externalization", "priority", "risk_debt"):
        assert key in row


def test_plan_respects_item_budget(snapshot):
    result = plan(snapshot, max_items=4)
    assert result["selected_count"] <= 4


def test_plan_respects_hour_budget(snapshot):
    result = plan(snapshot, max_hours=12)
    assert result["used_hours"] <= 12


def test_plan_is_review_only(snapshot):
    result = plan(snapshot)
    assert result["merge_authorized"] is False
    assert result["publication_authorized"] is False
    assert all(item["external_action_authorized"] is False for item in result["selected"])


def test_plan_has_no_permanent_cap(snapshot):
    assert plan(snapshot)["budget"]["permanent_total_cap"] is None


def test_plan_diversifies_categories(snapshot):
    selected = plan(snapshot, max_items=6, max_per_category=2)["selected"]
    counts = {}
    for item in selected: counts[item["category"]] = counts.get(item["category"], 0) + 1
    assert max(counts.values()) <= 2


def test_graphml_has_all_nodes(snapshot):
    text = graphml(snapshot)
    assert text.count("<node id=") == len(snapshot.prototypes)
    assert "portfolio-os" in text


def test_compare_identical(snapshot):
    delta = compare(snapshot, snapshot)
    assert not delta["added"] and not delta["removed"] and not delta["changed"]


def test_compare_detects_change(snapshot):
    first = snapshot.prototypes[0]
    changed = replace(first, summary=first.summary + " revised")
    right = replace(snapshot, snapshot_id="right", prototypes=(changed,) + snapshot.prototypes[1:])
    assert first.prototype_id in compare(snapshot, right)["changed"]


def test_bundle_is_byte_deterministic(snapshot, tmp_path):
    one, two = tmp_path / "one", tmp_path / "two"
    r1 = compile_bundle(snapshot, one); r2 = compile_bundle(snapshot, two)
    assert r1 == r2
    assert all((one / name).read_bytes() == (two / name).read_bytes() for name in r1)


def test_bundle_manifest_verifies(snapshot, tmp_path):
    root = tmp_path / "bundle"; compile_bundle(snapshot, root)
    manifest = json.loads((root / "manifest.json").read_text())
    for name, sha in manifest["files"].items():
        assert digest(json.loads((root / name).read_text())) != sha if name.endswith(".json") else True
        import hashlib
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == sha


def test_bundle_contains_expected_outputs(snapshot, tmp_path):
    root = tmp_path / "bundle"; receipts = compile_bundle(snapshot, root)
    expected = {"snapshot.json", "assessments.jsonl", "analysis.json", "plan.json", "audit.json", "portfolio.graphml", "REPORT.md", "m_minus.jsonl", "manifest.json"}
    assert set(receipts) == expected


def test_snapshot_roundtrip_file(snapshot, tmp_path):
    path = tmp_path / "snapshot.json"; path.write_text(json.dumps(snapshot.to_dict()))
    assert load_snapshot(path).sha256 == snapshot.sha256


def test_cli_seed(tmp_path):
    output = tmp_path / "seed.json"
    subprocess.run([sys.executable, "-m", "omega_prototype_portfolio_t", "seed", "--output", str(output)], check=True)
    assert len(json.loads(output.read_text())["prototypes"]) == 23


def test_cli_audit():
    completed = subprocess.run([sys.executable, "-m", "omega_prototype_portfolio_t", "audit"], check=False, capture_output=True, text=True)
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["status"] == "PASS"


def test_cli_oak():
    completed = subprocess.run([sys.executable, "-m", "omega_prototype_portfolio_t", "oak"], check=False, capture_output=True, text=True)
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["status"] == "PASS" and payload["bundle_deterministic"] is True


def test_cli_compile(tmp_path):
    root = tmp_path / "out"
    subprocess.run([sys.executable, "-m", "omega_prototype_portfolio_t", "compile", "--output-dir", str(root)], check=True)
    assert (root / "REPORT.md").exists()


def test_claim_early_certification_rejects():
    with pytest.raises(ValueError): ClaimBoundary("structured", "claim", certified=True)


def test_evidence_sha_validation():
    with pytest.raises(ValueError): Evidence("test", "ref", sha256="bad")


def test_invalid_relation_rejects():
    with pytest.raises(ValueError): Relation("equals", "x")


def test_invalid_action_budget_rejects():
    with pytest.raises(ValueError): NextAction("x", "test", 0, "evidence")
