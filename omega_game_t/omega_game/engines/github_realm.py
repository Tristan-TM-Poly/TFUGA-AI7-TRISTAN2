"""GitHubRealmEngine-T for GameEngineOS-T.

Internal maintenance simulation only. No remote repository action is performed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ..kernel import Action, ResourceFlow, SimulationResult, WorldState


@dataclass(slots=True)
class RepoZone:
    name: str
    health: float
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("RepoZone.name must be non-empty.")
        if not 0.0 <= self.health <= 1.0:
            raise ValueError("RepoZone.health must be in [0, 1].")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class RepoQuest:
    name: str
    target_zone: str
    expected_gain: float
    risk: float
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("RepoQuest.name must be non-empty.")
        if not 0.0 <= self.expected_gain <= 1.0:
            raise ValueError("RepoQuest.expected_gain must be in [0, 1].")
        if not 0.0 <= self.risk <= 1.0:
            raise ValueError("RepoQuest.risk must be in [0, 1].")

    def to_action(self) -> Action:
        return Action(
            name=self.name,
            description=f"Improve repo zone `{self.target_zone}` through a maintenance quest.",
            expected_flow=ResourceFlow(value=self.expected_gain * 0.5, knowledge=self.expected_gain),
            risk=self.risk,
            tags=list(self.tags) + [self.target_zone],
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class RepoWorld:
    repo_name: str
    zones: list[RepoZone]
    quests: list[RepoQuest]
    oak_controls: list[str] = field(default_factory=lambda: ["simulation_only", "human_review", "memory_recorded"])

    def __post_init__(self) -> None:
        if not self.repo_name.strip():
            raise ValueError("RepoWorld.repo_name must be non-empty.")
        if not self.zones:
            raise ValueError("RepoWorld.zones must be non-empty.")

    def health(self) -> float:
        return sum(zone.health for zone in self.zones) / len(self.zones)

    def to_world_state(self) -> WorldState:
        metrics = {zone.name: zone.health for zone in self.zones}
        metrics["repo_health"] = self.health()
        metrics["quest_count"] = float(len(self.quests))
        return WorldState(
            name=self.repo_name,
            domain="github_realm",
            resources={"knowledge": self.health(), "value": self.health()},
            metrics=metrics,
            constraints=list(self.oak_controls),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "repo_name": self.repo_name,
            "zones": [zone.to_dict() for zone in self.zones],
            "quests": [quest.to_dict() for quest in self.quests],
            "oak_controls": list(self.oak_controls),
            "health": self.health(),
        }


@dataclass(slots=True)
class GitHubRealmEngine:
    name: str = "GitHubRealmEngine-T"

    def propose_actions(self, world: WorldState) -> list[Action]:
        repo_health = world.get("repo_health", 0.50)
        return [
            Action(
                name="add_missing_tests",
                description="Add focused tests for the weakest behavior area.",
                expected_flow=ResourceFlow(value=0.12, knowledge=0.22),
                risk=0.08,
                tags=["tests", "quality"],
            ),
            Action(
                name="update_readme_map",
                description="Update the README map so the repo is easier to navigate.",
                expected_flow=ResourceFlow(value=0.10, knowledge=0.18),
                risk=0.05,
                tags=["docs", "clarity"],
            ),
            Action(
                name="add_schema_for_output",
                description="Add a JSON schema for a new structured output.",
                expected_flow=ResourceFlow(value=0.14, knowledge=0.16),
                risk=0.07,
                tags=["schema", "contract"],
            ),
            Action(
                name="prepare_oak_review",
                description="Prepare a review checklist for assumptions, limits and memory.",
                expected_flow=ResourceFlow(value=0.08, knowledge=0.20),
                risk=0.04,
                tags=["oak", "review"],
            ),
            Action(
                name="reduce_change_set_risk",
                description="Split or label large work into smaller reviewable parts.",
                expected_flow=ResourceFlow(value=0.16, knowledge=0.12),
                risk=0.06 if repo_health < 0.70 else 0.10,
                tags=["scope", "review"],
            ),
        ]

    def simulate(self, world: WorldState, action: Action) -> SimulationResult:
        repo_health = world.get("repo_health", 0.50)
        docs = world.get("docs", 0.50)
        tests = world.get("tests", 0.50)
        schemas = world.get("schemas", 0.50)
        oak = world.get("oak", 0.50)
        if "docs" in action.tags:
            docs = min(1.0, docs + 0.16)
        if "tests" in action.tags:
            tests = min(1.0, tests + 0.18)
        if "schema" in action.tags:
            schemas = min(1.0, schemas + 0.16)
        if "oak" in action.tags or "review" in action.tags:
            oak = min(1.0, oak + 0.14)
        new_health = max(0.0, min(1.0, (docs + tests + schemas + oak + repo_health) / 5.0 + action.expected_flow.normalized_score() * 0.05 - action.risk * 0.05))
        after = (
            world.with_metric("docs", docs)
            .with_metric("tests", tests)
            .with_metric("schemas", schemas)
            .with_metric("oak", oak)
            .with_metric("repo_health", new_health)
        )
        score = max(0.0, min(1.0, 0.20 + 0.70 * new_health - 0.10 * action.risk))
        return SimulationResult(
            engine=self.name,
            before=world,
            action=action,
            after=after,
            flow=action.expected_flow,
            score=score,
            oak_status="accepted" if action.risk < 0.25 else "caution",
            m_plus=[f"{action.name}_improves_repo"],
            m_minus=["no_remote_action_performed", "review_before_repo_change"],
            notes=["Repository maintenance simulation only."],
        )


def demo_repo_world() -> RepoWorld:
    return RepoWorld(
        repo_name="TFUGA-AI7-TRISTAN2",
        zones=[
            RepoZone("docs", 0.72, ["README map growing"]),
            RepoZone("tests", 0.64, ["many tests added"]),
            RepoZone("schemas", 0.68, ["schemas expanding"]),
            RepoZone("examples", 0.70, ["demos present"]),
            RepoZone("oak", 0.78, ["OAK notes visible"]),
        ],
        quests=[
            RepoQuest("add_missing_tests", "tests", 0.22, 0.08, ["tests"]),
            RepoQuest("update_readme_map", "docs", 0.18, 0.05, ["docs"]),
            RepoQuest("add_schema_for_output", "schemas", 0.16, 0.07, ["schema"]),
            RepoQuest("prepare_oak_review", "oak", 0.20, 0.04, ["oak"]),
        ],
    )


__all__ = ["GitHubRealmEngine", "RepoQuest", "RepoWorld", "RepoZone", "demo_repo_world"]
