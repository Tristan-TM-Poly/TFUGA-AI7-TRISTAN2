"""Evidence fusion and prioritization for Ω-ACTIONS-T∞."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .analyzer import analyze_repository
from .delta_ci import plan_delta
from .telemetry import analyze_telemetry


def _load_json(path: str | Path | None) -> Any | None:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_evidence_bundle(
    root: str | Path,
    *,
    changed_files: list[str] | None = None,
    telemetry_payload: Any | None = None,
    event: str = "pull_request",
) -> dict[str, Any]:
    """Fuse structural, impact and empirical evidence into ranked targets."""
    static = analyze_repository(root)
    delta = plan_delta(root, changed_files or [], event=event) if changed_files is not None else None
    telemetry = analyze_telemetry(telemetry_payload) if telemetry_payload is not None else None

    delta_by_path = {row["workflow"]: row for row in (delta or {}).get("workflows", [])}
    telemetry_by_name = {row["name"]: row for row in (telemetry or {}).get("workflows", [])}
    candidates: list[dict[str, Any]] = []

    for workflow in static.get("workflows", []):
        path = workflow["path"]
        name = workflow.get("name") or path
        delta_row = delta_by_path.get(path)
        tele = telemetry_by_name.get(name)
        run_count = int((tele or {}).get("run_count") or 0)
        duration_p95 = ((tele or {}).get("duration_seconds") or {}).get("p95")
        failure_rate = (tele or {}).get("failure_rate_completed")
        broad = bool(delta_row and delta_row.get("decision") == "RUN_BROAD_UNROUTED")
        rec_count = len(workflow.get("recommendations") or [])

        empirical_weight = max(run_count, 1)
        duration_weight = max(float(duration_p95 or 1.0), 1.0)
        risk_weight = 1.0 + float(failure_rate or 0.0)
        routing_weight = 2.0 if broad else 1.0
        structural_weight = 1.0 + min(rec_count, 8) * 0.10
        priority_score = round(
            empirical_weight * duration_weight * risk_weight * routing_weight * structural_weight,
            3,
        )

        candidates.append({
            "workflow": path,
            "name": name,
            "priority_score": priority_score,
            "run_count_sample": run_count,
            "duration_p95_seconds": duration_p95,
            "failure_rate_completed": failure_rate,
            "delta_decision": delta_row.get("decision") if delta_row else None,
            "broad_unrouted": broad,
            "static_recommendation_count": rec_count,
            "static_structural_depth": workflow.get("structural_depth"),
        })

    candidates.sort(key=lambda row: (-row["priority_score"], row["workflow"]))
    evidence_state = "STATIC_ONLY"
    if delta is not None:
        evidence_state = "STATIC_PLUS_DELTA"
    if telemetry is not None:
        evidence_state = "STATIC_PLUS_TELEMETRY"
    if delta is not None and telemetry is not None:
        evidence_state = "MEASURED_BASELINE_READY"

    return {
        "schema": "omega-actions-evidence/v0.35",
        "evidence_state": evidence_state,
        "static": static,
        "delta": delta,
        "telemetry": telemetry,
        "optimization_candidates": candidates,
        "top_candidates": candidates[:25],
        "oak_gates": {
            "static_structure_available": True,
            "delta_evidence_available": delta is not None,
            "telemetry_available": telemetry is not None,
            "automatic_rewrite_authorized": False,
            "measured_before_after_required_for_promotion": True,
        },
        "oak_limits": [
            "Priority score ranks investigation targets; it is not a speedup prediction.",
            "Telemetry workflow names may not uniquely map to files; unmatched runs remain evidence debt.",
            "Broad-trigger status increases priority but never authorizes removing a required check.",
            "Automatic workflow rewriting remains disabled until before/after evidence and rollback gates exist.",
        ],
    }


def render_markdown(bundle: dict[str, Any]) -> str:
    lines = [
        "# Ω-ACTIONS-T∞ — Evidence Bundle",
        "",
        f"- Evidence state: **{bundle['evidence_state']}**",
        f"- Workflows ranked: **{len(bundle['optimization_candidates'])}**",
        "",
        "## Highest-priority optimization targets",
        "",
    ]
    for row in bundle["top_candidates"][:20]:
        lines.append(
            f"- `{row['workflow']}` — score={row['priority_score']}, "
            f"sample_runs={row['run_count_sample']}, p95={row['duration_p95_seconds']}s, "
            f"delta={row['delta_decision']}, static_findings={row['static_recommendation_count']}"
        )
    lines += ["", "## OAK gates", ""]
    for key, value in bundle["oak_gates"].items():
        lines.append(f"- `{key}`: **{value}**")
    lines += ["", "## OAK limits", ""]
    lines.extend(f"- {item}" for item in bundle["oak_limits"])
    return "\n".join(lines) + "\n"


def write_bundle(
    root: str | Path,
    *,
    changed_files: list[str] | None = None,
    telemetry_payload: Any | None = None,
    event: str = "pull_request",
    json_out: str | Path | None = None,
    markdown_out: str | Path | None = None,
) -> dict[str, Any]:
    bundle = build_evidence_bundle(root, changed_files=changed_files, telemetry_payload=telemetry_payload, event=event)
    if json_out:
        Path(json_out).write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if markdown_out:
        Path(markdown_out).write_text(render_markdown(bundle), encoding="utf-8")
    return bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-actions-evidence", description="Fuse static, delta and telemetry evidence.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--changed-files")
    parser.add_argument("--telemetry")
    parser.add_argument("--event", choices=("pull_request", "push"), default="pull_request")
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    parser.add_argument("--format", choices=("summary", "json", "markdown"), default="summary")
    args = parser.parse_args(argv)

    changed = None
    if args.changed_files:
        changed = [line.strip() for line in Path(args.changed_files).read_text(encoding="utf-8").splitlines() if line.strip()]
    telemetry_payload = _load_json(args.telemetry)
    bundle = write_bundle(
        args.root,
        changed_files=changed,
        telemetry_payload=telemetry_payload,
        event=args.event,
        json_out=args.json_out,
        markdown_out=args.markdown_out,
    )
    if args.format == "json":
        print(json.dumps(bundle, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(render_markdown(bundle), end="")
    else:
        top = bundle["top_candidates"][0] if bundle["top_candidates"] else None
        print(
            "Ω-ACTIONS-T∞ evidence "
            f"state={bundle['evidence_state']} workflows={len(bundle['optimization_candidates'])} "
            f"top={top['workflow'] if top else 'none'}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
