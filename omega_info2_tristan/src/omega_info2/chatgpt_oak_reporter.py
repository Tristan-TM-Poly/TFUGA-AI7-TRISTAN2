"""Post-merge report helpers for M-CHATGPT-OAK.

The reporter prevents premature final summaries by requiring a merged context
unless a real blocker is present.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .chatgpt_oak_gate import ChatGPTOAKGate, GitHubRunContext


@dataclass(slots=True)
class GitHubWorkflowReport:
    title: str
    status: str
    body: str
    citations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_post_merge_report(
    context: GitHubRunContext,
    *,
    pr_number: int | None = None,
    pr_url: str | None = None,
    merge_sha: str | None = None,
    files_changed: list[str] | None = None,
    notes: list[str] | None = None,
) -> GitHubWorkflowReport:
    """Build a safe final report only after merge or real blocker.

    Raises ValueError when the context is green/mergeable but not merged. This
    encodes the negative memory: do not summarize a successful Go GitHub before
    the merge actually happened.
    """
    gate = ChatGPTOAKGate()
    decision = gate.evaluate_github_context(context)
    notes = notes or []
    files_changed = files_changed or []

    if context.real_blocker:
        return GitHubWorkflowReport(
            title="GitHub workflow blocked",
            status="BLOCKED_REAL",
            body=_blocked_body(context.real_blocker, pr_number, pr_url, notes),
            metadata={"decision": decision.to_dict(), "pr_number": pr_number, "pr_url": pr_url},
        )

    if not context.merged:
        raise ValueError("Cannot build final Go GitHub report before merge. Merge first or report a real blocker.")

    body = _merged_body(pr_number=pr_number, pr_url=pr_url, merge_sha=merge_sha, files_changed=files_changed, notes=notes)
    return GitHubWorkflowReport(
        title="GitHub workflow merged",
        status="MERGED",
        body=body,
        metadata={
            "decision": decision.to_dict(),
            "pr_number": pr_number,
            "pr_url": pr_url,
            "merge_sha": merge_sha,
            "files_changed": files_changed,
        },
    )


def _merged_body(
    *,
    pr_number: int | None,
    pr_url: str | None,
    merge_sha: str | None,
    files_changed: list[str],
    notes: list[str],
) -> str:
    pr_line = f"PR: #{pr_number}" if pr_number is not None else "PR: unknown"
    if pr_url:
        pr_line += f" ({pr_url})"
    sha_line = f"Merge SHA: {merge_sha}" if merge_sha else "Merge SHA: unknown"
    files = "\n".join(f"- {path}" for path in files_changed) if files_changed else "- No file list provided."
    note_block = "\n".join(f"- {note}" for note in notes) if notes else "- No extra notes."
    return f"""Go GitHub completed and merged.

{pr_line}
{sha_line}

Files changed:
{files}

Notes:
{note_block}
"""


def _blocked_body(real_blocker: str, pr_number: int | None, pr_url: str | None, notes: list[str]) -> str:
    pr_line = f"PR: #{pr_number}" if pr_number is not None else "PR: unknown"
    if pr_url:
        pr_line += f" ({pr_url})"
    note_block = "\n".join(f"- {note}" for note in notes) if notes else "- No extra notes."
    return f"""Go GitHub blocked by a real blocker.

{pr_line}
Blocker: {real_blocker}

Notes:
{note_block}
"""
