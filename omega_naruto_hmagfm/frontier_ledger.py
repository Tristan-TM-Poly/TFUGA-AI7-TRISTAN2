"""Federated manifest ledger for Ω-NARUTO frontier scale runs.

A ledger joins immutable finite runs into one global ordinal history. It rejects
range overlap, records gaps explicitly, and computes a deterministic federation
root from run boundaries and Merkle roots. The ledger does not copy corpus data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class LedgerFinding:
    code: str
    severity: str
    message: str
    run_id: str | None = None


@dataclass(frozen=True)
class FrontierRunEntry:
    run_id: str
    manifest_path: str
    start_ordinal: int
    next_ordinal: int
    written_records: int
    shard_count: int
    compressed_bytes: int
    uncompressed_bytes: int
    logical_corpus_sha256: str
    merkle_root_sha256: str
    complete: bool

    @property
    def range_records(self) -> int:
        return self.next_ordinal - self.start_ordinal


@dataclass(frozen=True)
class FrontierRunLedger:
    schema: str
    valid: bool
    contiguous: bool
    run_count: int
    total_records: int
    first_ordinal: int
    next_ordinal: int
    total_compressed_bytes: int
    total_uncompressed_bytes: int
    federation_root_sha256: str
    runs: tuple[FrontierRunEntry, ...]
    findings: tuple[LedgerFinding, ...]
    non_claim: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["runs"] = [asdict(item) | {"range_records": item.range_records} for item in self.runs]
        payload["findings"] = [asdict(item) for item in self.findings]
        return payload


def _canonical_run_id(payload: dict[str, object]) -> str:
    canonical = "|".join(
        (
            str(payload.get("start_ordinal", 0)),
            str(payload.get("next_ordinal", 0)),
            str(payload.get("written_records", 0)),
            str(payload.get("merkle_root_sha256", "")),
            str(payload.get("logical_corpus_sha256", "")),
        )
    )
    return "run-" + sha256(canonical.encode("utf-8")).hexdigest()[:24]


def _entry_from_manifest(path: Path) -> FrontierRunEntry:
    payload = json.loads(path.read_text(encoding="utf-8"))
    run_id = _canonical_run_id(payload)
    return FrontierRunEntry(
        run_id=run_id,
        manifest_path=str(path),
        start_ordinal=int(payload.get("start_ordinal", 0)),
        next_ordinal=int(payload.get("next_ordinal", 0)),
        written_records=int(payload.get("written_records", 0)),
        shard_count=int(payload.get("shard_count", 0)),
        compressed_bytes=int(payload.get("compressed_bytes", 0)),
        uncompressed_bytes=int(payload.get("uncompressed_bytes", 0)),
        logical_corpus_sha256=str(payload.get("logical_corpus_sha256", "")),
        merkle_root_sha256=str(payload.get("merkle_root_sha256", "")),
        complete=bool(payload.get("complete", False)),
    )


def _federation_root(runs: Iterable[FrontierRunEntry]) -> str:
    digest = sha256()
    for run in runs:
        digest.update(
            (
                f"{run.run_id}|{run.start_ordinal}|{run.next_ordinal}|"
                f"{run.written_records}|{run.merkle_root_sha256}\n"
            ).encode("utf-8")
        )
    return digest.hexdigest()


def build_run_ledger(
    manifest_paths: Iterable[Path],
    *,
    require_contiguous: bool = True,
) -> FrontierRunLedger:
    """Build a deterministic ledger from immutable scale manifests."""

    paths = tuple(manifest_paths)
    if not paths:
        raise ValueError("at least one manifest path is required")
    runs = tuple(sorted((_entry_from_manifest(path) for path in paths), key=lambda item: item.start_ordinal))
    findings: list[LedgerFinding] = []
    contiguous = True

    seen_ids: set[str] = set()
    previous: FrontierRunEntry | None = None
    for run in runs:
        if run.run_id in seen_ids:
            findings.append(
                LedgerFinding(
                    "LEDGER_DUPLICATE_RUN",
                    "P0",
                    "the same canonical run appears more than once",
                    run.run_id,
                )
            )
        seen_ids.add(run.run_id)
        if not run.complete:
            findings.append(
                LedgerFinding(
                    "LEDGER_INCOMPLETE_RUN",
                    "P0",
                    "run manifest is not complete",
                    run.run_id,
                )
            )
        if run.range_records != run.written_records:
            findings.append(
                LedgerFinding(
                    "LEDGER_RANGE_COUNT_MISMATCH",
                    "P0",
                    f"range contains {run.range_records}, manifest reports {run.written_records}",
                    run.run_id,
                )
            )
        if run.next_ordinal < run.start_ordinal:
            findings.append(
                LedgerFinding(
                    "LEDGER_NEGATIVE_RANGE",
                    "P0",
                    "next_ordinal is below start_ordinal",
                    run.run_id,
                )
            )
        if len(run.merkle_root_sha256) != 64:
            findings.append(
                LedgerFinding(
                    "LEDGER_INVALID_MERKLE_ROOT",
                    "P0",
                    "run Merkle root must be a SHA-256 hexadecimal digest",
                    run.run_id,
                )
            )
        if previous is not None:
            if run.start_ordinal < previous.next_ordinal:
                findings.append(
                    LedgerFinding(
                        "LEDGER_RANGE_OVERLAP",
                        "P0",
                        (
                            f"run starts at {run.start_ordinal} before previous run ends "
                            f"at {previous.next_ordinal}"
                        ),
                        run.run_id,
                    )
                )
            elif run.start_ordinal > previous.next_ordinal:
                contiguous = False
                findings.append(
                    LedgerFinding(
                        "LEDGER_RANGE_GAP",
                        "P1" if not require_contiguous else "P0",
                        (
                            f"gap from ordinal {previous.next_ordinal} to "
                            f"{run.start_ordinal}"
                        ),
                        run.run_id,
                    )
                )
        previous = run

    valid = not any(item.severity == "P0" for item in findings)
    return FrontierRunLedger(
        schema="omega_naruto_frontier.run_ledger.v3",
        valid=valid,
        contiguous=contiguous,
        run_count=len(runs),
        total_records=sum(item.written_records for item in runs),
        first_ordinal=runs[0].start_ordinal,
        next_ordinal=max(item.next_ordinal for item in runs),
        total_compressed_bytes=sum(item.compressed_bytes for item in runs),
        total_uncompressed_bytes=sum(item.uncompressed_bytes for item in runs),
        federation_root_sha256=_federation_root(runs),
        runs=runs,
        findings=tuple(findings),
        non_claim=(
            "Ledger federation proves manifest ordering and integrity references; "
            "it does not establish scientific truth, novelty, or usefulness."
        ),
    )


def write_run_ledger(
    manifest_paths: Iterable[Path],
    *,
    destination: Path,
    require_contiguous: bool = True,
) -> FrontierRunLedger:
    ledger = build_run_ledger(
        manifest_paths,
        require_contiguous=require_contiguous,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(ledger.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return ledger
