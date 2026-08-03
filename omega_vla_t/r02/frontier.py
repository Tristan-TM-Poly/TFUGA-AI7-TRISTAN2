"""Adaptive finite campaigns over the unbounded-policy Ω-VLA frontier."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any

from .address import FrontierCodec
from .catalogs import CATALOG, Catalog
from .dedup import ContentDeduplicator
from .models import ProblemCell, SaturationEntry
from .sqlite_index import SQLiteDigestIndex
from .store import StoreManifest, StreamingShardedJSONLWriter
from .theorem_factory import TheoremFactory


@dataclass(frozen=True)
class CampaignConfig:
    """Finite execution budget; never interpreted as a permanent total ceiling."""

    work_items: int
    seed: int = 0
    initial_batch: int = 256
    min_batch: int = 32
    max_batch: int = 8192
    records_per_shard: int = 1024
    min_utility: float = 0.0
    max_risk: float = 1.0
    output_dir: str | None = None
    resume: bool = False
    reset_output: bool = True
    checkpoint_every_batches: int = 1

    def __post_init__(self) -> None:
        if self.work_items < 0:
            raise ValueError("work_items cannot be negative")
        if self.initial_batch <= 0 or self.min_batch <= 0 or self.max_batch <= 0:
            raise ValueError("batch sizes must be positive")
        if not self.min_batch <= self.initial_batch <= self.max_batch:
            raise ValueError("require min_batch <= initial_batch <= max_batch")
        if self.records_per_shard <= 0:
            raise ValueError("records_per_shard must be positive")
        if not 0.0 <= self.min_utility <= 1.0:
            raise ValueError("min_utility must be in [0, 1]")
        if not 0.0 <= self.max_risk <= 1.0:
            raise ValueError("max_risk must be in [0, 1]")
        if self.checkpoint_every_batches <= 0:
            raise ValueError("checkpoint_every_batches must be positive")
        if self.resume and self.output_dir is None:
            raise ValueError("resume requires output_dir")
        if self.resume and self.reset_output:
            object.__setattr__(self, "reset_output", False)


@dataclass(frozen=True)
class BatchTelemetry:
    batch_index: int
    proposed: int
    accepted: int
    rejected_quality: int
    duplicates: int
    next_batch_size: int
    acceptance_rate: float
    duplicate_rate: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CampaignReport:
    system: str
    version: str
    logical_frontier_cells: int
    requested_work_items: int
    proposed_cells: int
    accepted_cells: int
    rejected_quality: int
    duplicates: int
    batches: tuple[BatchTelemetry, ...]
    saturation_ledger: tuple[SaturationEntry, ...]
    store_manifest: StoreManifest | None
    permanent_total_cap: None = None
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "version": self.version,
            "logical_frontier_cells": self.logical_frontier_cells,
            "requested_work_items": self.requested_work_items,
            "proposed_cells": self.proposed_cells,
            "accepted_cells": self.accepted_cells,
            "rejected_quality": self.rejected_quality,
            "duplicates": self.duplicates,
            "batches": [batch.to_dict() for batch in self.batches],
            "saturation_ledger": [entry.to_dict() for entry in self.saturation_ledger],
            "store_manifest": (
                self.store_manifest.to_dict() if self.store_manifest else None
            ),
            "permanent_total_cap": self.permanent_total_cap,
            "theorem_claimed": self.theorem_claimed,
            "formal_proof_claimed": self.formal_proof_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


@dataclass
class FrontierController:
    """Adjust batch size using measured quality and duplication, not a hard cap."""

    batch_size: int
    min_batch: int
    max_batch: int
    saturation_ledger: list[SaturationEntry] = field(default_factory=list)

    def observe(
        self,
        *,
        proposed: int,
        accepted: int,
        duplicates: int,
        rejected_quality: int,
    ) -> int:
        if proposed <= 0:
            return self.batch_size
        acceptance = accepted / proposed
        duplicate_rate = duplicates / proposed
        previous = self.batch_size

        if acceptance >= 0.80 and duplicate_rate <= 0.05:
            self.batch_size = min(self.max_batch, max(previous + 1, previous * 2))
        elif acceptance < 0.35 or duplicate_rate > 0.30:
            self.batch_size = max(self.min_batch, previous // 2)
        elif acceptance < 0.60:
            self.batch_size = max(self.min_batch, int(previous * 0.75))

        if self.batch_size == self.max_batch and previous < self.max_batch:
            self.saturation_ledger.append(
                SaturationEntry(
                    limit_name="configured_batch_envelope",
                    observed_at=proposed,
                    symptom="adaptive controller reached current per-batch envelope",
                    evidence=(
                        f"acceptance_rate={acceptance:.6f}",
                        f"duplicate_rate={duplicate_rate:.6f}",
                    ),
                    lost_work=0,
                    checkpoint_recovered=True,
                    redesign=(
                        "benchmark memory, CI duration and shard throughput before "
                        "raising the current batch envelope"
                    ),
                    next_frontier=None,
                    severity="informational",
                )
            )
        if rejected_quality > accepted and proposed >= self.min_batch:
            self.saturation_ledger.append(
                SaturationEntry(
                    limit_name="quality_filter_saturation",
                    observed_at=proposed,
                    symptom="more candidates rejected than accepted",
                    evidence=(f"rejected_quality={rejected_quality}",),
                    lost_work=0,
                    checkpoint_recovered=True,
                    redesign="retune catalogs or prioritize more testable addresses",
                    next_frontier=None,
                    severity="medium",
                )
            )
        return self.batch_size


def _quality_accept(cell: ProblemCell, config: CampaignConfig) -> bool:
    return (
        cell.utility_score() >= config.min_utility
        and cell.risk_score <= config.max_risk
    )


def _restore_saturation(payload: list[dict[str, Any]]) -> list[SaturationEntry]:
    return [
        SaturationEntry(
            limit_name=str(item["limit_name"]),
            observed_at=int(item["observed_at"]),
            symptom=str(item["symptom"]),
            evidence=tuple(str(value) for value in item.get("evidence", [])),
            lost_work=int(item["lost_work"]),
            checkpoint_recovered=bool(item["checkpoint_recovered"]),
            redesign=str(item["redesign"]),
            next_frontier=(
                None if item.get("next_frontier") is None else int(item["next_frontier"])
            ),
            severity=str(item.get("severity", "medium")),
        )
        for item in payload
    ]


def _checkpoint_payload(
    *,
    config: CampaignConfig,
    catalog: Catalog,
    proposed_total: int,
    accepted_total: int,
    rejected_total: int,
    duplicate_total: int,
    batch_index: int,
    controller: FrontierController,
    telemetry: list[BatchTelemetry],
    digest_count: int,
) -> dict[str, Any]:
    return {
        "system": "Ω-VLA-T∞²",
        "version": "R0.2-MAX",
        "seed": config.seed,
        "requested_work_items": config.work_items,
        "proposed_cells": proposed_total,
        "accepted_cells": accepted_total,
        "rejected_quality": rejected_total,
        "duplicates": duplicate_total,
        "next_offset": proposed_total,
        "next_batch_index": batch_index,
        "next_batch_size": controller.batch_size,
        "batches": [item.to_dict() for item in telemetry],
        "saturation_ledger": [
            entry.to_dict() for entry in controller.saturation_ledger
        ],
        "digest_count": digest_count,
        "catalog_summary": catalog.summary(),
        "permanent_total_cap": None,
        "theorem_claimed": False,
        "formal_proof_claimed": False,
        "scientific_validation_claimed": False,
    }


def run_campaign(
    config: CampaignConfig,
    *,
    catalog: Catalog = CATALOG,
) -> CampaignReport:
    """Run or resume one deterministic finite campaign.

    With ``output_dir`` the campaign uses SQLite deduplication and streaming
    shards. Without it, a bounded in-memory deduplicator is used for lightweight
    fixtures.
    """

    codec = FrontierCodec(catalog)
    target = min(config.work_items, codec.size)
    factory = TheoremFactory()
    output_root = Path(config.output_dir) if config.output_dir is not None else None

    proposed_total = 0
    accepted_total = 0
    rejected_total = 0
    duplicate_total = 0
    batch_index = 0
    telemetry: list[BatchTelemetry] = []
    restored_saturation: list[SaturationEntry] = []

    if config.resume:
        assert output_root is not None
        checkpoint_path = output_root / "checkpoint.json"
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("system") != "Ω-VLA-T∞²":
            raise ValueError("checkpoint belongs to a different system")
        if int(checkpoint.get("seed")) != config.seed:
            raise ValueError("resume seed must match checkpoint seed")
        proposed_total = int(checkpoint.get("proposed_cells", 0))
        accepted_total = int(checkpoint.get("accepted_cells", 0))
        rejected_total = int(checkpoint.get("rejected_quality", 0))
        duplicate_total = int(checkpoint.get("duplicates", 0))
        batch_index = int(checkpoint.get("next_batch_index", 0))
        telemetry = [
            BatchTelemetry(**item) for item in checkpoint.get("batches", [])
        ]
        restored_saturation = _restore_saturation(
            checkpoint.get("saturation_ledger", [])
        )
        if proposed_total > target:
            raise ValueError("resume target is smaller than completed checkpoint work")

    controller = FrontierController(
        batch_size=(
            int(checkpoint.get("next_batch_size"))
            if config.resume
            else config.initial_batch
        ),
        min_batch=config.min_batch,
        max_batch=config.max_batch,
        saturation_ledger=restored_saturation,
    )

    remaining = target - proposed_total
    indices = codec.iter_indices(
        remaining,
        seed=config.seed,
        start_offset=proposed_total,
    )

    memory_deduplicator = ContentDeduplicator() if output_root is None else None
    writer: StreamingShardedJSONLWriter | None = None
    disk_index: SQLiteDigestIndex | None = None
    store_manifest: StoreManifest | None = None

    if output_root is not None:
        writer = StreamingShardedJSONLWriter(
            output_root,
            records_per_shard=config.records_per_shard,
            prefix="research-cells",
            resume=config.resume,
            reset=(not config.resume and config.reset_output),
        )
        disk_index = SQLiteDigestIndex(
            output_root / "dedup.sqlite3",
            commit_interval=max(1, config.records_per_shard),
            reset=(not config.resume and config.reset_output),
        )
        disk_index.set_metadata("system", "Ω-VLA-T∞²")
        disk_index.set_metadata("version", "R0.2-MAX")
        disk_index.set_metadata("seed", str(config.seed))
        if config.resume and disk_index.count() != accepted_total:
            raise ValueError("SQLite digest count disagrees with checkpoint")

    try:
        while proposed_total < target:
            remaining = target - proposed_total
            current_size = min(controller.batch_size, remaining)
            raw_indices: list[int] = []
            for _ in range(current_size):
                try:
                    raw_indices.append(next(indices))
                except StopIteration:
                    break
            if not raw_indices:
                break

            cells = [factory.generate(codec.decode(index)) for index in raw_indices]
            batch_start_ordinal = proposed_total
            proposed_total += len(cells)
            quality_cells = [cell for cell in cells if _quality_accept(cell, config)]
            rejected = len(cells) - len(quality_cells)
            rejected_total += rejected

            accepted_batch = 0
            duplicate_batch = 0
            payloads = [cell.to_dict() for cell in quality_cells]
            if disk_index is not None and writer is not None:
                for local_ordinal, payload in enumerate(payloads):
                    is_new, _ = disk_index.add(
                        payload,
                        ordinal=batch_start_ordinal + local_ordinal,
                    )
                    if is_new:
                        writer.add(payload)
                        accepted_batch += 1
                    else:
                        duplicate_batch += 1
            else:
                assert memory_deduplicator is not None
                dedup_report = memory_deduplicator.filter(payloads)
                accepted_batch = len(dedup_report.accepted)
                duplicate_batch = len(dedup_report.duplicates)

            accepted_total += accepted_batch
            duplicate_total += duplicate_batch
            next_size = controller.observe(
                proposed=len(cells),
                accepted=accepted_batch,
                duplicates=duplicate_batch,
                rejected_quality=rejected,
            )
            telemetry.append(
                BatchTelemetry(
                    batch_index=batch_index,
                    proposed=len(cells),
                    accepted=accepted_batch,
                    rejected_quality=rejected,
                    duplicates=duplicate_batch,
                    next_batch_size=next_size,
                    acceptance_rate=(accepted_batch / len(cells)),
                    duplicate_rate=(duplicate_batch / len(cells)),
                )
            )
            batch_index += 1

            if (
                writer is not None
                and disk_index is not None
                and batch_index % config.checkpoint_every_batches == 0
            ):
                disk_index.commit()
                writer.checkpoint(
                    _checkpoint_payload(
                        config=config,
                        catalog=catalog,
                        proposed_total=proposed_total,
                        accepted_total=accepted_total,
                        rejected_total=rejected_total,
                        duplicate_total=duplicate_total,
                        batch_index=batch_index,
                        controller=controller,
                        telemetry=telemetry,
                        digest_count=disk_index.count(),
                    )
                )

        if writer is not None and disk_index is not None:
            disk_index.commit()
            store_manifest = writer.finalize(
                _checkpoint_payload(
                    config=config,
                    catalog=catalog,
                    proposed_total=proposed_total,
                    accepted_total=accepted_total,
                    rejected_total=rejected_total,
                    duplicate_total=duplicate_total,
                    batch_index=batch_index,
                    controller=controller,
                    telemetry=telemetry,
                    digest_count=disk_index.count(),
                )
            )
            writer.verify()
    finally:
        if disk_index is not None:
            disk_index.commit()
            disk_index.close()

    return CampaignReport(
        system="Ω-VLA-T∞²",
        version="R0.2-MAX",
        logical_frontier_cells=codec.size,
        requested_work_items=config.work_items,
        proposed_cells=proposed_total,
        accepted_cells=accepted_total,
        rejected_quality=rejected_total,
        duplicates=duplicate_total,
        batches=tuple(telemetry),
        saturation_ledger=tuple(controller.saturation_ledger),
        store_manifest=store_manifest,
    )
