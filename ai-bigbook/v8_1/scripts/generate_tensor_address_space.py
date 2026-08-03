#!/usr/bin/env python3
"""Generate the 65,536 AI-BIGBOOK tensor address nodes as JSONL.GZ."""
from __future__ import annotations
import gzip, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "v8_tensor_address_space_65536.jsonl.gz"
AXES = ["ontology", "math", "code", "physics", "signal", "agents", "safety", "publication"]
BLOCKS = ["canon", "corpus", "ffwt", "hgfm", "hyperalgebra", "agents", "redteam", "publication"]
MODES = ["real", "complex", "quaternionic", "octonionic", "sedenionic_sandbox"]
STATUSES = ["R0", "R1", "R2", "R3", "R4", "R5"]

def coords(i: int) -> dict:
    out = {}
    x = i
    for axis in reversed(AXES):
        out[axis] = x % 4
        x //= 4
    return {axis: out[axis] for axis in AXES}

def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    total = 4 ** len(AXES)
    with gzip.open(OUT, "wt", encoding="utf-8") as f:
        for i in range(total):
            row = {
                "id": i,
                "coords": coords(i),
                "block": BLOCKS[i % len(BLOCKS)],
                "mode": MODES[i % len(MODES)],
                "status": STATUSES[i % len(STATUSES)],
                "gate": "EvidenceGate+SafetyGate",
                "external_mutation": False
            }
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"[OK] wrote {OUT} with {total} nodes")

if __name__ == "__main__":
    main()
