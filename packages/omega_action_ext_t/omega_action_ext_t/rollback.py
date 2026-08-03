"""Rollback and compensation recipe registry."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class RollbackRecipe:
    action_type: str
    reversible: bool
    rollback_hint: str
    compensation_hint: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


DEFAULT_ROLLBACK_RECIPES: tuple[RollbackRecipe, ...] = (
    RollbackRecipe("create_file", True, "remove_created_file", "restore_from_backup_if_needed"),
    RollbackRecipe("create_branch", True, "delete_branch_after_review", "open_cleanup_issue"),
    RollbackRecipe("open_pr", True, "close_draft_pr", "open_followup_pr"),
    RollbackRecipe("create_event", True, "delete_or_update_event", "send_correction_note_if_invites_exist"),
    RollbackRecipe("create_draft", True, "delete_draft", "create_corrected_draft"),
    RollbackRecipe("publish_release", False, "unpublish_if_possible", "publish_correction_and_review_ip_impact"),
)


def recipe_for(action_type: str) -> RollbackRecipe | None:
    normalized = action_type.lower().strip()
    for recipe in DEFAULT_ROLLBACK_RECIPES:
        if recipe.action_type == normalized:
            return recipe
    return None


def recipes() -> list[dict[str, object]]:
    return [recipe.to_dict() for recipe in DEFAULT_ROLLBACK_RECIPES]
