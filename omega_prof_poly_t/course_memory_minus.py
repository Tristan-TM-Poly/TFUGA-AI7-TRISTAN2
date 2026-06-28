"""CourseMemoryMinus: anti-error memory for CourseCVCD."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True)
class CourseAntiError:
    concept: str
    error: str
    prevention_rule: str
    exercise_variant: str
    rubric_warning: str


@dataclass(frozen=True)
class CourseMemoryMinus:
    course_title: str
    anti_errors: Tuple[CourseAntiError, ...]
    next_action: str


def build_course_memory_minus(course_title: str, common_errors: Iterable[str]) -> CourseMemoryMinus:
    anti_errors = []
    for index, error in enumerate(common_errors, start=1):
        clean = str(error).strip() or f"common_error_{index}"
        concept = clean.split(":", 1)[0] if ":" in clean else f"concept_{index}"
        anti_errors.append(
            CourseAntiError(
                concept=concept,
                error=clean,
                prevention_rule=f"State assumptions and limits before applying {concept}.",
                exercise_variant=f"Variant {index}: expose and correct {clean}.",
                rubric_warning=f"Do not give full credit if {clean} is unaddressed.",
            )
        )
    return CourseMemoryMinus(
        course_title=course_title,
        anti_errors=tuple(anti_errors),
        next_action="inject_anti_errors_into_coursecvcd_exercises_and_rubrics",
    )
