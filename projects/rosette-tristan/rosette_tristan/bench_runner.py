from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .bench import RosetteBenchMetrics, metrics_from_counts
from .fidelity_pipeline import RosetteFidelityPipeline
from .real_render import render_mathtext_png
from .visual_oak import run_visual_oak


@dataclass
class BenchCaseResult:
    name: str
    status: str
    metrics: dict[str, float]
    outputs: dict[str, str] = field(default_factory=dict)
    oak_findings: list[str] = field(default_factory=list)
    memory_minus: list[str] = field(default_factory=list)


@dataclass
class RosetteBenchReport:
    suite: str
    cases: list[BenchCaseResult]
    aggregate_metrics: dict[str, float]
    oak_status: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": self.suite,
            "cases": [asdict(case) for case in self.cases],
            "aggregate_metrics": self.aggregate_metrics,
            "oak_status": self.oak_status,
            "warnings": self.warnings,
        }


def _write_fixture(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _average_metric(cases: list[BenchCaseResult], key: str) -> float:
    if not cases:
        return 0.0
    return round(sum(case.metrics.get(key, 0.0) for case in cases) / len(cases), 4)


def _fidelity_case(name: str, fixture: Path, out_dir: Path) -> BenchCaseResult:
    result = RosetteFidelityPipeline().compile(fixture, out_dir / name)
    page_refs = sum(1 for block in result.blocks if block.source.page is not None)
    bboxes = sum(1 for block in result.blocks if block.source.bbox is not None)
    grounded_claims = sum(1 for claim in result.claims if claim.evidence_ids)
    metrics = metrics_from_counts(
        blocks=len(result.blocks),
        page_refs=page_refs,
        bboxes=bboxes,
        claims=len(result.claims),
        grounded_claims=grounded_claims,
        uncertain=len(result.oak_findings),
        risky=0,
    ).to_dict()
    status = "passed" if result.blocks else "failed"
    return BenchCaseResult(
        name=name,
        status=status,
        metrics=metrics,
        outputs={"case_dir": str(out_dir / name)},
        oak_findings=result.oak_findings,
        memory_minus=result.memory_minus,
    )


def _visual_case(out_dir: Path) -> BenchCaseResult:
    case_dir = out_dir / "visual_match"
    case_dir.mkdir(parents=True, exist_ok=True)
    crop = case_dir / "source.png"
    render_mathtext_png("x=y", crop)
    report = run_visual_oak("x=y", reference_latex="x=y", source_crop_png=crop, out_dir=case_dir, equation_id="E1")
    metrics = RosetteBenchMetrics(
        text_fidelity=1.0,
        layout_fidelity=1.0,
        page_ref_coverage=0.0,
        bbox_coverage=0.0,
        equation_detection_f1=1.0,
        equation_render_score=report.visual_oak_score,
        claim_grounding_rate=0.0,
        code_execution_rate=0.0,
        oak_honesty_score=1.0,
    ).to_dict()
    return BenchCaseResult(
        name="visual_match",
        status="passed" if report.oak_status == "visual_match_not_certified" else "review",
        metrics=metrics,
        outputs={"case_dir": str(case_dir), "visual_oak_report": str(case_dir / "visual_oak_report.json")},
        oak_findings=report.warnings,
        memory_minus=report.memory_minus,
    )


def run_bench(out_dir: str | Path = "out_bench") -> RosetteBenchReport:
    out = Path(out_dir)
    fixtures = out / "fixtures"
    cases_out = out / "cases"
    out.mkdir(parents=True, exist_ok=True)

    clean = _write_fixture(
        fixtures / "clean_text.txt",
        "# Clean Text\n\nWe propose a small model.\n\n$$x=y$$\n",
    )
    paged = _write_fixture(
        fixtures / "paged_text.txt",
        "---PAGE 1---\n# Paged Text\n\nWe show the model.\n\n---PAGE 2---\nEquation:\n\n$$\\frac{dx}{dt}=-kx+u(t)$$\n",
    )

    cases = [
        _fidelity_case("clean_text", clean, cases_out),
        _fidelity_case("paged_text", paged, cases_out),
        _visual_case(cases_out),
    ]

    aggregate = {
        "text_fidelity": _average_metric(cases, "text_fidelity"),
        "layout_fidelity": _average_metric(cases, "layout_fidelity"),
        "page_ref_coverage": _average_metric(cases, "page_ref_coverage"),
        "equation_render_score": _average_metric(cases, "equation_render_score"),
        "claim_grounding_rate": _average_metric(cases, "claim_grounding_rate"),
        "oak_honesty_score": _average_metric(cases, "oak_honesty_score"),
    }
    failed = [case.name for case in cases if case.status == "failed"]
    oak_status = "bench_passed_not_certified" if not failed else "bench_failed"
    report = RosetteBenchReport(
        suite="rosette_minimal_oak_bench",
        cases=cases,
        aggregate_metrics=aggregate,
        oak_status=oak_status,
        warnings=["Synthetic fixtures are not proof of real PDF performance."],
    )
    (out / "rosette_bench_report.json").write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rosette-bench")
    parser.add_argument("--out", default="out_bench")
    args = parser.parse_args(argv)
    report = run_bench(args.out)
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return 0 if report.oak_status != "bench_failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
