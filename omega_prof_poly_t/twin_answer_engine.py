"""Twin answer engine for Omega absorb v1.7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .poly_research_twin_v3 import PolyResearchTwinV3


@dataclass(frozen=True)
class TwinAnswer:
    question: str
    answers: Tuple[str, ...]
    next_action: str


def answer_twin_question(twin: PolyResearchTwinV3, question: str) -> TwinAnswer:
    q = question.strip().lower().replace("_", "-")
    if q in {"best-courses", "courses", "course"}:
        answers = twin.best_course_modules()
    elif q in {"best-projects", "projects", "labs", "lab-projects"}:
        answers = twin.best_lab_projects()
    elif q in {"best-ip", "ip", "ip-candidates"}:
        answers = twin.best_ip_candidates()
    elif q in {"missing-evidence", "evidence"}:
        answers = twin.missing_evidence()
    elif q in {"weighted-routes", "routes"}:
        answers = twin.best_weighted_routes()
    elif q in {"next-10", "actions", "next-actions"}:
        answers = twin.next_10_actions()
    else:
        answers = ("unknown_question", "supported: best-courses, best-projects, best-ip, missing-evidence, weighted-routes, next-10")
    return TwinAnswer(question=q, answers=tuple(answers), next_action="render_twin_answer")


def render_twin_answer(answer: TwinAnswer) -> str:
    lines = [f"# Twin answer: {answer.question}", ""]
    lines.extend(f"- {item}" for item in (answer.answers or ("none",)))
    return "\n".join(lines) + "\n"
