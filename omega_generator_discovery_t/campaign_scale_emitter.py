"""Atomic resumable emitter for multi-epoch campaign partitions."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from .campaign import CampaignSpec
from .campaign_scale import ScalePartition, iter_epoch_bundles


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


@dataclass(frozen=True, slots=True)
class ScaleEmissionReport:
    status: str
    base_campaign_id: str
    base_campaign_fingerprint: str
    epoch_index: int
    global_partition_index: int
    generator_start: int
    generator_stop: int
    emitted_generator_bundles: int
    emitted_logical_records: int
    shards: int
    output_dir: str
    completed_at: str
    no_permanent_total_addition_cap: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ScalePartitionEmitter:
    """Emit one planned scale partition as atomic planner-ready JSONL shards."""

    def __init__(
        self,
        base: CampaignSpec,
        partition: ScalePartition,
        output_dir: str | Path,
        *,
        bundles_per_shard: int = 2_048,
    ):
        if bundles_per_shard < 1:
            raise ValueError("bundles_per_shard must be positive")
        self.base = base
        self.partition = partition
        self.output_dir = Path(output_dir)
        self.bundles_per_shard = bundles_per_shard
        self.checkpoint_path = self.output_dir / "checkpoint.json"
        self.shard_ledger_path = self.output_dir / "shards.jsonl"

    def emit(self, *, resume: bool = False) -> ScaleEmissionReport:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if not resume and any(self.output_dir.iterdir()):
            raise FileExistsError(f"output directory is not empty: {self.output_dir}")
        next_generator = self.partition.generator_start
        bundles = records = shards = 0
        if resume and self.checkpoint_path.exists():
            saved = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
            self._verify_checkpoint(saved)
            next_generator = int(saved["next_generator"])
            bundles = int(saved["emitted_generator_bundles"])
            records = int(saved["emitted_logical_records"])
            shards = int(saved["shards"])

        while next_generator < self.partition.generator_stop:
            stop = min(next_generator + self.bundles_per_shard, self.partition.generator_stop)
            shard = self._emit_shard(next_generator, stop)
            with self.shard_ledger_path.open("a", encoding="utf-8") as handle:
                handle.write(_json(shard) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            shards += 1
            bundles += stop - next_generator
            records += int(shard["logical_records"])
            next_generator = stop
            self._write_checkpoint(next_generator, bundles, records, shards)

        report = ScaleEmissionReport(
            status="completed",
            base_campaign_id=self.base.campaign_id,
            base_campaign_fingerprint=self.base.fingerprint,
            epoch_index=self.partition.epoch_index,
            global_partition_index=self.partition.global_partition_index,
            generator_start=self.partition.generator_start,
            generator_stop=self.partition.generator_stop,
            emitted_generator_bundles=bundles,
            emitted_logical_records=records,
            shards=shards,
            output_dir=str(self.output_dir),
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        _atomic_json(self.output_dir / "report.json", report.to_dict())
        return report

    def _verify_checkpoint(self, saved: Mapping[str, Any]) -> None:
        if saved.get("base_campaign_fingerprint") != self.base.fingerprint:
            raise ValueError("checkpoint base campaign fingerprint mismatch")
        if saved.get("partition") != self.partition.to_dict():
            raise ValueError("checkpoint partition mismatch")
        if int(saved.get("bundles_per_shard", -1)) != self.bundles_per_shard:
            raise ValueError("checkpoint shard policy mismatch")

    def _write_checkpoint(
        self,
        next_generator: int,
        bundles: int,
        records: int,
        shards: int,
    ) -> None:
        _atomic_json(
            self.checkpoint_path,
            {
                "status": "completed"
                if next_generator == self.partition.generator_stop
                else "running",
                "base_campaign_fingerprint": self.base.fingerprint,
                "partition": self.partition.to_dict(),
                "bundles_per_shard": self.bundles_per_shard,
                "next_generator": next_generator,
                "emitted_generator_bundles": bundles,
                "emitted_logical_records": records,
                "shards": shards,
            },
        )

    def _emit_shard(self, start: int, stop: int) -> dict[str, Any]:
        relative = Path("records") / (
            f"epoch-{self.partition.epoch_index:08d}-"
            f"bundle-{start:09d}-{stop:09d}.jsonl"
        )
        final_path = self.output_dir / relative
        final_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = final_path.with_suffix(final_path.suffix + ".tmp")
        digest = hashlib.sha256()
        count = byte_count = 0
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for record in iter_epoch_bundles(
                self.base,
                self.partition.epoch_index,
                start=start,
                stop=stop,
            ):
                line = _json(record) + "\n"
                encoded = line.encode("utf-8")
                handle.write(line)
                digest.update(encoded)
                count += 1
                byte_count += len(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, final_path)
        expected = (stop - start) * self.base.records_per_bundle
        if count != expected:
            raise RuntimeError(f"expected {expected} records, emitted {count}")
        return {
            "path": relative.as_posix(),
            "epoch_index": self.partition.epoch_index,
            "generator_start": start,
            "generator_stop": stop,
            "generator_bundles": stop - start,
            "logical_records": count,
            "bytes": byte_count,
            "sha256": digest.hexdigest(),
        }
