"""Idempotency and mail-loop suppression."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from .models import LoopCase, MailCommand


@dataclass(frozen=True, slots=True)
class AntiLoopResult:
    allowed: bool
    reasons: tuple[str, ...]
    fingerprint: str


def command_fingerprint(command: MailCommand) -> str:
    payload = {
        "repository": command.repository.lower(),
        "action": command.action.lower().strip(),
        "target": command.target.strip("/"),
        "objective": " ".join(command.objective.lower().split()),
        "required": sorted(" ".join(item.lower().split()) for item in command.required),
        "thread_id": command.thread_id,
        "message_id": command.message_id,
    }
    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def evaluate_mail(command: MailCommand, *, seen_fingerprints: set[str], owned_senders: set[str] | None = None) -> AntiLoopResult:
    reasons: list[str] = []
    fingerprint = command_fingerprint(command)
    if fingerprint in seen_fingerprints:
        reasons.append("duplicate_command")
    sender = (command.sender or "").lower()
    if owned_senders and sender in {item.lower() for item in owned_senders}:
        reasons.append("owned_sender_requires_explicit_non_auto_marker")
    if command.action.lower() in {"ack", "acknowledge", "auto_reply"}:
        reasons.append("auto_ack_not_development_work")
    return AntiLoopResult(not reasons, tuple(reasons) or ("new_development_event",), fingerprint)


def state_fingerprint(case: LoopCase) -> str:
    payload = {
        "state": case.state.value,
        "issue": case.issue_number,
        "branch": case.branch_name,
        "pr": case.pull_request_number,
        "iterations": case.iterations,
        "artifact_hashes": dict(sorted(case.artifact_hashes.items())),
        "failures": sorted(case.failure_signatures),
    }
    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
