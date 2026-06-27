"""Run a minimal LanguageValidators-T demo."""

from __future__ import annotations

import json

from omega_game.engines import LanguageQuest, LanguageValidators, PolyglotLanguageEngine


def main() -> None:
    quest = LanguageQuest(
        source_text="Document the new language validator module.",
        source_language="en",
        target_style="markdown_doc",
        audience="repo reviewer",
        intent="show purpose, checks, and OAK boundary",
        constraints=["limits visible"],
    )
    run = PolyglotLanguageEngine().transform(quest)
    report = LanguageValidators().validate(run)
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
