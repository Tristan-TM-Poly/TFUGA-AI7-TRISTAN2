"""Run a minimal LanguageCurriculum-T demo."""

from __future__ import annotations

import json

from omega_game.engines import default_language_curriculum


def main() -> None:
    curriculum = default_language_curriculum()
    quest = curriculum.quests_for_track("markdown_doc")[0]
    progress = curriculum.run_quest(quest)
    summary = curriculum.evaluate_progress([progress])
    print(json.dumps({"progress": progress.to_dict(), "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
