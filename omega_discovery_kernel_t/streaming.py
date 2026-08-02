"""Adaptive disk-backed frontier for tens of thousands of discovery events.

The streaming ledger avoids loading the full graph in memory.  It uses JSONL
shards for immutable event bytes, SQLite for identity/parent indexes, and a
checkpoint for resumability.  ``target_events`` in a frontier experiment is a
finite test objective, not a permanent architecture ceiling.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sqlite3
import time
from typing import Any, Iterable, Iterator, Mapping, Sequence, TextIO

from .catalog import event_spec
from .events import DiscoveryEvent, OAK_STATUSES, canonical_json, parse_timestamp


CORE_LOOP_EVENT_TYPES = (
    "ObservationEvent",
    "ClaimEvent",
    "GeneratorCandidate",
    "ExperimentSpec",
    "ResultPacket",
    "OAKTransition",
    "MMinusRule",
    "ActionProposal",
)

PROMOTED_STATUSES = {
    "DEMONSTRATED",
    "MEASURED",
    "CANONICAL",
    "CERTIFIED_MATH",
    "CERTIFIED_COMPUTATIONAL",
    "CERTIFIED_PHYSICS",
}


@dataclass(frozen=True, slots=True)
class AdaptiveFrontierConfig:
    initial_shard_bytes: int = 262_144
    shard_growth_factor: float = 2.0
    checkpoint_interval: int = 1_000
    commit_interval: int = 1_000
    low_latency_seconds: float = 0.005
    high_latency_seconds: float = 0.050
    minimum_free_bytes: int = 64 * 1024 * 1024
    deduplicate: bool = True
    require_provenance: bool = True
    require_units_for_results: bool = True
    require_uncertainty_for_results: bool = True

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.initial_shard_bytes <= 0:
            issues.append("initial_shard_bytes must be positive")
        if self.shard_growth_factor <= 1.0:
            issues.append("shard_growth_factor must be > 1")
        if self.checkpoint_interval <= 0:
            issues.append("checkpoint_interval must be positive")
        if self.commit_interval <= 0:
            issues.append("commit_interval must be positive")
        if self.low_latency_seconds <= 0 or self.high_latency_seconds <= 0:
            issues.append("latency thresholds must be positive")
        if self.low_latency_seconds >= self.high_latency_seconds:
            issues.append("low_latency_seconds must be lower than high_latency_seconds")
        if self.minimum_free_bytes < 0:
            issues.append("minimum_free_bytes must be non-negative")
        return issues


@dataclass(slots=True)
class FrontierTelemetry:
    accepted_events: int = 0
    duplicate_events: int = 0
    rejected_events: int = 0
    bytes_written: int = 0
    shards_closed: int = 0
    checkpoints_written: int = 0
    sqlite_commits: int = 0
    write_seconds: float = 0.0
    validation_seconds: float = 0.0
    started_at: float = field(default_factory=time.monotonic)
    last_event_timestamp: str | None = None
    event_type_counts: dict[str, int] = field(default_factory=dict)
    subject_count: int = 0

    def to_dict(self) -> dict[str, object]:
        elapsed = max(time.monotonic() - self.started_at, 1.0e-12)
        return {
            "accepted_events": self.accepted_events,
            "duplicate_events": self.duplicate_events,
            "rejected_events": self.rejected_events,
            "bytes_written": self.bytes_written,
            "shards_closed": self.shards_closed,
            "checkpoints_written": self.checkpoints_written,
            "sqlite_commits": self.sqlite_commits,
            "write_seconds": round(self.write_seconds, 6),
            "validation_seconds": round(self.validation_seconds, 6),
            "elapsed_seconds": round(elapsed, 6),
            "events_per_second": round(self.accepted_events / elapsed, 3),
            "bytes_per_second": round(self.bytes_written / elapsed, 3),
            "last_event_timestamp": self.last_event_timestamp,
            "event_type_counts": dict(sorted(self.event_type_counts.items())),
            "subject_count": self.subject_count,
        }


@dataclass(frozen=True, slots=True)
class FrontierCheckpoint:
    schema: str
    event_count: int
    duplicate_count: int
    rejected_count: int
    shard_index: int
    shard_target_bytes: int
    current_shard_bytes: int
    last_event_timestamp: str | None
    ledger_digest: str
    source_cursor: str | None
    complete: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FrontierExperimentConfig:
    target_events: int = 50_000
    namespace_count: int = 16
    seed: int = 7
    start_timestamp: str = "2026-08-02T18:00:00Z"
    failure_period: int = 1

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.target_events <= 0:
            issues.append("target_events must be positive for a finite experiment")
        if self.namespace_count <= 0:
            issues.append("namespace_count must be positive")
        if self.failure_period <= 0:
            issues.append("failure_period must be positive")
        try:
            parse_timestamp(self.start_timestamp)
        except ValueError:
            issues.append("start_timestamp is invalid")
        return issues


class StreamingDiscoveryLedger:
    """Append-only shard writer with SQLite ancestry and deduplication indexes."""

    def __init__(
        self,
        output_dir: str | Path,
        *,
        config: AdaptiveFrontierConfig | None = None,
        resume: bool = False,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.shards_dir = self.output_dir / "shards"
        self.config = config or AdaptiveFrontierConfig()
        issues = self.config.validate()
        if issues:
            raise ValueError("; ".join(issues))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.shards_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.output_dir / "frontier-index.sqlite3"
        self.checkpoint_path = self.output_dir / "checkpoint.json"
        self.manifest_path = self.output_dir / "manifest.json"
        self.telemetry_path = self.output_dir / "telemetry.json"
        self.m_minus_path = self.output_dir / "m_minus.jsonl"
        self.quarantine_path = self.output_dir / "quarantine.jsonl"
        self.connection = sqlite3.connect(self.index_path)
        self.connection.row_factory = sqlite3.Row
        self._initialize_database()
        self.telemetry = FrontierTelemetry()
        self.shard_index = 0
        self.shard_target_bytes = self.config.initial_shard_bytes
        self.current_shard_bytes = 0
        self.current_shard_path: Path | None = None
        self.current_stream: TextIO | None = None
        self.last_timestamp: str | None = None
        self.ledger_hasher = sha256()
        self.source_cursor: str | None = None
        self._pending_since_commit = 0
        self._known_subjects: set[str] = set()
        if resume and self.checkpoint_path.is_file():
            self._restore_checkpoint()
        else:
            self._restore_from_database_if_present()
        self._open_shard(append=resume and self.current_shard_path is not None)

    def _initialize_database(self) -> None:
        self.connection.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;
            PRAGMA temp_store=MEMORY;
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                subject_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                parent_ids TEXT NOT NULL,
                event_hash TEXT NOT NULL,
                source_hash TEXT,
                shard_path TEXT NOT NULL,
                byte_offset INTEGER NOT NULL,
                byte_length INTEGER NOT NULL,
                lineage_types TEXT NOT NULL,
                has_failed_result INTEGER NOT NULL,
                has_refutation INTEGER NOT NULL,
                status TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_events_subject ON events(subject_id);
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id TEXT PRIMARY KEY,
                first_event_id TEXT NOT NULL,
                last_event_id TEXT NOT NULL,
                event_count INTEGER NOT NULL,
                core_mask INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def _restore_from_database_if_present(self) -> None:
        row = self.connection.execute(
            "SELECT COUNT(*) AS count, MAX(timestamp) AS last_timestamp FROM events"
        ).fetchone()
        if row and int(row["count"] or 0):
            count = int(row["count"])
            self.telemetry.accepted_events = count
            self.last_timestamp = row["last_timestamp"]
            shard_row = self.connection.execute(
                "SELECT shard_path, byte_offset, byte_length FROM events ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
            if shard_row:
                path = Path(str(shard_row["shard_path"]))
                self.current_shard_path = self.output_dir / path
                try:
                    self.shard_index = int(path.stem.split("-")[-1])
                except ValueError:
                    self.shard_index = 0
                self.current_shard_bytes = int(shard_row["byte_offset"]) + int(shard_row["byte_length"])
            self._known_subjects = {
                str(item[0]) for item in self.connection.execute("SELECT subject_id FROM subjects")
            }
            self.telemetry.subject_count = len(self._known_subjects)
            for item in self.connection.execute(
                "SELECT event_type, COUNT(*) FROM events GROUP BY event_type"
            ):
                self.telemetry.event_type_counts[str(item[0])] = int(item[1])
            for item in self.connection.execute("SELECT event_hash FROM events ORDER BY rowid"):
                self.ledger_hasher.update(str(item[0]).encode("ascii"))

    def _restore_checkpoint(self) -> None:
        value = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        self.shard_index = int(value["shard_index"])
        self.shard_target_bytes = int(value["shard_target_bytes"])
        self.current_shard_bytes = int(value["current_shard_bytes"])
        self.last_timestamp = value.get("last_event_timestamp")
        self.source_cursor = value.get("source_cursor")
        self._restore_from_database_if_present()

    def _shard_relative_path(self, index: int) -> Path:
        return Path("shards") / f"events-{index:08d}.jsonl"

    def _open_shard(self, *, append: bool = False) -> None:
        if self.current_stream is not None:
            return
        if self.current_shard_path is None:
            self.current_shard_path = self.output_dir / self._shard_relative_path(self.shard_index)
        mode = "a" if append and self.current_shard_path.exists() else "w"
        self.current_stream = self.current_shard_path.open(mode, encoding="utf-8", newline="\n")
        if mode == "a":
            self.current_shard_bytes = self.current_shard_path.stat().st_size
        else:
            self.current_shard_bytes = 0

    def _close_shard(self) -> None:
        if self.current_stream is None:
            return
        self.current_stream.flush()
        self.current_stream.close()
        self.current_stream = None
        self.telemetry.shards_closed += 1

    def _adapt_after_shard(self, elapsed: float, bytes_written: int) -> None:
        if bytes_written <= 0:
            return
        latency_per_megabyte = elapsed / max(bytes_written / (1024.0**2), 1.0e-9)
        if latency_per_megabyte <= self.config.low_latency_seconds:
            self.shard_target_bytes = int(self.shard_target_bytes * self.config.shard_growth_factor)
        elif latency_per_megabyte >= self.config.high_latency_seconds:
            self.shard_target_bytes = max(
                self.config.initial_shard_bytes,
                int(self.shard_target_bytes / self.config.shard_growth_factor),
            )

    def _rotate_shard(self) -> None:
        started = time.monotonic()
        previous_bytes = self.current_shard_bytes
        self._close_shard()
        elapsed = time.monotonic() - started
        self._adapt_after_shard(elapsed, previous_bytes)
        self.shard_index += 1
        self.current_shard_path = self.output_dir / self._shard_relative_path(self.shard_index)
        self.current_shard_bytes = 0
        self._open_shard()

    def _disk_gate(self, next_bytes: int) -> None:
        free = shutil.disk_usage(self.output_dir).free
        required = self.config.minimum_free_bytes + max(next_bytes, self.shard_target_bytes)
        if free < required:
            raise RuntimeError(
                f"Backpressure: free disk {free} bytes is below required safety reserve {required} bytes"
            )

    def _event_row(self, event_id: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM events WHERE event_id = ?", (event_id,)
        ).fetchone()

    def _parent_lineage(self, event: DiscoveryEvent) -> tuple[set[str], bool, bool]:
        lineage_types: set[str] = set()
        has_failed_result = False
        has_refutation = False
        for parent_id in event.parent_ids:
            row = self._event_row(parent_id)
            if row is None:
                raise ValueError(f"Unknown parent event: {parent_id}")
            if str(row["subject_id"]) != event.subject_id and not bool(event.payload.get("cross_subject", False)):
                raise ValueError(f"Cross-subject parent {parent_id} requires payload.cross_subject=true")
            lineage_types.add(str(row["event_type"]))
            lineage_types.update(json.loads(str(row["lineage_types"])))
            has_failed_result = has_failed_result or bool(row["has_failed_result"])
            has_refutation = has_refutation or bool(row["has_refutation"])
        return lineage_types, has_failed_result, has_refutation

    def _enforce_gates(
        self,
        event: DiscoveryEvent,
        lineage_types: set[str],
        has_failed_result: bool,
        has_refutation: bool,
    ) -> None:
        spec = event_spec(event.event_type)
        if spec.required_parent_any and not (set(spec.required_parent_any) & lineage_types):
            raise ValueError(
                f"{event.event_type} requires ancestry containing one of {spec.required_parent_any}; "
                f"observed {sorted(lineage_types)}"
            )
        if event.event_type == "OAKTransition":
            target = str(event.payload.get("to_status", ""))
            if target not in OAK_STATUSES:
                raise ValueError(f"Unknown OAK target status: {target}")
            if target in PROMOTED_STATUSES and "ResultPacket" not in lineage_types:
                raise ValueError(f"Promotion to {target} requires ResultPacket ancestry")
        if event.event_type == "MMinusRule" and not (has_failed_result or has_refutation):
            raise ValueError("MMinusRule requires failed-result or refutation ancestry")
        if event.event_type == "PromotionEvent" and "ReplicationEvent" not in lineage_types and "ProofEvent" not in lineage_types:
            raise ValueError("PromotionEvent requires replication or proof ancestry")
        if event.event_type == "PublicationEvent" and not event.human_approval:
            raise ValueError("PublicationEvent requires explicit human approval")
        if event.event_type == "DeploymentEvent" and not event.human_approval:
            raise ValueError("DeploymentEvent requires explicit human approval")

    def _core_bit(self, event_type: str) -> int:
        try:
            return 1 << CORE_LOOP_EVENT_TYPES.index(event_type)
        except ValueError:
            return 0

    def append(self, event: DiscoveryEvent, *, source_cursor: str | None = None) -> bool:
        validation_started = time.monotonic()
        issues = event.validate()
        self.telemetry.validation_seconds += time.monotonic() - validation_started
        if issues:
            self.telemetry.rejected_events += 1
            self._quarantine(event, issues)
            raise ValueError("; ".join(issues))
        if self._event_row(event.event_id) is not None:
            self.telemetry.duplicate_events += 1
            if self.config.deduplicate:
                return False
            raise ValueError(f"Duplicate event_id: {event.event_id}")
        if self.last_timestamp and parse_timestamp(event.timestamp) < parse_timestamp(self.last_timestamp):
            self.telemetry.rejected_events += 1
            raise ValueError("Events must be appended in non-decreasing chronological order")
        if self.config.require_provenance and not (event.provenance or event.source_hash):
            self.telemetry.rejected_events += 1
            raise ValueError("Event requires provenance or source_hash")
        if event.event_type == "ResultPacket":
            if self.config.require_units_for_results and not event.units:
                raise ValueError("ResultPacket requires units")
            if self.config.require_uncertainty_for_results and not event.uncertainty:
                raise ValueError("ResultPacket requires uncertainty")

        lineage_types, has_failed_result, has_refutation = self._parent_lineage(event)
        self._enforce_gates(event, lineage_types, has_failed_result, has_refutation)
        lineage_types.add(event.event_type)
        event_failed_result = event.event_type == "ResultPacket" and not bool(event.payload.get("success", False))
        event_refutation = (
            event.event_type in {"RefutationEvent", "ModelRejectedEvent"}
            or (event.event_type == "OAKTransition" and event.payload.get("to_status") == "REFUTED")
        )
        has_failed_result = has_failed_result or event_failed_result
        has_refutation = has_refutation or event_refutation

        line = json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        encoded_length = len(line.encode("utf-8"))
        self._disk_gate(encoded_length)
        if self.current_shard_bytes and self.current_shard_bytes + encoded_length > self.shard_target_bytes:
            self._rotate_shard()
        assert self.current_stream is not None
        assert self.current_shard_path is not None
        offset = self.current_shard_bytes
        write_started = time.monotonic()
        self.current_stream.write(line)
        self.telemetry.write_seconds += time.monotonic() - write_started
        self.current_shard_bytes += encoded_length
        self.telemetry.bytes_written += encoded_length

        relative_shard = self.current_shard_path.relative_to(self.output_dir).as_posix()
        self.connection.execute(
            """
            INSERT INTO events (
                event_id, event_type, subject_id, timestamp, parent_ids, event_hash,
                source_hash, shard_path, byte_offset, byte_length, lineage_types,
                has_failed_result, has_refutation, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.event_type,
                event.subject_id,
                event.timestamp,
                json.dumps(list(event.parent_ids), separators=(",", ":")),
                event.event_hash,
                event.source_hash,
                relative_shard,
                offset,
                encoded_length,
                json.dumps(sorted(lineage_types), separators=(",", ":")),
                int(has_failed_result),
                int(has_refutation),
                event.status,
            ),
        )
        bit = self._core_bit(event.event_type)
        subject_row = self.connection.execute(
            "SELECT event_count, core_mask, first_event_id FROM subjects WHERE subject_id = ?",
            (event.subject_id,),
        ).fetchone()
        if subject_row is None:
            self.connection.execute(
                "INSERT INTO subjects VALUES (?, ?, ?, ?, ?)",
                (event.subject_id, event.event_id, event.event_id, 1, bit),
            )
            self._known_subjects.add(event.subject_id)
            self.telemetry.subject_count = len(self._known_subjects)
        else:
            self.connection.execute(
                "UPDATE subjects SET last_event_id = ?, event_count = ?, core_mask = ? WHERE subject_id = ?",
                (
                    event.event_id,
                    int(subject_row["event_count"]) + 1,
                    int(subject_row["core_mask"]) | bit,
                    event.subject_id,
                ),
            )

        if event.event_type == "MMinusRule":
            with self.m_minus_path.open("a", encoding="utf-8") as stream:
                stream.write(line)
        self.ledger_hasher.update(event.event_hash.encode("ascii"))
        self.telemetry.accepted_events += 1
        self.telemetry.event_type_counts[event.event_type] = self.telemetry.event_type_counts.get(event.event_type, 0) + 1
        self.telemetry.last_event_timestamp = event.timestamp
        self.last_timestamp = event.timestamp
        self.source_cursor = source_cursor
        self._pending_since_commit += 1

        if self._pending_since_commit >= self.config.commit_interval:
            self.connection.commit()
            self.telemetry.sqlite_commits += 1
            self._pending_since_commit = 0
        if self.telemetry.accepted_events % self.config.checkpoint_interval == 0:
            self.write_checkpoint(complete=False)
        return True

    def extend(self, events: Iterable[DiscoveryEvent]) -> int:
        accepted = 0
        for index, event in enumerate(events):
            if self.append(event, source_cursor=str(index)):
                accepted += 1
        return accepted

    def _quarantine(self, event: DiscoveryEvent, issues: Sequence[str]) -> None:
        record = {
            "event": event.to_dict(),
            "issues": list(issues),
            "recorded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        with self.quarantine_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")

    def checkpoint(self, *, complete: bool) -> FrontierCheckpoint:
        return FrontierCheckpoint(
            schema="omega_discovery_kernel.frontier_checkpoint.v0.2",
            event_count=self.telemetry.accepted_events,
            duplicate_count=self.telemetry.duplicate_events,
            rejected_count=self.telemetry.rejected_events,
            shard_index=self.shard_index,
            shard_target_bytes=self.shard_target_bytes,
            current_shard_bytes=self.current_shard_bytes,
            last_event_timestamp=self.last_timestamp,
            ledger_digest=self.ledger_hasher.hexdigest(),
            source_cursor=self.source_cursor,
            complete=complete,
        )

    def write_checkpoint(self, *, complete: bool) -> FrontierCheckpoint:
        if self.current_stream is not None:
            self.current_stream.flush()
        self.connection.commit()
        self.telemetry.sqlite_commits += 1
        self._pending_since_commit = 0
        checkpoint = self.checkpoint(complete=complete)
        temporary = self.checkpoint_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(checkpoint.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.checkpoint_path)
        self.telemetry.checkpoints_written += 1
        return checkpoint

    def subject_core_coverage(self) -> tuple[int, int]:
        full_mask = (1 << len(CORE_LOOP_EVENT_TYPES)) - 1
        row = self.connection.execute(
            "SELECT COUNT(*) AS total, SUM(CASE WHEN core_mask = ? THEN 1 ELSE 0 END) AS complete FROM subjects",
            (full_mask,),
        ).fetchone()
        return int(row["total"] or 0), int(row["complete"] or 0)

    def integrity_findings(self) -> list[str]:
        findings: list[str] = []
        duplicates = self.connection.execute(
            "SELECT event_id, COUNT(*) AS count FROM events GROUP BY event_id HAVING count > 1"
        ).fetchall()
        findings.extend(f"duplicate event id: {row['event_id']}" for row in duplicates)
        orphan_rows = self.connection.execute("SELECT event_id, parent_ids FROM events").fetchall()
        known = {str(row[0]) for row in self.connection.execute("SELECT event_id FROM events")}
        for row in orphan_rows:
            missing = set(json.loads(str(row["parent_ids"]))) - known
            if missing:
                findings.append(f"{row['event_id']}: missing parents {sorted(missing)}")
        return sorted(findings)

    def manifest(self, *, complete: bool) -> dict[str, object]:
        total_subjects, complete_subjects = self.subject_core_coverage()
        disk = shutil.disk_usage(self.output_dir)
        return {
            "schema": "omega_discovery_kernel.streaming_manifest.v0.2",
            "event_count": self.telemetry.accepted_events,
            "duplicate_count": self.telemetry.duplicate_events,
            "rejected_count": self.telemetry.rejected_events,
            "subject_count": total_subjects,
            "complete_subject_count": complete_subjects,
            "closed_loop_coverage": round(complete_subjects / total_subjects, 6) if total_subjects else 1.0,
            "shard_count": self.shard_index + 1,
            "current_shard_target_bytes": self.shard_target_bytes,
            "ledger_digest": self.ledger_hasher.hexdigest(),
            "checkpoint_complete": complete,
            "source_cursor": self.source_cursor,
            "integrity_findings": self.integrity_findings(),
            "disk_free_bytes": disk.free,
            "telemetry": self.telemetry.to_dict(),
            "config": asdict(self.config),
            "oak_status": "R0.2_STREAMED_WORKFLOW_EVIDENCE_NOT_SCIENTIFIC_CERTIFICATION",
            "unbounded_boundary": (
                "No permanent total-event ceiling is encoded. Every execution remains bounded by "
                "source exhaustion, storage, compute, time, quality, safety, legal, and rollback constraints."
            ),
        }

    def close(self, *, complete: bool = True) -> dict[str, object]:
        self._close_shard()
        checkpoint = self.write_checkpoint(complete=complete)
        manifest = self.manifest(complete=complete)
        self.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.telemetry_path.write_text(json.dumps(self.telemetry.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.connection.commit()
        self.connection.close()
        return {"checkpoint": checkpoint.to_dict(), "manifest": manifest}

    def __enter__(self) -> "StreamingDiscoveryLedger":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close(complete=exc is None)


def _timestamp(base: datetime, offset: int) -> str:
    return (base + timedelta(microseconds=offset)).isoformat().replace("+00:00", "Z")


def synthetic_closed_loop_stream(config: FrontierExperimentConfig) -> Iterator[DiscoveryEvent]:
    """Yield deterministic eight-event loops until ``target_events`` is reached."""
    issues = config.validate()
    if issues:
        raise ValueError("; ".join(issues))
    base = parse_timestamp(config.start_timestamp)
    produced = 0
    subject_index = 0
    while produced < config.target_events:
        namespace = subject_index % config.namespace_count
        subject_id = f"frontier-{namespace:03d}-subject-{subject_index:09d}"
        sequence: list[DiscoveryEvent] = []
        observation = DiscoveryEvent.create(
            "ObservationEvent",
            subject_id,
            _timestamp(base, produced),
            source_hash=f"sha256:synthetic-observation-{subject_index:09d}",
            provenance=("synthetic_closed_loop_stream",),
            domain="frontier-scale-test",
            status="synthetic",
            payload={
                "observation_kind": "deterministic_scalar_transition",
                "source_index": subject_index,
                "namespace": namespace,
                "value_before": float(subject_index),
                "value_after": float(subject_index + 1),
            },
            units={"value_before": "1", "value_after": "1"},
            uncertainty={"value_before": 0.0, "value_after": 0.0},
        )
        sequence.append(observation)
        claim = DiscoveryEvent.create(
            "ClaimEvent",
            subject_id,
            _timestamp(base, produced + 1),
            parent_ids=(observation.event_id,),
            provenance=("synthetic_closed_loop_stream",),
            domain="frontier-scale-test",
            status="hypothesis",
            payload={
                "claim_id": f"claim-{subject_index:09d}",
                "text": "A unit translation explains the synthetic transition.",
                "canonical_key": "unit translation explains transition",
                "scope": f"subject-{subject_index:09d}",
                "failure_conditions": ["held-out error exceeds zero tolerance"],
            },
        )
        sequence.append(claim)
        generator = DiscoveryEvent.create(
            "GeneratorCandidate",
            subject_id,
            _timestamp(base, produced + 2),
            parent_ids=(claim.event_id,),
            provenance=("synthetic_closed_loop_stream",),
            domain="frontier-scale-test",
            status="candidate",
            payload={
                "continuous_generators": ["translation"],
                "discrete_events": [],
                "singular_events": [],
                "residual": 0.0,
                "uncertainty": 0.0,
            },
            units={"residual": "1"},
            uncertainty={"residual": 0.0},
        )
        sequence.append(generator)
        experiment = DiscoveryEvent.create(
            "ExperimentSpec",
            subject_id,
            _timestamp(base, produced + 3),
            parent_ids=(generator.event_id,),
            provenance=("synthetic_closed_loop_stream",),
            domain="frontier-scale-test",
            status="dry_run",
            payload={
                "protocol": "predict one held-out scalar transition",
                "success_criteria": "candidate_error <= baseline_error",
                "rollback": "discard generated subject shard",
                "baseline": "identity predictor",
            },
            human_approval=False,
            reversible=True,
        )
        sequence.append(experiment)
        failed = subject_index % config.failure_period == 0
        result = DiscoveryEvent.create(
            "ResultPacket",
            subject_id,
            _timestamp(base, produced + 4),
            parent_ids=(experiment.event_id,),
            source_hash=f"sha256:synthetic-result-{subject_index:09d}",
            provenance=("synthetic_closed_loop_stream",),
            domain="frontier-scale-test",
            status="reproduced_synthetic",
            payload={
                "success": not failed,
                "metric": "absolute_error",
                "value": 1.0 if failed else 0.0,
                "baseline": {"name": "identity", "value": 0.5},
                "protocol": "predict one held-out scalar transition",
                "interpretation": "synthetic scale-path exercise only",
            },
            units={"absolute_error": "1"},
            uncertainty={"absolute_error": 0.0},
        )
        sequence.append(result)
        transition = DiscoveryEvent.create(
            "OAKTransition",
            subject_id,
            _timestamp(base, produced + 5),
            parent_ids=(result.event_id,),
            provenance=("synthetic_closed_loop_stream",),
            domain="epistemic-governance",
            status="synthetic_transition",
            payload={
                "from_status": "SIMULATED",
                "to_status": "REFUTED" if failed else "DEMONSTRATED",
                "cause": "synthetic held-out comparison",
            },
            human_approval=True,
        )
        sequence.append(transition)
        if not failed:
            # The mandatory eight-event stress loop deliberately demotes a successful
            # synthetic result into a scoped failure so M-minus ancestry remains honest.
            result = DiscoveryEvent.create(
                "ResultPacket",
                subject_id,
                _timestamp(base, produced + 6),
                parent_ids=(experiment.event_id,),
                source_hash=f"sha256:synthetic-negative-control-{subject_index:09d}",
                provenance=("synthetic_closed_loop_stream",),
                domain="frontier-scale-test",
                status="reproduced_synthetic_negative_control",
                payload={
                    "success": False,
                    "metric": "negative_control_error",
                    "value": 1.0,
                    "baseline": {"name": "constant", "value": 0.0},
                    "protocol": "mandatory negative-control path",
                    "interpretation": "negative-control event for M-minus scale coverage",
                },
                units={"negative_control_error": "1"},
                uncertainty={"negative_control_error": 0.0},
            )
            sequence.append(result)
        mminus = DiscoveryEvent.create(
            "MMinusRule",
            subject_id,
            _timestamp(base, produced + len(sequence)),
            parent_ids=(result.event_id, transition.event_id),
            provenance=("synthetic_closed_loop_stream",),
            domain="epistemic-governance",
            status="active_constraint",
            payload={
                "context": "synthetic frontier scale path",
                "prohibited_inference": "scale-test success implies scientific validity",
                "reusable_rule": "treat generated frontier records as workflow evidence only",
            },
        )
        sequence.append(mminus)
        action = DiscoveryEvent.create(
            "ActionProposal",
            subject_id,
            _timestamp(base, produced + len(sequence)),
            parent_ids=(mminus.event_id,),
            provenance=("synthetic_closed_loop_stream",),
            domain="frontier-planning",
            status="human_review_draft",
            payload={
                "action": "continue with the next deterministic subject",
                "expected_information_gain": 0.0,
                "rollback": "delete generated frontier directory",
                "risk": 0.0,
                "cost": 0.0,
            },
            reversible=True,
        )
        sequence.append(action)

        for event in sequence:
            if produced >= config.target_events:
                return
            yield event
            produced += 1
        subject_index += 1


def run_frontier_experiment(
    output_dir: str | Path,
    *,
    experiment: FrontierExperimentConfig | None = None,
    ledger_config: AdaptiveFrontierConfig | None = None,
    resume: bool = False,
) -> dict[str, object]:
    experiment = experiment or FrontierExperimentConfig()
    with StreamingDiscoveryLedger(output_dir, config=ledger_config, resume=resume) as ledger:
        accepted = ledger.extend(synthetic_closed_loop_stream(experiment))
        ledger.source_cursor = str(experiment.target_events)
        summary = {
            "schema": "omega_discovery_kernel.frontier_experiment.v0.2",
            "requested_events": experiment.target_events,
            "accepted_this_run": accepted,
            "experiment": asdict(experiment),
            "finite_target_is_not_permanent_ceiling": True,
        }
    manifest = json.loads((Path(output_dir) / "manifest.json").read_text(encoding="utf-8"))
    summary["manifest"] = manifest
    (Path(output_dir) / "experiment-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary
