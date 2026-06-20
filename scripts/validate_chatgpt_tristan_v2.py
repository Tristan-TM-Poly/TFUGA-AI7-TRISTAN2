#!/usr/bin/env python3
"""Validate ChatGPT Tristan OS v2 static interface and contracts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "interfaces" / "chatgpt-tristan-v2"
SCHEMAS = ROOT / "schemas" / "chatgpt-tristan"
REQUIRED_UI = [
    "index.html",
    "styles.css",
    "app.js",
    "data/theory-canon.json",
    "examples/session_spectro.json",
    "examples/session_publication.json",
]
REQUIRED_CONTRACTS = [
    "session_contract.json",
    "oak_card_contract.json",
]


def require(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def contains(path: Path, markers: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [marker for marker in markers if marker not in text]
    if missing:
        raise AssertionError(f"{path} missing markers: {missing}")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_session(path: Path) -> None:
    session = load_json(path)
    required = load_json(SCHEMAS / "session_contract.json")["required_fields"]
    missing = [field for field in required if field not in session]
    if missing:
        raise AssertionError(f"{path} missing session fields: {missing}")
    if session["version"] != "chatgpt-tristan-session.v2":
        raise AssertionError(f"{path} has unexpected version")


def main() -> int:
    for rel in REQUIRED_UI:
        require(UI / rel)
    for rel in REQUIRED_CONTRACTS:
        require(SCHEMAS / rel)

    contains(UI / "index.html", ["ChatGPT", "OAK", "HGFM", "prompt"])
    contains(UI / "app.js", ["compile", "Auto-OAK", "localStorage", "HGFM"])
    contains(UI / "styles.css", ["--a", "grid", "hero"])

    canon = load_json(UI / "data/theory-canon.json")
    if len(canon.get("entries", [])) < 5:
        raise AssertionError("theory canon should contain several entries")

    validate_session(UI / "examples/session_spectro.json")
    validate_session(UI / "examples/session_publication.json")
    print("ChatGPT Tristan OS v2 validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
