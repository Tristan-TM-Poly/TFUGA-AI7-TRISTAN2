from __future__ import annotations

from dataclasses import asdict, dataclass
import time
from typing import Any, Callable, Iterable, Iterator, Mapping

from .budget import AdaptiveBudgetController
from .ledger import IntentLedger
from .models import BudgetObservation, WorkRecord


Executor = Callable[[WorkRecord], tuple[str, Mapping[str, Any]]]


@dataclass(frozen=True)
class CampaignReport:
    intent_id: str
    status: str
    consumed: int
    inserted: int
    duplicates: int
    validated: int
    rejected: int
    blocked: int
    failed: int
    batches: int
    checkpoint_offset: int
    budget_state: Mapping[str, Any]
    elapsed_seconds: float
    source_exhausted: bool
    no_permanent_total_cap: bool = True
    remote_mutations: int = 0
    automatic_merge: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CampaignRunner:
    """Execute a finite stream with exact checkpoints and adaptive batches."""

    def __init__(
        self,
        ledger: IntentLedger,
        *,
        controller: AdaptiveBudgetController | None = None,
        worker_id: str = "omega-intent-r02",
    ) -> None:
        self.ledger = ledger
        self.controller = controller or AdaptiveBudgetController()
        self.worker_id = worker_id

    def run(
        self,
        intent_id: str,
        records: Iterable[WorkRecord],
        executor: Executor,
        *,
        checkpoint_key: str = "campaign",
        max_records: int | None = None,
    ) -> CampaignReport:
        if max_records is not None and max_records < 0:
            raise ValueError("max_records cannot be negative")
        checkpoint = self.ledger.load_checkpoint(intent_id, checkpoint_key) or {}
        skip = int(checkpoint.get("offset", 0))
        iterator = iter(records)
        for _ in range(skip):
            try:
                next(iterator)
            except StopIteration:
                break

        started = time.monotonic()
        consumed = inserted = duplicates = validated = rejected = blocked = failed = batches = 0
        source_exhausted = False

        while max_records is None or consumed < max_records:
            item_budget = self.controller.state.batch_items
            byte_budget = self.controller.state.batch_bytes
            batch: list[WorkRecord] = []
            batch_bytes = 0
            while len(batch) < item_budget and (max_records is None or consumed + len(batch) < max_records):
                try:
                    record = next(iterator)
                except StopIteration:
                    source_exhausted = True
                    break
                size = record.estimated_bytes
                batch.append(record)
                batch_bytes += size
                if batch_bytes >= byte_budget:
                    break
            if not batch:
                break

            batch_started = time.monotonic()
            terminal_entries: list[tuple[WorkRecord, str, Mapping[str, Any]]] = []
            failed_batch = 0
            for record in batch:
                try:
                    outcome, evidence = executor(record)
                    if outcome not in {"validated", "rejected", "blocked"}:
                        raise ValueError(f"unsupported executor outcome: {outcome}")
                    terminal_entries.append((record, outcome, dict(evidence)))
                except Exception as exc:
                    failed += 1
                    failed_batch += 1
                    self.ledger.record_residual(
                        intent_id,
                        "executor_failure",
                        {
                            "record_id": record.record_id,
                            "exception_type": type(exc).__name__,
                            "message": str(exc),
                        },
                        record_id=record.record_id,
                        severity="error",
                    )

            outcome_counts = self.ledger.terminalize_batch(terminal_entries)
            consumed += len(batch)
            inserted += outcome_counts["inserted"]
            duplicates += outcome_counts["duplicates"]
            validated += outcome_counts["validated"]
            rejected += outcome_counts["rejected"]
            blocked += outcome_counts["blocked"]
            batches += 1
            elapsed_batch = time.monotonic() - batch_started
            processed = len(batch)
            self.controller.observe(
                BudgetObservation(
                    processed=processed,
                    accepted=outcome_counts["validated"],
                    rejected=outcome_counts["rejected"] + outcome_counts["blocked"] + outcome_counts["duplicates"],
                    failed=failed_batch,
                    elapsed_seconds=elapsed_batch,
                )
            )
            self.ledger.save_checkpoint(
                intent_id,
                checkpoint_key,
                {
                    "offset": skip + consumed,
                    "batches": int(checkpoint.get("batches", 0)) + batches,
                    "budget_state": self.controller.state.to_dict(),
                    "last_batch_items": len(batch),
                    "source_exhausted": source_exhausted,
                },
            )
            if source_exhausted:
                break

        status = "completed" if source_exhausted else "checkpointed"
        return CampaignReport(
            intent_id=intent_id,
            status=status,
            consumed=consumed,
            inserted=inserted,
            duplicates=duplicates,
            validated=validated,
            rejected=rejected,
            blocked=blocked,
            failed=failed,
            batches=batches,
            checkpoint_offset=skip + consumed,
            budget_state=self.controller.state.to_dict(),
            elapsed_seconds=time.monotonic() - started,
            source_exhausted=source_exhausted,
        )


def synthetic_records(
    intent_id: str,
    count: int,
    *,
    start_offset: int = 0,
    namespaces: int = 16,
    dependency_stride: int = 0,
) -> Iterator[WorkRecord]:
    if count < 0 or start_offset < 0:
        raise ValueError("count and start_offset cannot be negative")
    if namespaces < 1:
        raise ValueError("namespaces must be positive")
    previous_id: str | None = None
    for offset in range(start_offset, start_offset + count):
        dependency_ids: tuple[str, ...] = ()
        payload = {
            "logical_offset": offset,
            "namespace": offset % namespaces,
            "candidate": f"intent-candidate-{offset:016d}",
        }
        probe = WorkRecord(intent_id=intent_id, kind="synthetic", payload=payload)
        if dependency_stride and offset > start_offset and (offset - start_offset) % dependency_stride == 0:
            dependency_ids = (previous_id,) if previous_id else ()
            probe = WorkRecord(
                intent_id=intent_id,
                kind="synthetic",
                payload=payload,
                dependency_ids=dependency_ids,
            )
        previous_id = probe.record_id
        yield probe


def deterministic_executor(record: WorkRecord) -> tuple[str, Mapping[str, Any]]:
    offset = int(record.payload.get("logical_offset", 0))
    if offset and offset % 997 == 0:
        return "rejected", {"reason": "deterministic_negative_fixture", "offset": offset}
    return "validated", {"fixture": "deterministic", "offset": offset}
