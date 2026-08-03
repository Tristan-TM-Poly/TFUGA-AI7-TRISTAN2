from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .engine import assess_sponsor_tier
from .models import SponsorTier
from .transparency import digest_payload


@dataclass(frozen=True)
class ProjectCard:
    name: str
    summary: str
    status: str
    evidence: tuple[str, ...]
    next_action: str
    repository_url: str | None = None


@dataclass(frozen=True)
class SponsorProfile:
    handle: str
    display_name: str
    mission: str
    public_commitments: tuple[str, ...]
    non_claims: tuple[str, ...]
    projects: tuple[ProjectCard, ...]
    tiers: tuple[SponsorTier, ...]
    contact_note: str

    def validate(self) -> None:
        if not self.handle.strip() or not self.display_name.strip() or not self.mission.strip():
            raise ValueError("handle, display_name, and mission are required")
        if not self.projects:
            raise ValueError("at least one project card is required")
        for tier in self.tiers:
            tier.validate()


def validate_profile(profile: SponsorProfile) -> dict[str, Any]:
    profile.validate()
    tiers = [assess_sponsor_tier(tier) for tier in profile.tiers]
    return {
        "valid": all(item["sustainable"] for item in tiers),
        "tiers": tiers,
        "profile_hash": digest_payload(
            {
                "handle": profile.handle,
                "display_name": profile.display_name,
                "mission": profile.mission,
                "public_commitments": profile.public_commitments,
                "non_claims": profile.non_claims,
                "projects": [asdict(item) for item in profile.projects],
                "tiers": [asdict(item) for item in profile.tiers],
                "contact_note": profile.contact_note,
            }
        ),
    }


def render_profile_readme(profile: SponsorProfile) -> str:
    validation = validate_profile(profile)
    lines = [
        f"# {profile.display_name}",
        "",
        profile.mission,
        "",
        "## Demonstrated and testable work",
        "",
    ]
    for project in profile.projects:
        lines.extend(
            [
                f"### {project.name}",
                "",
                project.summary,
                "",
                f"**Status:** `{project.status}`",
                "",
                "**Evidence:**",
                *[f"- {item}" for item in project.evidence],
                "",
                f"**Next falsifiable action:** {project.next_action}",
                "",
            ]
        )
        if project.repository_url:
            lines.extend([f"Repository: {project.repository_url}", ""])
    lines.extend(["## Public commitments", ""])
    lines.extend(f"- {item}" for item in profile.public_commitments)
    lines.extend(["", "## What support does not imply", ""])
    lines.extend(f"- {item}" for item in profile.non_claims)
    lines.extend(
        [
            "",
            "## Support",
            "",
            f"GitHub Sponsors: https://github.com/sponsors/{profile.handle}",
            "",
            profile.contact_note,
            "",
            f"Profile evidence hash: `{validation['profile_hash']}`",
            "",
        ]
    )
    return "\n".join(lines)


def render_sponsor_tiers(profile: SponsorProfile) -> str:
    validation = validate_profile(profile)
    lines = ["# Sustainable Sponsor Tiers", ""]
    for tier, assessment in zip(profile.tiers, validation["tiers"], strict=True):
        lines.extend(
            [
                f"## {tier.name} — {tier.monthly_minor / 100:.2f} {tier.currency}/month",
                "",
                *[f"- {benefit}" for benefit in tier.benefits],
                "",
                f"Estimated bounded delivery: {tier.monthly_delivery_minutes} minutes/month",
                f"Sustainability gate: {'PASS' if assessment['sustainable'] else 'FAIL'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Global boundaries",
            "",
            "- no unlimited consulting or custom development",
            "- no guaranteed scientific, financial, legal, or business result",
            "- no access to private or patent-sensitive work without a separate agreement",
            "- no banking, tax, credential, or confidential-client information through public channels",
            "",
        ]
    )
    return "\n".join(lines)


def write_profile_bundle(
    profile: SponsorProfile,
    output_dir: str | Path,
) -> dict[str, Any]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    readme = destination / "PROFILE_README.md"
    tiers = destination / "SPONSOR_TIERS.md"
    manifest = destination / "profile-manifest.json"
    readme.write_text(render_profile_readme(profile), encoding="utf-8")
    tiers.write_text(render_sponsor_tiers(profile), encoding="utf-8")
    validation = validate_profile(profile)
    manifest.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "readme": str(readme),
        "tiers": str(tiers),
        "manifest": str(manifest),
        **validation,
    }
