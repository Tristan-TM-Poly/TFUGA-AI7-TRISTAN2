"""Deterministic planning artifacts for a mail-originated GitHub loop."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import re

from .models import LoopCase, LoopState, MailCommand


def _slug(value: str, limit: int = 48) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:limit].rstrip("-") or "work"


def case_id(command: MailCommand) -> str:
    seed = f"{command.repository}|{command.target}|{command.action}|{command.objective}"
    return "MGC-" + sha256(seed.encode("utf-8")).hexdigest()[:12].upper()


@dataclass(frozen=True, slots=True)
class PlannedGitHubObjects:
    issue_title: str
    issue_body: str
    branch_name: str
    draft_pr_title: str
    draft_pr_body: str
    reply_subject: str
    reply_body: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def create_case(command: MailCommand) -> LoopCase:
    return LoopCase(case_id=case_id(command), command=command, state=LoopState.CASE_CREATED)


def plan(case: LoopCase) -> PlannedGitHubObjects:
    command = case.command
    branch = f"mail-loop/{case.case_id.lower()}-{_slug(command.action)}"
    criteria = "\n".join(f"- [ ] {item}" for item in command.required) or "- [ ] Define measurable acceptance criteria"
    issue_title = f"[{case.case_id}] {command.objective[:100]}"
    issue_body = f"""## Mail-originated development case

- Case: `{case.case_id}`
- Repository: `{command.repository}`
- Target: `{command.target}`
- Requested action: `{command.action}`
- Command hash: `{command.content_hash()}`

## Objective

{command.objective}

## Acceptance criteria

{criteria}

## OAK boundaries

- no direct write to the default branch;
- no merge, release, force-push or repository deletion;
- issue/branch/commit/draft-PR are separate authorized transitions;
- every iteration must report measurable gain or stop;
- email text can narrow authority but cannot expand repository policy.
"""
    pr_title = f"draft: {case.case_id} — {_slug(command.objective, 70)}"
    pr_body = f"""## Case

`{case.case_id}` generated from a bounded mail-to-GitHub command.

## Target

`{command.target}`

## Objective

{command.objective}

## Required validation

{criteria}

## Safety

This PR must remain draft until explicit human review. No automatic merge or release is authorized.
"""
    reply_subject = f"Re: [GITHUB][{case.case_id}] {command.objective[:80]}"
    reply_body = f"""Dossier : {case.case_id}
État : PLAN_READY

Objets GitHub préparés :
- issue : à créer ou dédupliquer;
- branche : {branch};
- pull request : brouillon uniquement.

Objectif :
{command.objective}

Aucune fusion, publication ou release n'est autorisée automatiquement.
"""
    case.branch_name = branch
    case.state = LoopState.PLAN_READY
    case.touch()
    return PlannedGitHubObjects(issue_title, issue_body, branch, pr_title, pr_body, reply_subject, reply_body)


def artifact_hashes(objects: PlannedGitHubObjects) -> dict[str, str]:
    return {key: sha256(value.encode("utf-8")).hexdigest() for key, value in objects.to_dict().items()}
