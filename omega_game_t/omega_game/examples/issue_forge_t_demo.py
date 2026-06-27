"""Run a minimal IssueForge-T demo."""

from __future__ import annotations

import json

from omega_game import TheorySpec, default_issue_forge, default_productizer, default_theory_compiler


def main() -> None:
    world = default_theory_compiler().compile(TheorySpec("OMEGA-CIRCUITS-T"))
    plan = default_productizer().productize(world)
    issue_set = default_issue_forge().forge(plan)
    print(json.dumps(issue_set.to_dict(), indent=2, ensure_ascii=False))
    print("\n--- MARKDOWN PREVIEW ---\n")
    print(issue_set.to_markdown()[:2000])


if __name__ == "__main__":
    main()
