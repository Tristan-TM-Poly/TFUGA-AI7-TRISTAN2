from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .models import Finding, stable_digest


def _finding(category: str, severity: str, message: str, evidence: str) -> Finding:
    return Finding(
        finding_id=f"FIND-{stable_digest((category, severity, message, evidence))[:16].upper()}",
        category=category,
        severity=severity,
        message=message,
        evidence=evidence,
    )


def audit_source(path: str | Path) -> tuple[Finding, ...]:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8", errors="replace")
    findings: list[Finding] = []
    if file_path.suffix == ".py":
        if re.search(r"\bassert\s+True\b", text):
            findings.append(_finding("trivial_assertion", "error", "test contains `assert True`", file_path.as_posix()))
        if "pytest.skip(" in text and "reason=" not in text:
            findings.append(_finding("unexplained_skip", "warning", "pytest.skip lacks an explicit reason", file_path.as_posix()))
        if re.search(r"except\s+Exception\s*:\s*pass", text, flags=re.MULTILINE):
            findings.append(_finding("hidden_failure", "error", "broad exception is silently ignored", file_path.as_posix()))
    if file_path.suffix in {".yml", ".yaml"}:
        if re.search(r"continue-on-error:\s*true", text, flags=re.IGNORECASE):
            findings.append(_finding("hidden_failure", "error", "workflow uses continue-on-error: true", file_path.as_posix()))
        if re.search(r"permissions:\s*write-all", text, flags=re.IGNORECASE):
            findings.append(_finding("excessive_permissions", "error", "workflow requests write-all permissions", file_path.as_posix()))
        for match in re.finditer(r"uses:\s*([^\s]+)", text):
            ref = match.group(1)
            if "@" in ref and not re.search(r"@[0-9a-fA-F]{40}$", ref):
                findings.append(_finding("unpinned_action", "warning", "workflow action is not pinned to a full commit SHA", ref))
    return tuple(findings)


def evidence_quality(findings: Iterable[Finding], *, dimensions: dict[str, float]) -> dict[str, float | str]:
    penalties = sum(0.15 if item.severity == "error" else 0.05 for item in findings)
    required = ("claim_alignment", "reproducibility", "adversarial_coverage", "platform_coverage", "mutation_resistance", "provenance")
    normalized = {key: max(0.0, min(1.0, float(dimensions.get(key, 0.0)))) for key in required}
    score = max(0.0, sum(normalized.values()) / len(required) - penalties)
    return {
        **normalized,
        "penalty": round(penalties, 4),
        "score": round(score, 4),
        "interpretation": "heuristic evidence-quality score, not a probability of correctness",
    }
