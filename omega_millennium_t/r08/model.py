from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

EVENT_SCHEMA = "omega-problem-routing-events/8"
REPORT_SCHEMA = "omega-problem-routing-report/8"
MANIFEST_SCHEMA = "omega-problem-routing-manifest/8"
GENESIS_HASH = "0" * 64

# Fixed operational routing deltas. These values rank where to spend research
# effort; they do not estimate the truth of a theorem or conjecture.
EVENT_RULES: Mapping[str, Mapping[str, Any]] = {
    "source_status_verified": {"delta": 8, "mminus": False, "category": "provenance"},
    "source_status_invalidated": {"delta": -25, "mminus": True, "category": "provenance"},
    "known_case_reproduced": {"delta": 12, "mminus": False, "category": "reproduction"},
    "valid_counterexample_found": {"delta": 18, "mminus": True, "category": "falsification"},
    "bound_improved": {"delta": 20, "mminus": False, "category": "result"},
    "bound_failed": {"delta": -6, "mminus": True, "category": "failure"},
    "assumption_discharged": {"delta": 15, "mminus": False, "category": "assumption"},
    "hidden_assumption_exposed": {"delta": 10, "mminus": True, "category": "assumption"},
    "formal_artifact_kernel_checked": {"delta": 25, "mminus": False, "category": "formal"},
    "formal_artifact_rejected": {"delta": -15, "mminus": True, "category": "formal"},
    "computation_success": {"delta": 6, "mminus": False, "category": "computation"},
    "computation_invalid_certificate": {"delta": -18, "mminus": True, "category": "computation"},
    "method_timeout": {"delta": -8, "mminus": True, "category": "failure"},
    "method_diverged": {"delta": -10, "mminus": True, "category": "failure"},
    "duplicate_known_work": {"delta": -20, "mminus": True, "category": "novelty"},
    "independent_review_accepted": {"delta": 20, "mminus": False, "category": "review"},
    "independent_review_challenged": {"delta": -12, "mminus": True, "category": "review"},
    "independent_review_rejected": {"delta": -25, "mminus": True, "category": "review"},
}


@dataclass(frozen=True)
class RoutingCell:
    cell_id: str
    problem_id: str
    front: str
    title: str
    initial_routing_score: int
    method_family: str
    active: bool
    provenance_refs: tuple[str, ...]
    cell_digest: str


@dataclass(frozen=True)
class RoutingEvent:
    event_id: str
    sequence: int
    occurred_at: str
    cell_id: str
    event_type: str
    evidence_ref: str
    observation: str
    source_digest: str
    previous_event_hash: str
    routing_delta: int
    category: str
    event_hash: str


def stable_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def parse_iso8601(value: str, field_name: str) -> str:
    candidate = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"{field_name} is not ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} requires timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def identifier(value: Any, field: str) -> str:
    result = str(value or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:\-]*", result):
        raise ValueError(f"invalid {field}: {result!r}")
    return result


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{line_number}: invalid JSON") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path.name}:{line_number}: row must be an object")
        rows.append(row)
    return rows


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, ensure_ascii=False) + "\n")
            count += 1
    return count


def file_receipt(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": path.name,
        "sha256": sha256(data).hexdigest(),
        "bytes": len(data),
        "rows": sum(1 for line in data.splitlines() if line.strip()),
    }


def build_cell(raw: Mapping[str, Any]) -> RoutingCell:
    cell_id = identifier(raw.get("cell_id"), "cell_id")
    problem_id = identifier(raw.get("problem_id"), "problem_id")
    front = identifier(raw.get("front"), "front")
    title = str(raw.get("title", "")).strip()
    method_family = str(raw.get("method_family", "")).strip()
    score = raw.get("initial_routing_score")
    active = raw.get("active", True)
    refs_raw = raw.get("provenance_refs")
    if not title or not method_family:
        raise ValueError(f"{cell_id}: title and method_family are required")
    if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
        raise ValueError(f"{cell_id}: initial_routing_score must be an integer in [0, 100]")
    if not isinstance(active, bool):
        raise ValueError(f"{cell_id}: active must be boolean")
    if not isinstance(refs_raw, list) or not all(isinstance(item, str) for item in refs_raw):
        raise ValueError(f"{cell_id}: provenance_refs must be a string list")
    refs = tuple(sorted({item.strip() for item in refs_raw if item.strip()}))
    if not refs:
        raise ValueError(f"{cell_id}: at least one provenance reference is required")
    base = {
        "cell_id": cell_id,
        "problem_id": problem_id,
        "front": front,
        "title": title,
        "initial_routing_score": score,
        "method_family": method_family,
        "active": active,
        "provenance_refs": refs,
    }
    return RoutingCell(**base, cell_digest=stable_digest(base))


def load_cells(path_like: str | Path) -> tuple[RoutingCell, ...]:
    rows = read_jsonl(Path(path_like))
    cells = tuple(sorted((build_cell(row) for row in rows), key=lambda item: item.cell_id))
    if len({cell.cell_id for cell in cells}) != len(cells):
        raise ValueError("duplicate cell_id")
    return cells


def load_event_bundle(path_like: str | Path, known_cells: set[str]) -> tuple[str, list[dict[str, Any]]]:
    path = Path(path_like)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != EVENT_SCHEMA:
        raise ValueError(f"{path}: unsupported event schema")
    ledger_id = identifier(payload.get("ledger_id"), "ledger_id")
    events = payload.get("events")
    if not isinstance(events, list) or not all(isinstance(item, Mapping) for item in events):
        raise ValueError(f"{path}: events must be an object list")
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for expected_sequence, raw in enumerate(events, 1):
        event_id = identifier(raw.get("event_id"), "event_id")
        if event_id in seen_ids:
            raise ValueError(f"{path}: duplicate event_id {event_id}")
        seen_ids.add(event_id)
        sequence = raw.get("sequence")
        if sequence != expected_sequence:
            raise ValueError(f"{event_id}: sequence must be contiguous from 1")
        cell_id = identifier(raw.get("cell_id"), "cell_id")
        if cell_id not in known_cells:
            raise ValueError(f"{event_id}: unknown cell_id")
        event_type = str(raw.get("event_type", "")).strip()
        if event_type not in EVENT_RULES:
            raise ValueError(f"{event_id}: unsupported event_type {event_type!r}")
        evidence_ref = str(raw.get("evidence_ref", "")).strip()
        observation = str(raw.get("observation", "")).strip()
        source_digest = str(raw.get("source_digest", "")).strip()
        if not evidence_ref or not observation:
            raise ValueError(f"{event_id}: evidence_ref and observation are required")
        if not re.fullmatch(r"[a-f0-9]{64}", source_digest):
            raise ValueError(f"{event_id}: source_digest must be SHA-256")
        normalized.append({
            "event_id": event_id,
            "sequence": sequence,
            "occurred_at": parse_iso8601(str(raw.get("occurred_at", "")), "occurred_at"),
            "cell_id": cell_id,
            "event_type": event_type,
            "evidence_ref": evidence_ref,
            "observation": observation,
            "source_digest": source_digest,
        })
    return ledger_id, normalized
