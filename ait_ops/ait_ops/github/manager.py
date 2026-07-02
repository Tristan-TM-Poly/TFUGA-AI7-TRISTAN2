from __future__ import annotations
from ait_ops.core.models import GitHubOpsPlan


def slug(text: str) -> str:
    return '-'.join(''.join(ch.lower() if ch.isalnum() else '-' for ch in text).split('-'))[:56] or 'ops-plan'


def build_github_plan(intent: str, repository: str = 'Tristan-TM-Poly/TFUGA-AI7-TRISTAN2') -> GitHubOpsPlan:
    s = slug(intent)
    branch = f'codex/{s}'
    pr_body = f'''## What changed

AIT-GitHubManager prepared an OAK-safe GitHub operation plan for:

{intent}

## Gates

- draft PR by default
- no direct write to the default branch
- no history rewrite
- local tests required
- CI green required
- human approval or explicit automerge policy required

## OAK status

Plan only. External actions disabled by default.
'''
    return GitHubOpsPlan(repository, branch, f'Add {s}', f'[ops] {intent[:80]}', pr_body, True, False, False)
