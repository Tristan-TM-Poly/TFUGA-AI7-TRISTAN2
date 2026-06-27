"""Run a minimal DemoForge-T demo."""

from __future__ import annotations

import json

from omega_game import (
    TheorySpec,
    default_demo_forge,
    default_issue_forge,
    default_productizer,
    default_sprint_forge,
    default_theory_compiler,
)


def main() -> None:
    world = default_theory_compiler().compile(TheorySpec("OMEGA-CIRCUITS-T"))
    product = default_productizer().productize(world)
    issue_set = default_issue_forge().forge(product)
    sprint = default_sprint_forge().forge(issue_set)
    demo = default_demo_forge().forge(product, sprint)
    print(json.dumps(demo.to_dict(), indent=2, ensure_ascii=False))
    print("\n--- MARKDOWN PREVIEW ---\n")
    print(demo.to_markdown())


if __name__ == "__main__":
    main()
