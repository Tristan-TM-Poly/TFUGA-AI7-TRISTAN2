"""Generated GitHub work packet bundle for Omega absorb v1.6."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

from .github_packet_generator import GitHubWorkPacket, generate_github_work_packet, render_github_packet_markdown
from .json_exports import to_deterministic_json
from .next_actions_engine import NextAction


@dataclass(frozen=True)
class GitHubWorkBundle:
    packets: Tuple[GitHubWorkPacket, ...]
    branch_manifest_json: str
    pr_body: str
    next_action: str


def build_github_work_bundle(actions: Iterable[NextAction]) -> GitHubWorkBundle:
    packets = tuple(generate_github_work_packet(action.packet_type) for action in actions)
    branch_manifest_json = to_deterministic_json(
        {
            "branches": [packet.branch_name for packet in packets],
            "packet_count": len(packets),
            "next_action": "create_branch_and_apply_packet",
        }
    )
    pr_body = "Generated local GitHub work bundle."
    return GitHubWorkBundle(packets=packets, branch_manifest_json=branch_manifest_json, pr_body=pr_body, next_action="write_github_work_bundle")


def write_github_work_bundle(bundle: GitHubWorkBundle, output_dir: str | Path = "generated/omega_absorb_poly_prof_v16/github_work_bundle") -> Tuple[str, ...]:
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)
    written = []
    for index, packet in enumerate(bundle.packets, start=1):
        path = base / f"issue_{index:03d}.md"
        path.write_text(render_github_packet_markdown(packet), encoding="utf-8")
        written.append(str(path))
    branch_path = base / "branch_manifest.json"
    branch_path.write_text(bundle.branch_manifest_json, encoding="utf-8")
    written.append(str(branch_path))
    pr_path = base / "pr_body.md"
    pr_path.write_text(bundle.pr_body, encoding="utf-8")
    written.append(str(pr_path))
    return tuple(written)
