from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Callable, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import PullRequestSnapshot, RepositorySnapshot
from .snapshot import SnapshotBundle


Transport = Callable[[str, dict[str, str], float], tuple[int, bytes, dict[str, str]]]


def _default_transport(url: str, headers: dict[str, str], timeout: float) -> tuple[int, bytes, dict[str, str]]:
    request = Request(url, headers=headers, method="GET")
    with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed GitHub API base
        return response.status, response.read(), dict(response.headers.items())


class GitHubReadOnlyScanner:
    """Read-only GitHub REST scanner with pagination and bounded response bytes.

    The scanner exposes no write methods.  It stores PR-body digests rather than
    complete bodies by default, reducing unnecessary content retention.
    """

    def __init__(
        self,
        *,
        token: str | None = None,
        api_base: str = "https://api.github.com",
        timeout_seconds: float = 30.0,
        max_response_bytes: int = 8_000_000,
        transport: Transport = _default_transport,
    ) -> None:
        if not api_base.startswith("https://"):
            raise ValueError("api_base must use HTTPS")
        if timeout_seconds <= 0 or max_response_bytes <= 0:
            raise ValueError("timeout and response budget must be positive")
        self._token = token
        self._api_base = api_base.rstrip("/")
        self._timeout = timeout_seconds
        self._max_response_bytes = max_response_bytes
        self._transport = transport

    @classmethod
    def from_environment(cls, token_env: str = "GITHUB_TOKEN", **kwargs: Any) -> "GitHubReadOnlyScanner":
        return cls(token=os.environ.get(token_env), **kwargs)

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "omega-github-mycelium-t-read-only/0.1",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _get_json(self, path: str, params: dict[str, Any]) -> Any:
        query = urlencode(params)
        url = f"{self._api_base}{path}?{query}" if query else f"{self._api_base}{path}"
        status, payload, _headers = self._transport(url, self._headers(), self._timeout)
        if status != 200:
            raise RuntimeError(f"GitHub read failed with HTTP {status}: {path}")
        if len(payload) > self._max_response_bytes:
            raise RuntimeError("GitHub response exceeded configured byte budget")
        return json.loads(payload.decode("utf-8"))

    def _paginate(self, path: str, params: dict[str, Any]) -> Iterable[dict[str, Any]]:
        page = 1
        while True:
            values = self._get_json(path, {**params, "per_page": 100, "page": page})
            if not isinstance(values, list):
                raise RuntimeError("expected a paginated GitHub list response")
            if not values:
                return
            for value in values:
                if isinstance(value, dict):
                    yield value
            if len(values) < 100:
                return
            page += 1

    def list_owned_repositories(self, owner: str) -> tuple[RepositorySnapshot, ...]:
        repositories: list[RepositorySnapshot] = []
        for value in self._paginate(
            "/user/repos",
            {"affiliation": "owner", "sort": "full_name", "direction": "asc"},
        ):
            full_name = str(value.get("full_name", ""))
            if not full_name.startswith(f"{owner}/"):
                continue
            permissions = tuple(
                name for name, enabled in dict(value.get("permissions") or {}).items() if enabled
            )
            repositories.append(
                RepositorySnapshot(
                    full_name=full_name,
                    visibility=str(value.get("visibility") or ("private" if value.get("private") else "public")),
                    default_branch=str(value.get("default_branch") or "main"),
                    archived=bool(value.get("archived", False)),
                    size_kb=int(value.get("size") or 0),
                    permissions=permissions,
                    topics=tuple(value.get("topics") or ()),
                    metadata={
                        "id": value.get("id"),
                        "fork": bool(value.get("fork", False)),
                        "disabled": bool(value.get("disabled", False)),
                    },
                )
            )
        return tuple(sorted(repositories, key=lambda item: item.full_name.lower()))

    def list_open_pull_requests(self, repository: RepositorySnapshot) -> tuple[PullRequestSnapshot, ...]:
        values: list[PullRequestSnapshot] = []
        owner, name = repository.full_name.split("/", 1)
        path = f"/repos/{owner}/{name}/pulls"
        for value in self._paginate(path, {"state": "open", "sort": "updated", "direction": "desc"}):
            body = str(value.get("body") or "")
            head = dict(value.get("head") or {})
            base = dict(value.get("base") or {})
            labels = tuple(str(label.get("name")) for label in value.get("labels") or () if label.get("name"))
            values.append(
                PullRequestSnapshot(
                    repo_full_name=repository.full_name,
                    number=int(value["number"]),
                    title=str(value.get("title") or "untitled"),
                    state="open",
                    draft=bool(value.get("draft", True)),
                    mergeable=None,
                    base_branch=str(base.get("ref") or repository.default_branch),
                    head_branch=str(head.get("ref") or "unknown"),
                    head_sha=str(head.get("sha")) if head.get("sha") else None,
                    url=str(value.get("html_url") or ""),
                    labels=labels,
                    body_digest=hashlib.sha256(body.encode("utf-8")).hexdigest(),
                    metadata={"updated_at": value.get("updated_at")},
                )
            )
        return tuple(values)

    def scan_owner(self, owner: str) -> SnapshotBundle:
        repositories = self.list_owned_repositories(owner)
        pull_requests: list[PullRequestSnapshot] = []
        for repository in repositories:
            pull_requests.extend(self.list_open_pull_requests(repository))
        return SnapshotBundle(
            repositories=repositories,
            pull_requests=tuple(sorted(pull_requests, key=lambda item: (item.repo_full_name, item.number))),
            source="github_rest_read_only",
            completeness="all_owned_repositories_and_open_pull_requests_returned_by_paginated_api",
            metadata={
                "owner": owner,
                "remote_mutations_performed": False,
                "full_pr_bodies_retained": False,
            },
        )
