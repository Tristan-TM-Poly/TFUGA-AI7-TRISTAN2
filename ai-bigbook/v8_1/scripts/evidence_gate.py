#!/usr/bin/env python3
"""Minimal EvidenceGate for AI-BIGBOOK claims JSONL."""
from __future__ import annotations
import json, sys
from pathlib import Path

LEVELS = {"R0":0,"R1":1,"R2":2,"R3":3,"R4":4,"R5":5}

def gate(claim: dict) -> dict:
    pr = float(claim.get("power_real", 0.0))
    level = claim.get("reality_level", "R0")
    if not 0.0 <= pr <= 1.0:
        return {"id": claim.get("id"), "status": "blocked", "reason": "PowerReal outside [0,1]"}
    if level not in LEVELS:
        return {"id": claim.get("id"), "status": "blocked", "reason": "Unknown reality level"}
    if LEVELS[level] >= 4 and pr < 0.75:
        return {"id": claim.get("id"), "status": "blocked", "reason": "R4/R5 claim lacks evidence score"}
    return {"id": claim.get("id"), "status": "allowed_local_patch", "reason": "EvidenceGate passed"}

def main(path: str) -> int:
    p = Path(path)
    ok = True
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        result = gate(json.loads(line))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        ok = ok and not result["status"].startswith("blocked")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "ai-bigbook/v8_1/specs/CLAIMS_REGISTRY_SEED.jsonl"))
