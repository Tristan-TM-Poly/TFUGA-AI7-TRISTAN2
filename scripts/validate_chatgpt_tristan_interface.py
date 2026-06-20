#!/usr/bin/env python3
"""Validate the static ChatGPT × Tristan OS interface."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERFACE = ROOT / "interfaces" / "chatgpt-tristan"
REQUIRED = [
    "index.html",
    "styles.css",
    "app.js",
    "prompts.json",
    "manifest.webmanifest",
    "README.md",
]


def assert_contains(path: Path, needles: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path} missing required markers: {missing}")


def main() -> int:
    for name in REQUIRED:
        path = INTERFACE / name
        if not path.exists():
            raise FileNotFoundError(path)

    prompts = json.loads((INTERFACE / "prompts.json").read_text(encoding="utf-8"))
    manifest = json.loads((INTERFACE / "manifest.webmanifest").read_text(encoding="utf-8"))
    if prompts.get("version") != "chatgpt-tristan-prompts.v1":
        raise AssertionError("Unexpected prompts version")
    if "ChatGPT" not in manifest.get("name", ""):
        raise AssertionError("Manifest name must mention ChatGPT")

    assert_contains(INTERFACE / "index.html", ["ChatGPT × Tristan OS", "promptOutput", "modeList"])
    assert_contains(INTERFACE / "app.js", ["OAK", "ZÉRO-TOUCH", "localStorage", "buildPrompt"])
    assert_contains(INTERFACE / "README.md", ["OAK boundary", "Ce que ce n’est pas"])
    print("ChatGPT Tristan interface validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
