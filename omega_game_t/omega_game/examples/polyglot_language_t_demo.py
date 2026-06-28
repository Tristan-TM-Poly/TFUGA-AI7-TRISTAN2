"""Run a minimal PolyglotLanguageEngine-T demo."""

from __future__ import annotations

import json

from omega_game.engines import LanguageQuest, PolyglotLanguageEngine


def main() -> None:
    quest = LanguageQuest(
        source_text="Explain my GameEngineOS prototype for a new contributor.",
        source_language="en",
        target_style="markdown_doc",
        audience="repo reviewer",
        intent="make the module understandable and safe to review",
        constraints=["plain language", "limits visible"],
    )
    run = PolyglotLanguageEngine().transform(quest)
    print(json.dumps(run.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
