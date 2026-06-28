"""Run a minimal LanguageDatasetForge-T demo."""

from __future__ import annotations

import json

from omega_game.engines import default_language_dataset_forge


def main() -> None:
    dataset = default_language_dataset_forge().forge(max_items=3)
    print(json.dumps(dataset.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
