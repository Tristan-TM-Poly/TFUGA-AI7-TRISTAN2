from __future__ import annotations

from typing import Any

from omega_cognitive_computer_t import Opcode

TTM_PRIMITIVES: tuple[str, ...] = (
    "OBSERVE", "RETRIEVE", "NORMALIZE", "REPRESENT", "COMPARE", "COMPOSE",
    "TRANSFORM", "SIMULATE", "PROVE", "TEST", "FALSIFY", "CALIBRATE",
    "BENCH", "ABLATE", "COMPRESS", "CRYSTALLIZE", "ROLLBACK",
)

_COGNITIVE_MAP: dict[str, Opcode] = {
    "OBSERVE": Opcode.MEASURE,
    "REPRESENT": Opcode.REPRESENT,
    "COMPARE": Opcode.BENCHMARK,
    "COMPOSE": Opcode.MERGE,
    "SIMULATE": Opcode.SIMULATE,
    "PROVE": Opcode.PROVE,
    "FALSIFY": Opcode.ATTACK,
    "BENCH": Opcode.BENCHMARK,
    "COMPRESS": Opcode.COMPRESS,
    "CRYSTALLIZE": Opcode.CRYSTALLIZE,
}

_CAPABILITY_MAP: dict[str, str] = {
    "RETRIEVE": "retrieve",
    "NORMALIZE": "normalize",
    "TRANSFORM": "transform",
    "TEST": "validation",
    "CALIBRATE": "calibrate",
    "ABLATE": "ablation",
    "ROLLBACK": "rollback",
}


def primitive_contract(name: str) -> dict[str, Any]:
    key = str(name).strip().upper()
    if key not in TTM_PRIMITIVES:
        raise KeyError(key)
    if key in _COGNITIVE_MAP:
        return {
            "primitive": key,
            "execution_layer": "omega_cognitive_computer_t",
            "canonical_opcode": _COGNITIVE_MAP[key].value,
            "new_isa_instruction": False,
        }
    return {
        "primitive": key,
        "execution_layer": "omega_capability_os_t",
        "capability_role": _CAPABILITY_MAP[key],
        "new_isa_instruction": False,
    }
