"""Command-line interface for Ω-REVOLUTION-DIVERSIFICATION-T∞."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .ablation import canonical_ablation_fixture, run_mminus_ablation
from .compiler import RevolutionDiversificationCompiler
from .demo_data import build_demo_cells
from .portfolio import QualityObservation, decide_quality, score_hypotheses
from .raman_loop import canonical_raman_fixture, run_raman_loop
from .registry import registry_payload
from .truth_audit import audit_repository, canonical_truth_audit_fixture


def _print(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile and validate diversified Tristan discovery cells."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    registry = sub.add_parser("registry", help="Print the canonical 64-module registry.")
    registry.add_argument("--output")

    ablation = sub.add_parser("mminus-ablation", help="Run the deterministic M⁻ ablation.")
    ablation.add_argument("--output")

    audit = sub.add_parser("truth-audit", help="Run the known-fixture repository audit.")
    audit.add_argument("--output")

    raman = sub.add_parser("raman-loop", help="Run the synthetic Raman discovery loop.")
    raman.add_argument("--output")

    quality = sub.add_parser("quality-demo", help="Evaluate a representative quality state.")
    quality.add_argument("--output")

    compile_cmd = sub.add_parser("compile-demo", help="Compile and export the full R0.1 demo.")
    compile_cmd.add_argument("--output-dir", required=True)

    return parser


def _write_optional(path: str | None, payload: Any) -> None:
    if path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "registry":
        payload = registry_payload()
        _write_optional(args.output, payload)
        _print(payload)
        return 0
    if args.command == "mminus-ablation":
        payload = run_mminus_ablation(canonical_ablation_fixture()).to_dict()
        _write_optional(args.output, payload)
        _print(payload)
        return 0
    if args.command == "truth-audit":
        payload = audit_repository(canonical_truth_audit_fixture()).to_dict()
        _write_optional(args.output, payload)
        _print(payload)
        return 0
    if args.command == "raman-loop":
        reference, training, holdout, peaks = canonical_raman_fixture()
        payload = run_raman_loop(reference, training, holdout, peaks).to_dict()
        _write_optional(args.output, payload)
        _print(payload)
        return 0
    if args.command == "quality-demo":
        cells = build_demo_cells()
        all_hypotheses = [h for cell in cells for h in cell.hypotheses]
        scores = score_hypotheses(all_hypotheses)
        observation = QualityObservation(
            generated_objects=1000,
            unique_objects=900,
            formalized_claims=120,
            claims_with_evidence=85,
            claims_with_falsification=110,
            externally_validated_claims=12,
            duplicate_objects=75,
            orphan_objects=0,
            circular_evidence_links=0,
            repeated_errors_prevented=18,
            repeated_errors_observed=4,
        )
        payload = {
            "observation": observation.to_dict(),
            "decision": decide_quality(observation).to_dict(),
            "portfolio": [score.to_dict() for score in scores],
        }
        _write_optional(args.output, payload)
        _print(payload)
        return 0
    if args.command == "compile-demo":
        compiler = RevolutionDiversificationCompiler(
            cells=build_demo_cells(),
            repository_snapshots=(canonical_truth_audit_fixture(),),
        )
        compiled = compiler.export(args.output_dir)
        _print(
            {
                "output_dir": str(Path(args.output_dir)),
                "metrics": compiled.metrics,
                "manifest_sha256": compiled.manifest["manifest_sha256"],
                "oak_boundary": (
                    "Synthetic and internal validations are not independent scientific "
                    "or market validation."
                ),
            }
        )
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
