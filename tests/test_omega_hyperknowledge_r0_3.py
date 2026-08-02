from __future__ import annotations

import json
from pathlib import Path

from omega_wiki_t.action_queue import build_action_queue
from omega_wiki_t.contradiction_engine import detect_claim_collisions
from omega_wiki_t.hyperknowledge import HyperKnowledgeCompiler
from omega_wiki_t.knowledge_cell import (
    ClaimAtom,
    EvidenceRecord,
    KnowledgeCell,
    OakTransition,
    audit_cells,
)


ROOT = Path(__file__).resolve().parents[1]


def test_checked_in_knowledge_cells_are_structurally_valid() -> None:
    ffwt = KnowledgeCell.read(ROOT / "data/knowledge_cells/ffwt_hac_cvcd_r0_3.json")
    omega_lin = KnowledgeCell.read(ROOT / "data/knowledge_cells/omega_lin_t_r0_3.json")

    assert ffwt.validate() == []
    assert omega_lin.validate() == []
    assert ffwt.oak_status == "REFORMULATED"
    assert ffwt.transitions[-2].to_status == "REFUTED"
    assert ffwt.transitions[-1].to_status == "REFORMULATED"
    assert omega_lin.oak_status == "DEMONSTRATED"
    assert omega_lin.evidence_by_kind("baseline")


def test_audit_detects_missing_equation_baseline_test_and_ip_gate() -> None:
    claim = ClaimAtom(
        claim_id="CLM-PHYS-001",
        text="A physical device produces a measurable field effect.",
        canonical_key="device produces field effect",
        domain="physics",
        failure_conditions=(),
    )
    cell = KnowledgeCell(
        cell_id="KC-PHYS-001",
        subject="Physical prototype",
        definition="A deliberately incomplete fixture for audit testing.",
        domain="physics",
        oak_status="CANONICAL",
        claims=[claim],
        evidence=[
            EvidenceRecord(
                evidence_id="EVD-CODE-001",
                kind="code",
                title="Prototype code",
                supports_claim_ids=(claim.claim_id,),
            ),
            EvidenceRecord(
                evidence_id="EVD-RESULT-001",
                kind="result",
                title="Unbaselined result",
                supports_claim_ids=(claim.claim_id,),
            ),
        ],
        transitions=[
            OakTransition(
                transition_id="TR-PHYS-001",
                timestamp="2026-01-01T00:00:00Z",
                from_status="IDEA",
                to_status="CANONICAL",
                cause="Deliberately invalid promotion fixture.",
                evidence_ids=("EVD-RESULT-001",),
            )
        ],
        risks=["brevet candidate"],
        next_actions=[],
        public_disclosure=True,
    )

    report = audit_cells([cell])
    categories = {finding.category for finding in report.findings}

    assert "physics_without_equation" in categories
    assert "result_without_baseline" in categories
    assert "code_without_test" in categories
    assert "ip_disclosure_risk" in categories
    assert "missing_failure_condition" in categories
    assert report.metrics["evidence_coverage"] == 1.0
    assert report.metrics["falsification_coverage"] == 0.0


def test_contradiction_engine_separates_opposition_from_scope_tension() -> None:
    affirm = ClaimAtom(
        claim_id="CLM-A",
        text="Method improves reconstruction.",
        canonical_key="method improves reconstruction",
        domain="signal-processing",
        polarity="affirm",
        scope="synthetic benchmark",
        failure_conditions=("no improvement",),
    )
    deny_same_scope = ClaimAtom(
        claim_id="CLM-B",
        text="Method does not improve reconstruction.",
        canonical_key="method improves reconstruction",
        domain="signal-processing",
        polarity="deny",
        scope="synthetic benchmark",
        failure_conditions=("consistent improvement",),
    )
    deny_other_scope = ClaimAtom(
        claim_id="CLM-C",
        text="Method does not improve spectroscopy classification.",
        canonical_key="method improves reconstruction",
        domain="signal-processing",
        polarity="deny",
        scope="real spectroscopy classification",
        failure_conditions=("classification improvement",),
    )

    cells = [
        KnowledgeCell("KC-A", "A", "A cell", "signals", "FORMALIZED", claims=[affirm]),
        KnowledgeCell("KC-B", "B", "B cell", "signals", "FORMALIZED", claims=[deny_same_scope]),
        KnowledgeCell("KC-C", "C", "C cell", "signals", "FORMALIZED", claims=[deny_other_scope]),
    ]
    collisions = detect_claim_collisions(cells)
    kinds = {collision.kind for collision in collisions}

    assert "potential_contradiction" in kinds
    assert "scope_tension" in kinds


def test_compiler_writes_audit_collisions_queue_and_human_report(tmp_path: Path) -> None:
    ffwt = KnowledgeCell.read(ROOT / "data/knowledge_cells/ffwt_hac_cvcd_r0_3.json")
    omega_lin = KnowledgeCell.read(ROOT / "data/knowledge_cells/omega_lin_t_r0_3.json")
    bundle = HyperKnowledgeCompiler.compile([ffwt, omega_lin])
    output = HyperKnowledgeCompiler.write(bundle, tmp_path / "bundle")

    expected = {
        "manifest.json",
        "knowledge-cells.json",
        "knowledge-cells.jsonl",
        "audit.json",
        "claim-collisions.json",
        "action-queue.json",
        "action-queue.jsonl",
        "report.md",
    }
    assert expected == {path.name for path in output.iterdir()}

    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["cell_count"] == 2
    assert manifest["claim_count"] == 3
    assert manifest["oak_status"].startswith("R0.3_")
    assert "Coverage metrics" in (output / "report.md").read_text(encoding="utf-8")


def test_action_queue_prioritizes_contradictions_before_enrichment() -> None:
    left = KnowledgeCell(
        "KC-L",
        "Left",
        "Left cell",
        "test",
        "FORMALIZED",
        claims=[
            ClaimAtom(
                "CLM-L",
                "X works.",
                "x works",
                "test",
                polarity="affirm",
                scope="same",
                failure_conditions=("X fails",),
            )
        ],
    )
    right = KnowledgeCell(
        "KC-R",
        "Right",
        "Right cell",
        "test",
        "FORMALIZED",
        claims=[
            ClaimAtom(
                "CLM-R",
                "X does not work.",
                "x works",
                "test",
                polarity="deny",
                scope="same",
                failure_conditions=("X works",),
            )
        ],
    )
    cells = [left, right]
    audit = audit_cells(cells)
    collisions = detect_claim_collisions(cells)
    queue = build_action_queue(cells, audit.findings, collisions)

    assert queue[0].priority == "P0"
    assert any(item.category == "potential_contradiction" for item in queue)
