from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .bench_corpus import CorpusCase, load_manifest, validate_manifest
from .fidelity_pipeline import RosetteFidelityPipeline


@dataclass
class CorpusCaseBenchResult:
    case_id: str
    case_type: str
    status: str
    counts: dict[str, int]
    expectation_results: dict[str, bool]
    oak_findings: list[str] = field(default_factory=list)
    memory_minus: list[str] = field(default_factory=list)
    outputs: dict[str, str] = field(default_factory=dict)


@dataclass
class CorpusBenchReport:
    manifest: str
    suite: str
    case_results: list[CorpusCaseBenchResult]
    aggregate: dict[str, float | int]
    oak_status: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest,
            "suite": self.suite,
            "case_results": [asdict(result) for result in self.case_results],
            "aggregate": self.aggregate,
            "oak_status": self.oak_status,
            "warnings": self.warnings,
        }


def _case_counts(result) -> dict[str, int]:
    return {
        "blocks": len(result.blocks),
        "equations": len(result.equations),
        "claims": len(result.claims),
        "page_refs": sum(1 for block in result.blocks if block.source.page is not None),
        "bboxes": sum(1 for block in result.blocks if block.source.bbox is not None),
    }


def _evaluate_expectations(case: CorpusCase, counts: dict[str, int]) -> dict[str, bool]:
    expected = case.expected
    return {
        "min_blocks": counts["blocks"] >= expected.min_blocks,
        "min_equations": counts["equations"] >= expected.min_equations,
        "min_claims": counts["claims"] >= expected.min_claims,
        "requires_page_refs": (counts["page_refs"] > 0) if expected.requires_page_refs else True,
        "requires_bboxes": (counts["bboxes"] > 0) if expected.requires_bboxes else True,
        "requires_visual_oak": True if not expected.requires_visual_oak else False,
    }


def _status_from_expectations(expectations: dict[str, bool]) -> str:
    if all(expectations.values()):
        return "passed_not_certified"
    if not expectations.get("requires_visual_oak", True):
        return "blocked_visual_oak_required"
    return "failed_expectations"


def run_corpus_case(case: CorpusCase, corpus_root: Path, out_dir: Path) -> CorpusCaseBenchResult:
    case_path = corpus_root / case.path
    case_out = out_dir / case.case_id
    case_out.mkdir(parents=True, exist_ok=True)
    try:
        result = RosetteFidelityPipeline().compile(case_path, case_out)
        counts = _case_counts(result)
        expectations = _evaluate_expectations(case, counts)
        status = _status_from_expectations(expectations)
        memory_minus = list(result.memory_minus)
        if status != "passed_not_certified":
            memory_minus.append(f"corpus_case_expectation_failure:{case.case_id}")
        return CorpusCaseBenchResult(
            case_id=case.case_id,
            case_type=case.case_type,
            status=status,
            counts=counts,
            expectation_results=expectations,
            oak_findings=list(result.oak_findings),
            memory_minus=memory_minus,
            outputs={"case_dir": str(case_out)},
        )
    except Exception as exc:
        return CorpusCaseBenchResult(
            case_id=case.case_id,
            case_type=case.case_type,
            status="runner_error",
            counts={"blocks": 0, "equations": 0, "claims": 0, "page_refs": 0, "bboxes": 0},
            expectation_results={},
            oak_findings=[str(exc)],
            memory_minus=["corpus_case_runner_error"],
            outputs={"case_dir": str(case_out)},
        )


def _aggregate(results: list[CorpusCaseBenchResult]) -> dict[str, float | int]:
    total = len(results)
    passed = sum(1 for result in results if result.status == "passed_not_certified")
    failed = sum(1 for result in results if result.status != "passed_not_certified")
    total_expectations = sum(len(result.expectation_results) for result in results)
    passed_expectations = sum(sum(1 for ok in result.expectation_results.values() if ok) for result in results)
    return {
        "case_count": total,
        "passed_cases": passed,
        "failed_cases": failed,
        "case_pass_rate": round(passed / max(1, total), 4),
        "expectation_pass_rate": round(passed_expectations / max(1, total_expectations), 4),
    }


def run_corpus_bench(manifest_path: str | Path, out_dir: str | Path = "out_corpus_bench") -> CorpusBenchReport:
    manifest_path = Path(manifest_path)
    manifest = load_manifest(manifest_path)
    corpus_root = manifest_path.parent
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    validation_findings = validate_manifest(manifest, root=corpus_root)
    errors = [finding for finding in validation_findings if finding.severity == "error"]
    case_results: list[CorpusCaseBenchResult] = []
    if not errors:
        case_results = [run_corpus_case(case, corpus_root, out / "cases") for case in manifest.cases]
    aggregate = _aggregate(case_results)
    if errors:
        oak_status = "corpus_bench_invalid_manifest"
    elif aggregate["failed_cases"] == 0:
        oak_status = "corpus_bench_passed_not_certified"
    else:
        oak_status = "corpus_bench_failed_expectations"

    report = CorpusBenchReport(
        manifest=str(manifest_path),
        suite=manifest.name,
        case_results=case_results,
        aggregate=aggregate,
        oak_status=oak_status,
        warnings=[
            "Corpus bench validates extraction expectations, not scientific truth.",
            "Real certification requires licensed ground-truth corpora and independent review.",
        ] + [f"{finding.severity}:{finding.case_id}:{finding.message}" for finding in validation_findings],
    )
    (out / "corpus_bench_report.json").write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rosette-corpus-bench")
    parser.add_argument("manifest")
    parser.add_argument("--out", default="out_corpus_bench")
    args = parser.parse_args(argv)
    report = run_corpus_bench(args.manifest, args.out)
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return 0 if report.oak_status == "corpus_bench_passed_not_certified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
