from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Iterable, List

from .core import ErrorRecord


@dataclass(frozen=True)
class MemoryCard:
    prompt: str
    answer: str
    card_type: str
    interval_days: int = 1
    due: str = ""
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["due"] = data["due"] or date.today().isoformat()
        data["tags"] = list(self.tags)
        return data


def spaced_interval(previous_interval: int, quality: int) -> int:
    """Small SM-2 inspired interval update.

    quality: 0-5, where <3 means failed recall.
    """

    quality = max(0, min(5, int(quality)))
    if quality < 3:
        return 1
    multiplier = 1.5 + quality / 2.0
    return max(1, round(previous_interval * multiplier))


def cards_from_invariants(skill: str, invariants: Iterable[str], tags: Iterable[str] = ()) -> List[MemoryCard]:
    base_tags = tuple(tags)
    cards: List[MemoryCard] = []
    for inv in invariants:
        cards.append(
            MemoryCard(
                prompt=f"Définis l'invariant '{inv}' dans {skill} et donne un exemple.",
                answer=f"Invariant à expliquer: {inv}. Ajouter définition, exemple, contre-exemple, unité/test.",
                card_type="invariant",
                tags=base_tags + ("omega_learn_t", "invariant"),
            )
        )
    return cards


def cards_from_errors(errors: Iterable[ErrorRecord], tags: Iterable[str] = ()) -> List[MemoryCard]:
    base_tags = tuple(tags)
    cards: List[MemoryCard] = []
    for err in errors:
        cards.append(
            MemoryCard(
                prompt=f"Quelle erreur M⁻ faut-il éviter? {err.name}",
                answer=f"Cause: {err.cause}\nCorrection: {err.correction}\nTest futur: {err.future_test}",
                card_type="m_minus",
                tags=base_tags + ("omega_learn_t", "m_minus"),
            )
        )
    return cards


def oak_cards(skill: str, questions: Iterable[str], tags: Iterable[str] = ()) -> List[MemoryCard]:
    base_tags = tuple(tags)
    return [
        MemoryCard(
            prompt=f"OAK check pour {skill}: {q}",
            answer="Répondre sans notes, produire preuve/test/résidu, puis enregistrer l'évidence.",
            card_type="oak",
            tags=base_tags + ("omega_learn_t", "oak"),
        )
        for q in questions
    ]


def schedule_cards(cards: Iterable[MemoryCard], days_from_now: int = 1) -> List[dict]:
    due = (date.today() + timedelta(days=days_from_now)).isoformat()
    return [{**card.to_dict(), "due": due} for card in cards]
