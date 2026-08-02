"""High-level dry-run engine for Ω-MAIL-GITHUB-LOOP-T."""
from __future__ import annotations

from dataclasses import dataclass

from .anti_loop import AntiLoopResult, evaluate_mail
from .authority import AuthorityResult, evaluate_action
from .command_parser import parse_command
from .models import GitAction, LoopCase, LoopPolicy
from .workflow import PlannedGitHubObjects, artifact_hashes, create_case, plan


@dataclass(slots=True)
class DryRunResult:
    case: LoopCase
    anti_loop: AntiLoopResult
    authority: dict[str, AuthorityResult]
    objects: PlannedGitHubObjects

    def to_dict(self) -> dict:
        return {
            "case": self.case.to_dict(),
            "anti_loop": {
                "allowed": self.anti_loop.allowed,
                "reasons": list(self.anti_loop.reasons),
                "fingerprint": self.anti_loop.fingerprint,
            },
            "authority": {
                key: {"allowed": value.allowed, "reasons": list(value.reasons)}
                for key, value in self.authority.items()
            },
            "objects": self.objects.to_dict(),
        }


def dry_run_email(text: str, *, policy: LoopPolicy | None = None, seen_fingerprints: set[str] | None = None, sender: str | None = None, message_id: str | None = None, thread_id: str | None = None) -> DryRunResult:
    policy = policy or LoopPolicy()
    command = parse_command(text, sender=sender, message_id=message_id, thread_id=thread_id)
    anti = evaluate_mail(command, seen_fingerprints=seen_fingerprints or set())
    case = create_case(command)
    objects = plan(case)
    case.artifact_hashes.update(artifact_hashes(objects))
    actions = [
        GitAction.READ_REPOSITORY,
        GitAction.CREATE_ISSUE,
        GitAction.CREATE_BRANCH,
        GitAction.CREATE_COMMIT,
        GitAction.OPEN_DRAFT_PR,
        GitAction.MERGE,
        GitAction.RELEASE,
    ]
    authority = {action.value: evaluate_action(command, policy, action) for action in actions}
    return DryRunResult(case, anti, authority, objects)
