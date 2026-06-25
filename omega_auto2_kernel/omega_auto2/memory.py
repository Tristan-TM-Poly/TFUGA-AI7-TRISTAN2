from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Auto2Memory:
    """Mémoire minimale M⁺/M⁻ pour apprendre des workflows."""

    m_plus: list[dict[str, str]] = field(default_factory=list)
    m_minus: list[dict[str, str]] = field(default_factory=list)

    def record_success(self, pattern: str, reason: str) -> None:
        self.m_plus.append({"pattern": pattern, "reason": reason})

    def record_failure(self, error: str, cause: str, anti_rule: str) -> None:
        self.m_minus.append({"error": error, "cause": cause, "anti_rule": anti_rule})

    def anti_rules(self) -> list[str]:
        return [entry["anti_rule"] for entry in self.m_minus]


def default_memory() -> Auto2Memory:
    memory = Auto2Memory()
    memory.record_success("generate_yaml_before_code", "réduit les erreurs de conception")
    memory.record_success("dry_run_before_deploy", "évite les actions irréversibles")
    memory.record_failure(
        "automation_without_goal",
        "objectif flou",
        "ne jamais automatiser une tâche dont l'objectif est flou",
    )
    memory.record_failure(
        "permission_overreach",
        "permissions trop larges",
        "appliquer le moindre privilège par défaut",
    )
    return memory
