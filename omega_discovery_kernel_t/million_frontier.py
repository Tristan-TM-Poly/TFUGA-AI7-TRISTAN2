"""Ω-DISCOVERY-KERNEL-T∞ R0.3 million-event frontier.

This module exercises a genuinely large append-only event ledger without
materializing one million Python event objects at once. Every compact record is
still an individual, content-hashed event with a deterministic identity,
subject, event type, parent, sequence, timestamp offset, shard location, and
SQLite index row.

The one-million target is a finite OAKBench objective, never a permanent
architecture ceiling. Physical storage, time, memory, legal, safety, quality,
and rollback constraints remain active.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import shutil
import sqlite3
import time
from typing import Any, Iterator, Sequence, TextIO

from .events import canonical_json

COMPACT_CORE_EVENT_TYPES: tuple[str, ...] = (
    "ObservationEvent",
    "ClaimEvent",
    "GeneratorCandidate",
    "ExperimentSpec",
    "ResultPacket",
    "OAKTransition",
    "MMinusRule",
    "ActionProposal",
)

_EVENT_CODE = {name: index for index, name in enumerate(COMPACT_CORE_EVENT_TYPES)}
_FULL_MASK = (1 << len(COMPACT_CORE_EVENT_TYPES)) - 1
_ZERO_DIGEST = "0" * 64


def _stable_digest(*parts: object) -> str:
    raw = "\x1f".join(canonical_json(part) for part in parts).encode("utf-8")
    return sha256(raw).hexdigest()


def _event_id(seed: int, sequence: int, subject_index: int, slot: int) -> str:
    return f"evt_{_stable_digest('million-frontier', seed, sequence, subject_index, slot)[:24]}"


def _chain_digest(previous: str, event_hash: str) -> str:
    return sha256((previous + event_hash).encode("ascii")).hexdigest()


def _rss_bytes() -> int:
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux reports KiB; macOS reports bytes. GitHub Actions uses Linux.
    return int(usage * 1024 if usage < 10**10 else usage)


@dataclass(frozen=True, slots=True)
class MillionFrontierConfig:
    """Finite frontier calibration, not a total-event controller ceiling."""

    target_events: int = 1_000_000
    forced_interrupt_after: int = 524_288
    seed: int = 73
    namespace_count: int = 256
    initial_shard_bytes: int = 4 * 1024 * 1024
    shard_growth_factor: float = 1.6
    checkpoint_interval: int = 50_000
    sqlite_batch_size: int = 10_000
    minimum_free_bytes: int = 512 * 1024 * 1024
    latency_saturation_seconds_per_10k: float = 8.0
    rss_saturation_bytes: int = 2 * 1024 * 1024 * 1024

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.target_events <= 0:
            issues.append("target_events must be positive for a finite experiment")
        if self.target_events % len(COMPACT_CORE_EVENT_TYPES):
            issues.append("target_events must be divisible by the eight-event core loop")
        if not 0 < self.forced_interrupt_after < self.target_events:
            issues.append("forced_interrupt_after must be inside the finite target")
        if self.forced_interrupt_after % len(COMPACT_CORE_EVENT_TYPES):
            issues.append("forced_interrupt_after must end on a complete subject boundary")
        if self.namespace_count <= 0:
            issues.append("namespace_count must be positive")
        if self.initial_shard_bytes <= 0:
            issues.append("initial_shard_bytes must be positive")
        if self.shard_growth_factor <= 1.0:
            issues.append("shard_growth_factor must be greater than one")
        if self.checkpoint_interval <= 0:
            issues.append("checkpoint_interval must be positive")
        if self.sqlite_batch_size <= 0:
            issues.append("sqlite_batch_size must be positive")
        if self.minimum_free_bytes < 0:
            issues.append("minimum_free_bytes must be non-negative")
        return issues


@dataclass(frozen=True, slots=True)
class CompactEventRecord:
    sequence: int
    event_id: str
    event_code: int
    subject_index: int
    namespace_index: int
    parent_sequence: int | None
    timestamp_offset_us: int
    event_hash: str

    @property
    def event_type(self) -> str:
        return COMPACT_CORE_EVENT_TYPES[self.event_code]

    def json_array(self) -> list[object]:
        return [
            self.sequence,
            self.event_id,
            self.event_code,
            self.subject_index,
            self.namespace_index,
            self.parent_sequence,
            self.timestamp_offset_us,
            self.event_hash,
        ]


@dataclass(frozen=True, slots=True)
class SaturationRecord:
    saturation_id: str
    kind: str
    event_count: int
    shard_index: int
    observed_value: float | int | str
    threshold: float | int | str
    context: str
    negative_memory_rule: str
    redesign_action: str
    recorded_at_epoch_s: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class MillionTelemetry:
    accepted_events: int = 0
    duplicate_events: int = 0
    rejected_events: int = 0
    bytes_written: int = 0
    shards_closed: int = 0
    sqlite_commits: int = 0
    checkpoints_written: int = 0
    forced_interruptions: int = 0
    saturation_records: int = 0
    started_at: float = field(default_factory=time.monotonic)
    phase_started_at: float = field(default_factory=time.monotonic)
    peak_rss_bytes: int = 0
    last_batch_seconds: float = 0.0

    def update_rss(self) -> int:
        current = _rss_bytes()
        self.peak_rss_bytes = max(self.peak_rss_bytes, current)
        return current

    def to_dict(self) -> dict[str, object]:
        elapsed = max(time.monotonic() - self.started_at, 1.0e-9)
        return {
            "accepted_events": self.accepted_events,
            "duplicate_events": self.duplicate_events,
            "rejected_events": self.rejected_events,
            "bytes_written": self.bytes_written,
            "shards_closed": self.shards_closed,
            "sqlite_commits": self.sqlite_commits,
            "checkpoints_written": self.checkpoints_written,
            "forced_interruptions": self.forced_interruptions,
            "saturation_records": self.saturation_records,
            "elapsed_seconds": round(elapsed, 6),
            "events_per_second": round(self.accepted_events / elapsed, 3),
            "bytes_per_second": round(self.bytes_written / elapsed, 3),
            "peak_rss_bytes": self.peak_rss_bytes,
            "last_batch_seconds": round(self.last_batch_seconds, 6),
        }


class ForcedInterruption(RuntimeError):
    """Expected OAKBench interruption used to validate exact resume semantics."""


class CompactMillionFrontier:
    """Disk-backed compact event ledger optimized for million-scale OAKBench runs."""

    def __init__(
        self,
        output_dir: str | Path,
        *,
        config: MillionFrontierConfig | None = None,
        resume: bool = False,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.config = config or MillionFrontierConfig()
        issues = self.config.validate()
        if issues:
            raise ValueError("; ".join(issues))
        self.shards_dir = self.output_dir / "shards"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.shards_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.output_dir / "million-index.sqlite3"
        self.checkpoint_path = self.output_dir / "million-checkpoint.json"
        self.manifest_path = self.output_dir / "million-manifest.json"
        self.telemetry_path = self.output_dir / "million-telemetry.json"
        self.saturation_path = self.output_dir / "saturation-m-minus.jsonl"
        self.templates_path = self.output_dir / "event-templates.json"

        self.connection = sqlite3.connect(self.index_path)
        self.connection.row_factory = sqlite3.Row
        self._initialize_database()

        self.telemetry = MillionTelemetry()
        self.next_sequence = 0
        self.shard_index = 0
        self.shard_target_bytes = self.config.initial_shard_bytes
        self.current_shard_bytes = 0
        self.current_shard_path: Path | None = None
        self.current_stream: TextIO | None = None
        self.ledger_digest = _ZERO_DIGEST
        self._batch_rows: list[tuple[object, ...]] = []
        self._batch_started = time.monotonic()
        self._closed = False

        if resume:
            self._restore()
        elif self._existing_event_count():
            raise FileExistsError(
                f"frontier already contains events: {self.output_dir}; use resume=True or a new directory"
            )
        self._write_templates()
        self._open_shard(append=resume)

    def _initialize_database(self) -> None:
        self.connection.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;
            PRAGMA temp_store=MEMORY;
            PRAGMA cache_size=-65536;
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY,
                event_id TEXT NOT NULL UNIQUE,
                event_code INTEGER NOT NULL,
                subject_index INTEGER NOT NULL,
                namespace_index INTEGER NOT NULL,
                parent_sequence INTEGER,
                timestamp_offset_us INTEGER NOT NULL,
                event_hash TEXT NOT NULL,
                shard_path TEXT NOT NULL,
                byte_offset INTEGER NOT NULL,
                byte_length INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_million_event_id ON events(event_id);
            CREATE INDEX IF NOT EXISTS idx_million_subject ON events(subject_index);
            CREATE INDEX IF NOT EXISTS idx_million_parent ON events(parent_sequence);
            CREATE TABLE IF NOT EXISTS subjects (
                subject_index INTEGER PRIMARY KEY,
                namespace_index INTEGER NOT NULL,
                event_count INTEGER NOT NULL,
                core_mask INTEGER NOT NULL,
                first_sequence INTEGER NOT NULL,
                last_sequence INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def _existing_event_count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS count FROM events").fetchone()
        return int(row["count"] or 0)

    def _write_templates(self) -> None:
        if self.templates_path.exists():
            return
        templates = {
            "schema": "omega_discovery_kernel.compact_templates.v0.3",
            "record_array_fields": [
                "sequence",
                "event_id",
                "event_code",
                "subject_index",
                "namespace_index",
                "parent_sequence",
                "timestamp_offset_us",
                "event_hash",
            ],
            "event_types": [
                {
                    "code": code,
                    "event_type": name,
                    "provenance": "omega_discovery_kernel_t.million_frontier",
                    "domain": "million-scale-workflow-validation",
                    "status": "synthetic_scale_fixture_not_scientific_evidence",
                }
                for code, name in enumerate(COMPACT_CORE_EVENT_TYPES)
            ],
            "timestamp_origin": "2026-08-02T18:30:00Z",
            "parent_rule": "slot zero has no parent; other slots reference the previous sequence in the same subject",
            "identity_rule": "deterministic SHA-256-derived evt identifier",
            "hash_rule": "SHA-256 over canonical compact semantic fields",
        }
        self.templates_path.write_text(
            json.dumps(templates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def _restore(self) -> None:
        count = self._existing_event_count()
        if not count:
            return
        row = self.connection.execute(
            "SELECT * FROM events ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        self.next_sequence = int(row["sequence"]) + 1
        relative = Path(str(row["shard_path"]))
        self.current_shard_path = self.output_dir / relative
        self.current_shard_bytes = int(row["byte_offset"]) + int(row["byte_length"])
        try:
            self.shard_index = int(relative.stem.split("-")[-1])
        except ValueError:
            self.shard_index = 0
        checkpoint = {}
        if self.checkpoint_path.exists():
            checkpoint = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        self.shard_target_bytes = int(
            checkpoint.get("shard_target_bytes", self.config.initial_shard_bytes)
        )
        self.ledger_digest = str(checkpoint.get("ledger_digest", _ZERO_DIGEST))
        if self.ledger_digest == _ZERO_DIGEST:
            for digest_row in self.connection.execute(
                "SELECT event_hash FROM events ORDER BY sequence"
            ):
                self.ledger_digest = _chain_digest(
                    self.ledger_digest, str(digest_row["event_hash"])
                )
        self.telemetry.accepted_events = count
        bytes_row = self.connection.execute(
            "SELECT COALESCE(SUM(byte_length), 0) AS total FROM events"
        ).fetchone()
        self.telemetry.bytes_written = int(bytes_row["total"] or 0)
        self.telemetry.update_rss()

    def _relative_shard(self) -> Path:
        return Path("shards") / f"compact-events-{self.shard_index:08d}.jsonl"

    def _open_shard(self, *, append: bool) -> None:
        if self.current_stream is not None:
            return
        if self.current_shard_path is None:
            self.current_shard_path = self.output_dir / self._relative_shard()
        mode = "a" if append and self.current_shard_path.exists() else "w"
        self.current_stream = self.current_shard_path.open(mode, encoding="utf-8", newline="\n")
        self.current_shard_bytes = self.current_shard_path.stat().st_size if mode == "a" else 0

    def _flush_batch(self) -> None:
        if not self._batch_rows:
            return
        started = time.monotonic()
        self.connection.executemany(
            """
            INSERT INTO events (
                sequence, event_id, event_code, subject_index, namespace_index,
                parent_sequence, timestamp_offset_us, event_hash, shard_path,
                byte_offset, byte_length
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            self._batch_rows,
        )
        subject_updates: dict[int, tuple[int, int, int, int]] = {}
        for row in self._batch_rows:
            sequence = int(row[0])
            event_code = int(row[2])
            subject_index = int(row[3])
            namespace_index = int(row[4])
            current = subject_updates.get(subject_index)
            bit = 1 << event_code
            if current is None:
                subject_updates[subject_index] = (namespace_index, 1, bit, sequence)
            else:
                subject_updates[subject_index] = (
                    current[0], current[1] + 1, current[2] | bit, sequence
                )
        for subject_index, (namespace_index, count, mask, last_sequence) in subject_updates.items():
            first_sequence = subject_index * len(COMPACT_CORE_EVENT_TYPES)
            self.connection.execute(
                """
                INSERT INTO subjects (
                    subject_index, namespace_index, event_count, core_mask,
                    first_sequence, last_sequence
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(subject_index) DO UPDATE SET
                    event_count = subjects.event_count + excluded.event_count,
                    core_mask = subjects.core_mask | excluded.core_mask,
                    last_sequence = excluded.last_sequence
                """,
                (
                    subject_index,
                    namespace_index,
                    count,
                    mask,
                    first_sequence,
                    last_sequence,
                ),
            )
        self.connection.commit()
        self.telemetry.sqlite_commits += 1
        self.telemetry.last_batch_seconds = time.monotonic() - started
        self._batch_rows.clear()
        self._batch_started = time.monotonic()
        self._observe_batch_saturations()

    def _observe_batch_saturations(self) -> None:
        rss = self.telemetry.update_rss()
        if self.telemetry.last_batch_seconds >= self.config.latency_saturation_seconds_per_10k:
            self.record_saturation(
                kind="sqlite_batch_latency",
                observed_value=self.telemetry.last_batch_seconds,
                threshold=self.config.latency_saturation_seconds_per_10k,
                context="SQLite batch commit exceeded the calibrated latency frontier.",
                negative_memory_rule="Do not increase batch or index complexity without measuring commit latency.",
                redesign_action="Reduce batch size, repartition indexes, or move cold lineage data to separate storage.",
            )
        if rss >= self.config.rss_saturation_bytes:
            self.record_saturation(
                kind="resident_memory",
                observed_value=rss,
                threshold=self.config.rss_saturation_bytes,
                context="Peak resident memory crossed the calibrated safety frontier.",
                negative_memory_rule="Never trade unbounded RAM growth for throughput.",
                redesign_action="Reduce SQLite cache, batch size, and in-process state; preserve disk-backed indexes.",
            )

    def _disk_gate(self, next_bytes: int) -> None:
        free = shutil.disk_usage(self.output_dir).free
        required = self.config.minimum_free_bytes + max(next_bytes, self.shard_target_bytes)
        if free < required:
            self.record_saturation(
                kind="disk_backpressure",
                observed_value=free,
                threshold=required,
                context="Free storage fell below the rollback and shard-finalization reserve.",
                negative_memory_rule="Never continue writing when rollback storage cannot be guaranteed.",
                redesign_action="Pause, checkpoint, expand storage, compact indexes, or move immutable shards.",
            )
            raise RuntimeError(
                f"disk backpressure: {free} free bytes is below required reserve {required}"
            )

    def _rotate_shard(self) -> None:
        self._flush_batch()
        assert self.current_stream is not None
        self.current_stream.flush()
        os.fsync(self.current_stream.fileno())
        self.current_stream.close()
        self.current_stream = None
        self.telemetry.shards_closed += 1
        self.shard_index += 1
        self.shard_target_bytes = max(
            self.shard_target_bytes + 1,
            int(self.shard_target_bytes * self.config.shard_growth_factor),
        )
        self.current_shard_path = self.output_dir / self._relative_shard()
        self.current_shard_bytes = 0
        self._open_shard(append=False)

    def make_record(self, sequence: int) -> CompactEventRecord:
        subject_index, slot = divmod(sequence, len(COMPACT_CORE_EVENT_TYPES))
        namespace_index = subject_index % self.config.namespace_count
        parent_sequence = None if slot == 0 else sequence - 1
        event_id = _event_id(self.config.seed, sequence, subject_index, slot)
        semantic = {
            "sequence": sequence,
            "event_id": event_id,
            "event_type": COMPACT_CORE_EVENT_TYPES[slot],
            "subject_index": subject_index,
            "namespace_index": namespace_index,
            "parent_sequence": parent_sequence,
            "timestamp_offset_us": sequence,
            "seed": self.config.seed,
            "status": "synthetic_scale_fixture_not_scientific_evidence",
        }
        return CompactEventRecord(
            sequence=sequence,
            event_id=event_id,
            event_code=slot,
            subject_index=subject_index,
            namespace_index=namespace_index,
            parent_sequence=parent_sequence,
            timestamp_offset_us=sequence,
            event_hash=sha256(canonical_json(semantic).encode("utf-8")).hexdigest(),
        )

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
        if record.parent_sequence is not None:
            if record.parent_sequence != record.sequence - 1:
                raise ValueError("compact parent must be the previous sequence in the subject")
            parent = self.connection.execute(
                "SELECT subject_index FROM events WHERE sequence = ?",
                (record.parent_sequence,),
            ).fetchone()
            if parent is None and not any(
                int(row[0]) == record.parent_sequence for row in self._batch_rows
            ):
                raise ValueError(f"missing compact parent sequence {record.parent_sequence}")
            if parent is not None and int(parent["subject_index"]) != record.subject_index:
                raise ValueError("compact parent crosses a subject boundary")

        line = json.dumps(record.json_array(), separators=(",", ":")) + "\n"
        encoded = line.encode("utf-8")
        self._disk_gate(len(encoded))
        if self.current_shard_bytes and self.current_shard_bytes + len(encoded) > self.shard_target_bytes:
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
        self.ledger_digest = _chain_digest(self.ledger_digest, record.event_hash)
        self.next_sequence += 1
        self.telemetry.accepted_events += 1
        self.telemetry.bytes_written += len(encoded)

        if len(self._batch_rows) >= self.config.sqlite_batch_size:
            self._flush_batch()
        if self.next_sequence % self.config.checkpoint_interval == 0:
            self.write_checkpoint(complete=False)
        return True

    def record_saturation(
        self,
        *,
        kind: str,
        observed_value: float | int | str,
        threshold: float | int | str,
        context: str,
        negative_memory_rule: str,
        redesign_action: str,
    ) -> SaturationRecord:
        record = SaturationRecord(
            saturation_id=f"M-{_stable_digest(kind, self.next_sequence, observed_value, threshold)[:24]}",
            kind=kind,
            event_count=self.next_sequence,
            shard_index=self.shard_index,
            observed_value=observed_value,
            threshold=threshold,
            context=context,
            negative_memory_rule=negative_memory_rule,
            redesign_action=redesign_action,
            recorded_at_epoch_s=time.time(),
        )
        with self.saturation_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        self.telemetry.saturation_records += 1
        return record

    def write_checkpoint(self, *, complete: bool) -> dict[str, object]:
        self._flush_batch()
        if self.current_stream is not None:
            self.current_stream.flush()
        checkpoint = {
            "schema": "omega_discovery_kernel.million_checkpoint.v0.3",
            "next_sequence": self.next_sequence,
            "target_events": self.config.target_events,
            "shard_index": self.shard_index,
            "shard_target_bytes": self.shard_target_bytes,
            "current_shard_bytes": self.current_shard_bytes,
            "ledger_digest": self.ledger_digest,
            "complete": complete,
            "finite_target_is_not_permanent_ceiling": True,
        }
        temporary = self.checkpoint_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(temporary, self.checkpoint_path)
        self.telemetry.checkpoints_written += 1
        return checkpoint

    def run(self, *, interrupt_at: int | None = None) -> int:
        accepted_this_phase = 0
        for sequence in range(self.next_sequence, self.config.target_events):
            if interrupt_at is not None and sequence >= interrupt_at:
                self.telemetry.forced_interruptions += 1
                self.record_saturation(
                    kind="forced_interruption",
                    observed_value=sequence,
                    threshold=interrupt_at,
                    context="OAKBench deliberately terminated the writer on a complete-subject boundary.",
                    negative_memory_rule="Never treat process completion as proof of resumability; force interruption and verify exact continuation.",
                    redesign_action="Resume from checkpoint, reject duplicates, verify digest continuity and subject completeness.",
                )
                self.write_checkpoint(complete=False)
                raise ForcedInterruption(f"forced interruption at event {sequence}")
            if self.append(self.make_record(sequence)):
                accepted_this_phase += 1
        return accepted_this_phase

    def integrity_report(self) -> dict[str, int | bool | str]:
        self._flush_batch()
        count_row = self.connection.execute(
            "SELECT COUNT(*) AS count, COUNT(DISTINCT event_id) AS distinct_ids FROM events"
        ).fetchone()
        orphan_row = self.connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM events child
            LEFT JOIN events parent ON child.parent_sequence = parent.sequence
            WHERE child.parent_sequence IS NOT NULL AND parent.sequence IS NULL
            """
        ).fetchone()
        subject_row = self.connection.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN event_count = 8 AND core_mask = ? THEN 1 ELSE 0 END) AS complete
            FROM subjects
            """,
            (_FULL_MASK,),
        ).fetchone()
        mminus_row = self.connection.execute(
            "SELECT COUNT(*) AS count FROM events WHERE event_code = ?",
            (_EVENT_CODE["MMinusRule"],),
        ).fetchone()
        sequence_row = self.connection.execute(
            "SELECT MIN(sequence) AS minimum, MAX(sequence) AS maximum FROM events"
        ).fetchone()
        event_count = int(count_row["count"] or 0)
        distinct_ids = int(count_row["distinct_ids"] or 0)
        subjects = int(subject_row["total"] or 0)
        complete_subjects = int(subject_row["complete"] or 0)
        return {
            "event_count": event_count,
            "distinct_event_ids": distinct_ids,
            "duplicate_ids": event_count - distinct_ids,
            "orphan_parent_count": int(orphan_row["count"] or 0),
            "subject_count": subjects,
            "complete_subject_count": complete_subjects,
            "m_minus_event_count": int(mminus_row["count"] or 0),
            "minimum_sequence": int(sequence_row["minimum"] or 0),
            "maximum_sequence": int(sequence_row["maximum"] or -1),
            "contiguous": event_count == 0
            or (
                int(sequence_row["minimum"] or 0) == 0
                and int(sequence_row["maximum"] or -1) == event_count - 1
            ),
            "all_subjects_complete": subjects == complete_subjects,
            "ledger_digest": self.ledger_digest,
        }

    def manifest(self, *, complete: bool) -> dict[str, object]:
        integrity = self.integrity_report()
        saturation_count = 0
        if self.saturation_path.exists():
            saturation_count = sum(
                1 for line in self.saturation_path.read_text(encoding="utf-8").splitlines() if line.strip()
            )
        return {
            "schema": "omega_discovery_kernel.million_manifest.v0.3",
            "config": asdict(self.config),
            "checkpoint_complete": complete,
            "next_sequence": self.next_sequence,
            "shard_count": self.shard_index + 1,
            "current_shard_target_bytes": self.shard_target_bytes,
            "integrity": integrity,
            "telemetry": self.telemetry.to_dict(),
            "saturation_record_count": saturation_count,
            "record_encoding": "one compact JSON array per event plus SQLite index row",
            "remote_mutations": 0,
            "oak_status": "R0.3_MILLION_SCALE_WORKFLOW_VALIDATION_NOT_SCIENTIFIC_EVIDENCE",
            "unbounded_boundary": (
                "The million-event target is a finite OAKBench experiment. No permanent total-event ceiling "
                "is encoded; physical resources, safety, legal constraints, quality gates and rollback remain binding."
            ),
        }

    def close(self, *, complete: bool) -> dict[str, object]:
        if self._closed:
            return json.loads(self.manifest_path.read_text(encoding="utf-8")) if self.manifest_path.exists() else {}
        self._flush_batch()
        if self.current_stream is not None:
            self.current_stream.flush()
            os.fsync(self.current_stream.fileno())
            self.current_stream.close()
            self.current_stream = None
            self.telemetry.shards_closed += 1
        self.write_checkpoint(complete=complete)
        manifest = self.manifest(complete=complete)
        self.manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        self.telemetry_path.write_text(
            json.dumps(self.telemetry.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.connection.commit()
        self.connection.close()
        self._closed = True
        return manifest

    def __enter__(self) -> "CompactMillionFrontier":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close(complete=exc is None and self.next_sequence == self.config.target_events)


def run_forced_resume_million_frontier(
    output_dir: str | Path,
    *,
    config: MillionFrontierConfig | None = None,
) -> dict[str, object]:
    """Force one interruption, resume exactly, and validate the final frontier."""

    config = config or MillionFrontierConfig()
    issues = config.validate()
    if issues:
        raise ValueError("; ".join(issues))
    output = Path(output_dir)
    phase_one = {"accepted": 0, "interrupted": False}
    try:
        with CompactMillionFrontier(output, config=config, resume=False) as frontier:
            phase_one["accepted"] = frontier.run(interrupt_at=config.forced_interrupt_after)
    except ForcedInterruption:
        phase_one["interrupted"] = True
    if not phase_one["interrupted"]:
        raise AssertionError("the configured forced interruption did not occur")

    with CompactMillionFrontier(output, config=config, resume=True) as frontier:
        accepted_phase_two = frontier.run()
        final_manifest = frontier.close(complete=True)

    summary = {
        "schema": "omega_discovery_kernel.million_forced_resume.v0.3",
        "phase_one": phase_one,
        "phase_two": {"accepted": accepted_phase_two, "resumed": True},
        "target_events": config.target_events,
        "forced_interrupt_after": config.forced_interrupt_after,
        "exact_total_reached": final_manifest["integrity"]["event_count"] == config.target_events,
        "manifest": final_manifest,
        "finite_target_is_not_permanent_ceiling": True,
    }
    (output / "million-experiment-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary
