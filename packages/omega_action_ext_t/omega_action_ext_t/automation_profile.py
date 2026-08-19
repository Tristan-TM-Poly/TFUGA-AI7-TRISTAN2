"""Automation profiles for Ω-ACTION-EXT-T.

Profiles define how far the system may go without a fresh human decision. They
are deliberately conservative: full preparation can be automated, but final
external effects remain bounded by OAKGate, approval state, and connector mode.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum


class AutomationMode(str, Enum):
    OFF = "off"
    PREPARE_ONLY = "prepare_only"
    DRAFT_AND_QUEUE = "draft_and_queue"
    SAFE_REVERSIBLE = "safe_reversible"
    APPROVED_ONLY = "approved_only"


@dataclass(frozen=True)
class AutomationProfile:
    name: str
    mode: AutomationMode
    allow_real_connectors: bool = False
    allow_public_outputs: bool = False
    allow_financial_actions: bool = False
    allow_destructive_actions: bool = False
    require_ledger: bool = True
    require_manifest_hash: bool = True
    require_approval_for_humans: bool = True

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["mode"] = self.mode.value
        return data


PROFILE_OFF = AutomationProfile(name="off", mode=AutomationMode.OFF)
PROFILE_DEFAULT = AutomationProfile(name="default", mode=AutomationMode.DRAFT_AND_QUEUE)
PROFILE_MAX_PREP = AutomationProfile(name="max_prepare", mode=AutomationMode.PREPARE_ONLY)
PROFILE_SAFE_REVERSIBLE = AutomationProfile(
    name="safe_reversible",
    mode=AutomationMode.SAFE_REVERSIBLE,
    allow_public_outputs=False,
    allow_financial_actions=False,
    allow_destructive_actions=False,
)


def default_profiles() -> list[dict[str, object]]:
    return [
        PROFILE_OFF.to_dict(),
        PROFILE_MAX_PREP.to_dict(),
        PROFILE_DEFAULT.to_dict(),
        PROFILE_SAFE_REVERSIBLE.to_dict(),
    ]
