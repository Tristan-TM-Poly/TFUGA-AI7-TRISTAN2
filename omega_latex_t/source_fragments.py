from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping


class SourceFragmentError(ValueError):
    pass


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


@dataclass(frozen=True)
class SourceFragmentReceipt:
    source_id: str
    locator: str
    source_sha256: str
    fragment_sha256: str
    start_line: int
    end_line: int
    byte_count: int
    line_count: int
    encoding: str = "utf-8"

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "source_id": self.source_id,
            "locator": self.locator,
            "source_sha256": self.source_sha256,
            "fragment_sha256": self.fragment_sha256,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "byte_count": self.byte_count,
            "line_count": self.line_count,
            "encoding": self.encoding,
            "boundary": "integrity/provenance receipt only; fragment identity does not establish entailment, correctness, authorship or scientific truth",
        }


def extract_text_fragment(path: str | Path, source_id: str, *, start_line: int = 1, end_line: int | None = None, encoding: str = "utf-8") -> tuple[str, SourceFragmentReceipt]:
    file_path = Path(path)
    raw = file_path.read_bytes()
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError as exc:
        raise SourceFragmentError(f"source is not valid {encoding}: {file_path}") from exc
    lines = text.splitlines(keepends=True)
    if start_line < 1:
        raise SourceFragmentError("start_line must be >= 1")
    resolved_end = len(lines) if end_line is None else int(end_line)
    if resolved_end < start_line:
        raise SourceFragmentError("end_line must be >= start_line")
    if start_line > max(len(lines), 1):
        raise SourceFragmentError("start_line exceeds source length")
    resolved_end = min(resolved_end, len(lines))
    fragment = "".join(lines[start_line - 1:resolved_end])
    fragment_bytes = fragment.encode(encoding)
    locator = f"lines:{start_line}-{resolved_end}"
    receipt = SourceFragmentReceipt(
        source_id=str(source_id),
        locator=locator,
        source_sha256=_digest(raw),
        fragment_sha256=_digest(fragment_bytes),
        start_line=start_line,
        end_line=resolved_end,
        byte_count=len(fragment_bytes),
        line_count=max(0, resolved_end - start_line + 1),
        encoding=encoding,
    )
    return fragment, receipt


def validate_receipt(receipt: Mapping[str, Any], *, fragment_text: str | None = None) -> tuple[dict[str, str], ...]:
    findings: list[dict[str, str]] = []
    for field in ("source_id", "locator", "source_sha256", "fragment_sha256"):
        if not str(receipt.get(field, "")).strip():
            findings.append({"code": "SOURCE_FRAGMENT_FIELD_MISSING", "severity": "error", "message": f"missing {field}"})
    for field in ("source_sha256", "fragment_sha256"):
        value = str(receipt.get(field, ""))
        if value and (len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.lower())):
            findings.append({"code": "SOURCE_FRAGMENT_HASH_INVALID", "severity": "error", "message": f"{field} must be a SHA-256 hex digest"})
    try:
        start = int(receipt.get("start_line", 0)); end = int(receipt.get("end_line", 0))
        if start < 1 or end < start:
            raise ValueError
    except (TypeError, ValueError):
        findings.append({"code": "SOURCE_FRAGMENT_RANGE_INVALID", "severity": "error", "message": "invalid line range"})
    if fragment_text is not None:
        encoding = str(receipt.get("encoding", "utf-8"))
        actual = _digest(fragment_text.encode(encoding))
        if actual != str(receipt.get("fragment_sha256", "")):
            findings.append({"code": "SOURCE_FRAGMENT_HASH_MISMATCH", "severity": "error", "message": "fragment text does not match receipt hash"})
    return tuple(findings)


def source_fragment_report(doc: Any) -> dict[str, Any]:
    provenance = dict(getattr(doc, "provenance", {}) or {})
    receipts = provenance.get("source_fragments", ())
    entries = []
    for index, raw in enumerate(receipts if isinstance(receipts, (list, tuple)) else ()):
        if not isinstance(raw, Mapping):
            entries.append({"index": index, "findings": [{"code": "SOURCE_FRAGMENT_INVALID", "severity": "error", "message": "receipt must be an object"}]})
            continue
        entries.append({"index": index, "receipt": dict(raw), "findings": list(validate_receipt(raw))})
    known_sources = {str(getattr(source, "id", "")): source for source in getattr(doc, "sources", ())}
    for entry in entries:
        receipt = entry.get("receipt", {})
        if not isinstance(receipt, Mapping):
            continue
        source_id = str(receipt.get("source_id", ""))
        source = known_sources.get(source_id)
        if source is None:
            entry["findings"].append({"code": "SOURCE_FRAGMENT_UNKNOWN_SOURCE", "severity": "error", "message": f"receipt references unregistered source {source_id!r}"})
            continue
        registered_sha = str(getattr(source, "sha256", "") or "").lower()
        receipt_sha = str(receipt.get("source_sha256", "")).lower()
        if registered_sha and registered_sha != receipt_sha:
            entry["findings"].append({"code": "SOURCE_FRAGMENT_SOURCE_HASH_MISMATCH", "severity": "error", "message": "receipt source hash does not match registered Source.sha256"})
    semantic_hash = getattr(doc, "semantic_hash", lambda: "")()
    return {"semantic_hash": semantic_hash, "count": len(entries), "entries": entries, "boundary": "source fragments are immutable identity/provenance receipts; they do not certify semantic support"}


def receipt_json(receipt: SourceFragmentReceipt) -> str:
    return json.dumps(receipt.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
