"""Google Drive manifest adapter for Omega Universal Absorber.

The adapter is intentionally offline and OAK-safe: it does not fetch private
Drive bytes by itself. It converts an exported/listed Drive inventory into a
normalized source manifest that the absorber pipeline can audit, deduplicate,
and later route to an authorized downloader.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class DriveManifestItem:
    source_id: str
    name: str
    mime_type: str
    size_bytes: int | None
    web_url: str | None
    modified_time: str | None
    sha256: str | None
    oak_status: str
    warnings: tuple[str, ...]


REQUIRED_MINIMUM_KEYS = ("id", "name")


def _safe_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _first(row: dict, *keys: str) -> object:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def item_from_row(row: dict) -> DriveManifestItem:
    source_id = str(_first(row, "id", "file_id", "source_id") or "")
    name = str(_first(row, "name", "filename", "path") or "")
    mime_type = str(_first(row, "mimeType", "mime_type", "type") or "unknown")
    size = _safe_int(_first(row, "size", "size_bytes"))
    url = _first(row, "webViewLink", "web_url", "url")
    modified = _first(row, "modifiedTime", "modified_time", "updated_at")
    sha256 = _first(row, "sha256", "hash")
    warnings: list[str] = []
    if not source_id:
        warnings.append("missing_drive_file_id")
    if not name:
        warnings.append("missing_name")
    if "folder" in mime_type.lower():
        warnings.append("folder_requires_recursive_listing")
    if size == 0:
        warnings.append("empty_file")
    if sha256 is None:
        warnings.append("missing_content_hash_until_downloaded")
    oak_status = "metadata_only_no_content_downloaded"
    return DriveManifestItem(
        source_id=source_id,
        name=name,
        mime_type=mime_type,
        size_bytes=size,
        web_url=str(url) if url is not None else None,
        modified_time=str(modified) if modified is not None else None,
        sha256=str(sha256) if sha256 is not None else None,
        oak_status=oak_status,
        warnings=tuple(warnings),
    )


def load_manifest_rows(path: str | Path) -> list[dict]:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".csv":
        return list(csv.DictReader(text.splitlines()))
    payload = json.loads(text)
    if isinstance(payload, list):
        return [dict(item) for item in payload]
    if isinstance(payload, dict):
        for key in ("files", "items", "objects", "data"):
            if isinstance(payload.get(key), list):
                return [dict(item) for item in payload[key]]
    raise ValueError("Drive manifest must be a JSON list, JSON object with files/items/objects/data, or CSV")


def normalize_drive_manifest(path: str | Path) -> list[DriveManifestItem]:
    return [item_from_row(row) for row in load_manifest_rows(path)]


def write_normalized_manifest(items: Sequence[DriveManifestItem], output_path: str | Path) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps([asdict(item) for item in items], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def audit_manifest(items: Sequence[DriveManifestItem]) -> dict:
    warnings = sorted({warning for item in items for warning in item.warnings})
    pdfs = [item for item in items if item.name.lower().endswith(".pdf") or "pdf" in item.mime_type.lower()]
    folders = [item for item in items if "folder" in item.mime_type.lower()]
    return {
        "status": "metadata_only_dry_run",
        "items": len(items),
        "pdf_like_items": len(pdfs),
        "folders": len(folders),
        "warnings": warnings,
        "oak_gates": [
            "Drive metadata is not content extraction",
            "OAuth least privilege is required before downloading bytes",
            "Do not publish private Drive files or generated excerpts without IP/privacy review",
            "Folder links require recursive manifest expansion before completeness claims",
        ],
    }


def render_audit_markdown(audit: dict) -> str:
    lines = ["# Drive Manifest OAK Audit", ""]
    for key in ("status", "items", "pdf_like_items", "folders"):
        lines.append(f"- {key}: `{audit.get(key)}`")
    lines.append("- warnings:")
    lines.extend(f"  - {warning}" for warning in audit.get("warnings", []))
    lines.append("- OAK gates:")
    lines.extend(f"  - {gate}" for gate in audit.get("oak_gates", []))
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-drive-manifest", description="Normalize and audit a Drive file manifest")
    parser.add_argument("input", help="Drive manifest JSON or CSV")
    parser.add_argument("--output", default="generated/drive_manifest.normalized.json")
    parser.add_argument("--audit", action="store_true", help="Print OAK audit instead of writing only")
    return parser


def run_cli(argv: Sequence[str] | None = None) -> str:
    args = build_parser().parse_args(argv)
    items = normalize_drive_manifest(args.input)
    path = write_normalized_manifest(items, args.output)
    audit = audit_manifest(items)
    if args.audit:
        return render_audit_markdown(audit) + f"\nnormalized_manifest={path}\n"
    return f"normalized_items={len(items)} path={path}\n"


def main() -> None:
    sys.stdout.write(run_cli())


if __name__ == "__main__":
    main()
