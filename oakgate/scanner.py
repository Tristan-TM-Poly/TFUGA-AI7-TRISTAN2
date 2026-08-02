"""Load OAK claims from JSON or fenced Markdown blocks with source lines."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Iterable

from .model import Claim, ScannedClaim, SourceLocation


_OAK_BLOCK = re.compile(
    r"^```oak-claim[ \t]*\r?\n(?P<body>.*?)^```[ \t]*$",
    re.MULTILINE | re.DOTALL,
)


def _json_claims(path: Path) -> list[ScannedClaim]:
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else [raw]
    if not all(isinstance(item, dict) for item in items):
        raise ValueError(f"{path}: input must be a JSON object or list of objects")
    return [
        ScannedClaim(
            claim=Claim.from_dict(item),
            source=SourceLocation(str(path), 1, 1),
        )
        for item in items
    ]


def _markdown_claims(path: Path) -> list[ScannedClaim]:
    text = path.read_text(encoding="utf-8")
    claims: list[ScannedClaim] = []
    for match in _OAK_BLOCK.finditer(text):
        body = match.group("body")
        raw = json.loads(body)
        if not isinstance(raw, dict):
            raise ValueError(f"{path}: each oak-claim block must contain one JSON object")
        start_line = text.count("\n", 0, match.start("body")) + 1
        end_line = start_line + max(0, body.count("\n"))
        claims.append(
            ScannedClaim(
                claim=Claim.from_dict(raw),
                source=SourceLocation(str(path), start_line, end_line),
            )
        )
    if not claims:
        raise ValueError(f"{path}: no ```oak-claim fenced JSON block found")
    return claims


def load_scanned_claims(path: Path) -> list[ScannedClaim]:
    suffix = path.suffix.casefold()
    if suffix == ".json":
        return _json_claims(path)
    if suffix in {".md", ".markdown"}:
        return _markdown_claims(path)
    raise ValueError(f"{path}: supported inputs are .json, .md, and .markdown")


def expand_inputs(paths: Iterable[Path], *, recursive: bool = False) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        if path.is_file():
            expanded.append(path)
            continue
        if path.is_dir() and recursive:
            expanded.extend(
                candidate
                for candidate in sorted(path.rglob("*"))
                if candidate.is_file()
                and candidate.suffix.casefold() in {".json", ".md", ".markdown"}
            )
            continue
        if path.is_dir():
            raise ValueError(f"{path}: directory input requires --recursive")
        raise ValueError(f"{path}: file or directory not found")
    if not expanded:
        raise ValueError("no supported input files found")
    return expanded
