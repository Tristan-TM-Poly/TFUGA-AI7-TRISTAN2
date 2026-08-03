from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import re
from typing import Iterable

_ALLOWED_MODES = {"api", "dump", "oai", "web"}
_ALLOWED_ACCESS = {"ready", "key_required", "review_required"}
_ALLOWED_TEXT = {"metadata_only", "open_only", "licensed_only", "forbidden"}


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class SourceProfile:
    source_id: str
    name: str
    tier: int
    authority_score: float
    domains: tuple[str, ...]
    modes: tuple[str, ...]
    endpoints: tuple[str, ...]
    access_state: str
    full_text_policy: str
    license_note: str
    policy_url: str
    refresh_days: int
    requests_per_second: float
    pilot_budget: int
    topics: tuple[str, ...]
    notes: str = ""
    required_env: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]+", self.source_id):
            errors.append("invalid_source_id")
        if self.tier not in {0, 1, 2, 3}:
            errors.append("invalid_tier")
        if not 0.0 <= self.authority_score <= 1.0:
            errors.append("invalid_authority_score")
        if not self.domains:
            errors.append("missing_domains")
        if not self.endpoints:
            errors.append("missing_endpoints")
        if not set(self.modes) <= _ALLOWED_MODES:
            errors.append("invalid_mode")
        if self.access_state not in _ALLOWED_ACCESS:
            errors.append("invalid_access_state")
        if self.full_text_policy not in _ALLOWED_TEXT:
            errors.append("invalid_full_text_policy")
        if self.refresh_days < 1 or self.requests_per_second <= 0 or self.pilot_budget < 1:
            errors.append("invalid_budget_or_rate")
        if not self.policy_url.startswith("https://"):
            errors.append("invalid_policy_url")
        return errors

    @property
    def digest(self) -> str:
        return sha256(canonical_json(asdict(self)).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {**asdict(self), "digest": self.digest}


@dataclass(frozen=True)
class CampaignPlan:
    campaign_id: str
    sources: tuple[SourceProfile, ...]
    skipped: tuple[dict[str, str], ...]
    metadata_only: bool
    execute_network: bool

    @property
    def digest(self) -> str:
        payload = {
            "campaign_id": self.campaign_id,
            "sources": [item.to_dict() for item in self.sources],
            "skipped": list(self.skipped),
            "metadata_only": self.metadata_only,
            "execute_network": self.execute_network,
        }
        return sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "omega-web-hg-best-sites-plan/1.0",
            "campaign_id": self.campaign_id,
            "sources": [item.to_dict() for item in self.sources],
            "skipped": list(self.skipped),
            "metadata_only": self.metadata_only,
            "execute_network": self.execute_network,
            "source_count": len(self.sources),
            "pilot_request_budget": sum(item.pilot_budget for item in self.sources),
            "digest": self.digest,
            "claim_boundaries": {
                "source_is_best_proven": False,
                "content_truth_certified": False,
                "license_clearance_automated": False,
                "full_text_republication_authorized": False,
            },
        }


def audit_profiles(profiles: Iterable[SourceProfile]) -> dict[str, object]:
    profiles = tuple(profiles)
    ids = [item.source_id for item in profiles]
    errors = {item.source_id: item.validate() for item in profiles if item.validate()}
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    return {
        "status": "PASS" if not errors and not duplicates else "FAIL",
        "sources": len(profiles),
        "duplicates": duplicates,
        "errors": errors,
        "full_text_enabled": [item.source_id for item in profiles if item.full_text_policy != "metadata_only"],
        "review_required": [item.source_id for item in profiles if item.access_state == "review_required"],
        "key_required": [item.source_id for item in profiles if item.access_state == "key_required"],
    }
