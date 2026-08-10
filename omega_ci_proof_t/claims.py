from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

from .models import Claim, sorted_unique

_ALLOWED_PROMOTIONS = {
    "FERTILE": {"PROTOTYPED", "BLOCKED", "REFUTED"},
    "PROTOTYPED": {"MEASURED", "BLOCKED", "REFUTED"},
    "MEASURED": {"BLOCKED", "REFUTED"},
    "BLOCKED": {"FERTILE", "PROTOTYPED"},
    "REFUTED": set(),
}


class ClaimRegistry:
    def __init__(self, claims: Iterable[Claim] = ()) -> None:
        self._claims: dict[str, Claim] = {}
        for claim in claims:
            self.add(claim)

    def add(self, claim: Claim) -> None:
        if claim.claim_id in self._claims:
            raise ValueError(f"duplicate claim_id: {claim.claim_id}")
        self._claims[claim.claim_id] = claim

    def get(self, claim_id: str) -> Claim:
        try:
            return self._claims[claim_id]
        except KeyError as exc:
            raise KeyError(f"unknown claim_id: {claim_id}") from exc

    def all(self) -> tuple[Claim, ...]:
        return tuple(self._claims[key] for key in sorted(self._claims))

    def for_packages(self, packages: Iterable[str]) -> tuple[Claim, ...]:
        wanted = set(packages)
        return tuple(
            claim for claim in self.all()
            if wanted.intersection(claim.subject_packages)
        )

    def required_test_ids(self, claim_ids: Iterable[str]) -> tuple[str, ...]:
        values: list[str] = []
        for claim_id in claim_ids:
            values.extend(self.get(claim_id).required_test_ids)
        return sorted_unique(values)

    def promote(self, claim_id: str, new_status: str) -> Claim:
        current = self.get(claim_id)
        if new_status not in _ALLOWED_PROMOTIONS[current.status]:
            raise ValueError(f"invalid claim transition: {current.status} -> {new_status}")
        promoted = Claim(
            claim_id=current.claim_id,
            statement=current.statement,
            subject_packages=current.subject_packages,
            required_test_ids=current.required_test_ids,
            assumptions=current.assumptions,
            domain_of_validity=current.domain_of_validity,
            status=new_status,
            evidence_ttl_days=current.evidence_ttl_days,
        )
        self._claims[claim_id] = promoted
        return promoted

    def to_dict(self) -> dict[str, object]:
        return {"schema": "omega-ci-claim-registry/v1", "claims": [claim.to_dict() for claim in self.all()]}

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "ClaimRegistry":
        claims_raw = raw.get("claims", [])
        if not isinstance(claims_raw, list):
            raise TypeError("claims must be a list")
        claims = []
        for item in claims_raw:
            if not isinstance(item, Mapping):
                raise TypeError("claim entry must be an object")
            claims.append(Claim(
                claim_id=str(item["claim_id"]),
                statement=str(item["statement"]),
                subject_packages=tuple(str(value) for value in item.get("subject_packages", [])),
                required_test_ids=tuple(str(value) for value in item.get("required_test_ids", [])),
                assumptions=tuple(str(value) for value in item.get("assumptions", [])),
                domain_of_validity=tuple(str(value) for value in item.get("domain_of_validity", [])),
                status=str(item.get("status", "FERTILE")),
                evidence_ttl_days=int(item.get("evidence_ttl_days", 30)),
            ))
        return cls(claims)

    @classmethod
    def from_json(cls, path: str | Path) -> "ClaimRegistry":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, Mapping):
            raise TypeError("claim registry must be an object")
        return cls.from_mapping(raw)
