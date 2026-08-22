from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .representation_tournament import TournamentCase


@dataclass(frozen=True)
class SourceAnchorCheck:
    case_id: str
    source_ref: str
    path: str
    anchor: str
    file_exists: bool
    anchor_found: bool
    passed: bool
    reason: str


def verify_source_anchor(
    case: TournamentCase,
    *,
    repo_root: str | Path = Path("."),
) -> SourceAnchorCheck:
    """Verify that a frozen benchmark source_ref still resolves inside the repository.

    The contract is intentionally lexical and fail-closed: `path::anchor` must point
    to a UTF-8 repository file and the declared anchor token must occur in that file.
    This proves repository anchoring only; it does not prove semantic equivalence or
    that the benchmark record faithfully models the referenced object.
    """

    ref = case.source_ref.strip()
    if "::" not in ref:
        return SourceAnchorCheck(
            case.id,
            case.source_ref,
            "",
            "",
            False,
            False,
            False,
            "source_ref must use path::anchor",
        )

    path_text, anchor = (part.strip() for part in ref.split("::", 1))
    if not path_text or not anchor:
        return SourceAnchorCheck(
            case.id,
            case.source_ref,
            path_text,
            anchor,
            False,
            False,
            False,
            "source_ref path and anchor must be non-empty",
        )

    root = Path(repo_root).resolve()
    candidate = (root / path_text).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return SourceAnchorCheck(
            case.id,
            case.source_ref,
            path_text,
            anchor,
            False,
            False,
            False,
            "source_ref escapes repository root",
        )

    if not candidate.is_file():
        return SourceAnchorCheck(
            case.id,
            case.source_ref,
            path_text,
            anchor,
            False,
            False,
            False,
            "source file does not exist",
        )

    try:
        text = candidate.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return SourceAnchorCheck(
            case.id,
            case.source_ref,
            path_text,
            anchor,
            True,
            False,
            False,
            "source file is not UTF-8 text",
        )

    found = anchor in text
    return SourceAnchorCheck(
        case.id,
        case.source_ref,
        path_text,
        anchor,
        True,
        found,
        found,
        "anchor token found" if found else "anchor token not found",
    )


def verify_source_anchors(
    cases: Iterable[TournamentCase],
    *,
    repo_root: str | Path = Path("."),
) -> tuple[SourceAnchorCheck, ...]:
    return tuple(verify_source_anchor(case, repo_root=repo_root) for case in cases)
