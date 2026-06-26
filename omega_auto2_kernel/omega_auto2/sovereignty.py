from __future__ import annotations

from dataclasses import dataclass

RED_LOCKS = {
    "delete_files",
    "public_publish",
    "external_email",
    "spend_money",
    "change_permissions",
    "ip_disclosure",
    "legal_commitment",
    "medical_decision",
    "unsafe_physical_action",
}


@dataclass(frozen=True)
class SovereigntyDecision:
    allowed: bool
    requires_human: bool
    red_locks: list[str]
    mode: str = "draft_only"

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def human_sovereignty_check(actions: list[str]) -> SovereigntyDecision:
    touched = sorted(set(actions).intersection(RED_LOCKS))
    return SovereigntyDecision(
        allowed=not touched,
        requires_human=bool(touched),
        red_locks=touched,
    )
