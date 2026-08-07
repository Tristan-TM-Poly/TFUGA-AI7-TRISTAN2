from __future__ import annotations

import json
from pathlib import Path

from omega_summary_fractal_t.lineage import (
    build_system_lineage,
    convergence_candidates,
    proof_debt,
    render_convergence_candidates,
    render_evolution,
    render_proof_debt,
)
from omega_summary_fractal_t.render import write_operational_views
from omega_summary_fractal_t.summarizer import SummaryEngine


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "lineage-demo"
    root.mkdir()
    (root / "README.md").write_text("# Lineage demo\n", encoding="utf-8")

    alpha = root / "omega_alpha_core_t"
    alpha.mkdir()
    (alpha / "README.md").write_text("# Alpha Core\n\nShared alpha engine.\n", encoding="utf-8")
    (alpha / "core.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")

    alpha_lab = root / "omega_alpha_lab_t"
    alpha_lab.mkdir()
    (alpha_lab / "README.md").write_text("# Alpha Lab\n\nShared alpha laboratory.\n", encoding="utf-8")
    (alpha_lab / "lab.py").write_text(
        "from omega_alpha_core_t.core import alpha\n\ndef run():\n    return alpha()\n",
        encoding="utf-8",
    )

    tests = root / "tests"
    tests.mkdir()
    (tests / "test_alpha_core.py").write_text(
        "from omega_alpha_core_t.core import alpha\n\ndef test_alpha():\n    assert alpha() == 1\n",
        encoding="utf-8",
    )
    return root


def test_lineage_contains_status_metrics_and_dependencies(tmp_path):
    bundle = SummaryEngine(_repo(tmp_path)).generate(depth=9, audience="oak")
    lineage = build_system_lineage(bundle)
    by_system = {item["system"]: item for item in lineage["systems"]}
    assert by_system["omega_alpha_core_t"]["status"] == "tested"
    assert any(
        item["relation"] == "DEPENDS_ON" and item["target"] == "omega_alpha_core_t"
        for item in by_system["omega_alpha_lab_t"]["outgoing_relations"]
    )
    assert "novelty" in lineage["boundary"]


def test_proof_debt_never_infers_external_validation(tmp_path):
    bundle = SummaryEngine(_repo(tmp_path)).generate(depth=9, audience="oak")
    rows = proof_debt(bundle)
    assert rows
    assert all("external_validation_not_inferred" in row["missing"] for row in rows)
    assert "external" in render_proof_debt(bundle).casefold()


def test_convergence_is_review_only(tmp_path):
    bundle = SummaryEngine(_repo(tmp_path)).generate(depth=9, audience="oak")
    candidates = convergence_candidates(bundle, threshold=0.1)
    assert candidates
    assert all(item["status"] == "review_required" for item in candidates)
    assert all(item["automatic_merge"] is False for item in candidates)
    assert "Aucune fusion automatique" in render_convergence_candidates(bundle)


def test_operational_views_emit_lineage_family(tmp_path):
    bundle = SummaryEngine(_repo(tmp_path)).generate(depth=9, audience="oak")
    out = tmp_path / "out"
    generated = write_operational_views(bundle, out)
    for key in ("evolution", "proof_debt", "convergence", "lineage"):
        assert generated[key].exists()
    payload = json.loads((out / "SYSTEM_LINEAGE.json").read_text(encoding="utf-8"))
    assert payload["fingerprint"] == bundle.cache_fingerprint
    assert "Chronologie Git" in render_evolution(bundle)
