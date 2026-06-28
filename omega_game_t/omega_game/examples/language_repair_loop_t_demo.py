"""Run a minimal LanguageRepairLoop-T demo."""

from __future__ import annotations

import json

from omega_game.engines import LanguageRepairLoop
from omega_game.engines.polyglot_language import LanguageRun


def main() -> None:
    run = LanguageRun(
        target_style="markdown_doc",
        audience="repo reviewer",
        draft="too short",
        clarity_score=0.2,
        safety_score=0.2,
        structure_score=0.1,
        oak_notes=[],
        m_plus=[],
        m_minus=[],
        next_quest="repair",
    )
    result = LanguageRepairLoop().repair(run, target_score=0.80, max_attempts=3)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
