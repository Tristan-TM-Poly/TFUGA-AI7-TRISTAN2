from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, Mapping

from .memory_codec import MemoryCard


def export_cards_csv(cards: Iterable[MemoryCard | Mapping], output: str | Path) -> Path:
    """Export cards in an Anki-friendly CSV: front, back, tags, due."""

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["front", "back", "tags", "due", "card_type"])
        writer.writeheader()
        for card in cards:
            data = card.to_dict() if isinstance(card, MemoryCard) else dict(card)
            writer.writerow(
                {
                    "front": data.get("prompt", ""),
                    "back": data.get("answer", ""),
                    "tags": " ".join(data.get("tags", [])),
                    "due": data.get("due", ""),
                    "card_type": data.get("card_type", ""),
                }
            )
    return path


def export_json(payload: Mapping, output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def export_markdown(markdown: str, output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return path
