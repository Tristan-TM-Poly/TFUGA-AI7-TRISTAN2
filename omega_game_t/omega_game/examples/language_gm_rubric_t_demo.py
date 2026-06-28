"""Run a minimal LanguageGM Rubric-T demo."""

from __future__ import annotations

import json

from omega_game.engines import LanguageGMRubric, LanguageQuest, PolyglotLanguageEngine


def main() -> None:
    quest = LanguageQuest(
        source_text="Explain this module for a repo reviewer.",
        source_language="en",
        target_style="markdown_doc",
        audience="repo reviewer",
        intent="document behavior and review limits",
        constraints=["plain language", "limits visible"],
    )
    run = PolyglotLanguageEngine().transform(quest)
    evaluation = LanguageGMRubric().evaluate(run, expected_intent=quest.intent)
    print(json.dumps(evaluation.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
