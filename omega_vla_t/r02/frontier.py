"""Adaptive finite campaigns over the unbounded-policy Ω-VLA frontier."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .address import FrontierCodec
from .catalogs import CATALOG, Catalog
from .dedup import ContentDeduplicator
from .models import ProblemCell, SaturationEntry
from .store import ShardedJSONLStore, StoreManifest
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


def run_campaign(
    config: CampaignConfig,
    *,
    catalog: Catalog = CATALOG,
) -> CampaignReport:
    """Run one deterministic, finite campaign over a huge logical address space."""

    codec = FrontierCodec(catalog)
    factory = TheoremFactory()
    controller = FrontierController(
        batch_size=config.initial_batch,
        min_batch=config.min_batch,
        max_batch=config.max_batch,
    )
    deduplicator = ContentDeduplicator()

    target = min(config.work_items, codec.size)
    indices = codec.iter_indices(target, seed=config.seed)
    accepted_payloads: list[dict[str, Any]] = []
    telemetry: list[BatchTelemetry] = []
    proposed_total = 0
    rejected_total = 0
    duplicate_total = 0
    batch_index = 0

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
        proposed_total += len(cells)
        quality_cells = [cell for cell in cells if _quality_accept(cell, config)]
        rejected = len(cells) - len(quality_cells)
        rejected_total += rejected

        report = deduplicator.filter(cell.to_dict() for cell in quality_cells)
        accepted_payloads.extend(dict(payload) for payload in report.accepted)
        duplicate_total += len(report.duplicates)
        next_size = controller.observe(
            proposed=len(cells),
            accepted=len(report.accepted),
            duplicates=len(report.duplicates),
            rejected_quality=rejected,
        )
        telemetry.append(
            BatchTelemetry(
                batch_index=batch_index,
                proposed=len(cells),
                accepted=len(report.accepted),
                rejected_quality=rejected,
                duplicates=len(report.duplicates),
                next_batch_size=next_size,
                acceptance_rate=(len(report.accepted) / len(cells)),
                duplicate_rate=(len(report.duplicates) / len(cells)),
            )
        )
        batch_index += 1

    store_manifest: StoreManifest | None = None
    if config.output_dir is not None:
        store = ShardedJSONLStore(
            Path(config.output_dir),
            records_per_shard=config.records_per_shard,
            prefix="research-cells",
        )
        checkpoint = {
            "system": "Ω-VLA-T∞²",
            "version": "R0.2-MAX",
            "seed": config.seed,
            "requested_work_items": config.work_items,
            "proposed_cells": proposed_total,
            "accepted_cells": len(accepted_payloads),
            "known_digests": list(deduplicator.snapshot()),
            "permanent_total_cap": None,
        }
        store_manifest = store.write(accepted_payloads, checkpoint=checkpoint)

    return CampaignReport(
        system="Ω-VLA-T∞²",
        version="R0.2-MAX",
        logical_frontier_cells=codec.size,
        requested_work_items=config.work_items,
        proposed_cells=proposed_total,
        accepted_cells=len(accepted_payloads),
        rejected_quality=rejected_total,
        duplicates=duplicate_total,
        batches=tuple(telemetry),
        saturation_ledger=tuple(controller.saturation_ledger),
        store_manifest=store_manifest,
    )
