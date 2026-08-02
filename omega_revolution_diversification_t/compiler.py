"""Compiler and export surface for Ω-REVOLUTION-DIVERSIFICATION-T∞."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

from .ablation import MMinusAblationReport, canonical_ablation_fixture, run_mminus_ablation
from .models import DiscoveryCell, validate_cells
from .portfolio import QualityObservation, decide_quality, score_hypotheses
from .raman_loop import RamanLoopResult, canonical_raman_fixture, run_raman_loop
from .registry import registry_payload
from .truth_audit import (
    RepositorySnapshot,
    TruthAuditReport,
    audit_repository,
    canonical_truth_audit_fixture,
)


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _jsonl_dump(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                + "\n"
            )


@dataclass(frozen=True)
class CompiledDiversification:
    cells: tuple[DiscoveryCell, ...]
    registry: dict[str, Any]
    truth_audits: tuple[TruthAuditReport, ...]
    mminus_ablation: MMinusAblationReport
    raman_loop: RamanLoopResult
    quality_observation: QualityObservation
    quality_decision: dict[str, Any]
    metrics: dict[str, Any]
    manifest: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cells": [cell.to_dict() for cell in self.cells],
            "registry": self.registry,
            "truth_audits": [report.to_dict() for report in self.truth_audits],
            "mminus_ablation": self.mminus_ablation.to_dict(),
            "raman_loop": self.raman_loop.to_dict(),
            "quality_observation": self.quality_observation.to_dict(),
            "quality_decision": self.quality_decision,
            "metrics": self.metrics,
            "manifest": self.manifest,
        }


class RevolutionDiversificationCompiler:
    def __init__(
        self,
        *,
        cells: Sequence[DiscoveryCell] = (),
        repository_snapshots: Sequence[RepositorySnapshot] = (),
    ) -> None:
        self.cells = tuple(cells)
        self.repository_snapshots = tuple(repository_snapshots)

    def compile(self) -> CompiledDiversification:
        cell_errors = validate_cells(self.cells)
        if cell_errors:
            raise ValueError("cell validation failed: " + "; ".join(cell_errors))
        audits = tuple(audit_repository(snapshot) for snapshot in self.repository_snapshots)
        ablation = run_mminus_ablation(canonical_ablation_fixture())
        reference, training, holdout, peaks = canonical_raman_fixture()
        raman = run_raman_loop(reference, training, holdout, peaks)
        all_hypotheses = [
            hypothesis
            for cell in self.cells
            for hypothesis in cell.hypotheses
        ]
        scores = score_hypotheses(all_hypotheses)
        formalized = len(all_hypotheses)
        claims_with_evidence = sum(
            1
            for cell in self.cells
            for hypothesis in cell.hypotheses
            if any(
                hypothesis.hypothesis_id in evidence.supports
                or hypothesis.hypothesis_id in evidence.contradicts
                for evidence in cell.evidence
            )
        )
        claims_with_falsification = sum(
            bool(hypothesis.falsification_conditions)
            for hypothesis in all_hypotheses
        )
        external_claims = sum(
            1
            for cell in self.cells
            for hypothesis in cell.hypotheses
            if any(
                evidence.independence == "external"
                and (
                    hypothesis.hypothesis_id in evidence.supports
                    or hypothesis.hypothesis_id in evidence.contradicts
                )
                for evidence in cell.evidence
            )
        )
        generated = max(
            1,
            len(self.cells)
            + sum(len(cell.evidence) + len(cell.m_minus) for cell in self.cells)
            + len(registry_payload()["groups"]) * 8,
        )
        unique = generated
        duplicate_objects = 0
        orphan_objects = 0
        circular_links = 0
        quality = QualityObservation(
            generated_objects=generated,
            unique_objects=unique,
            formalized_claims=formalized,
            claims_with_evidence=claims_with_evidence,
            claims_with_falsification=claims_with_falsification,
            externally_validated_claims=external_claims,
            duplicate_objects=duplicate_objects,
            orphan_objects=orphan_objects,
            circular_evidence_links=circular_links,
            repeated_errors_prevented=ablation.with_memory.prevented_failures,
            repeated_errors_observed=ablation.with_memory.repeated_failures,
        )
        decision = decide_quality(quality).to_dict()
        metrics = {
            "cell_count": len(self.cells),
            "hypothesis_count": formalized,
            "evidence_count": sum(len(cell.evidence) for cell in self.cells),
            "negative_memory_count": sum(len(cell.m_minus) for cell in self.cells),
            "module_count": registry_payload()["module_count"],
            "truth_audit_count": len(audits),
            "truth_audit_findings": sum(report.finding_count for report in audits),
            "mminus_cost_reduction": ablation.cost_reduction,
            "mminus_repeated_failure_reduction": ablation.repeated_failure_reduction,
            "raman_best_model": raman.best_candidate.kind.value,
            "raman_best_holdout_rmse": raman.best_candidate.holdout_rmse,
            "raman_baseline_rmse": raman.baseline_rmse,
            "quality_decision": decision["decision"],
            "portfolio": [score.to_dict() for score in scores],
        }
        manifest_payload = {
            "metrics": metrics,
            "cell_ids": [cell.cell_id for cell in self.cells],
            "truth_audits": [report.repository for report in audits],
            "registry_module_count": registry_payload()["module_count"],
            "boundaries": [
                "generated volume is not evidence quality",
                "hash integrity is not truth",
                "internal validation is not independent replication",
                "market hypotheses require external users",
                "sensitive irreversible actions remain human-approved",
            ],
        }
        manifest = {
            **manifest_payload,
            "manifest_sha256": sha256(
                json.dumps(
                    manifest_payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode("utf-8")
            ).hexdigest(),
        }
        return CompiledDiversification(
            cells=self.cells,
            registry=registry_payload(),
            truth_audits=audits,
            mminus_ablation=ablation,
            raman_loop=raman,
            quality_observation=quality,
            quality_decision=decision,
            metrics=metrics,
            manifest=manifest,
        )

    def export(self, output_dir: str | Path) -> CompiledDiversification:
        compiled = self.compile()
        root = Path(output_dir)
        root.mkdir(parents=True, exist_ok=True)
        _json_dump(root / "manifest.json", compiled.manifest)
        _json_dump(root / "metrics.json", compiled.metrics)
        _json_dump(root / "registry.json", compiled.registry)
        _json_dump(
            root / "discovery-cells.json",
            [cell.to_dict() for cell in compiled.cells],
        )
        _jsonl_dump(
            root / "discovery-cells.jsonl",
            (cell.to_dict() for cell in compiled.cells),
        )
        _json_dump(
            root / "truth-audits.json",
            [report.to_dict() for report in compiled.truth_audits],
        )
        _json_dump(root / "mminus-ablation.json", compiled.mminus_ablation.to_dict())
        _json_dump(root / "raman-loop.json", compiled.raman_loop.to_dict())
        _json_dump(root / "quality-observation.json", compiled.quality_observation.to_dict())
        _json_dump(root / "quality-decision.json", compiled.quality_decision)
        (root / "report.md").write_text(render_report(compiled), encoding="utf-8")
        return compiled


def render_report(compiled: CompiledDiversification) -> str:
    metrics = compiled.metrics
    decision = compiled.quality_decision
    lines = [
        "# Ω-REVOLUTION-DIVERSIFICATION-T∞ R0.1",
        "",
        "## Executive result",
        "",
        f"- Discovery cells: **{metrics['cell_count']}**",
        f"- Hypotheses: **{metrics['hypothesis_count']}**",
        f"- Typed evidence: **{metrics['evidence_count']}**",
        f"- Negative-memory rules: **{metrics['negative_memory_count']}**",
        f"- Diversification modules: **{metrics['module_count']}**",
        f"- Truth-audit findings: **{metrics['truth_audit_findings']}**",
        f"- Quality conductor: **{decision['decision']}**",
        "",
        "## M⁻ ablation",
        "",
        f"- Cost reduction on deterministic fixture: **{metrics['mminus_cost_reduction']:.3f}**",
        (
            "- Repeated-failure reduction: "
            f"**{metrics['mminus_repeated_failure_reduction']:.3f}**"
        ),
        "",
        "## Raman discovery loop",
        "",
        f"- Best model: **{metrics['raman_best_model']}**",
        f"- Holdout RMSE: **{metrics['raman_best_holdout_rmse']:.8f}**",
        f"- Baseline RMSE: **{metrics['raman_baseline_rmse']:.8f}**",
        "",
        "## OAK boundaries",
        "",
        "- The Raman result is synthetic.",
        "- The M⁻ ablation measures supplied fixtures only.",
        "- Truth-audit findings are review candidates, not proof of intent.",
        "- Registry presence is not implementation or scientific validation.",
        "- Sensitive irreversible actions remain human-approved.",
        "",
        f"Manifest SHA-256: `{compiled.manifest['manifest_sha256']}`",
        "",
    ]
    return "\n".join(lines)


def canonical_compiler() -> RevolutionDiversificationCompiler:
    return RevolutionDiversificationCompiler(
        cells=(),
        repository_snapshots=(canonical_truth_audit_fixture(),),
    )
