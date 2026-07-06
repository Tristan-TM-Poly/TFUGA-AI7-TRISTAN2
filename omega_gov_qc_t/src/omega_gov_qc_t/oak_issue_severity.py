"""Deterministic review-severity policy for Ω-GOV-QC-T issue drafts.

The policy maps local review signals to workflow priorities. It does not produce
findings, decisions or public-authority outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class SeverityDecision:
    """A local review-priority decision."""

    priority: str
    status: str
    reasons: Tuple[str, ...]
    oak_note: str = "Severity is a workflow triage signal, not a final finding."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OAKIssueSeverityPolicy:
    """Assign conservative local issue-draft severity."""

    def dataset_health(self, report: Dict[str, Any]) -> SeverityDecision:
        """Return severity from a DatasetHealthReport-like dict."""

        band = str(report.get("band", "unknown"))
        missing_ratio = _as_float(report.get("missing_ratio"), default=0.0)
        duplicate_ratio = _as_float(report.get("duplicate_ratio"), default=0.0)
        machine_readable = bool(report.get("machine_readable", True))
        reasons = []

        if not machine_readable:
            reasons.append("dataset_not_machine_readable")
        if band in {"blocked", "poor"}:
            reasons.append(f"dataset_band_{band}")
        if missing_ratio > 0.5:
            reasons.append("missing_ratio_above_0_50")
        elif missing_ratio > 0.2:
            reasons.append("missing_ratio_above_0_20")
        if duplicate_ratio > 0.2:
            reasons.append("duplicate_ratio_above_0_20")

        if not machine_readable or band == "blocked" or missing_ratio > 0.5:
            priority = "P0"
            status = "blocked_until_dataset_review"
        elif band == "poor" or missing_ratio > 0.2 or duplicate_ratio > 0.2:
            priority = "P1"
            status = "review_required"
        elif band == "review":
            priority = "P2"
            status = "review_recommended"
        else:
            priority = "P3"
            status = "routine_review"

        return SeverityDecision(priority=priority, status=status, reasons=tuple(reasons or ["no_high_severity_dataset_signal"]))

    def risk_register(self, risks: Dict[str, Any]) -> SeverityDecision:
        """Return severity from a RiskRegister-like export section.

        The policy reads the exported RiskTensor fields when available:
        `band`, `blocks_deployment`, `risk_pressure`, and individual risk axes.
        """

        risk_items = _extract_items(risks)
        quality_report = risks.get("quality_report", {}) if isinstance(risks, dict) else {}
        reasons = []
        max_score = 0
        max_pressure = 0
        high_impact_count = 0
        critical_count = 0
        blocker_count = 0

        quality_blockers = quality_report.get("blockers", []) if isinstance(quality_report, dict) else []
        if quality_blockers:
            blocker_count += len(quality_blockers)
            reasons.append("quality_report_contains_blockers")

        for item in risk_items:
            if not isinstance(item, dict):
                continue
            score = _risk_total(item)
            pressure = int(_as_float(item.get("risk_pressure"), default=float(_risk_pressure(item))))
            band = str(item.get("band", "")).lower()
            blocks_deployment = bool(item.get("blocks_deployment", False))
            max_score = max(max_score, score)
            max_pressure = max(max_pressure, pressure)

            if blocks_deployment:
                blocker_count += 1
            if band == "critical":
                critical_count += 1
            if band == "high" or pressure >= 16 or score >= 20:
                high_impact_count += 1

        if blocker_count:
            reasons.append("risk_register_contains_blocker")
        if critical_count:
            reasons.append("risk_register_contains_critical_band")
        if high_impact_count:
            reasons.append("risk_register_contains_high_impact_items")
        if max_pressure:
            reasons.append(f"max_risk_pressure_{max_pressure}")
        if max_score:
            reasons.append(f"max_risk_total_{max_score}")

        if blocker_count or critical_count:
            priority = "P0"
            status = "blocked_until_risk_review"
        elif high_impact_count or max_pressure >= 16 or max_score >= 20:
            priority = "P1"
            status = "risk_review_required"
        elif risk_items:
            priority = "P2"
            status = "risk_review_recommended"
        else:
            priority = "P3"
            status = "routine_review"

        return SeverityDecision(priority=priority, status=status, reasons=tuple(reasons or ["no_high_severity_risk_signal"]))

    def source_registry(self, sources: Dict[str, Any]) -> SeverityDecision:
        """Return severity from a source-registry-like section."""

        items = _extract_items(sources)
        reasons = []
        if not items:
            return SeverityDecision(priority="P1", status="source_review_required", reasons=("no_sources_exported",))

        missing_locator = 0
        missing_permission = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            if not item.get("locator"):
                missing_locator += 1
            if not item.get("permission"):
                missing_permission += 1
        if missing_locator:
            reasons.append("source_locator_missing")
        if missing_permission:
            reasons.append("source_permission_missing")

        if missing_locator or missing_permission:
            return SeverityDecision(priority="P1", status="source_review_required", reasons=tuple(reasons))
        return SeverityDecision(priority="P3", status="routine_review", reasons=("sources_have_basic_fields",))


def _as_float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_items(section: Any) -> Tuple[Dict[str, Any], ...]:
    if section is None:
        return tuple()
    if isinstance(section, list):
        return tuple(item for item in section if isinstance(item, dict))
    if isinstance(section, dict):
        for key in ("items", "records", "sources", "risks", "risk_tensors"):
            nested = section.get(key)
            if isinstance(nested, list):
                return tuple(item for item in nested if isinstance(item, dict))
            if isinstance(nested, dict):
                return tuple(item for item in nested.values() if isinstance(item, dict))
        if all(isinstance(value, dict) for value in section.values()):
            return tuple(section.values())
    return tuple()


def _risk_pressure(item: Dict[str, Any]) -> int:
    fields = ("legal", "privacy", "security", "fairness", "human_impact")
    return sum(int(_as_float(item.get(field), default=0.0)) for field in fields)


def _risk_total(item: Dict[str, Any]) -> int:
    fields = (
        "legal",
        "privacy",
        "security",
        "fairness",
        "human_impact",
        "reversibility",
        "evidence_quality",
        "public_utility",
    )
    return sum(int(_as_float(item.get(field), default=0.0)) for field in fields)


def severity_json(decision: SeverityDecision) -> str:
    """Serialize one severity decision."""

    return json.dumps(decision.to_dict(), indent=2, sort_keys=True)
