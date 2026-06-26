from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenesisReport:
    intention_decoded: str
    mode: str
    genesis_tree: dict[str, object]
    idea_candidates: list[dict[str, object]]
    compressed_top_ideas: list[str]
    prototype_plan: list[str]
    oak_report: dict[str, object]
    revenue_ip_paths: list[str]
    github_plan: list[str]
    m_plus: list[str]
    m_minus: list[str]
    next_action: str

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()
