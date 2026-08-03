from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable

from .catalog import BEST_SITES_V1
from .models import CampaignPlan, SourceProfile, canonical_json


@dataclass(frozen=True)
class PlannerOptions:
    include_tiers: tuple[int, ...] = (0, 1)
    include_review_required: bool = False
    include_key_required: bool = False
    metadata_only: bool = True
    execute_network: bool = False


def build_plan(
    profiles: Iterable[SourceProfile] = BEST_SITES_V1,
    *,
    options: PlannerOptions = PlannerOptions(),
) -> CampaignPlan:
    selected: list[SourceProfile] = []
    skipped: list[dict[str, str]] = []
    for profile in sorted(profiles, key=lambda item: (item.tier, -item.authority_score, item.source_id)):
        if profile.tier not in options.include_tiers:
            skipped.append({"source_id": profile.source_id, "reason": "tier_not_selected"})
            continue
        if profile.access_state == "review_required" and not options.include_review_required:
            skipped.append({"source_id": profile.source_id, "reason": "policy_review_required"})
            continue
        if profile.access_state == "key_required":
            missing = [name for name in profile.required_env if not os.getenv(name)]
            if missing and not options.include_key_required:
                skipped.append({"source_id": profile.source_id, "reason": "missing_required_key"})
                continue
        if options.metadata_only and profile.full_text_policy not in {"metadata_only", "forbidden"}:
            # The source remains usable, but the plan records a metadata-only override.
            profile = SourceProfile(
                **{**profile.__dict__, "full_text_policy": "metadata_only", "notes": (profile.notes + " Metadata-only campaign override.").strip()}
            )
        selected.append(profile)
    campaign_id = "best-sites-v1-" + "-".join(str(item) for item in options.include_tiers)
    return CampaignPlan(
        campaign_id=campaign_id,
        sources=tuple(selected),
        skipped=tuple(skipped),
        metadata_only=options.metadata_only,
        execute_network=options.execute_network,
    )


def materialize_plan(plan: CampaignPlan, output_dir: str | Path) -> Path:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "campaign-plan.json").write_text(canonical_json(plan.to_dict()) + "\n", encoding="utf-8")
    lines = [
        "# Ω-WEB-HG-T∞ Best Sites campaign",
        "",
        f"Campaign: `{plan.campaign_id}`",
        f"Digest: `{plan.digest}`",
        f"Sources selected: {len(plan.sources)}",
        f"Metadata-only: `{str(plan.metadata_only).lower()}`",
        f"Network execution authorized: `{str(plan.execute_network).lower()}`",
        "",
        "## Sources",
        "",
    ]
    for source in plan.sources:
        lines.extend(
            [
                f"### {source.name}",
                f"- id: `{source.source_id}`",
                f"- tier: `{source.tier}`",
                f"- access: `{source.access_state}`",
                f"- modes: `{', '.join(source.modes)}`",
                f"- full text: `{source.full_text_policy}`",
                f"- pilot budget: `{source.pilot_budget}` requests/items",
                f"- policy: {source.policy_url}",
                "",
            ]
        )
    if plan.skipped:
        lines.extend(["## Skipped", ""])
        lines.extend(f"- `{item['source_id']}` — {item['reason']}" for item in plan.skipped)
        lines.append("")
    lines.extend(
        [
            "## OAK boundary",
            "",
            "This plan is a deterministic routing artifact. It does not itself fetch remote content, certify truth, clear copyright, or authorize full-text republication.",
        ]
    )
    (root / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root
