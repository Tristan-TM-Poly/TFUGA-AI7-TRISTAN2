from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any, Iterable, Iterator, Mapping, TextIO
import uuid


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^\w.-]+", "-", value.strip(), flags=re.UNICODE).strip("-._")
    return cleaned or f"unnamed-{_sha256_text(value)[:12]}"


@dataclass(frozen=True)
class AdditionRecord:
    """One logical addition routed into a deterministic Git shard."""

    addition_id: str
    namespace: str
    kind: str
    payload: Mapping[str, Any]
    provenance: tuple[str, ...] = ()
    risk: str = "normal"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "AdditionRecord":
        namespace = str(raw.get("namespace", "general")).strip() or "general"
        kind = str(raw.get("kind", "addition")).strip() or "addition"
        payload = raw.get("payload")
        if payload is None:
            payload = {
                key: value
                for key, value in raw.items()
                if key not in {"addition_id", "id", "namespace", "kind", "provenance", "risk", "metadata"}
            }
        if not isinstance(payload, Mapping):
            raise ValueError("payload must be a JSON object")
        provenance_raw = raw.get("provenance", ())
        if isinstance(provenance_raw, str):
            provenance = (provenance_raw,)
        elif isinstance(provenance_raw, (list, tuple)):
            provenance = tuple(str(item) for item in provenance_raw)
        else:
            raise ValueError("provenance must be a string or array")
        risk = str(raw.get("risk", "normal")).strip() or "normal"
        metadata = raw.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise ValueError("metadata must be a JSON object")
        identity_basis = {
            "namespace": namespace,
            "kind": kind,
            "payload": payload,
            "provenance": provenance,
        }
        addition_id = str(raw.get("addition_id") or raw.get("id") or _sha256_text(_canonical_json(identity_basis)))
        return cls(
            addition_id=addition_id,
            namespace=namespace,
            kind=kind,
            payload=dict(payload),
            provenance=provenance,
            risk=risk,
            metadata=dict(metadata),
        )

    @property
    def fingerprint(self) -> str:
        return _sha256_text(
            _canonical_json(
                {
                    "namespace": self.namespace,
                    "kind": self.kind,
                    "payload": self.payload,
                    "provenance": self.provenance,
                }
            )
        )

    def normalized(self) -> dict[str, Any]:
        return {
            "addition_id": self.addition_id,
            "fingerprint": self.fingerprint,
            "namespace": self.namespace,
            "kind": self.kind,
            "payload": dict(self.payload),
            "provenance": list(self.provenance),
            "risk": self.risk,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class GitHubPlanPolicy:
    """Starting calibration for adaptive shards, never a total-addition ceiling."""

    initial_shard_bytes: int = 262_144
    shard_growth_factor: float = 2.0
    strict_records: bool = False
    require_provenance: bool = False
    approval_risks: tuple[str, ...] = ("ip_sensitive", "public", "irreversible", "legal", "financial")

    def __post_init__(self) -> None:
        if self.initial_shard_bytes < 1:
            raise ValueError("initial_shard_bytes must be positive")
        if self.shard_growth_factor <= 1.0:
            raise ValueError("shard_growth_factor must be greater than 1")


@dataclass(frozen=True)
class ShardRecord:
    path: str
    namespace: str
    kind: str
    sequence: int
    additions: int
    bytes: int
    sha256: str
    byte_budget_used: int
    requires_human_approval: bool


@dataclass(frozen=True)
class GitHubPlanReport:
    run_id: str
    status: str
    raw_records: int
    unique_additions: int
    duplicates: int
    invalid_records: int
    shards: int
    payload_bytes: int
    namespaces: int
    approval_required_additions: int
    output_dir: str
    proposed_branch: str
    generated_at: str
    no_total_addition_cap: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PlanIndex:
    """Disk-backed uniqueness and shard index for runs larger than RAM."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS fingerprints (fingerprint TEXT PRIMARY KEY, addition_id TEXT NOT NULL)"
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS shards (
                path TEXT PRIMARY KEY,
                namespace TEXT NOT NULL,
                kind TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                additions INTEGER NOT NULL,
                bytes INTEGER NOT NULL,
                sha256 TEXT NOT NULL,
                byte_budget_used INTEGER NOT NULL,
                requires_human_approval INTEGER NOT NULL
            )
            """
        )

    def add_fingerprint(self, fingerprint: str, addition_id: str) -> bool:
        cursor = self.connection.execute(
            "INSERT OR IGNORE INTO fingerprints(fingerprint, addition_id) VALUES (?, ?)",
            (fingerprint, addition_id),
        )
        return cursor.rowcount == 1

    def record_shard(self, record: ShardRecord) -> None:
        self.connection.execute(
            """
            INSERT INTO shards(
                path, namespace, kind, sequence, additions, bytes, sha256,
                byte_budget_used, requires_human_approval
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.path,
                record.namespace,
                record.kind,
                record.sequence,
                record.additions,
                record.bytes,
                record.sha256,
                record.byte_budget_used,
                int(record.requires_human_approval),
            ),
        )

    def iter_shards(self) -> Iterator[ShardRecord]:
        rows = self.connection.execute(
            """
            SELECT path, namespace, kind, sequence, additions, bytes, sha256,
                   byte_budget_used, requires_human_approval
            FROM shards ORDER BY namespace, kind, sequence
            """
        )
        for row in rows:
            yield ShardRecord(
                path=str(row[0]),
                namespace=str(row[1]),
                kind=str(row[2]),
                sequence=int(row[3]),
                additions=int(row[4]),
                bytes=int(row[5]),
                sha256=str(row[6]),
                byte_budget_used=int(row[7]),
                requires_human_approval=bool(row[8]),
            )

    def commit(self) -> None:
        self.connection.commit()

    def close(self) -> None:
        self.connection.commit()
        self.connection.close()


class AdaptiveShardWriter:
    """Streaming writer whose shard budget grows after successful finalization."""

    def __init__(
        self,
        *,
        output_root: Path,
        staging_root: Path,
        namespace: str,
        kind: str,
        initial_byte_budget: int,
        growth_factor: float,
        approval_risks: frozenset[str],
        on_finalize: Any,
    ):
        self.output_root = output_root
        self.staging_root = staging_root
        self.namespace = namespace
        self.kind = kind
        self.byte_budget = initial_byte_budget
        self.growth_factor = growth_factor
        self.approval_risks = approval_risks
        self.on_finalize = on_finalize
        self.sequence = 0
        self.handle: TextIO | None = None
        self.temporary_path: Path | None = None
        self.count = 0
        self.byte_count = 0
        self.digest = hashlib.sha256()
        self.requires_human_approval = False

    def add(self, record: AdditionRecord) -> None:
        line = _canonical_json(record.normalized()) + "\n"
        encoded = line.encode("utf-8")
        if self.handle is not None and self.count and self.byte_count + len(encoded) > self.byte_budget:
            self.finalize()
        if self.handle is None:
            self._open()
        assert self.handle is not None
        self.handle.write(line)
        self.digest.update(encoded)
        self.count += 1
        self.byte_count += len(encoded)
        self.requires_human_approval = self.requires_human_approval or record.risk in self.approval_risks

    def _open(self) -> None:
        self.sequence += 1
        stage_dir = self.staging_root / _slug(self.namespace) / _slug(self.kind)
        stage_dir.mkdir(parents=True, exist_ok=True)
        self.temporary_path = stage_dir / f"shard-{self.sequence:08d}.jsonl.tmp"
        self.handle = self.temporary_path.open("w", encoding="utf-8", newline="\n")
        self.count = 0
        self.byte_count = 0
        self.digest = hashlib.sha256()
        self.requires_human_approval = False

    def finalize(self) -> None:
        if self.handle is None or self.temporary_path is None:
            return
        self.handle.flush()
        os.fsync(self.handle.fileno())
        self.handle.close()
        relative = Path("shards") / _slug(self.namespace) / _slug(self.kind) / f"shard-{self.sequence:08d}.jsonl"
        final_path = self.output_root / relative
        final_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(self.temporary_path, final_path)
        record = ShardRecord(
            path=relative.as_posix(),
            namespace=self.namespace,
            kind=self.kind,
            sequence=self.sequence,
            additions=self.count,
            bytes=self.byte_count,
            sha256=self.digest.hexdigest(),
            byte_budget_used=self.byte_budget,
            requires_human_approval=self.requires_human_approval,
        )
        self.on_finalize(record)
        self.byte_budget = max(self.byte_budget + 1, int(self.byte_budget * self.growth_factor))
        self.handle = None
        self.temporary_path = None
        self.count = 0
        self.byte_count = 0
        self.digest = hashlib.sha256()
        self.requires_human_approval = False


class GitHubDryRunPlanner:
    """Compile an open-ended addition stream into a reversible GitHub tree plan.

    The planner performs no GitHub mutation. It writes deterministic shards and
    append-only plan ledgers locally so an actuator can later review, stage,
    commit, push, and open a PR through explicit approval gates.
    """

    def __init__(
        self,
        output_dir: str | Path,
        *,
        policy: GitHubPlanPolicy | None = None,
        proposed_branch: str = "feat/omega-unbounded-generated",
    ):
        self.output_dir = Path(output_dir)
        self.policy = policy or GitHubPlanPolicy()
        self.proposed_branch = proposed_branch
        self.run_id = f"unbounded-{uuid.uuid4().hex[:16]}"
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.index: PlanIndex | None = None
        self._writers: dict[tuple[str, str], AdaptiveShardWriter] = {}
        self._tree_handle: TextIO | None = None
        self._rollback_handle: TextIO | None = None
        self._checkpoint_path = self.output_dir / "checkpoint.json"
        self._stats = defaultdict(int)
        self._namespaces: set[str] = set()

    def plan(self, records: Iterable[Mapping[str, Any] | AdditionRecord]) -> GitHubPlanReport:
        self._prepare_output()
        assert self.index is not None
        try:
            for raw in records:
                self._stats["raw_records"] += 1
                try:
                    record = raw if isinstance(raw, AdditionRecord) else AdditionRecord.from_mapping(raw)
                    if self.policy.require_provenance and not record.provenance:
                        raise ValueError("provenance is required by policy")
                except (TypeError, ValueError) as exc:
                    self._record_invalid(raw, exc)
                    if self.policy.strict_records:
                        raise
                    continue

                if not self.index.add_fingerprint(record.fingerprint, record.addition_id):
                    self._stats["duplicates"] += 1
                    self._append_jsonl(
                        self.output_dir / "duplicates.jsonl",
                        {
                            "addition_id": record.addition_id,
                            "fingerprint": record.fingerprint,
                            "reason": "semantic_identity_already_observed",
                        },
                    )
                    continue

                self._stats["unique_additions"] += 1
                self._namespaces.add(record.namespace)
                if record.risk in self.policy.approval_risks:
                    self._stats["approval_required_additions"] += 1
                writer = self._writer_for(record.namespace, record.kind)
                writer.add(record)

            for writer in self._writers.values():
                writer.finalize()
            self.index.commit()
            self._write_commit_plan()
            report = self._build_report(status="planned")
            self._write_reports(report)
            return report
        except Exception:
            for writer in self._writers.values():
                if writer.handle is not None:
                    writer.handle.close()
            self._write_checkpoint(status="interrupted")
            raise
        finally:
            if self._tree_handle is not None:
                self._tree_handle.close()
            if self._rollback_handle is not None:
                self._rollback_handle.close()
            if self.index is not None:
                self.index.close()

    def _prepare_output(self) -> None:
        if self.output_dir.exists() and any(self.output_dir.iterdir()):
            raise FileExistsError(f"output directory is not empty: {self.output_dir}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / ".staging").mkdir(parents=True, exist_ok=True)
        self.index = PlanIndex(self.output_dir / "plan-index.sqlite3")
        self._tree_handle = (self.output_dir / "tree.jsonl").open("a", encoding="utf-8")
        self._rollback_handle = (self.output_dir / "rollback.jsonl").open("a", encoding="utf-8")
        self._write_checkpoint(status="running")

    def _writer_for(self, namespace: str, kind: str) -> AdaptiveShardWriter:
        key = (namespace, kind)
        writer = self._writers.get(key)
        if writer is None:
            writer = AdaptiveShardWriter(
                output_root=self.output_dir,
                staging_root=self.output_dir / ".staging",
                namespace=namespace,
                kind=kind,
                initial_byte_budget=self.policy.initial_shard_bytes,
                growth_factor=self.policy.shard_growth_factor,
                approval_risks=frozenset(self.policy.approval_risks),
                on_finalize=self._record_shard,
            )
            self._writers[key] = writer
        return writer

    def _record_shard(self, record: ShardRecord) -> None:
        assert self.index is not None
        assert self._tree_handle is not None
        assert self._rollback_handle is not None
        self.index.record_shard(record)
        self.index.commit()
        self._stats["shards"] += 1
        self._stats["payload_bytes"] += record.bytes
        self._tree_handle.write(_canonical_json(asdict(record)) + "\n")
        self._tree_handle.flush()
        self._rollback_handle.write(
            _canonical_json(
                {
                    "operation": "delete_generated_path",
                    "path": record.path,
                    "expected_sha256": record.sha256,
                    "precondition": "path_was_created_by_this_plan",
                }
            )
            + "\n"
        )
        self._rollback_handle.flush()
        self._write_checkpoint(status="running")

    def _record_invalid(self, raw: Any, exc: Exception) -> None:
        self._stats["invalid_records"] += 1
        self._append_jsonl(
            self.output_dir / "quarantine.jsonl",
            {
                "raw": raw,
                "error": str(exc),
                "status": "quarantined_not_integrated",
            },
        )
        self._append_jsonl(
            self.output_dir / "m_minus.jsonl",
            {
                "event_id": f"M-{uuid.uuid4().hex[:16]}",
                "type": "invalid_addition_record",
                "error": str(exc),
                "iteration_record": self._stats["raw_records"],
                "status": "observed",
            },
        )

    def _write_commit_plan(self) -> None:
        assert self.index is not None
        path = self.output_dir / "commit-plan.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for shard in self.index.iter_shards():
                handle.write(
                    _canonical_json(
                        {
                            "commit_group": f"namespace:{_slug(shard.namespace)}",
                            "path": shard.path,
                            "expected_sha256": shard.sha256,
                            "additions": shard.additions,
                            "message": f"feat({_slug(shard.namespace)}): integrate adaptive shard {shard.sequence}",
                            "requires_human_approval": shard.requires_human_approval,
                            "stage_command": f"git add -- {shard.path}",
                        }
                    )
                    + "\n"
                )

    def _build_report(self, *, status: str) -> GitHubPlanReport:
        return GitHubPlanReport(
            run_id=self.run_id,
            status=status,
            raw_records=self._stats["raw_records"],
            unique_additions=self._stats["unique_additions"],
            duplicates=self._stats["duplicates"],
            invalid_records=self._stats["invalid_records"],
            shards=self._stats["shards"],
            payload_bytes=self._stats["payload_bytes"],
            namespaces=len(self._namespaces),
            approval_required_additions=self._stats["approval_required_additions"],
            output_dir=str(self.output_dir),
            proposed_branch=self.proposed_branch,
            generated_at=self.generated_at,
        )

    def _write_reports(self, report: GitHubPlanReport) -> None:
        payload = {
            **report.to_dict(),
            "policy": asdict(self.policy),
            "boundary": (
                "Dry-run only. No branch, commit, push, PR, publication, deletion, permission change, "
                "or external API mutation is performed by this planner."
            ),
            "next_gate": "Review plan, verify hashes and tests, then authorize each GitHub write phase explicitly.",
        }
        (self.output_dir / "manifest.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        semantic_diff = {
            "logical_additions": report.unique_additions,
            "duplicates_removed": report.duplicates,
            "invalid_quarantined": report.invalid_records,
            "generated_shards": report.shards,
            "namespaces_touched": report.namespaces,
            "approval_required_additions": report.approval_required_additions,
            "epistemic_status": "integration_plan_not_external_validation",
        }
        (self.output_dir / "semantic-diff.json").write_text(
            json.dumps(semantic_diff, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        oak = {
            "status": "PASS_DRY_RUN_PLAN" if report.invalid_records == 0 else "PASS_WITH_QUARANTINE",
            "checks": {
                "no_total_addition_cap": report.no_total_addition_cap,
                "disk_backed_deduplication": True,
                "atomic_shard_finalize": True,
                "content_hashes": True,
                "rollback_ledger": True,
                "human_approval_routing": True,
                "remote_mutations": 0,
            },
            "limits": [
                "R0.2 plans Git tree content but does not call the GitHub API.",
                "Independent semantic or scientific validity still requires domain-specific OAK gates.",
                "Filesystem, disk, time, cost, provider quotas, and safety remain physical constraints.",
            ],
        }
        (self.output_dir / "oak-report.json").write_text(
            json.dumps(oak, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self._write_checkpoint(status="completed")

    def _write_checkpoint(self, *, status: str) -> None:
        payload = {
            "run_id": self.run_id,
            "status": status,
            "stats": dict(self._stats),
            "namespaces": sorted(self._namespaces),
            "generated_at": self.generated_at,
        }
        temporary = self._checkpoint_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        os.replace(temporary, self._checkpoint_path)

    @staticmethod
    def _append_jsonl(path: Path, value: Any) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(_canonical_json(value) + "\n")


def iter_jsonl(path: str | Path) -> Iterator[Mapping[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at line {line_number}: {exc}") from exc
            if not isinstance(value, Mapping):
                raise ValueError(f"line {line_number} must contain a JSON object")
            yield value


def synthetic_additions(count: int, *, namespaces: int = 8) -> Iterator[Mapping[str, Any]]:
    if count < 0:
        raise ValueError("count cannot be negative")
    if namespaces < 1:
        raise ValueError("namespaces must be positive")
    for index in range(count):
        namespace_index = index % namespaces
        yield {
            "addition_id": f"synthetic-{index:012d}",
            "namespace": f"domain-{namespace_index:04d}",
            "kind": "claim" if index % 3 else "test",
            "payload": {
                "index": index,
                "statement": f"Synthetic logical addition {index}",
                "value": index * index,
            },
            "provenance": [f"synthetic://generator/{index}"],
            "risk": "normal",
        }
