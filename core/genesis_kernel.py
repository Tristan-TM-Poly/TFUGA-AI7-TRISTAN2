#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: Guarded Auto-Genesis Kernel

Purpose
-------
This kernel operationalizes the OMEGA-FFWT-HAC-CVCD-ASP-MAX canon in a guarded,
falsifiable way:

1. Read the repository's theory/prototype corpus.
2. Run the OAK benchmark prototype when available.
3. Produce a machine-readable registry: CANON / FERTILE / M_MINUS.
4. Produce a Markdown research report and improvement queue.
5. Never rewrite source code autonomously; only write reports/auto_genesis/*.

This is intentional: OAK autonomy is allowed to measure, report, and queue
improvements, but direct code self-modification remains gated by human review or
explicit future tooling.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "auto_genesis"
OAK_REPORT_FROM_BENCH = ROOT / "omega_max_oak_report.json"
PROTOTYPE = ROOT / "prototypes" / "omega_max_benchmark.py"
THEORY_DIR = ROOT / "docs" / "theories"

CANON_THRESHOLD = 80.0
FERTILE_THRESHOLD = 55.0


@dataclass
class GenesisFinding:
    name: str
    category: str
    status: str
    evidence: Dict[str, Any]
    next_action: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_report_dir() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def run_command(command: List[str], cwd: Path) -> Dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-12000:],
        "stderr": completed.stderr[-12000:],
    }


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive report path
        return {"error": f"failed to parse {path}: {exc}"}


def list_theory_files() -> List[Dict[str, Any]]:
    if not THEORY_DIR.exists():
        return []
    files: List[Dict[str, Any]] = []
    for path in sorted(THEORY_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        title = next((line.strip("# ").strip() for line in lines if line.startswith("#")), path.name)
        files.append({
            "path": str(path.relative_to(ROOT)),
            "title": title,
            "bytes": path.stat().st_size,
            "lines": len(lines),
            "mentions_oak": "OAK" in text,
            "mentions_cvcd": "CVCD" in text,
            "mentions_ffwt": "FFWT" in text,
        })
    return files


def classify_oak_score(score: float) -> str:
    if score >= CANON_THRESHOLD:
        return "CANON"
    if score >= FERTILE_THRESHOLD:
        return "FERTILE"
    return "M_MINUS"


def run_oak_benchmark() -> Dict[str, Any]:
    if not PROTOTYPE.exists():
        return {
            "available": False,
            "run": None,
            "report": None,
            "note": "prototypes/omega_max_benchmark.py not found",
        }

    run = run_command([sys.executable, str(PROTOTYPE.relative_to(ROOT))], cwd=ROOT)
    report = read_json(OAK_REPORT_FROM_BENCH)
    return {
        "available": True,
        "run": run,
        "report": report,
    }


def extract_findings(theories: List[Dict[str, Any]], benchmark: Dict[str, Any]) -> List[GenesisFinding]:
    findings: List[GenesisFinding] = []

    if theories:
        findings.append(GenesisFinding(
            name="Theory corpus integrity",
            category="canon",
            status="CANON",
            evidence={
                "theory_files": len(theories),
                "ffwt_files": sum(1 for item in theories if item["mentions_ffwt"]),
                "cvcd_files": sum(1 for item in theories if item["mentions_cvcd"]),
                "oak_files": sum(1 for item in theories if item["mentions_oak"]),
            },
            next_action="Keep theories linked to executable benchmarks and ablation reports.",
        ))
    else:
        findings.append(GenesisFinding(
            name="Theory corpus integrity",
            category="canon",
            status="M_MINUS",
            evidence={"theory_files": 0},
            next_action="Add docs/theories/*.md canon files before claiming theory-to-code closure.",
        ))

    report = benchmark.get("report") if benchmark else None
    if isinstance(report, dict) and "results" in report:
        for result in report.get("results", []):
            score = float(result.get("oak_score", 0.0))
            status = classify_oak_score(score)
            findings.append(GenesisFinding(
                name=f"{result.get('benchmark', 'unknown')} — {result.get('relation_type', 'unknown')}",
                category="benchmark",
                status=status,
                evidence={
                    "oak_score": score,
                    "errors": result.get("errors", {}),
                    "extracted": result.get("extracted", {}),
                    "ground_truth": result.get("ground_truth", {}),
                    "notes": result.get("notes", ""),
                },
                next_action=(
                    "Promote to regression test and compare against FFT/STFT/CWT baselines."
                    if status == "CANON" else
                    "Improve estimator robustness or move invariant to M_MINUS with failure signature."
                ),
            ))
    else:
        status = "M_MINUS" if benchmark.get("available") else "FERTILE"
        findings.append(GenesisFinding(
            name="Executable OAK benchmark",
            category="benchmark",
            status=status,
            evidence={
                "available": benchmark.get("available"),
                "returncode": (benchmark.get("run") or {}).get("returncode"),
                "stderr": (benchmark.get("run") or {}).get("stderr"),
            },
            next_action="Fix benchmark execution and require JSON OAK report generation.",
        ))

    return findings


def improvement_queue(findings: Iterable[GenesisFinding]) -> List[Dict[str, Any]]:
    queue: List[Dict[str, Any]] = []
    for finding in findings:
        if finding.category == "benchmark" and finding.status == "CANON":
            queue.append({
                "priority": "P0",
                "item": f"Freeze {finding.name} as regression benchmark",
                "rationale": "CANON OAK score reached; future code must not regress this result.",
                "suggested_file": "tests/test_omega_max_benchmark.py",
            })
        elif finding.status == "M_MINUS":
            queue.append({
                "priority": "P1",
                "item": f"Investigate rejected finding: {finding.name}",
                "rationale": "Rejected or failed invariants must be stored as negative memory.",
                "suggested_file": "reports/auto_genesis/m_minus_registry.json",
            })

    queue.append({
        "priority": "P0",
        "item": "Replace Haar/analytic surrogate with true adaptive FFWT core",
        "rationale": "Current prototype is executable but not yet the full fractal wavelet transform.",
        "suggested_file": "core/ffwt_core.py",
    })
    queue.append({
        "priority": "P1",
        "item": "Add baseline comparison suite: FFT, STFT, DWT/CWT, PCA/SVD",
        "rationale": "OAK requires measurable gains against standard methods.",
        "suggested_file": "prototypes/baselines.py",
    })
    queue.append({
        "priority": "P1",
        "item": "Add ablation matrix R/C/H/O/S16",
        "rationale": "Hyperalgebraic claims must beat simpler algebras before canonization.",
        "suggested_file": "prototypes/algebra_ablation.py",
    })
    return queue


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines: List[str] = []
    lines.append("# TTM Auto-Genesis OAK Report")
    lines.append("")
    lines.append(f"Generated: `{payload['generated_at']}`")
    lines.append("")
    lines.append("## Verdict summary")
    lines.append("")
    for key in ["CANON", "FERTILE", "M_MINUS"]:
        lines.append(f"- **{key}**: {payload['summary'].get(key, 0)}")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    for finding in payload["findings"]:
        lines.append(f"### {finding['name']}")
        lines.append("")
        lines.append(f"- Category: `{finding['category']}`")
        lines.append(f"- Status: `{finding['status']}`")
        lines.append(f"- Next action: {finding['next_action']}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(finding["evidence"], indent=2, ensure_ascii=False, sort_keys=True))
        lines.append("```")
        lines.append("")
    lines.append("## Improvement queue")
    lines.append("")
    for item in payload["improvement_queue"]:
        lines.append(f"- **{item['priority']}** — {item['item']}")
        lines.append(f"  - Rationale: {item['rationale']}")
        lines.append(f"  - Suggested file: `{item['suggested_file']}`")
    lines.append("")
    lines.append("## Guardrails")
    lines.append("")
    lines.append("This workflow is intentionally guarded: it writes reports only. It does not autonomously rewrite source code.")
    lines.append("Future self-modifying behavior must be implemented through pull requests, tests, and explicit review gates.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> Dict[str, Any]:
    ensure_report_dir()
    theories = list_theory_files()
    benchmark = run_oak_benchmark()
    findings = extract_findings(theories, benchmark)

    summary = {"CANON": 0, "FERTILE": 0, "M_MINUS": 0}
    for finding in findings:
        summary[finding.status] = summary.get(finding.status, 0) + 1

    payload: Dict[str, Any] = {
        "system": "TTM-TFUGA-AI7-TRISTAN2 Guarded Auto-Genesis",
        "generated_at": now_iso(),
        "root": str(ROOT),
        "summary": summary,
        "theories": theories,
        "benchmark_run": benchmark.get("run"),
        "findings": [asdict(item) for item in findings],
        "improvement_queue": improvement_queue(findings),
        "guardrails": {
            "writes_source_code": False,
            "writes_reports_only": True,
            "allowed_output_dir": str(REPORT_DIR.relative_to(ROOT)),
            "requires_human_review_for_code_changes": True,
        },
    }

    write_json(REPORT_DIR / "auto_genesis_report.json", payload)
    write_markdown(REPORT_DIR / "AUTO_GENESIS_REPORT.md", payload)

    m_minus = [item for item in payload["findings"] if item["status"] == "M_MINUS"]
    write_json(REPORT_DIR / "m_minus_registry.json", {"generated_at": payload["generated_at"], "items": m_minus})

    print(json.dumps({
        "generated_at": payload["generated_at"],
        "summary": summary,
        "report_dir": str(REPORT_DIR.relative_to(ROOT)),
        "guarded": True,
    }, indent=2, ensure_ascii=False, sort_keys=True))
    return payload


if __name__ == "__main__":
    main()
