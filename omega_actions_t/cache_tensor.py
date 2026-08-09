"""Empirical cache-value analysis for Ω-ACTIONS-T∞ CacheTensor R0.5."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _observations(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("caches", "observations", "records"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def evaluate_cache(row: dict[str, Any]) -> dict[str, Any]:
    name = str(row.get("name") or row.get("key") or "cache")
    attempts = max(int(row.get("attempts") or row.get("runs") or 0), 0)
    hits = max(int(row.get("hits") or 0), 0)
    misses = max(int(row.get("misses") or max(attempts - hits, 0)), 0)
    if attempts == 0:
        attempts = hits + misses
    restore_total = max(float(row.get("restore_seconds_total") or 0.0), 0.0)
    save_total = max(float(row.get("save_seconds_total") or 0.0), 0.0)
    saved_per_hit = max(float(row.get("saved_seconds_per_hit") or row.get("avoided_seconds_per_hit") or 0.0), 0.0)
    gross_saved = hits * saved_per_hit
    overhead = restore_total + save_total
    net = gross_saved - overhead
    if attempts < 5:
        decision = "INSUFFICIENT_EVIDENCE"
    elif net > 0:
        decision = "KEEP_OR_EXPAND"
    else:
        decision = "REMOVE_OR_REDESIGN"
    return {
        "name": name,
        "attempts": attempts,
        "hits": hits,
        "misses": misses,
        "hit_rate": round(hits / attempts, 6) if attempts else None,
        "saved_seconds_per_hit": round(saved_per_hit, 6),
        "gross_saved_seconds": round(gross_saved, 6),
        "restore_seconds_total": round(restore_total, 6),
        "save_seconds_total": round(save_total, 6),
        "overhead_seconds_total": round(overhead, 6),
        "net_saved_seconds": round(net, 6),
        "net_saved_seconds_per_attempt": round(net / attempts, 6) if attempts else None,
        "overhead_seconds_per_attempt": round(overhead / attempts, 6) if attempts else None,
        "value_ratio": round(gross_saved / overhead, 6) if overhead else (None if gross_saved == 0 else float("inf")),
        "bytes_restored": int(row.get("bytes_restored") or 0),
        "bytes_saved": int(row.get("bytes_saved") or 0),
        "decision": decision,
    }


def analyze_caches(payload: Any) -> dict[str, Any]:
    caches = [evaluate_cache(row) for row in _observations(payload)]
    caches.sort(key=lambda row: (-float(row["net_saved_seconds"]), row["name"]))
    attempts = sum(int(row["attempts"]) for row in caches)
    net = sum(float(row["net_saved_seconds"]) for row in caches)
    negative = [row for row in caches if row["decision"] == "REMOVE_OR_REDESIGN"]
    insufficient = [row for row in caches if row["decision"] == "INSUFFICIENT_EVIDENCE"]
    recommendations: list[dict[str, Any]] = []
    if negative:
        recommendations.append({
            "id": "remove-negative-value-cache",
            "priority": "high",
            "caches": [row["name"] for row in negative],
            "message": "Measured cache overhead exceeds estimated avoided work; remove, coarsen or redesign these cache policies.",
        })
    if insufficient:
        recommendations.append({
            "id": "collect-more-cache-evidence",
            "priority": "low",
            "caches": [row["name"] for row in insufficient],
            "message": "Fewer than five attempts are available; keep the decision provisional.",
        })
    return {
        "schema": "omega-actions-cache-tensor/v0.5",
        "aggregate": {
            "cache_count": len(caches),
            "attempts": attempts,
            "net_saved_seconds": round(net, 6),
            "negative_value_caches": len(negative),
            "insufficient_evidence_caches": len(insufficient),
        },
        "caches": caches,
        "recommendations": recommendations,
        "oak_limits": [
            "Saved time per hit must come from measurement or a declared estimate; the analyzer does not invent it.",
            "Cache value is workload-dependent and can change after dependency, runner or key-policy changes.",
            "Positive time value does not override cache-poisoning, confidentiality or provenance constraints.",
            "Caches must never be used for secrets or as a substitute for reproducible dependency definitions.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    a = report["aggregate"]
    lines = [
        "# Ω-ACTIONS-T∞ — CacheTensor", "",
        f"- Caches: **{a['cache_count']}**", f"- Attempts: **{a['attempts']}**",
        f"- Net estimated/measured value: **{a['net_saved_seconds']} s**",
        f"- Negative-value caches: **{a['negative_value_caches']}**", "", "## Cache values", "",
    ]
    for row in report["caches"]:
        lines.append(
            f"- `{row['name']}` — {row['decision']}, hit_rate={row['hit_rate']}, "
            f"net={row['net_saved_seconds']} s, per_attempt={row['net_saved_seconds_per_attempt']} s"
        )
    lines += ["", "## OAK limits", ""]
    lines.extend(f"- {item}" for item in report["oak_limits"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-actions-cache", description="Evaluate empirical GitHub Actions cache value.")
    parser.add_argument("input", help="JSON cache observations")
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    parser.add_argument("--format", choices=("summary", "json", "markdown"), default="summary")
    args = parser.parse_args(argv)
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = analyze_caches(payload)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.markdown_out:
        Path(args.markdown_out).write_text(render_markdown(report), encoding="utf-8")
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(render_markdown(report), end="")
    else:
        a = report["aggregate"]
        print(f"Ω-ACTIONS-T∞ cache caches={a['cache_count']} attempts={a['attempts']} net={a['net_saved_seconds']}s negative={a['negative_value_caches']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
