from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RepoSpec:
    name: str
    description: str
    role: str
    capabilities: tuple[str, ...]
    consumes: tuple[str, ...] = ()
    produces: tuple[str, ...] = ()
    relations: tuple[dict[str, str], ...] = ()
    split_score: float = 0.0
    split_rationale: tuple[str, ...] = ()
    visibility: str = "private"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RepoSpec":
        visibility = str(payload.get("visibility", "private")).lower()
        if visibility != "private":
            raise ValueError("Repo Genesis v0.1 is private-by-default and refuses non-private specs")
        score = float(payload.get("split_score", 0.0))
        if not 0.0 <= score <= 1.0:
            raise ValueError("split_score must be in [0, 1]")
        return cls(
            name=str(payload["name"]),
            description=str(payload["description"]),
            role=str(payload["role"]),
            capabilities=tuple(map(str, payload.get("capabilities", ()))),
            consumes=tuple(map(str, payload.get("consumes", ()))),
            produces=tuple(map(str, payload.get("produces", ()))),
            relations=tuple(dict(item) for item in payload.get("relations", ())),
            split_score=score,
            split_rationale=tuple(map(str, payload.get("split_rationale", ()))),
            visibility=visibility,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "role": self.role,
            "capabilities": list(self.capabilities),
            "consumes": list(self.consumes),
            "produces": list(self.produces),
            "relations": list(self.relations),
            "split_score": self.split_score,
            "split_rationale": list(self.split_rationale),
            "visibility": self.visibility,
        }


@dataclass(frozen=True)
class Constellation:
    constellation_id: str
    owner: str
    source_repository: str
    source_sha: str
    source_prs: tuple[int, ...]
    repositories: tuple[RepoSpec, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Constellation":
        repos = tuple(RepoSpec.from_dict(item) for item in payload.get("repositories", ()))
        names = [r.name for r in repos]
        if len(names) != len(set(names)):
            raise ValueError("repository names must be unique")
        return cls(
            constellation_id=str(payload["constellation_id"]),
            owner=str(payload["owner"]),
            source_repository=str(payload["source_repository"]),
            source_sha=str(payload["source_sha"]),
            source_prs=tuple(int(x) for x in payload.get("source_prs", ())),
            repositories=repos,
        )
