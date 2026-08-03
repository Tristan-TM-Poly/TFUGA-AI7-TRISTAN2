"""Report writers for Ω-EMR-SOURCE-T∞."""

from __future__ import annotations

import json
from pathlib import Path

from .models import SourcePlan
from .oak import OAKReport


def _candidate_lines(plan: SourcePlan) -> list[str]:
    candidates = plan.recommended[:5] or plan.conditional[:5]
    if not candidates:
        return ["- No viable mechanism at the requested prototype tier."]
    return [
        f"- `{item.mechanism_id}` — score {item.score:.4f}, "
        f"tier `{item.required_prototype_tier}`, status `{item.status}`"
        for item in candidates
    ]


def markdown_report(plan: SourcePlan, oak: OAKReport) -> str:
    lines = [
        "# Ω-EMR-SOURCE-T∞ source plan",
        "",
        f"- Spectral region: `{plan.spectral_region}`",
        f"- Center frequency: `{plan.target.center_frequency_hz:.9g} Hz`",
        f"- Wavelength: `{plan.wavelength_m:.9g} m`",
        f"- Photon energy: `{plan.photon_energy_ev:.9g} eV`",
        f"- Safety status: `{plan.safety_status}`",
        f"- OAK status: `{oak.status}`",
        f"- Epistemic status: `{plan.epistemic_status}`",
        "",
        "## Highest-ranked mechanisms",
        "",
        *_candidate_lines(plan),
        "",
        "## Architecture",
        "",
        *[f"- {item}" for item in plan.architecture_blocks],
        "",
        "## Metrology",
        "",
        *[f"- {item}" for item in plan.metrology_plan],
        "",
        "## Required controls",
        "",
        *[f"- {item}" for item in plan.required_controls],
        "",
        "## OAK next actions",
        "",
        *[f"- {item}" for item in oak.next_actions],
        "",
        "## Scientific hygiene",
        "",
        "This artifact is a source-family selection and validation plan. It is "
        "not a safety certification, legal authorization, construction manual, "
        "measured result or proof of superior performance.",
        "",
    ]
    return "\n".join(lines)


def write_bundle(plan: SourcePlan, oak: OAKReport, output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = output_dir / "source-plan.json"
    oak_path = output_dir / "oak-report.json"
    report_path = output_dir / "report.md"
    plan_path.write_text(
        json.dumps(plan.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    oak_path.write_text(
        json.dumps(oak.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(markdown_report(plan, oak), encoding="utf-8")
    return {
        "source_plan": str(plan_path),
        "oak_report": str(oak_path),
        "markdown_report": str(report_path),
    }
