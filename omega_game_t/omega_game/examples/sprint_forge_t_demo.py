"""Run a minimal SprintForge-T demo."""

from __future__ import annotations

import json

from omega_game import (
    TheorySpec,
    default_issue_forge,
    default_productizer,
    default_sprint_forge,
    default_theory_compiler,
)


def main() -> None:
    world = default_theory_compiler().compile(TheorySpec("OMEGA-CIRCUITS-T"))
    plan = default_productizer().productize(world)
    issue_set = default_issue_forge().forge(plan)
    sprint = default_sprint_forge().forge(issue_set)
    print(json.dumps(sprint.to_dict(), indent=2, ensure_ascii=False))
    print("\n--- MARKDOWN PREVIEW ---\n")
    print(sprint.to_markdown())


if __name__ == "__main__":
    main()
