from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from ..families import proth_number
from .models import CampaignManifest, CandidateTask


def _canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True, slots=True)
class PlannerPolicy:
    exponent_min: int
    exponent_max: int
    k_min: int = 1
    k_max: int = 999
    shard_size: int = 256
    max_value: int = 2**64 - 1

    def validate(self) -> None:
        if self.exponent_min < 1 or self.exponent_max < self.exponent_min:
            raise ValueError("invalid exponent interval")
        if self.k_min < 1 or self.k_max < self.k_min:
            raise ValueError("invalid k interval")
        if self.shard_size < 1:
            raise ValueError("shard_size must be positive")
        if self.max_value < 3 or self.max_value >= 2**64:
            raise ValueError("R0.2 max_value must fit the unsigned 64-bit proof domain")


class CampaignPlanner:
    def __init__(self, policy: PlannerPolicy):
        policy.validate()
        self.policy = policy

    def build(self) -> CampaignManifest:
        tasks: list[CandidateTask] = []
        ordinal = 0
        for exponent in range(self.policy.exponent_min, self.policy.exponent_max + 1):
            upper = min(self.policy.k_max, 2**exponent - 1)
            start = max(1, self.policy.k_min)
            if start % 2 == 0:
                start += 1
            for k in range(start, upper + 1, 2):
                value = proth_number(k, exponent)
                if value > self.policy.max_value:
                    break
                shard_index = ordinal // self.policy.shard_size
                task_id = f"proth-{exponent:03d}-{k:020d}"
                tasks.append(
                    CandidateTask(
                        task_id=task_id,
                        shard_id=f"shard-{shard_index:08d}",
                        ordinal=ordinal,
                        family="proth",
                        exponent=exponent,
                        k=k,
                        value=value,
                    )
                )
                ordinal += 1
        policy_dict = asdict(self.policy)
        body = {
            "manifest_version": "2.0",
            "policy": policy_dict,
            "tasks": [task.to_dict() for task in tasks],
        }
        digest = hashlib.sha256(_canonical(body)).hexdigest()
        campaign_id = f"omega-prime-campaign-{digest[:16]}"
        shard_count = 0 if not tasks else 1 + tasks[-1].ordinal // self.policy.shard_size
        return CampaignManifest(
            manifest_version="2.0",
            campaign_id=campaign_id,
            policy=policy_dict,
            shard_count=shard_count,
            task_count=len(tasks),
            tasks=tuple(tasks),
            sha256=digest,
            claims={
                "finite_plan_is_permanent_compute_cap": False,
                "external_novelty_checked": False,
                "record_claimed": False,
            },
        )


def verify_manifest(manifest: CampaignManifest | dict[str, object]) -> bool:
    payload = manifest.to_dict() if isinstance(manifest, CampaignManifest) else dict(manifest)
    tasks = payload.get("tasks")
    policy = payload.get("policy")
    if not isinstance(tasks, list) or not isinstance(policy, dict):
        return False
    body = {"manifest_version": payload.get("manifest_version"), "policy": policy, "tasks": tasks}
    expected = hashlib.sha256(_canonical(body)).hexdigest()
    if expected != payload.get("sha256"):
        return False
    ids = [task.get("task_id") for task in tasks if isinstance(task, dict)]
    ordinals = [task.get("ordinal") for task in tasks if isinstance(task, dict)]
    return len(ids) == len(set(ids)) and ordinals == list(range(len(ordinals)))
