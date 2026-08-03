#!/usr/bin/env python3
"""Omni Translator V8.3 prototype.

Projects a section vector into machine, orchestration, expert, and public layers.
This is a representation tool, not an EvidenceGate bypass.

OAK-safe CI note:
This smoke-test helper intentionally uses only Python's standard library so the
read-only local CI can run without dependency installation or network access.
"""
from __future__ import annotations

import binascii
import json
import math
import struct
import sys


def _float16_hex_prefix(vector: list[float], prefix_chars: int = 64) -> str:
    """Return a compact deterministic half-precision byte projection.

    `struct` format code `e` stores IEEE-754 binary16 values and is available in
    modern CPython. This replaces the previous NumPy-only conversion while
    preserving the same local, non-mutating representation intent.
    """
    raw = b"".join(struct.pack("<e", float(x)) for x in vector)
    encoded = binascii.hexlify(raw).decode("ascii")
    return encoded[:prefix_chars] + ("..." if len(encoded) > prefix_chars else "")


def _l2_norm(vector: list[float]) -> float:
    return math.sqrt(sum(float(x) * float(x) for x in vector))


def translate(vector: list[float], concept_id: str, register: str = "R2") -> dict:
    return {
        "concept_id": concept_id,
        "reality_register": register,
        "machine_hex_prefix": _float16_hex_prefix(vector),
        "agent_contract": {
            "concept": concept_id,
            "vector_norm": _l2_norm(vector),
            "action": "PROPOSE_LOCAL_PATCH",
            "requires": ["EvidenceGate", "ApprovalSentinel"],
        },
        "latex_stub": rf"\\mathcal{{H}}_{{{concept_id}}} = \\sum_i v_i \\mathbf{{e}}_i",
        "public_projection": (
            f"{concept_id} is represented as a compact vector object that can "
            "generate explanations, code stubs, and tests while preserving its "
            "evidence status."
        ),
    }


def main() -> int:
    concept = sys.argv[1] if len(sys.argv) > 1 else "AI_BIGBOOK_SECTION"
    raw_vector = sys.argv[2] if len(sys.argv) > 2 else "0.9,-0.4,0.1,0.88"
    vector = [float(x) for x in raw_vector.split(",") if x.strip()]
    if not vector:
        print("vector must contain at least one numeric coordinate", file=sys.stderr)
        return 2
    print(json.dumps(translate(vector, concept), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
