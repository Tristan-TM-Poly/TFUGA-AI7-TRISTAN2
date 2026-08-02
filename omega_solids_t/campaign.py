from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterator, Sequence
import hashlib
import json

from .mixed_radix import MixedRadixSpace
from .models import CandidateCell, EpistemicStatus
from .vocabularies import (
    WORLDS, ARCHITECTURES, DEFECT_PROFILES, PROCESS_PROFILES,
    ENVIRONMENT_PROFILES, mechanism_subset,
)

@dataclass(frozen=True)
class CampaignSpec:
    campaign_id: str
    worlds: tuple[dict, ...]
    architectures: tuple[dict, ...]
    defect_profiles: tuple[dict, ...]
    process_profiles: tuple[dict, ...]
    environment_profiles: tuple[dict, ...] = ()
    mechanism_width: int = 4

    def __post_init__(self) -> None:
        if not self.campaign_id:
            raise ValueError("campaign_id is required")
        for name in ("worlds", "architectures", "defect_profiles", "process_profiles"):
            if not getattr(self, name):
                raise ValueError(f"{name} cannot be empty")
        if self.mechanism_width < 0:
            raise ValueError("mechanism_width cannot be negative")

    @property
    def base_space(self) -> MixedRadixSpace:
        return MixedRadixSpace(
            (len(self.worlds), len(self.architectures), len(self.defect_profiles), len(self.process_profiles)),
            ("world", "architecture", "defect", "process"),
        )

    @property
    def base_cardinality(self) -> int:
        return self.base_space.cardinality

    @property
    def contextual_cardinality(self) -> int:
        return self.base_cardinality * max(1, len(self.environment_profiles))

    @property
    def fingerprint(self) -> str:
        payload = {
            "campaign_id": self.campaign_id,
            "world_ids": [x["id"] for x in self.worlds],
            "architecture_ids": [x["id"] for x in self.architectures],
            "defect_ids": [x["id"] for x in self.defect_profiles],
            "process_ids": [x["id"] for x in self.process_profiles],
            "environment_ids": [x["id"] for x in self.environment_profiles],
            "mechanism_width": self.mechanism_width,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def candidate_at(self, index: int, environment_index: int = 0) -> CandidateCell:
        wi, ai, di, pi = self.base_space.decode(index)
        world = self.worlds[wi]
        arch = self.architectures[ai]
        defect = self.defect_profiles[di]
        process = self.process_profiles[pi]
        if self.environment_profiles:
            if not 0 <= environment_index < len(self.environment_profiles):
                raise IndexError(environment_index)
            environment = self.environment_profiles[environment_index]
        else:
            environment = {"id": "env-unspecified", "temperature_K": 298.15, "pressure_Pa": 101325.0, "medium": "unspecified"}
        candidate_id = f"{self.campaign_id}:{index:012d}:e{environment_index:02d}"
        descriptor = {
            "world_index": wi,
            "architecture_index": ai,
            "defect_index": di,
            "process_index": pi,
            "hierarchy_depth": arch["hierarchy_depth"],
            "defect_criticality": defect["criticality"],
            "temperature_K": environment["temperature_K"],
            "pressure_Pa": environment["pressure_Pa"],
            "topology": arch["topology"],
            "order_class": arch["order_class"],
            "medium": environment["medium"],
            "generated_not_certified": True,
        }
        required = tuple(dict.fromkeys((
            "schema", "units", "provenance", "uncertainty", "baseline",
            "domain_of_validity", "stability", "fabricability",
            *world["required_checks"],
        )))
        return CandidateCell(
            candidate_id=candidate_id,
            campaign_id=self.campaign_id,
            logical_index=index,
            world_id=world["id"],
            world_name=world["name"],
            architecture_id=arch["id"],
            architecture_name=arch["name"],
            defect_profile_id=defect["id"],
            process_profile_id=process["id"],
            environment_profile_id=environment["id"],
            mechanism_ids=mechanism_subset(wi, ai, self.mechanism_width),
            descriptor=descriptor,
            required_checks=required,
            epistemic_status=EpistemicStatus.GENERATED,
            provenance_ids=(f"vocab:{world['id']}", f"campaign:{self.fingerprint[:16]}"),
        )

    def iter_candidates(self, start: int = 0, stop: int | None = None, environment_index: int = 0) -> Iterator[CandidateCell]:
        stop = self.base_cardinality if stop is None else min(stop, self.base_cardinality)
        for index in range(start, stop):
            yield self.candidate_at(index, environment_index)

    def plan(self, target_records_per_partition: int = 8192) -> dict:
        if target_records_per_partition <= 0:
            raise ValueError("partition target must be positive")
        count = (self.base_cardinality + target_records_per_partition - 1) // target_records_per_partition
        parts = []
        for i in range(count):
            start = i * target_records_per_partition
            stop = min(self.base_cardinality, start + target_records_per_partition)
            parts.append({"partition": i, "start": start, "stop": stop, "records": stop-start})
        return {
            "campaign_id": self.campaign_id,
            "campaign_fingerprint": self.fingerprint,
            "base_cardinality": self.base_cardinality,
            "environment_variants": max(1, len(self.environment_profiles)),
            "contextual_cardinality": self.contextual_cardinality,
            "partition_target": target_records_per_partition,
            "partition_count": count,
            "partitions": parts,
            "no_permanent_total_candidate_cap": True,
            "boundary": "Each execution is finite and bounded by explicit work, resources, quality, rollback, safety, IP and provider constraints.",
        }


def default_campaign_spec() -> CampaignSpec:
    return CampaignSpec(
        campaign_id="omega-solid-64x64x16x8-r02",
        worlds=tuple(dict(x) for x in WORLDS),
        architectures=tuple(dict(x) for x in ARCHITECTURES),
        defect_profiles=tuple(dict(x) for x in DEFECT_PROFILES),
        process_profiles=tuple(dict(x) for x in PROCESS_PROFILES),
        environment_profiles=tuple(dict(x) for x in ENVIRONMENT_PROFILES),
    )
