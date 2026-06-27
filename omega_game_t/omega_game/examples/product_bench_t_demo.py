"""Run a minimal ProductBench-T demo."""

from __future__ import annotations

import json

from omega_game import TheorySpec, default_product_bench, default_productizer, default_theory_compiler


def main() -> None:
    compiled = default_theory_compiler().compile(TheorySpec("OMEGA-CIRCUITS-T"))
    plan = default_productizer().productize(compiled)
    score = default_product_bench().evaluate(plan)
    print(json.dumps(score.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
