from __future__ import annotations

import json
from typing import Any, Callable
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE_URL = "https://www.codewars.com/api/v1"
JsonTransport = Callable[[str], dict[str, Any]]


def profile_url(username: str) -> str:
    normalized = username.strip()
    if not normalized:
        raise ValueError("username must not be empty")
    return f"{BASE_URL}/users/{quote(normalized, safe='')}"


def completed_url(username: str, page: int = 0) -> str:
    if page < 0:
        raise ValueError("page must be non-negative")
    return f"{profile_url(username)}/code-challenges/completed?page={page}"


def _public_json_transport(url: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "omega-code-dojo-t/0.1 (+metadata-only)",
        },
    )
    with urlopen(request, timeout=15) as response:  # nosec B310: fixed HTTPS API base
        return json.loads(response.read().decode("utf-8"))


def fetch_profile(
    username: str,
    *,
    transport: JsonTransport = _public_json_transport,
) -> dict[str, Any]:
    return transport(profile_url(username))


def fetch_completed_page(
    username: str,
    page: int = 0,
    *,
    transport: JsonTransport = _public_json_transport,
) -> dict[str, Any]:
    return transport(completed_url(username, page))


def normalize_progress(
    profile: dict[str, Any],
    completed_page: dict[str, Any],
) -> dict[str, Any]:
    overall = profile.get("ranks", {}).get("overall", {})
    completed = completed_page.get("data", [])
    language_counts: dict[str, int] = {}
    for challenge in completed:
        for language in set(challenge.get("completedLanguages", [])):
            language_counts[language] = language_counts.get(language, 0) + 1
    return {
        "username": profile.get("username"),
        "honor": profile.get("honor"),
        "overall_rank": overall.get("name"),
        "overall_score": overall.get("score"),
        "total_completed_reported": profile.get("codeChallenges", {}).get(
            "totalCompleted"
        ),
        "page_items": len(completed),
        "total_items": completed_page.get("totalItems"),
        "total_pages": completed_page.get("totalPages"),
        "language_counts_on_page": dict(sorted(language_counts.items())),
        "challenge_ids": sorted(
            challenge["id"] for challenge in completed if challenge.get("id")
        ),
        "source": "codewars-public-api-v1-metadata",
    }
