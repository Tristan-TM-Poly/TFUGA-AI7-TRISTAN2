"""JSON serialization helpers with explicit enum reconstruction."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import AutonomyLevel, CompanyRecord, CompanyState, DivisionRecord, EvidenceRef


def company_from_dict(payload: dict[str, Any]) -> CompanyRecord:
    divisions = [
        DivisionRecord(**{**item, "autonomy_level": AutonomyLevel(int(item.get("autonomy_level", 2)))})
        for item in payload.get("divisions", [])
    ]
    evidence = [EvidenceRef(**item) for item in payload.get("evidence", [])]
    return CompanyRecord(**{
        **payload,
        "state": CompanyState(payload.get("state", CompanyState.CANDIDATE_LEGAL_ENTITY.value)),
        "autonomy_level": AutonomyLevel(int(payload.get("autonomy_level", 2))),
        "divisions": divisions,
        "evidence": evidence,
    })


def load_company(path: Path) -> CompanyRecord:
    return company_from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_company(company: CompanyRecord, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(company.to_dict(), indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
