from __future__ import annotations

from email import policy
from email.parser import BytesParser
from hashlib import sha256
from pathlib import Path
import json


def audit_mht(path: str | Path) -> dict:
    path = Path(path)
    raw = path.read_bytes()
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    part_types: dict[str, int] = {}
    parts = 0
    for part in msg.walk():
        if part.is_multipart():
            continue
        parts += 1
        part_types[part.get_content_type()] = part_types.get(part.get_content_type(), 0) + 1
    return {
        "filename": path.name,
        "bytes": len(raw),
        "sha256": sha256(raw).hexdigest(),
        "subject": msg.get("Subject"),
        "snapshot_location": msg.get("Snapshot-Content-Location"),
        "leaf_parts": parts,
        "content_types": dict(sorted(part_types.items())),
        "claim": "This manifest proves bytes and MIME structure only; it does not independently verify claims inside the archived conversation.",
    }


def write_manifest(source: str | Path, output: str | Path) -> None:
    Path(output).write_text(json.dumps(audit_mht(source), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
