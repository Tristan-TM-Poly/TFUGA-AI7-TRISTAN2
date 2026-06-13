"""Cloud runner for FTPCI-Omega auto meta-generation.

Writes latest machine-readable and markdown reports using only Python stdlib.
Designed for GitHub Actions free compute on public repositories.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import os

from sage_tristan.auto_meta_generator import run_generation


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|")


def write_markdown(result: dict, path: Path, run_label: str) -> None:
    top = result["top16"]
    bottom = result["negative_memory_bottom16"]
    created_at = datetime.now(timezone.utc).isoformat()

    lines = [
        f"# Auto Meta-Generation Latest — {run_label}",
        "",
        f"**Generated UTC:** `{created_at}`  ",
        f"**Engine:** `{result['engine']}`  ",
        f"**Cycles:** `{result['cycles']}`  ",
        f"**Beam width:** `{result['beam_width']}`  ",
        f"**Approx candidates:** `{result['evaluated_candidates_approx']}`  ",
        f"**Salt:** `{result['salt']}`",
        "",
        "> OAK: architecture/meta-generation output only. Not a physics proof; promote only after tests, predictions, and validation.",
        "",
        "## Top 16 candidates",
        "",
        "| rank | id | score | OAK | status | seed | next action |",
        "|---:|---|---:|---:|---|---|---|",
    ]
    for rank, candidate in enumerate(top, start=1):
        lines.append(
            "| {rank} | `{id}` | {score:.3f} | {oak:.3f} | {status} | {seed} | {action} |".format(
                rank=rank,
                id=candidate["id"],
                score=float(candidate["total"]),
                oak=float(candidate["oak_score"]),
                status=_md_escape(candidate["status"]),
                seed=_md_escape(candidate["seed"]),
                action=_md_escape(candidate["next_action"]),
            )
        )

    lines.extend(
        [
            "",
            "## Bottom 16 negative-memory candidates",
            "",
            "| rank | id | score | OAK | status | seed |",
            "|---:|---|---:|---:|---|---|",
        ]
    )
    for rank, candidate in enumerate(bottom, start=1):
        lines.append(
            "| {rank} | `{id}` | {score:.3f} | {oak:.3f} | {status} | {seed} |".format(
                rank=rank,
                id=candidate["id"],
                score=float(candidate["total"]),
                oak=float(candidate["oak_score"]),
                status=_md_escape(candidate["status"]),
                seed=_md_escape(candidate["seed"]),
            )
        )

    lines.extend(
        [
            "",
            "## Next OAK moves",
            "",
            "1. Decompress the best selected candidate into a one-page codex.",
            "2. Generate 16 testable hypotheses from the top16.",
            "3. Add real data or benchmark outputs before promoting any physical claim.",
            "4. Keep bottom16 in memory negative to prune future runs.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run and persist FTPCI-Omega auto meta-generation.")
    parser.add_argument("--cycles", type=int, default=int(os.getenv("FTPCI_CYCLES", "16")))
    parser.add_argument("--beam-width", type=int, default=int(os.getenv("FTPCI_BEAM_WIDTH", "16")))
    parser.add_argument("--run-label", default=os.getenv("FTPCI_RUN_LABEL", "manual-local"))
    parser.add_argument("--salt", default=os.getenv("FTPCI_RUN_SALT", "manual-local"))
    args = parser.parse_args()

    result = run_generation(cycles=args.cycles, beam_width=args.beam_width, salt=args.salt)
    result["run_label"] = args.run_label
    result["generated_at_utc"] = datetime.now(timezone.utc).isoformat()

    reports_dir = Path("reports")
    examples_dir = Path("examples")
    reports_dir.mkdir(exist_ok=True)
    examples_dir.mkdir(exist_ok=True)

    json_path = reports_dir / "auto_meta_generation_latest.json"
    md_path = reports_dir / "auto_meta_generation_latest.md"
    summary_path = examples_dir / "auto_meta_generation_latest.summary.json"

    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(result, md_path, args.run_label)

    summary = {
        "engine": result["engine"],
        "run_label": args.run_label,
        "generated_at_utc": result["generated_at_utc"],
        "cycles": result["cycles"],
        "beam_width": result["beam_width"],
        "evaluated_candidates_approx": result["evaluated_candidates_approx"],
        "top3": [
            {
                "rank": idx + 1,
                "id": candidate["id"],
                "score": candidate["total"],
                "oak_score": candidate["oak_score"],
                "status": candidate["status"],
                "seed": candidate["seed"],
            }
            for idx, candidate in enumerate(result["top16"][:3])
        ],
        "oak_note": result["oak_note"],
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    print(f"wrote {summary_path}")


if __name__ == "__main__":
    main()
