#!/usr/bin/env python3
"""Zero-touch OAK corpus analyzer seed.

This script indexes local text-like repository files, extracts claim-like lines,
assigns conservative initial OAK statuses, and writes three outputs:

- report.md
- m_minus.jsonl
- canon.yml

It is intentionally dependency-free. It is not a proof engine. It is a first
friction layer that prevents fertile claims from silently becoming certified.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".py",
    ".yaml",
    ".yml",
    ".json",
    ".tex",
    ".rst",
}

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
}

CLAIM_PATTERNS = [
    re.compile(r"\b(th[eé]or[eè]me|axiome|claim|postulat|conjecture)\b", re.I),
    re.compile(r"\b(proves?|prouve|d[eé]montre|valid[eé]|certifi[eé]|mesur[eé])\b", re.I),
    re.compile(r"\b(always|jamais|toujours|parfait|z[eé]ro|canon|OAK-[0-9])\b", re.I),
    re.compile(r"\b(SNR|RMSE|R2|MAE|F1|accuracy|benchmark|baseline)\b", re.I),
]

M_MINUS_PATTERNS = [
    re.compile(r"\b(r[eé]sidu z[eé]ro|0\.0+%|parfait|absolute|impossible de|prouv[eé] sans test)\b", re.I),
    re.compile(r"\b(OAK-7|CANON|CERTIFIED)\b.*\b(sans|without|no)\b.*\b(test|preuve|evidence|mesure)\b", re.I),
]

STATUS_KEYWORDS = [
    ("CERTIFIED", re.compile(r"\b(certified|certifi[eé]|OAK-8|CANON)\b", re.I)),
    ("MEASURED", re.compile(r"\b(measured|mesur[eé]|donn[eé]es r[eé]elles|instrumental)\b", re.I)),
    ("SIMULATED", re.compile(r"\b(simulated|simulation|synthetic|synth[eé]tique)\b", re.I)),
    ("SIMULATION_READY", re.compile(r"\b(protocol|protocole|benchmark|baseline|testable|OAK-3)\b", re.I)),
    ("FORMALIZED", re.compile(r"\b(definition|d[eé]finition|theorem|th[eé]or[eè]me|axiom|axiome|equation|[A-Z]_H\s*=)\b", re.I)),
]


@dataclass
class FileRecord:
    path: str
    sha256: str
    chars: int
    lines: int


@dataclass
class ClaimRecord:
    source: str
    line: int
    text: str
    status: str
    risk: str
    next_action: str


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_EXTENSIONS:
            yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def infer_status(text: str) -> str:
    for status, pattern in STATUS_KEYWORDS:
        if pattern.search(text):
            return status
    return "CONCEPT"


def infer_risk(text: str) -> str:
    for pattern in M_MINUS_PATTERNS:
        if pattern.search(text):
            return "M_MINUS_CANDIDATE"
    if re.search(r"\b(perfect|parfait|zero|z[eé]ro|always|toujours)\b", text, re.I):
        return "OVERCLAIM_RISK"
    if re.search(r"\b(OAK-7|OAK-8|canon|certified|certifi[eé])\b", text, re.I):
        return "CERTIFICATION_RISK"
    return "NORMAL"


def next_action_for(status: str, risk: str) -> str:
    if risk != "NORMAL":
        return "Create OAKReport with evidence, failure condition, and downgrade if needed."
    if status in {"CERTIFIED", "MEASURED"}:
        return "Attach source data, reproduction instructions, and external evidence."
    if status == "SIMULATED":
        return "Add baseline comparison and mark as not measured."
    if status == "SIMULATION_READY":
        return "Run the minimal test and write residue."
    if status == "FORMALIZED":
        return "Add example, counterexample, and executable test."
    return "Convert into module card or leave as concept."


def extract_claims(path: Path, root: Path, text: str) -> list[ClaimRecord]:
    claims: list[ClaimRecord] = []
    rel = path.relative_to(root).as_posix()
    for idx, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or len(stripped) < 20:
            continue
        if any(pattern.search(stripped) for pattern in CLAIM_PATTERNS):
            status = infer_status(stripped)
            risk = infer_risk(stripped)
            claims.append(
                ClaimRecord(
                    source=rel,
                    line=idx,
                    text=stripped[:500],
                    status=status,
                    risk=risk,
                    next_action=next_action_for(status, risk),
                )
            )
    return claims


def write_report(out_dir: Path, files: list[FileRecord], claims: list[ClaimRecord]) -> None:
    status_counts: dict[str, int] = {}
    risk_counts: dict[str, int] = {}
    for claim in claims:
        status_counts[claim.status] = status_counts.get(claim.status, 0) + 1
        risk_counts[claim.risk] = risk_counts.get(claim.risk, 0) + 1

    lines = [
        "# OAK Corpus Report",
        "",
        f"Generated: {_dt.datetime.utcnow().isoformat(timespec='seconds')}Z",
        "",
        "## Summary",
        "",
        f"- Files indexed: {len(files)}",
        f"- Claim-like lines: {len(claims)}",
        f"- M_MINUS candidates: {risk_counts.get('M_MINUS_CANDIDATE', 0)}",
        f"- Overclaim risks: {risk_counts.get('OVERCLAIM_RISK', 0)}",
        "",
        "## Status counts",
        "",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"- {status}: {count}")

    lines.extend(["", "## Top risky claims", ""])
    risky = [c for c in claims if c.risk != "NORMAL"][:50]
    for claim in risky:
        lines.extend(
            [
                f"### {claim.source}:{claim.line}",
                "",
                f"- status: `{claim.status}`",
                f"- risk: `{claim.risk}`",
                f"- next_action: {claim.next_action}",
                "",
                "> " + claim.text.replace("\n", " "),
                "",
            ]
        )

    out_dir.joinpath("report.md").write_text("\n".join(lines), encoding="utf-8")


def write_m_minus(out_dir: Path, claims: list[ClaimRecord]) -> None:
    with out_dir.joinpath("m_minus.jsonl").open("w", encoding="utf-8") as fh:
        for claim in claims:
            if claim.risk == "NORMAL":
                continue
            entry = {
                "failure_id": f"AUTO-{sha256_text(claim.source + str(claim.line) + claim.text)[:12]}",
                "source": claim.source,
                "line": claim.line,
                "failed_claim": claim.text,
                "risk": claim.risk,
                "guardrail": "Fertile claims cannot be promoted without evidence, attack, residue, and reuse.",
                "next_test": claim.next_action,
            }
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def write_canon_seed(out_dir: Path, claims: list[ClaimRecord]) -> None:
    selected = [c for c in claims if c.status in {"FORMALIZED", "SIMULATION_READY", "SIMULATED", "MEASURED", "CERTIFIED"}][:100]
    lines = [
        "# Generated canon seed. Review manually before trusting.",
        "registry:",
        f"  generated_at: \"{_dt.datetime.utcnow().isoformat(timespec='seconds')}Z\"",
        "  rule: \"No canon without definition, evidence, attack, residue and reuse.\"",
        "claims:",
    ]
    for i, claim in enumerate(selected, start=1):
        safe_text = claim.text.replace('"', "'")
        lines.extend(
            [
                f"  - id: AUTO_CLAIM_{i:04d}",
                f"    source: \"{claim.source}\"",
                f"    line: {claim.line}",
                f"    status: \"{claim.status}\"",
                f"    risk: \"{claim.risk}\"",
                f"    text: \"{safe_text}\"",
                f"    next_action: \"{claim.next_action}\"",
            ]
        )
    out_dir.joinpath("canon.yml").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a corpus and emit OAK seed reports.")
    parser.add_argument("root", nargs="?", default=".", help="Corpus/repository root to analyze")
    parser.add_argument("--out", default="oak_out", help="Output directory")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    files: list[FileRecord] = []
    claims: list[ClaimRecord] = []

    for path in iter_files(root):
        text = read_text(path)
        rel = path.relative_to(root).as_posix()
        files.append(FileRecord(path=rel, sha256=sha256_text(text), chars=len(text), lines=text.count("\n") + 1))
        claims.extend(extract_claims(path, root, text))

    out_dir.joinpath("files.json").write_text(
        json.dumps([asdict(record) for record in files], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    out_dir.joinpath("claims.json").write_text(
        json.dumps([asdict(record) for record in claims], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_report(out_dir, files, claims)
    write_m_minus(out_dir, claims)
    write_canon_seed(out_dir, claims)

    print(f"Indexed {len(files)} files")
    print(f"Extracted {len(claims)} claim-like lines")
    print(f"Wrote outputs to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
