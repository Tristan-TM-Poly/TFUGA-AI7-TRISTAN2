from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

from .models import SupplyChainFinding

_USE_PATTERN = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")

APPROVED_ACTIONS = {
    "actions/checkout": "11bd71901bbe5b1630ceea73d27597364c9af683",
    "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
}


class SupplyChainAuditor:
    def audit_text(self, text: str, *, workflow_path: str = "<memory>") -> tuple[SupplyChainFinding, ...]:
        findings: list[SupplyChainFinding] = []
        for use in _USE_PATTERN.findall(text):
            if use.startswith("./"):
                continue
            if "@" not in use:
                findings.append(SupplyChainFinding(workflow_path, use, "", "error", "action reference lacks @ref", False))
                continue
            action, reference = use.rsplit("@", 1)
            pinned = bool(_SHA_PATTERN.fullmatch(reference))
            approved = APPROVED_ACTIONS.get(action) == reference
            if not pinned:
                findings.append(SupplyChainFinding(workflow_path, action, reference, "error", "action is not pinned to an immutable 40-character SHA", False))
            elif action in APPROVED_ACTIONS and not approved:
                findings.append(SupplyChainFinding(workflow_path, action, reference, "warning", "action SHA is immutable but differs from the reviewed allowlist", False))
            else:
                findings.append(SupplyChainFinding(workflow_path, action, reference, "info", "action is immutably pinned", approved or action not in APPROVED_ACTIONS))
        return tuple(findings)

    def audit_path(self, path: str | Path) -> tuple[SupplyChainFinding, ...]:
        file_path = Path(path)
        return self.audit_text(file_path.read_text(encoding="utf-8"), workflow_path=file_path.as_posix())

    def pin_known_actions(self, text: str, *, replacements: Mapping[str, str] | None = None) -> str:
        pins = dict(APPROVED_ACTIONS)
        if replacements:
            pins.update(replacements)
        result = text
        for action, sha in pins.items():
            result = re.sub(rf"{re.escape(action)}@[^\s#]+", f"{action}@{sha}", result)
        return result
