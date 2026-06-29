"""Generate Ω action dashboard reports from JSON snapshots.

This module is intentionally stdlib-only so it can run in lightweight CI and local
OAK review environments without extra dependencies.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


Number = int | float


def load_snapshot(path: str | Path) -> dict[str, Any]:
    """Load a dashboard snapshot JSON file."""

    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("snapshot root must be a JSON object")
    return data


def _as_number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(default)
    if isinstance(value, (int, float)):
        return float(value)
    return float(default)


def _count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return len(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    return 0


def _list(snapshot: Mapping[str, Any], key: str) -> list[Any]:
    value = snapshot.get(key, [])
    return value if isinstance(value, list) else []


def rank_next_best_actions(actions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return actions sorted by descending score, preserving dictionaries."""

    normalized = [dict(action) for action in actions]
    return sorted(normalized, key=lambda item: _as_number(item.get("score")), reverse=True)


def compute_metrics(snapshot: Mapping[str, Any]) -> dict[str, float]:
    """Compute dashboard metrics, honoring provided metric values when present."""

    provided = snapshot.get("metrics", {})
    provided = provided if isinstance(provided, Mapping) else {}

    proof_assets = _count(snapshot.get("proof_assets", []))
    merged_prs = _count(snapshot.get("merged_PRs", []))
    demo_packets = _count(snapshot.get("demo_packets", []))
    official_routes = _count(snapshot.get("official_routes", []))
    documented_failures = _count(snapshot.get("M_minus_new", []))

    proof_capital_default = (
        proof_assets * 5
        + merged_prs * 4
        + demo_packets * 5
        + official_routes * 4
        + documented_failures * 2
    )

    attempted_actions = max(1, _count(snapshot.get("actions_attempted", [])))
    safe_actions = _count(snapshot.get("safe_actions", []))
    upgraded_actions = _count(snapshot.get("loop_upgrades", []))
    assets_created = _count(snapshot.get("assets_created", []))
    frictions_burned = _count(snapshot.get("frictions_burned", []))

    return {
        "proof_capital": _as_number(provided.get("proof_capital"), proof_capital_default),
        "proof_capital_delta": _as_number(provided.get("proof_capital_delta"), proof_capital_default),
        "friction_burn_rate": _as_number(provided.get("friction_burn_rate"), frictions_burned),
        "OAK_safety_ratio": _as_number(provided.get("OAK_safety_ratio"), safe_actions / attempted_actions),
        "loop_upgrade_rate": _as_number(provided.get("loop_upgrade_rate"), upgraded_actions / attempted_actions),
        "asset_conversion_rate": _as_number(provided.get("asset_conversion_rate"), assets_created / attempted_actions),
    }


def normalize_dashboard(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a raw snapshot into a stable dashboard report object."""

    next_best_actions = rank_next_best_actions(_list(snapshot, "next_best_actions"))
    top_blockers = _list(snapshot, "top_blockers")
    lanes = snapshot.get("lanes", {}) if isinstance(snapshot.get("lanes", {}), Mapping) else {}
    governor = snapshot.get("external_action_governor", {})
    governor = governor if isinstance(governor, Mapping) else {}

    return {
        "dashboard_id": snapshot.get("dashboard_id", "omega-action-dashboard"),
        "generated_at": snapshot.get("generated_at", "unknown"),
        "cycle_window": snapshot.get("cycle_window", {}),
        "executive_state": {
            "active_loops": _list(snapshot, "active_loops"),
            "top_blockers": top_blockers,
            "next_best_actions": next_best_actions,
        },
        "lanes": lanes,
        "metrics": compute_metrics(snapshot),
        "memory": {
            "M_plus_new": _list(snapshot, "M_plus_new"),
            "M_minus_new": _list(snapshot, "M_minus_new"),
            "anti_repetition_rules_added": _list(snapshot, "anti_repetition_rules_added"),
        },
        "external_action_governor": governor,
    }


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    header = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def render_markdown(report: Mapping[str, Any]) -> str:
    """Render a normalized dashboard report as Markdown."""

    metrics = report.get("metrics", {}) if isinstance(report.get("metrics", {}), Mapping) else {}
    executive = report.get("executive_state", {}) if isinstance(report.get("executive_state", {}), Mapping) else {}
    memory = report.get("memory", {}) if isinstance(report.get("memory", {}), Mapping) else {}
    governor = report.get("external_action_governor", {})
    governor = governor if isinstance(governor, Mapping) else {}
    lanes = report.get("lanes", {}) if isinstance(report.get("lanes", {}), Mapping) else {}

    lines = [
        f"# Ω Action Dashboard Report — {report.get('dashboard_id', 'unknown')}",
        "",
        f"Generated at: `{report.get('generated_at', 'unknown')}`",
        "",
        "## Metrics",
        "",
        _table(
            ["Metric", "Value"],
            [[key, f"{_as_number(value):.3f}"] for key, value in metrics.items()],
        ),
        "",
        "## Next Best Actions",
        "",
    ]

    actions = executive.get("next_best_actions", []) if isinstance(executive.get("next_best_actions", []), list) else []
    if actions:
        lines.append(
            _table(
                ["Score", "Lane", "Action", "Decision", "Expected output"],
                [
                    [
                        f"{_as_number(action.get('score')):.3f}",
                        action.get("lane", "unknown"),
                        action.get("title", action.get("action_id", "unknown")),
                        action.get("decision", action.get("decision_band", "unknown")),
                        action.get("expected_output", "unknown"),
                    ]
                    for action in actions
                ],
            )
        )
    else:
        lines.append("No next-best actions recorded.")

    lines.extend(["", "## Blockers", ""])
    blockers = executive.get("top_blockers", []) if isinstance(executive.get("top_blockers", []), list) else []
    if blockers:
        lines.append(
            _table(
                ["Class", "Lane", "Safest next action"],
                [
                    [
                        blocker.get("blocker_class", "unknown"),
                        blocker.get("affected_lane", "unknown"),
                        blocker.get("safest_next_action", "unknown"),
                    ]
                    for blocker in blockers
                    if isinstance(blocker, Mapping)
                ],
            )
        )
    else:
        lines.append("No blockers recorded.")

    lines.extend(["", "## Lanes", ""])
    if lanes:
        for lane, lane_state in lanes.items():
            lines.append(f"### {lane}")
            lines.append("")
            if isinstance(lane_state, Mapping):
                rows = [[key, value] for key, value in lane_state.items()]
                lines.append(_table(["Field", "Value"], rows))
            else:
                lines.append(str(lane_state))
            lines.append("")
    else:
        lines.append("No lane data recorded.")

    lines.extend(["", "## M+ / M- Memory", ""])
    lines.append(f"M+ new: `{_count(memory.get('M_plus_new', []))}`")
    lines.append(f"M- new: `{_count(memory.get('M_minus_new', []))}`")
    lines.append(f"Anti-repetition rules added: `{_count(memory.get('anti_repetition_rules_added', []))}`")

    lines.extend(["", "## External Action Governor", ""])
    if governor:
        rows = [[key, _count(value)] for key, value in governor.items()]
        lines.append(_table(["Class", "Count"], rows))
    else:
        lines.append("No external action governor state recorded.")

    lines.extend(["", "## OAK Summary", ""])
    lines.append("Reward safe proof accumulation over raw activity volume.")
    return "\n".join(lines) + "\n"


def write_dashboard_report(
    snapshot_path: str | Path,
    markdown_out: str | Path,
    json_out: str | Path | None = None,
) -> dict[str, Any]:
    """Load a snapshot, write Markdown and optional normalized JSON, return report."""

    snapshot = load_snapshot(snapshot_path)
    report = normalize_dashboard(snapshot)
    Path(markdown_out).write_text(render_markdown(report), encoding="utf-8")
    if json_out is not None:
        Path(json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate an Ω action dashboard report from a JSON snapshot.")
    parser.add_argument("snapshot", help="Path to dashboard snapshot JSON")
    parser.add_argument("--markdown-out", default="ACTION_DASHBOARD_REPORT.md", help="Markdown report output path")
    parser.add_argument("--json-out", default=None, help="Optional normalized JSON output path")
    args = parser.parse_args(argv)
    write_dashboard_report(args.snapshot, args.markdown_out, args.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
