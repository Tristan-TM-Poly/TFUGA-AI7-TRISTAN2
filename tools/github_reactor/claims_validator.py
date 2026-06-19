#!/usr/bin/env python3
"""Validate the GitHub Reactor claims registry.

The registry is JSON Lines. Each claim must carry status, evidence, residue,
and a next test so repository statements remain reviewable and comparable.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
from dataclasses import dataclass, asdict

REQUIRED_FIELDS = {"id", "claim", "domain", "oak_status", "evidence", "residue", "next_test"}
ALLOWED_STATUS = {"CANON", "FERTILE", "OAK_TEST", "REPAIR", "M_MINUS", "ARCHIVE"}


@dataclass
class ClaimFinding:
    severity: str
    item: str
    message: str


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def validate_claims(path: pathlib.Path) -> list[ClaimFinding]:
    findings: list[ClaimFinding] = []
    if not path.exists():
        return [ClaimFinding("error", str(path), "claims registry missing")]
    seen: set[str] = set()
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        return [ClaimFinding("error", str(path), "claims registry empty")]
    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            findings.append(ClaimFinding("error", f"line {line_no}", f"invalid JSON: {exc}"))
            continue
        claim_id = str(item.get("id", f"line {line_no}"))
        missing = sorted(REQUIRED_FIELDS - set(item))
        if missing:
            findings.append(ClaimFinding("error", claim_id, f"missing fields: {', '.join(missing)}"))
        if claim_id in seen:
            findings.append(ClaimFinding("error", claim_id, "duplicate claim id"))
        seen.add(claim_id)
        status = item.get("oak_status")
        if status not in ALLOWED_STATUS:
            findings.append(ClaimFinding("error", claim_id, f"invalid oak_status: {status}"))
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            findings.append(ClaimFinding("error", claim_id, "evidence must be a non-empty list"))
        residue = item.get("residue")
        if not isinstance(residue, list):
            findings.append(ClaimFinding("error", claim_id, "residue must be a list"))
        next_test = item.get("next_test")
        if not isinstance(next_test, str) or not next_test.strip():
            findings.append(ClaimFinding("error", claim_id, "next_test must be a non-empty string"))
    return findings


def write_reports(out: pathlib.Path, findings: list[ClaimFinding]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    error_count = sum(1 for item in findings if item.severity == "error")
    warning_count = sum(1 for item in findings if item.severity == "warning")
    payload = {
        "generated_at": utc_now(),
        "status": "pass" if error_count == 0 else "fail",
        "error_count": error_count,
        "warning_count": warning_count,
        "findings": [asdict(item) for item in findings],
    }
    (out / "claims_validation_report.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# GitHub Reactor Claims Validation",
        "",
        f"Generated: `{payload['generated_at']}`",
        f"Status: `{payload['status']}`",
        f"Errors: `{error_count}`",
        f"Warnings: `{warning_count}`",
        "",
    ]
    if findings:
        lines.append("## Findings")
        lines.append("")
        for finding in findings:
            lines.append(f"- **{finding.severity}** `{finding.item}` — {finding.message}")
    else:
        lines.append("No validation findings.")
    (out / "CLAIMS_VALIDATION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--claims", default="claims/github_reactor_claims.jsonl")
    parser.add_argument("--out", default="reports/github-autonomous-reactor")
    args = parser.parse_args()
    root = pathlib.Path(args.repo_root).resolve()
    findings = validate_claims(root / args.claims)
    write_reports(root / args.out, findings)
    error_count = sum(1 for item in findings if item.severity == "error")
    print(json.dumps({"status": "pass" if error_count == 0 else "fail", "findings": len(findings), "out": args.out}, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
