from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date


def stackoverflow_license_for_date(created: date) -> str:
    if created < date(2011, 4, 8):
        return "CC-BY-SA-2.5"
    if created < date(2018, 5, 2):
        return "CC-BY-SA-3.0"
    return "CC-BY-SA-4.0"


@dataclass(frozen=True)
class StackOverflowAttribution:
    question_id: int
    answer_id: int | None
    title: str
    author: str | None
    url: str
    created: str
    license_id: str
    usage_mode: str
    attribution_text: str

    def asdict(self) -> dict[str, object]:
        return asdict(self)


def build_attribution(
    question_id: int,
    title: str,
    url: str,
    created: date,
    author: str | None = None,
    answer_id: int | None = None,
    usage_mode: str = "pattern/explanation, no direct snippet",
) -> StackOverflowAttribution:
    license_id = stackoverflow_license_for_date(created)
    author_part = f" by {author}" if author else ""
    return StackOverflowAttribution(
        question_id=question_id,
        answer_id=answer_id,
        title=title,
        author=author,
        url=url,
        created=created.isoformat(),
        license_id=license_id,
        usage_mode=usage_mode,
        attribution_text=(
            f"Derived from StackOverflow question {question_id}{author_part}: "
            f"'{title}', {url}, licensed under {license_id}."
        ),
    )
