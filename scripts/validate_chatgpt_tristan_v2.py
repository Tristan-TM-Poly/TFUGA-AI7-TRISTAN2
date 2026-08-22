#!/usr/bin/env python3
"""Validate ChatGPT Tristan OS v2 static interface, addons, and contracts."""

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
    "app.v21.js",
    "app.v22.js",
    "app.v23.js",
    "app.v24.js",
    "data/theory-canon.json",
    "examples/session_spectro.json",
    "examples/session_publication.json",
    "examples/virtual_university_genome.json",
]
REQUIRED_CONTRACTS = [
    "session_contract.json",
    "oak_card_contract.json",
    "university_genome_contract.json",
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
    if not session.get("negative_memory"):
        raise AssertionError(f"{path} should include negative memory")


def validate_university_genome(path: Path) -> None:
    genome = load_json(path)
    schema = load_json(SCHEMAS / "university_genome_contract.json")
    missing = [field for field in schema["required"] if field not in genome]
    if missing:
        raise AssertionError(f"{path} missing UniversityGenome fields: {missing}")
    if genome["version"] != "omega-virtual-university-genome.v0.1":
        raise AssertionError("unexpected UniversityGenome version")
    if genome["institution_type"] != "virtual_university":
        raise AssertionError("UniversityGenome must identify virtual_university")
    multiplayer = genome["multiplayer"]
    if multiplayer.get("contract_status") == "prototype_only" and not multiplayer.get("realtime_backend_required"):
        raise AssertionError("prototype multiplayer must state that a realtime backend is required")
    if not multiplayer.get("authenticated_members_required"):
        raise AssertionError("subscriber multiplayer must require authenticated members")
    for agent in genome.get("agents", []):
        if agent.get("identity") != "AI agent/persona":
            raise AssertionError("every Tristan Virtual must be explicitly identified as an AI agent/persona")
    constitution = set(genome.get("governance", {}).get("constitution", []))
    required_invariants = {"Agent != Human", "Capability != Authority", "Simulation != Reality", "Generated != Verified"}
    if not required_invariants.issubset(constitution):
        raise AssertionError("UniversityGenome is missing OAK constitution invariants")
    if genome.get("metrics", {}).get("verified_capability", 0) != 0:
        raise AssertionError("example scaffold must not claim verified capability")


def main() -> int:
    for rel in REQUIRED_UI:
        require(UI / rel)
    for rel in REQUIRED_CONTRACTS:
        require(SCHEMAS / rel)

    contains(UI / "index.html", ["ChatGPT", "OAK", "HGFM", "prompt", "v2.1", "v2.2", "v2.3", "Universités v2.4", "app.v24.js"])
    contains(UI / "app.js", ["compile", "Auto-OAK", "localStorage", "HGFM", "publication package"])
    contains(UI / "app.v21.js", ["Prompt Diff", "safetyRadar", "canonizeSession", "fertility_is_not_proof"])
    contains(UI / "app.v22.js", ["Iteration Chain", "estimateImpact", "1024 candidates", "heuristic_score"])
    contains(UI / "app.v23.js", ["Score History", "local process trend", "not proof"])
    contains(UI / "app.v24.js", ["UniversityGenome", "prototype_only", "SIMULATED", "Agent != Human", "realtime_backend_required"])
    contains(UI / "styles.css", ["--a", "grid", "hero"])

    canon = load_json(UI / "data/theory-canon.json")
    if len(canon.get("entries", [])) < 5:
        raise AssertionError("theory canon should contain several entries")

    oak_contract = load_json(SCHEMAS / "oak_card_contract.json")
    if "prototype is not proof" not in oak_contract.get("anti_illusion_rules", []):
        raise AssertionError("OAK contract must preserve anti-illusion rules")

    validate_session(UI / "examples/session_spectro.json")
    validate_session(UI / "examples/session_publication.json")
    validate_university_genome(UI / "examples/virtual_university_genome.json")
    print("ChatGPT Tristan OS v2.4 validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
