from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


ALLOWED_CASE_TYPES = {
    "clean_text",
    "paged_text",
    "pdf_digital",
    "pdf_two_column",
    "equation_heavy",
    "table_heavy",
    "figure_heavy",
    "scanned_pdf",
    "patent_claims",
    "old_math_scan",
}


@dataclass
class CorpusExpectation:
    min_blocks: int = 1
    min_equations: int = 0
    min_claims: int = 0
    requires_page_refs: bool = False
    requires_bboxes: bool = False
    requires_visual_oak: bool = False
    allowed_oak_status: list[str] = field(default_factory=list)


@dataclass
class CorpusCase:
    case_id: str
    case_type: str
    path: str
    license: str = "unknown"
    source: str = "synthetic_or_user_supplied"
    expected: CorpusExpectation = field(default_factory=CorpusExpectation)
    notes: list[str] = field(default_factory=list)


@dataclass
class CorpusValidationFinding:
    case_id: str
    severity: str
    message: str


@dataclass
class CorpusManifest:
    name: str
    version: str
    cases: list[CorpusCase]
    oak_rules: list[str] = field(default_factory=lambda: [
        "do_not_commit_copyrighted_pdfs_without_license",
        "ground_truth_required_for_certification",
        "synthetic_cases_only_prove_pipeline_coherence",
    ])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _expectation_from_dict(data: dict[str, Any]) -> CorpusExpectation:
    return CorpusExpectation(
        min_blocks=int(data.get("min_blocks", 1)),
        min_equations=int(data.get("min_equations", 0)),
        min_claims=int(data.get("min_claims", 0)),
        requires_page_refs=bool(data.get("requires_page_refs", False)),
        requires_bboxes=bool(data.get("requires_bboxes", False)),
        requires_visual_oak=bool(data.get("requires_visual_oak", False)),
        allowed_oak_status=list(data.get("allowed_oak_status", [])),
    )


def manifest_from_dict(data: dict[str, Any]) -> CorpusManifest:
    cases: list[CorpusCase] = []
    for raw in data.get("cases", []):
        cases.append(
            CorpusCase(
                case_id=str(raw["case_id"]),
                case_type=str(raw["case_type"]),
                path=str(raw["path"]),
                license=str(raw.get("license", "unknown")),
                source=str(raw.get("source", "synthetic_or_user_supplied")),
                expected=_expectation_from_dict(raw.get("expected", {})),
                notes=list(raw.get("notes", [])),
            )
        )
    return CorpusManifest(
        name=str(data.get("name", "rosette_corpus")),
        version=str(data.get("version", "0.1.0")),
        cases=cases,
        oak_rules=list(data.get("oak_rules", CorpusManifest("", "", []).oak_rules)),
    )


def load_manifest(path: str | Path) -> CorpusManifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return manifest_from_dict(data)


def validate_manifest(manifest: CorpusManifest, root: str | Path | None = None) -> list[CorpusValidationFinding]:
    root_path = Path(root) if root is not None else None
    findings: list[CorpusValidationFinding] = []
    seen: set[str] = set()
    if not manifest.cases:
        findings.append(CorpusValidationFinding("manifest", "error", "manifest has no cases"))
    for case in manifest.cases:
        if case.case_id in seen:
            findings.append(CorpusValidationFinding(case.case_id, "error", "duplicate case_id"))
        seen.add(case.case_id)
        if case.case_type not in ALLOWED_CASE_TYPES:
            findings.append(CorpusValidationFinding(case.case_id, "error", f"unsupported case_type: {case.case_type}"))
        if case.license.lower() in {"unknown", "restricted", "copyrighted_unknown"} and not case.path.endswith(".txt"):
            findings.append(CorpusValidationFinding(case.case_id, "warning", "non-text case has unknown/restricted license"))
        if root_path is not None and not (root_path / case.path).exists():
            findings.append(CorpusValidationFinding(case.case_id, "error", f"missing file: {case.path}"))
        if case.expected.requires_bboxes and case.case_type in {"clean_text", "paged_text"}:
            findings.append(CorpusValidationFinding(case.case_id, "warning", "bbox requirement on text fixture may be impossible"))
        if case.expected.requires_visual_oak and case.expected.min_equations == 0:
            findings.append(CorpusValidationFinding(case.case_id, "warning", "visual OAK requested but min_equations is zero"))
    return findings


def corpus_quality_score(findings: list[CorpusValidationFinding]) -> float:
    if not findings:
        return 1.0
    penalty = 0.0
    for finding in findings:
        penalty += 0.35 if finding.severity == "error" else 0.1
    return round(max(0.0, 1.0 - penalty), 4)


def create_minimal_corpus(root: str | Path) -> Path:
    root_path = Path(root)
    cases_dir = root_path / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    (cases_dir / "clean_text.txt").write_text("# Clean\n\nWe propose a model.\n\n$$x=y$$\n", encoding="utf-8")
    (cases_dir / "paged_text.txt").write_text(
        "---PAGE 1---\n# Paged\n\nWe show a model.\n\n---PAGE 2---\nEquation:\n\n$$\\frac{dx}{dt}=-kx+u(t)$$\n",
        encoding="utf-8",
    )
    manifest = CorpusManifest(
        name="rosette_minimal_annotated_corpus",
        version="0.1.0",
        cases=[
            CorpusCase(
                case_id="clean_text_001",
                case_type="clean_text",
                path="cases/clean_text.txt",
                license="synthetic",
                expected=CorpusExpectation(min_blocks=1, min_equations=1, min_claims=1),
            ),
            CorpusCase(
                case_id="paged_text_001",
                case_type="paged_text",
                path="cases/paged_text.txt",
                license="synthetic",
                expected=CorpusExpectation(min_blocks=2, min_equations=1, min_claims=1, requires_page_refs=True),
            ),
        ],
    )
    manifest_path = root_path / "corpus_manifest.json"
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path


def validate_corpus(manifest_path: str | Path) -> dict[str, Any]:
    manifest_path = Path(manifest_path)
    manifest = load_manifest(manifest_path)
    findings = validate_manifest(manifest, root=manifest_path.parent)
    return {
        "manifest": str(manifest_path),
        "name": manifest.name,
        "version": manifest.version,
        "case_count": len(manifest.cases),
        "findings": [asdict(finding) for finding in findings],
        "corpus_quality_score": corpus_quality_score(findings),
        "oak_status": "corpus_valid_not_certified" if not any(f.severity == "error" for f in findings) else "corpus_invalid",
        "oak_rules": manifest.oak_rules,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rosette-bench-corpus")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--out", default="rosette_corpus")
    validate = sub.add_parser("validate")
    validate.add_argument("manifest")
    validate.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    if args.command == "init":
        manifest_path = create_minimal_corpus(args.out)
        report = validate_corpus(manifest_path)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    if args.command == "validate":
        report = validate_corpus(args.manifest)
        text = json.dumps(report, indent=2, ensure_ascii=False)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
        print(text)
        return 0 if report["oak_status"] != "corpus_invalid" else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
