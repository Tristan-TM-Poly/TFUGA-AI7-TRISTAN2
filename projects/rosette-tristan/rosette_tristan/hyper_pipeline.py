from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .absorption import build_absorption_ladder
from .bench import metrics_from_counts
from .claim_graph import build_claim_graph
from .code_forge import forge_equation_code
from .consensus import ArtifactVote, build_consensus
from .equation_oak import dimensional_oak
from .fidelity_pipeline import RosetteFidelityPipeline
from .figure_repro import plan_figure_reproduction
from .ip_guardian import classify_ip_guardian
from .memory import default_rosette_memory


class RosetteHyperAbsorptionPipeline:
    def __init__(self, extractor: str = "auto") -> None:
        self.extractor = extractor

    def compile(self, input_path: str | Path, out_dir: str | Path) -> dict:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        fidelity_out = out / "fidelity"
        result = RosetteFidelityPipeline(extractor=self.extractor).compile(input_path, fidelity_out)

        consensus_items = []
        for idx, equation in enumerate(result.equations, 1):
            votes = [
                ArtifactVote("equation", equation.latex, equation.source.extractor, weight=1.0, confidence=equation.confidence),
                ArtifactVote("equation", equation.latex, "rosette-fidelity", weight=0.8, confidence=0.75),
            ]
            consensus_items.append(build_consensus(votes, artifact_id=f"E{idx}").to_dict())

        equation_checks = [dimensional_oak(eq.latex, equation_id=f"E{idx}").to_dict() for idx, eq in enumerate(result.equations, 1)]
        claim_graph = [assessment.to_dict() for assessment in build_claim_graph(result.claims, result.equations)]
        code_forge = [forge_equation_code(eq.latex, equation_id=f"E{idx}", level=3).to_dict() for idx, eq in enumerate(result.equations, 1)]
        figure_plan = [plan_figure_reproduction("", figure_id="F1").to_dict()]
        absorption = build_absorption_ladder(result, build_claim_graph(result.claims, result.equations)).to_dict()
        memory = default_rosette_memory().to_dict()
        ip_report = classify_ip_guardian("\n".join(block.text for block in result.blocks)).to_dict()

        page_refs = sum(1 for block in result.blocks if block.source.page is not None)
        bboxes = sum(1 for block in result.blocks if block.source.bbox is not None)
        grounded_claims = sum(1 for claim in claim_graph if claim["classification"] != "CLAIM_UNSUPPORTED")
        metrics = metrics_from_counts(
            blocks=len(result.blocks),
            page_refs=page_refs,
            bboxes=bboxes,
            claims=len(result.claims),
            grounded_claims=grounded_claims,
            uncertain=len(result.oak_findings),
            risky=0,
        ).to_dict()

        payload = {
            "hyper_absorption_version": "0.1.0",
            "input_path": str(input_path),
            "fidelity": result.to_dict(),
            "consensus": consensus_items,
            "equation_oak": equation_checks,
            "claim_graph": claim_graph,
            "code_forge": code_forge,
            "figure_reproduction": figure_plan,
            "absorption": absorption,
            "memory": memory,
            "ip_guardian": ip_report,
            "bench_metrics": metrics,
            "oak_status": "hyper_research_usable_not_certified",
        }
        (out / "hyper_absorption.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        (out / "absorption_ladder.json").write_text(json.dumps(absorption, indent=2, ensure_ascii=False), encoding="utf-8")
        (out / "claim_evidence_graph.json").write_text(json.dumps(claim_graph, indent=2, ensure_ascii=False), encoding="utf-8")
        (out / "equation_oak.json").write_text(json.dumps(equation_checks, indent=2, ensure_ascii=False), encoding="utf-8")
        (out / "ip_guardian.json").write_text(json.dumps(ip_report, indent=2, ensure_ascii=False), encoding="utf-8")
        return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rosette-hyper")
    parser.add_argument("input")
    parser.add_argument("--out", default="out_hyper")
    parser.add_argument("--extractor", choices=["auto", "text", "pymupdf"], default="auto")
    args = parser.parse_args(argv)
    payload = RosetteHyperAbsorptionPipeline(extractor=args.extractor).compile(args.input, args.out)
    print(
        "hyper_absorption "
        f"equations={len(payload['equation_oak'])} "
        f"claims={len(payload['claim_graph'])} "
        f"oak_status={payload['oak_status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
