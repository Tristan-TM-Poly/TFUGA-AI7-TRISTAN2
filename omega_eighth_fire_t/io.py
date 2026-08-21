from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import FireMetrics, FireProposal, GateResult


def proposal_from_dict(payload: dict[str, Any]) -> FireProposal:
    gates = {str(name): GateResult(**value) for name, value in payload["gates"].items()}
    metrics = FireMetrics(**payload["metrics"])
    return FireProposal(
        proposal_id=str(payload["proposal_id"]),
        purpose=str(payload["purpose"]),
        beneficiaries=tuple(map(str, payload["beneficiaries"])),
        capability=str(payload["capability"]),
        method=str(payload["method"]),
        metrics=metrics,
        gates=gates,
        provenance=tuple(map(str, payload.get("provenance", []))),
        falsifiers=tuple(map(str, payload.get("falsifiers", []))),
        exit_path=str(payload.get("exit_path", "")),
        rollback=str(payload.get("rollback", "")),
        rights_notes=str(payload.get("rights_notes", "")),
        metadata=dict(payload.get("metadata", {})),
    )


def load_proposal(path: str | Path) -> FireProposal:
    return proposal_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
