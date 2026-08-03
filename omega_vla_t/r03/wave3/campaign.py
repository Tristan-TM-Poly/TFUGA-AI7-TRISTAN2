"""Deterministic bounded campaigns over the identity frontier."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .factory import instantiate
from .falsify import test_identity
from .frontier import IdentityFrontierCodec


@dataclass(frozen=True)
class CampaignConfig:
    count: int
    seed: int = 0
    start_offset: int = 0
    trials_per_identity: int = 4
    tolerance: float = 1e-8

    def __post_init__(self) -> None:
        if self.count < 0 or self.start_offset < 0:
            raise ValueError("count and start_offset must be nonnegative")
        if self.trials_per_identity < 1 or self.tolerance <= 0:
            raise ValueError("trials and tolerance must be positive")


@dataclass(frozen=True)
class CampaignReport:
    count_requested: int
    generated: int
    numerically_supported: int
    falsified: int
    incomplete: int
    unique_instances: int
    start_offset: int
    next_offset: int
    logical_frontier_size: int
    aggregate_sha256: str
    records: tuple[dict[str, Any], ...]
    permanent_total_cap: None = None
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False

    @property
    def passed(self) -> bool:
        return self.generated == self.count_requested and self.unique_instances == self.generated

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["passed"] = self.passed
        return payload


def run_campaign(config: CampaignConfig) -> CampaignReport:
    codec = IdentityFrontierCodec()
    records: list[dict[str, Any]] = []
    identities: set[str] = set()
    supported = falsified = incomplete = 0

    for ordinal, address in enumerate(
        codec.iter_addresses(
            config.count,
            seed=config.seed,
            start_offset=config.start_offset,
        )
    ):
        schema, instance = instantiate(address)
        report = test_identity(
            schema,
            instance,
            seed=config.seed + ordinal * 1009,
            trials=config.trials_per_identity,
            tolerance=config.tolerance,
            minimize=True,
        )
        if report.counterexample is not None:
            falsified += 1
        elif report.passed:
            supported += 1
        else:
            incomplete += 1
        identities.add(instance.instance_id)
        records.append(
            {
                "ordinal": ordinal,
                "frontier_offset": config.start_offset + ordinal,
                "instance": instance.to_dict(),
                "test_report": report.to_dict(),
            }
        )

    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return CampaignReport(
        count_requested=config.count,
        generated=len(records),
        numerically_supported=supported,
        falsified=falsified,
        incomplete=incomplete,
        unique_instances=len(identities),
        start_offset=config.start_offset,
        next_offset=config.start_offset + len(records),
        logical_frontier_size=codec.size,
        aggregate_sha256=sha256(canonical.encode()).hexdigest(),
        records=tuple(records),
    )


def write_campaign(report: CampaignReport, output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
