"""Checkpointed, sharded and resume-safe logical frontier materialization."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from .catalog import catalog_index
from .frontier import LogicalFrontier
from .ir import derive_obligations
from .model import CampaignManifest, CellStatus, MaterializationRecord
from .oak import evaluate_static_gate


def _campaign_id(frontier: LogicalFrontier, start: int, count: int) -> str:
    payload = f"{frontier.size}:{frontier.algorithm_ids[0]}:{frontier.algorithm_ids[-1]}:{start}:{count}".encode()
    return "camp_" + sha256(payload).hexdigest()[:24]


def materialize(
    frontier: LogicalFrontier,
    output_dir: Path,
    *,
    start_index: int = 0,
    count: int,
    shard_size: int = 2048,
    resume: bool = False,
) -> CampaignManifest:
    if count < 0 or shard_size < 1:
        raise ValueError("count must be non-negative and shard_size positive")
    if start_index < 0 or start_index + count > frontier.size:
        raise ValueError("requested interval exceeds frontier")
    output_dir.mkdir(parents=True, exist_ok=True)
    shards_dir = output_dir / "shards"
    shards_dir.mkdir(exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    campaign_id = _campaign_id(frontier, start_index, count)
    next_index = start_index
    accepted = rejected = duplicate_ids = 0
    shards: list[dict[str, object]] = []
    seen: set[str] = set()
    if resume and manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        if previous["campaign_id"] != campaign_id:
            raise ValueError("resume manifest belongs to another campaign")
        next_index = int(previous["next_index"])
        accepted = int(previous["accepted"])
        rejected = int(previous["rejected"])
        duplicate_ids = int(previous["duplicate_ids"])
        shards = list(previous["shards"])
        for shard in shards:
            path = output_dir / str(shard["path"])
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    if line:
                        seen.add(json.loads(line)["variant_id"])
    specs = catalog_index(len(frontier.algorithm_ids))
    end_index = start_index + count
    shard_number = len(shards)
    while next_index < end_index:
        shard_end = min(next_index + shard_size, end_index)
        lines: list[str] = []
        shard_accepted = shard_rejected = 0
        first_global = next_index
        while next_index < shard_end:
            variant = frontier.address_at(next_index)
            spec = specs[variant.algorithm_id]
            decision = evaluate_static_gate(spec, variant)
            obligations = derive_obligations(variant.strategy, variant.precision, variant.layout, variant.parallelism)
            record = MaterializationRecord(
                global_index=next_index,
                variant=variant,
                status=CellStatus.LOGICAL if decision.accepted else CellStatus.REJECTED,
                obligations=obligations + decision.warnings,
                accepted=decision.accepted,
                rejection_reason=decision.reason,
            )
            payload = record.to_dict()
            if payload["variant_id"] in seen:
                duplicate_ids += 1
            else:
                seen.add(str(payload["variant_id"]))
            if decision.accepted:
                accepted += 1
                shard_accepted += 1
            else:
                rejected += 1
                shard_rejected += 1
            lines.append(json.dumps(payload, sort_keys=True, separators=(",", ":")))
            next_index += 1
        content = "\n".join(lines) + ("\n" if lines else "")
        digest = sha256(content.encode()).hexdigest()
        relative = Path("shards") / f"shard-{shard_number:06d}.jsonl"
        (output_dir / relative).write_text(content, encoding="utf-8")
        shards.append({
            "path": relative.as_posix(),
            "sha256": digest,
            "records": len(lines),
            "accepted": shard_accepted,
            "rejected": shard_rejected,
            "first_global_index": first_global,
            "last_global_index": next_index - 1,
        })
        shard_number += 1
        manifest = CampaignManifest(
            campaign_id=campaign_id,
            frontier_size=frontier.size,
            start_index=start_index,
            requested_count=count,
            next_index=next_index,
            accepted=accepted,
            rejected=rejected,
            duplicate_ids=duplicate_ids,
            shards=tuple(shards),
        )
        manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return CampaignManifest(
        campaign_id=campaign_id,
        frontier_size=frontier.size,
        start_index=start_index,
        requested_count=count,
        next_index=next_index,
        accepted=accepted,
        rejected=rejected,
        duplicate_ids=duplicate_ids,
        shards=tuple(shards),
    )
