"""Collect local repository state into an Ω action dashboard snapshot.

The collector is intentionally read-only and stdlib-only. It does not call GitHub,
Gmail, the web, or any external system. It scans local repository files and emits a
JSON snapshot that can be passed to dashboard_report_generator.py.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT_MARKERS = (".git", "pyproject.toml", "README.md")


def utc_now_iso() -> str:
    """Return a UTC timestamp suitable for snapshot metadata."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _exists(root: Path, relative: str) -> bool:
    return (root / relative).exists()


def _safe_dirs(root: Path, relative: str) -> list[str]:
    base = root / relative
    if not base.exists() or not base.is_dir():
        return []
    return sorted(path.name for path in base.iterdir() if path.is_dir() and not path.name.startswith("."))


def _safe_files(root: Path, relative: str, suffixes: Iterable[str] = (".md", ".yaml", ".yml", ".json", ".py")) -> list[str]:
    base = root / relative
    if not base.exists():
        return []
    suffix_set = tuple(suffixes)
    if base.is_file():
        return [relative] if base.suffix in suffix_set else []
    files: list[str] = []
    for path in base.rglob("*"):
        if path.is_file() and path.suffix in suffix_set:
            files.append(path.relative_to(root).as_posix())
    return sorted(files)


def collect_demo_packets(root: Path) -> dict[str, Any]:
    packets = _safe_dirs(root, "demo_packets")
    ready = [name for name in packets if (root / "demo_packets" / name / "README.md").exists()]
    seed = [name for name in packets if "seed" in (root / "demo_packets" / name / "README.md").read_text(encoding="utf-8", errors="ignore").lower()] if packets else []
    missing_examples = [
        name for name in packets
        if not (root / "demo_packets" / name / "oak_report_example.md").exists()
        and not (root / "demo_packets" / name / "example.md").exists()
    ]
    return {
        "ready_packets": len(ready),
        "seed_packets": len(seed),
        "missing_examples": len(missing_examples),
        "routed_targets": 0,
        "packet_names": packets,
        "missing_example_packets": missing_examples,
    }


def collect_github_lane(root: Path) -> dict[str, int]:
    workflows = _safe_files(root, ".github/workflows", suffixes=(".yml", ".yaml"))
    tests = _safe_files(root, "tests", suffixes=(".py",))
    return {
        "open_PRs": 0,
        "mergeable_clean_PRs": 0,
        "draft_PRs": 0,
        "pending_checks": 0,
        "repaired_blockers": 0,
        "merged_PRs": 0,
        "workflow_files": len(workflows),
        "test_files": len(tests),
    }


def collect_university_lane(root: Path) -> dict[str, int]:
    route_files = _safe_files(root, "university_outreach/quebec_universities", suffixes=(".yaml", ".yml", ".md"))
    joined = "\n".join(
        (root / file).read_text(encoding="utf-8", errors="ignore")
        for file in route_files[:50]
        if (root / file).exists()
    )
    return {
        "GREEN_EMAIL": joined.count("GREEN_EMAIL"),
        "GREEN_FORM": joined.count("GREEN_FORM"),
        "YELLOW_RESEARCH": joined.count("YELLOW_RESEARCH"),
        "RED_REJECTED": joined.count("RED_REJECTED"),
        "replies_pending_action": joined.count("RESPONSE_ACTION_REQUIRED"),
        "route_files": len(route_files),
    }


def collect_assets(root: Path) -> dict[str, list[str]]:
    docs_assets = _safe_files(root, "docs", suffixes=(".md",))
    orchestration_assets = _safe_files(root, "orchestration", suffixes=(".yaml", ".yml", ".md"))
    code_assets = _safe_files(root, "tools", suffixes=(".py",)) + _safe_files(root, "omega_vtp_t", suffixes=(".py",))
    demo_packets = _safe_dirs(root, "demo_packets")
    return {
        "docs_assets": docs_assets,
        "orchestration_assets": orchestration_assets,
        "code_assets": sorted(code_assets),
        "demo_packets": demo_packets,
    }


def build_next_best_actions(root: Path, assets: dict[str, list[str]], packets: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    if _exists(root, "tools/action_dashboard/dashboard_report_generator.py") and not _exists(root, "tools/action_dashboard/snapshot_collector.py"):
        actions.append({
            "action_id": "add_snapshot_collector",
            "lane": "dashboard",
            "title": "Add dashboard snapshot collector",
            "score": 0.95,
            "decision": "ACT_NOW_INTERNAL_SAFE",
            "expected_output": "JSON snapshot collector",
        })

    if packets.get("missing_examples", 0):
        actions.append({
            "action_id": "complete_seed_packet_examples",
            "lane": "proof_packets",
            "title": "Complete missing proof-packet examples",
            "score": 0.78,
            "decision": "PREPARE_OR_REPAIR",
            "expected_output": "OAK report examples for seed packets",
        })

    if _exists(root, ".github/workflows/action-dashboard-ci.yml"):
        actions.append({
            "action_id": "extend_dashboard_ci_to_snapshot_collector",
            "lane": "github",
            "title": "Extend dashboard CI to snapshot collector",
            "score": 0.83,
            "decision": "PREPARE_OR_REPAIR",
            "expected_output": "CI coverage for snapshot collection",
        })

    return sorted(actions, key=lambda item: float(item.get("score", 0)), reverse=True)


def collect_snapshot(root: str | Path = ".") -> dict[str, Any]:
    """Collect a dashboard snapshot from a local repository root."""

    root_path = Path(root).resolve()
    packets = collect_demo_packets(root_path)
    assets = collect_assets(root_path)
    generated_at = utc_now_iso()

    proof_assets = [
        *assets["docs_assets"],
        *assets["orchestration_assets"],
        *[f"demo_packets/{name}" for name in assets["demo_packets"]],
    ]

    actions_attempted = ["collect_snapshot"]
    safe_actions = ["collect_snapshot"]
    loop_upgrades = ["snapshot_collector"] if _exists(root_path, "tools/action_dashboard/snapshot_collector.py") else []
    assets_created = ["dashboard_snapshot"]
    frictions_burned = ["manual_dashboard_snapshot"]

    snapshot = {
        "dashboard_id": "omega-action-dashboard-local-snapshot",
        "generated_at": generated_at,
        "cycle_window": {"start": generated_at, "end": generated_at},
        "active_loops": [
            {"loop_id": "All-GitHub Action Loop", "cadence": "hourly", "status": "configured"},
            {"loop_id": "University Action Loop", "cadence": "weekly", "status": "configured"},
        ],
        "top_blockers": [],
        "next_best_actions": build_next_best_actions(root_path, assets, packets),
        "lanes": {
            "github": collect_github_lane(root_path),
            "universities": collect_university_lane(root_path),
            "proof_packets": {key: value for key, value in packets.items() if not isinstance(value, list)},
            "assets": {
                "code_assets": len(assets["code_assets"]),
                "docs_assets": len(assets["docs_assets"]),
                "proof_packets": len(assets["demo_packets"]),
                "OAK_reports": len([item for item in assets["docs_assets"] if "OAK" in item.upper()]),
                "route_assets": collect_university_lane(root_path)["route_files"],
                "IP_review_packets": len([item for item in proof_assets if "IP" in item.upper()]),
            },
        },
        "proof_assets": proof_assets,
        "merged_PRs": [],
        "demo_packets": assets["demo_packets"],
        "official_routes": [],
        "actions_attempted": actions_attempted,
        "safe_actions": safe_actions,
        "loop_upgrades": loop_upgrades,
        "assets_created": assets_created,
        "frictions_burned": frictions_burned,
        "M_plus_new": ["local snapshot collector converts repository state into dashboard input"],
        "M_minus_new": [],
        "anti_repetition_rules_added": [],
        "external_action_governor": {
            "internal_auto": ["collect_snapshot"],
            "external_prepared": [],
            "external_approved": [],
            "external_executed": [],
            "blocked_until_approval": [],
        },
    }
    return snapshot


def write_snapshot(root: str | Path, output: str | Path) -> dict[str, Any]:
    snapshot = collect_snapshot(root)
    Path(output).write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect a local Ω action dashboard snapshot.")
    parser.add_argument("--root", default=".", help="Repository root to scan")
    parser.add_argument("--out", default="ACTION_DASHBOARD_SNAPSHOT.json", help="Snapshot JSON output path")
    args = parser.parse_args(argv)
    write_snapshot(args.root, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
