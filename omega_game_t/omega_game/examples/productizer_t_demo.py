"""Run a minimal Productizer-T demo."""

from __future__ import annotations

import json

from omega_game import TheorySpec, default_productizer, default_theory_compiler


def main() -> None:
    compiler = default_theory_compiler()
    planner = default_productizer()
    theories = [
        TheorySpec("OMEGA-CIRCUITS-T"),
        TheorySpec("OMEGA-ENERGY-T"),
        TheorySpec("OMEGA-PREUVE-T"),
        TheorySpec("OMEGA-COMP-REV-IP"),
        TheorySpec("OMEGA-LASER-T"),
        TheorySpec("OMEGA-GAME-T"),
    ]
    worlds = compiler.compile_many(theories)
    plans = [plan.to_dict() for plan in planner.productize_many(worlds)]
    print(json.dumps({"planner": "Productizer-T", "plans": plans}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
