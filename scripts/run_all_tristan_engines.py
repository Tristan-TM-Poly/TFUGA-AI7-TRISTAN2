"""Run all Tristan prototype engines and persist a combined summary."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from sage_tristan.auto_meta_generator import run_generation
from sage_tristan.ait_pantheon import run_ait_cycle
from sage_tristan.jkd_yy3_tristan2 import run_jyt2
from sage_tristan.omega_mghfm_tgnt import run_cycle as run_omega_mghfm_tgnt


def main() -> None:
    reports = Path("reports")
    reports.mkdir(exist_ok=True)

    auto_meta = run_generation(cycles=4, beam_width=8, salt="all-engines")
    ait = run_ait_cycle("Build verified AIT systems with OAK, FTPCI, HGFM and memory negative.", cycles=1, salt="all-engines")
    jyt2 = run_jyt2(cycles=1, salt="all-engines")
    omega = run_omega_mghfm_tgnt(
        [
            "prime tensor gaps",
            "LOG EXP codex",
            "OAK memory negative",
            "JKD YY3 Tristan2",
            "TGNT von Neumann architecture",
        ]
    )

    summary = {
        "engine": "Tristan Combined Engine Runner",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "auto_meta_top1": auto_meta["top16"][0],
        "ait_pantheon_top1": ait["top16"][0],
        "jkd_yy3_tristan2_top1": jyt2["top1_jkd"],
        "omega_mghfm_tgnt_statuses": omega["cycle"]["oak"]["statuses"],
        "omega_mghfm_tgnt_top_jkd_actions": omega["cycle"]["jkd"]["top_jkd_actions"],
        "omega_mghfm_tgnt_signature": omega["cycle"]["log_layers"]["Lomega_minimal_fertile_signature"],
        "oak_note": "Combined architectural run only. Promote outputs only after tests, review and local validation.",
    }

    (reports / "tristan_combined_latest.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (reports / "tristan_combined_latest.md").write_text(render_markdown(summary), encoding="utf-8")

    print("Tristan combined runner complete")
    print("auto_meta", summary["auto_meta_top1"]["id"], summary["auto_meta_top1"].get("total"))
    print("ait", summary["ait_pantheon_top1"]["id"], summary["ait_pantheon_top1"]["score"])
    print("jyt2", summary["jkd_yy3_tristan2_top1"]["id"], summary["jkd_yy3_tristan2_top1"]["score"])
    print("omega", summary["omega_mghfm_tgnt_statuses"])


def render_markdown(summary: dict) -> str:
    lines = [
        "# Tristan Combined Engine Latest",
        "",
        f"**Generated UTC:** `{summary['generated_at_utc']}`",
        "",
        "## Top outputs",
        "",
        f"- Auto Meta top1: `{summary['auto_meta_top1']['id']}` score `{summary['auto_meta_top1'].get('total')}`",
        f"- AIT Pantheon top1: `{summary['ait_pantheon_top1']['id']}` score `{summary['ait_pantheon_top1']['score']}`",
        f"- JKD-YY3-Tristan² top1: `{summary['jkd_yy3_tristan2_top1']['id']}` score `{summary['jkd_yy3_tristan2_top1']['score']}`",
        f"- Ω-MGHFM-TGNT OAK statuses: `{summary['omega_mghfm_tgnt_statuses']}`",
        "",
        "## Ω-MGHFM-TGNT signature",
        "",
        "```json",
        json.dumps(summary["omega_mghfm_tgnt_signature"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Ω-MGHFM-TGNT top JKD actions",
        "",
    ]
    for action in summary["omega_mghfm_tgnt_top_jkd_actions"]:
        lines.append(f"- `{action['action']}` — JKD `{action['jkd_score']}`")
    lines.extend(
        [
            "",
            "## OAK",
            "",
            summary["oak_note"],
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
