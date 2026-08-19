#!/usr/bin/env python3
"""Prototype vector factorisation for AI-BIGBOOK sections.

Input: a JSONL file where each row has {"section_id": str, "vector": [float, ...]}.
Output: one factorized section vector per section as JSONL.
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np


def factorise(vectors: list[list[float]], rank: int = 3) -> dict:
    matrix = np.asarray(vectors, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0:
        raise ValueError("Expected a non-empty 2D matrix")
    u, s, vt = np.linalg.svd(matrix, full_matrices=False)
    r = max(1, min(rank, len(s)))
    retained = float(np.sum(s[:r]) / np.sum(s)) if np.sum(s) else 0.0
    dominant = (vt[0, :] * s[0]).tolist()
    return {"rank": r, "power_real_retained": retained, "section_vector": dominant}


def main(src: str, dst: str, rank: int = 3) -> int:
    groups: dict[str, list[list[float]]] = defaultdict(list)
    for line in Path(src).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        groups[str(row["section_id"])].append(row["vector"])
    out = []
    for section_id, vectors in groups.items():
        result = factorise(vectors, rank=rank)
        result["section_id"] = section_id
        out.append(json.dumps(result, ensure_ascii=False, sort_keys=True))
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"[OK] wrote {dst} for {len(out)} sections")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: tensor_factorise.py input_vectors.jsonl output_section_factors.jsonl [rank]", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 3))
