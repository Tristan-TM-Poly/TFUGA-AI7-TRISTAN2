"""Connector Alias Registry for Ω-AIT-SELF-STABILIZING-REFACTOR-KERNEL-T.

Preserves canonical meaning when an environment requires a safer filename.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectorAlias:
    canonical_name: str
    actual_file: str
    status: str = "connector_safe_alias"


@dataclass(frozen=True)
class AliasRegistry:
    aliases: tuple[ConnectorAlias, ...]

    def resolve(self, canonical_name: str) -> str | None:
        for alias in self.aliases:
            if alias.canonical_name == canonical_name:
                return alias.actual_file
        return None


def default_alias_registry() -> AliasRegistry:
    return AliasRegistry(
        aliases=(
            ConnectorAlias("safe_fork_engine", "tools/option_selector.py"),
            ConnectorAlias("infinite_useful_work", "tools/useful_work_catalog.py"),
            ConnectorAlias("progress_trace", "schemas/progress_log.schema.json"),
            ConnectorAlias("task_queue_node", "schemas/task_queue_item.schema.json"),
            ConnectorAlias("pending_refactoring_graph", "configs/pending_next_steps.yaml"),
        )
    )
