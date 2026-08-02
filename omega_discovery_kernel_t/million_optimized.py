"""Optimized million-scale writer preserving the R0.3 integrity contract.

The reference implementation in :mod:`million_frontier` is intentionally
explicit. This specialization removes two artificial throughput bottlenecks:

- filesystem free-space queries on every event;
- SQLite parent lookups when parentage is derivable exactly from sequence.

Disk safety is checked at every SQLite batch and before every shard rotation.
Parentage remains deterministic: slot zero has no parent; slots one through
seven point to the immediately preceding sequence in the same eight-event
subject.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .million_frontier import (
    COMPACT_CORE_EVENT_TYPES,
    CompactEventRecord,
    CompactMillionFrontier as ReferenceCompactMillionFrontier,
    ForcedInterruption,
    MillionFrontierConfig,
)


class CompactMillionFrontier(ReferenceCompactMillionFrontier):
    """Million-event writer with batched resource gates and arithmetic lineage."""

    def append(self, record: CompactEventRecord) -> bool:
        if record.sequence < self.next_sequence:
            self.telemetry.duplicate_events += 1
            return False
        if record.sequence != self.next_sequence:
            self.telemetry.rejected_events += 1
            raise ValueError(
                f"non-contiguous sequence: expected {self.next_sequence}, observed {record.sequence}"
            )
        expected = self.make_record(record.sequence)
        if record != expected:
            self.telemetry.rejected_events += 1
            raise ValueError(f"compact event validation failed at sequence {record.sequence}")

        subject_index, slot = divmod(record.sequence, len(COMPACT_CORE_EVENT_TYPES))
        if record.subject_index != subject_index or record.event_code != slot:
            raise ValueError("event sequence does not match its subject and core-loop slot")
        expected_parent = None if slot == 0 else record.sequence - 1
        if record.parent_sequence != expected_parent:
            raise ValueError(
                f"invalid compact parent at sequence {record.sequence}: "
                f"expected {expected_parent}, observed {record.parent_sequence}"
            )
        if expected_parent is not None and expected_parent // len(COMPACT_CORE_EVENT_TYPES) != subject_index:
            raise ValueError("compact parent crosses a subject boundary")

        line = json.dumps(record.json_array(), separators=(",", ":")) + "\n"
        encoded = line.encode("utf-8")

        # Resource queries are intentionally batched. The safety gate is still
        # evaluated before a new batch and before any shard rotation.
        if not self._batch_rows:
            self._disk_gate(len(encoded) * self.config.sqlite_batch_size)
        if self.current_shard_bytes and self.current_shard_bytes + len(encoded) > self.shard_target_bytes:
            self._disk_gate(max(len(encoded), self.shard_target_bytes))
            self._rotate_shard()

        assert self.current_stream is not None
        assert self.current_shard_path is not None
        offset = self.current_shard_bytes
        self.current_stream.write(line)
        self.current_shard_bytes += len(encoded)
        relative = self.current_shard_path.relative_to(self.output_dir).as_posix()
        self._batch_rows.append(
            (
                record.sequence,
                record.event_id,
                record.event_code,
                record.subject_index,
                record.namespace_index,
                record.parent_sequence,
                record.timestamp_offset_us,
                record.event_hash,
                relative,
                offset,
                len(encoded),
            )
        )
        from .million_frontier import _chain_digest  # local import keeps the public API minimal

        self.ledger_digest = _chain_digest(self.ledger_digest, record.event_hash)
        self.next_sequence += 1
        self.telemetry.accepted_events += 1
        self.telemetry.bytes_written += len(encoded)

        if len(self._batch_rows) >= self.config.sqlite_batch_size:
            self._flush_batch()
        if self.next_sequence % self.config.checkpoint_interval == 0:
            self.write_checkpoint(complete=False)
        return True


def run_forced_resume_million_frontier(
    output_dir: str | Path,
    *,
    config: MillionFrontierConfig | None = None,
) -> dict[str, object]:
    """Force interruption, restore the exact cursor, then reach the finite target."""

    config = config or MillionFrontierConfig()
    issues = config.validate()
    if issues:
        raise ValueError("; ".join(issues))
    output = Path(output_dir)
    interrupted = False
    try:
        with CompactMillionFrontier(output, config=config, resume=False) as frontier:
            frontier.run(interrupt_at=config.forced_interrupt_after)
    except ForcedInterruption:
        interrupted = True
    if not interrupted:
        raise AssertionError("the configured forced interruption did not occur")

    incomplete_checkpoint = json.loads(
        (output / "million-checkpoint.json").read_text(encoding="utf-8")
    )
    if incomplete_checkpoint["complete"]:
        raise AssertionError("forced interruption checkpoint must remain incomplete")
    phase_one_accepted = int(incomplete_checkpoint["next_sequence"])
    if phase_one_accepted != config.forced_interrupt_after:
        raise AssertionError(
            f"interruption cursor mismatch: {phase_one_accepted} != {config.forced_interrupt_after}"
        )

    with CompactMillionFrontier(output, config=config, resume=True) as frontier:
        accepted_phase_two = frontier.run()
        final_manifest = frontier.close(complete=True)

    expected_phase_two = config.target_events - config.forced_interrupt_after
    if accepted_phase_two != expected_phase_two:
        raise AssertionError(
            f"resume wrote {accepted_phase_two} events; expected {expected_phase_two}"
        )

    summary: dict[str, Any] = {
        "schema": "omega_discovery_kernel.million_forced_resume.v0.3",
        "phase_one": {
            "accepted": phase_one_accepted,
            "interrupted": True,
            "checkpoint_complete": False,
        },
        "phase_two": {
            "accepted": accepted_phase_two,
            "resumed": True,
        },
        "target_events": config.target_events,
        "forced_interrupt_after": config.forced_interrupt_after,
        "exact_total_reached": final_manifest["integrity"]["event_count"] == config.target_events,
        "manifest": final_manifest,
        "finite_target_is_not_permanent_ceiling": True,
        "optimization": {
            "per_event_disk_queries": 0,
            "per_event_parent_sql_queries": 0,
            "disk_gate_frequency": "once per SQLite batch and before shard rotation",
            "parent_validation": "deterministic arithmetic from sequence and eight-event slot",
        },
    }
    (output / "million-experiment-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary
