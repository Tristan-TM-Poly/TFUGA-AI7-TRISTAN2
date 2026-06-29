"""GitHub packet generator seed for Omega absorb v1.4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class GitHubFilePacket:
    path: str
    purpose: str


@dataclass(frozen=True)
class GitHubWorkPacket:
    title: str
    body: str
    labels: Tuple[str, ...]
    branch_name: str
    files: Tuple[GitHubFilePacket, ...]
    tests: Tuple[str, ...]
    oak_status: str
    next_action: str


def generate_github_work_packet(feature: str = "omega_absorb_next") -> GitHubWorkPacket:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in feature).strip("-") or "omega-absorb-next"
    files = (
        GitHubFilePacket(f"omega_prof_poly_t/{safe}.py", "implementation"),
        GitHubFilePacket(f"tests/test_{safe.replace('-', '_')}.py", "tests"),
        GitHubFilePacket(f"docs/omega-prof-poly/{safe.upper().replace('-', '_')}.md", "documentation"),
    )
    return GitHubWorkPacket(
        title=f"Add {feature}",
        body="Generated local work packet with implementation, tests and docs.",
        labels=("omega-absorb", "oak", "zero-touch"),
        branch_name=f"work-{safe}",
        files=files,
        tests=tuple(file.path for file in files if file.purpose == "tests"),
        oak_status="packet_seed",
        next_action="create_branch_and_apply_packet",
    )


def render_github_packet_markdown(packet: GitHubWorkPacket) -> str:
    lines = [f"# {packet.title}", "", packet.body, "", "## Files"]
    lines.extend(f"- `{item.path}`: {item.purpose}" for item in packet.files)
    lines.extend(["", "## Tests"])
    lines.extend(f"- `{test}`" for test in packet.tests)
    lines.extend(["", "## Labels", ", ".join(packet.labels), "", "## Next action", packet.next_action])
    return "\n".join(lines).strip() + "\n"
