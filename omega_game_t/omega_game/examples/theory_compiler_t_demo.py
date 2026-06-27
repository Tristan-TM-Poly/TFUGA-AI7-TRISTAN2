"""Run a minimal TheoryCompiler-T demo.

Usage from this directory:

    python -m omega_game.examples.theory_compiler_t_demo
"""

from __future__ import annotations

import json

from omega_game import TheorySpec, default_theory_compiler


def main() -> None:
    compiler = default_theory_compiler()
    theories = [
        TheorySpec("Ω-CIRCUITS-T", concepts=["RLC", "resonance", "phase"]),
        TheorySpec("Ω-ENERGY-T", concepts=["microgrid", "battery", "losses"]),
        TheorySpec("Ω-PREUVE-T", concepts=["source", "evidence", "counterhypothesis"]),
        TheorySpec("Ω-COMP-REV-IP", concepts=["prototype", "IP", "revenue"]),
        TheorySpec("Ω-LASER-T", concepts=["cavity", "gain", "residue"]),
        TheorySpec("Ω-GAME-T", concepts=["world", "GM", "OAKBench"]),
    ]
    compiled = [world.to_dict() for world in compiler.compile_many(theories)]
    print(json.dumps({"compiler": "TheoryCompiler-T", "compiled": compiled}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
