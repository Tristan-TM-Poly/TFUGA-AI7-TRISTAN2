"""Report rendering and serialization for Ω-AI-TRISTAN-LAB v0.2."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .models import BayesAxisScore, IPClassification, OAKReport, RevenuePath, TheoryCard


def to_jsonable(value: Any) -> Any:
    """Recursively convert dataclasses/enums into JSON-safe Python objects."""

    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    return value


class ReportRenderer:
    """Render Ω-AI-Tristan reports to JSON and Markdown."""

    def to_json_text(self, report: dict[str, Any], pretty: bool = True) -> str:
        return json.dumps(to_jsonable(report), ensure_ascii=False, indent=2 if pretty else None)

    def write_json(self, report: dict[str, Any], path: str | Path, pretty: bool = True) -> Path:
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        path_obj.write_text(self.to_json_text(report, pretty=pretty), encoding="utf-8")
        return path_obj

    def to_markdown(self, report: dict[str, Any]) -> str:
        card = report.get("theory_card")
        oak = report.get("oak_report")
        bayes = report.get("bayes_score")
        ip = report.get("ip_classification")
        revenue_paths = report.get("revenue_paths") or []
        bayes_decision = report.get("bayes_decision", "")

        lines: list[str] = ["# Ω-AI-TRISTAN-LAB Report", ""]
        if isinstance(card, TheoryCard):
            lines.extend(self._render_card(card))
        if isinstance(oak, OAKReport):
            lines.extend(self._render_oak(oak))
        if isinstance(bayes, BayesAxisScore):
            lines.extend(self._render_bayes(bayes, str(bayes_decision)))
        if isinstance(ip, IPClassification):
            lines.extend(self._render_ip(ip))
        if revenue_paths and all(isinstance(path, RevenuePath) for path in revenue_paths):
            lines.extend(self._render_revenue(revenue_paths))
        lines.extend([
            "## OAK Reminder",
            "",
            "This report is a decision aid, not proof, legal advice, financial advice, or a guarantee of revenue.",
            "",
        ])
        return "\n".join(lines)

    def write_markdown(self, report: dict[str, Any], path: str | Path) -> Path:
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        path_obj.write_text(self.to_markdown(report), encoding="utf-8")
        return path_obj

    @staticmethod
    def _render_card(card: TheoryCard) -> list[str]:
        return [
            "## TheoryCard",
            "",
            f"- **Name:** {card.name}",
            f"- **Purpose:** {card.purpose}",
            f"- **OAK status:** {card.oak_status.value}",
            f"- **Next action:** {card.next_action}",
            "",
            "### Inputs",
            *[f"- {item}" for item in card.inputs],
            "",
            "### Outputs",
            *[f"- {item}" for item in card.outputs],
            "",
            "### Tests",
            *[f"- {item}" for item in card.tests],
            "",
            "### Risks",
            *[f"- {item}" for item in card.risks],
            "",
        ]

    @staticmethod
    def _render_oak(oak: OAKReport) -> list[str]:
        return [
            "## OAK Report",
            "",
            f"- **Status:** {oak.status.value}",
            f"- **Score:** {oak.score}",
            f"- **Next action:** {oak.next_action}",
            "",
            "### Strengths",
            *[f"- {item}" for item in oak.strengths],
            "",
            "### Missing evidence",
            *[f"- {item}" for item in oak.missing_evidence],
            "",
            "### Negative memory M⁻",
            *[f"- {item}" for item in oak.negative_memory],
            "",
        ]

    @staticmethod
    def _render_bayes(score: BayesAxisScore, decision: str) -> list[str]:
        rows = [
            ("truth", score.truth),
            ("utility", score.utility),
            ("fertility", score.fertility),
            ("testability", score.testability),
            ("safety", score.safety),
            ("novelty", score.novelty),
            ("revenue", score.revenue),
            ("compressibility", score.compressibility),
        ]
        return [
            "## Bayes-Tristan Score",
            "",
            f"- **Decision:** {decision}",
            f"- **Weighted total:** {score.weighted_total():.3f}",
            "",
            "| Axis | Score |",
            "|---|---:|",
            *[f"| {axis} | {value:.3f} |" for axis, value in rows],
            "",
        ]

    @staticmethod
    def _render_ip(ip: IPClassification) -> list[str]:
        return [
            "## IP Classification",
            "",
            f"- **Label:** {ip.label}",
            f"- **Confidence:** {ip.confidence}",
            f"- **Next action:** {ip.next_action}",
            "",
            "### Rationale",
            *[f"- {item}" for item in ip.rationale],
            "",
            "### Safe public actions",
            *[f"- {item}" for item in ip.safe_public_actions],
            "",
            "### Blocked actions",
            *[f"- {item}" for item in ip.blocked_actions],
            "",
        ]

    @staticmethod
    def _render_revenue(paths: list[RevenuePath]) -> list[str]:
        lines = [
            "## Revenue Map",
            "",
            "| Path | Customer | Validation test | Confidence |",
            "|---|---|---|---:|",
        ]
        for path in paths:
            lines.append(
                f"| {path.name} | {path.customer} | {path.validation_test} | {path.confidence:.2f} |"
            )
        lines.append("")
        return lines
