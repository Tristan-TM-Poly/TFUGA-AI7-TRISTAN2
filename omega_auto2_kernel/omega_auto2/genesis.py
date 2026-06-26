from __future__ import annotations

from .genesis_report import GenesisReport
from .genesis_score import rank_genesis_ideas
from .genesis_tree import build_genesis_tree

DEFAULT_IDEAS = [
    "AUTO-GENESIS Kernel",
    "Genesis GitHub Factory",
    "Genesis Report Builder",
    "HEAL Genesis",
    "Science Digest Genesis",
]


def auto_genesis(intent: str, mode: str = "max") -> GenesisReport:
    decoded = intent.strip() or "Build AUTO-GENESIS"
    ideas = rank_genesis_ideas(DEFAULT_IDEAS)
    top = [idea["name"] for idea in ideas[:3]]
    return GenesisReport(
        intention_decoded=decoded,
        mode=mode,
        genesis_tree=build_genesis_tree(decoded),
        idea_candidates=ideas,
        compressed_top_ideas=top,
        prototype_plan=["modules", "cli", "tests", "docs"],
        oak_report={
            "status": "draft_ready",
            "external_actions_added": False,
            "red_locks": [],
        },
        revenue_ip_paths=["audit", "prototype_factory", "digest_engine"],
        github_plan=["branch", "draft_pr", "ci", "merge_if_safe"],
        m_plus=["small_modules", "tests", "ci_green"],
        m_minus=["version_drift", "giant_files", "overreach"],
        next_action="open_auto_genesis_pr",
    )
