"""Run a minimal GameMasterAcademy-T demo."""

from __future__ import annotations

import json

from omega_game.masters import default_gamemaster_academy


def main() -> None:
    academy = default_gamemaster_academy()
    profile = academy.profile("RepoGM", "repo", "builder")
    quest = academy.quests_for("repo")[0]
    evaluation = academy.evaluate(profile, quest)
    print(json.dumps(evaluation.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
