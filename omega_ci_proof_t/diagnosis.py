from __future__ import annotations

import re
from typing import Mapping

from .models import FailureDiagnostic, stable_digest


def diagnose_pytest_log(text: str, *, mminus_patterns: Mapping[str, str] | None = None) -> FailureDiagnostic:
    failing = tuple(sorted(set(re.findall(r"FAILED\s+([^\s]+)", text))))
    lowered = text.lower()
    if "syntaxerror" in lowered:
        failure_class, stage, confidence = "syntax_regression", "collection", 0.95
    elif "modulenotfounderror" in lowered or "importerror" in lowered:
        failure_class, stage, confidence = "dependency_or_import_regression", "collection", 0.9
    elif "timeout" in lowered:
        failure_class, stage, confidence = "timeout_or_nontermination", "execution", 0.82
    elif "assertionerror" in lowered or failing:
        failure_class, stage, confidence = "deterministic_test_regression", "test", 0.86
    else:
        failure_class, stage, confidence = "unclassified_failure", "unknown", 0.35

    suspected: list[str] = []
    proposed: list[str] = ["reproduce the smallest failing test", "inspect the changed-path impact closure"]
    minimal: dict[str, str] = {}
    for pattern, cause in (mminus_patterns or {}).items():
        if pattern.lower() in lowered:
            suspected.append(cause)
            minimal["matched_pattern"] = pattern
            proposed.append("apply the corresponding M-minus regression rule")
    if ".github" in text and "github/workflows" in text:
        suspected.append("path normalization may have removed the leading dot")
        proposed.append("verify exact './' prefix removal instead of generic lstrip")
    if not suspected:
        suspected.append("cause not isolated from available log evidence")
    payload = (failure_class, stage, failing, tuple(suspected), minimal)
    return FailureDiagnostic(
        diagnostic_id=f"DIAG-{stable_digest(payload)[:16].upper()}",
        failure_class=failure_class,
        stage=stage,
        failing_tests=failing,
        suspected_causes=tuple(suspected),
        minimal_reproduction=minimal,
        proposed_actions=tuple(dict.fromkeys(proposed)),
        confidence=confidence,
    )
