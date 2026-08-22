"""Student-side multi-specialization planning for Ω-PROF-POLY-T.

This module compiles a broad, interdisciplinary course portfolio instead of
forcing a student into one narrow specialization. It is deliberately generic:
no private transcript data and no live institutional course offering are
embedded in the package.

OAK boundary: a generated plan is decision support, not an official course
registration. Current prerequisites, term offerings, degree requirements,
credit attribution, timetable conflicts, and registration eligibility must be
verified against authoritative institutional data before execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from .core import OAKStatus, clamp01


DEFAULT_AXES: Tuple[str, ...] = (
    "quantum",
    "photonics",
    "nano_materials",
    "energy_nuclear",
    "biomedical",
    "computation_ai",
    "electronics_instrumentation",
    "mechanics_thermal",
    "entrepreneurship_governance",
)


class EvidenceState(str, Enum):
    """Freshness/authority state of a course record."""

    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    STALE = "stale"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class CourseCandidate:
    """One candidate course or academic activity.

    `axes` are broad skill/specialization domains. A course can span several
    axes; that intersection is intentionally rewarded by the planner.
    """

    code: str
    title: str
    credits: int
    axes: Tuple[str, ...]
    prerequisites: Tuple[str, ...] = field(default_factory=tuple)
    terms: Tuple[str, ...] = field(default_factory=tuple)
    required: bool = False
    repeat_repair: bool = False
    workload: float = 0.5
    evidence_state: EvidenceState = EvidenceState.UNVERIFIED
    source: str = ""

    def __post_init__(self) -> None:
        if self.credits <= 0:
            raise ValueError("credits must be positive")
        if not self.code.strip():
            raise ValueError("course code must be non-empty")
        if not self.axes:
            raise ValueError("at least one specialization axis is required")


@dataclass(frozen=True)
class StudentProfile:
    """Minimal, privacy-preserving planning state.

    The package intentionally needs only course codes and aggregate credits;
    names, student IDs, addresses, dates of birth, and grade histories are not
    required.
    """

    completed_courses: Tuple[str, ...] = field(default_factory=tuple)
    earned_credits: int = 0
    target_credits: int = 120
    required_missing: Tuple[str, ...] = field(default_factory=tuple)
    desired_axes: Tuple[str, ...] = DEFAULT_AXES
    max_term_credits: int = 15
    min_full_time_credits: int = 12
    target_term: str = ""

    def __post_init__(self) -> None:
        if self.earned_credits < 0:
            raise ValueError("earned_credits must be non-negative")
        if self.target_credits <= 0:
            raise ValueError("target_credits must be positive")
        if self.max_term_credits <= 0:
            raise ValueError("max_term_credits must be positive")
        if self.min_full_time_credits < 0:
            raise ValueError("min_full_time_credits must be non-negative")


@dataclass(frozen=True)
class PlanWeights:
    """Weights for the transparent portfolio objective."""

    required: float = 5.0
    repeat_repair: float = 3.5
    graduation_progress: float = 2.5
    new_axis: float = 3.0
    bridge: float = 1.6
    verified_evidence: float = 1.0
    workload_penalty: float = 0.7
    stale_penalty: float = 0.8
    unverified_penalty: float = 0.5


@dataclass(frozen=True)
class PlannedCourse:
    code: str
    title: str
    credits: int
    axes: Tuple[str, ...]
    score: float
    score_per_credit: float
    reasons: Tuple[str, ...]
    evidence_state: EvidenceState


@dataclass(frozen=True)
class MultiSpecializationPlan:
    selected: Tuple[PlannedCourse, ...]
    total_credits: int
    projected_total_credits: int
    axis_coverage: Mapping[str, Tuple[str, ...]]
    uncovered_axes: Tuple[str, ...]
    missing_required: Tuple[str, ...]
    warnings: Tuple[str, ...]
    oak_status: OAKStatus
    registration_ready: bool

    @property
    def selected_codes(self) -> Tuple[str, ...]:
        return tuple(course.code for course in self.selected)


def _term_is_eligible(course: CourseCandidate, target_term: str) -> bool:
    if not target_term or not course.terms:
        return True
    return target_term in course.terms


def _prerequisites_met(course: CourseCandidate, completed: set[str]) -> bool:
    return set(course.prerequisites).issubset(completed)


def _score_course(
    course: CourseCandidate,
    profile: StudentProfile,
    selected_credits: int,
    covered_axes: set[str],
    weights: PlanWeights,
) -> Tuple[float, Tuple[str, ...]]:
    desired = set(profile.desired_axes)
    course_axes = set(course.axes) & desired
    new_axes = course_axes - covered_axes
    reasons: List[str] = []
    score = 0.0

    if course.required or course.code in profile.required_missing:
        score += weights.required
        reasons.append("required-degree-progress")

    if course.repeat_repair:
        score += weights.repeat_repair
        reasons.append("repeat-repair")

    remaining_degree_credits = max(0, profile.target_credits - profile.earned_credits - selected_credits)
    if remaining_degree_credits > 0:
        progress_fraction = min(course.credits, remaining_degree_credits) / max(1, remaining_degree_credits)
        score += weights.graduation_progress * progress_fraction
        reasons.append("graduation-progress")

    if new_axes:
        score += weights.new_axis * len(new_axes)
        reasons.append("new-axis:" + ",".join(sorted(new_axes)))

    bridge_count = max(0, len(course_axes) - 1)
    if bridge_count:
        score += weights.bridge * bridge_count
        reasons.append(f"bridge-{len(course_axes)}-axes")

    if course.evidence_state == EvidenceState.VERIFIED:
        score += weights.verified_evidence
        reasons.append("verified-source")
    elif course.evidence_state == EvidenceState.STALE:
        score -= weights.stale_penalty
        reasons.append("stale-source")
    elif course.evidence_state == EvidenceState.UNVERIFIED:
        score -= weights.unverified_penalty
        reasons.append("unverified-source")
    else:
        return float("-inf"), ("blocked-source",)

    score -= weights.workload_penalty * clamp01(course.workload)
    reasons.append("workload-accounted")
    return score, tuple(reasons)


def compile_polyspecialist_plan(
    profile: StudentProfile,
    candidates: Iterable[CourseCandidate],
    weights: PlanWeights = PlanWeights(),
) -> MultiSpecializationPlan:
    """Compile a maximum-coverage interdisciplinary term plan.

    Strategy:
    1. filter completed, blocked, unavailable, and unmet-prerequisite courses;
    2. force eligible required/missing-degree courses first;
    3. greedily maximize marginal axis coverage + bridge density + graduation
       progress + repeat repair value under the term credit budget;
    4. emit OAK warnings whenever live institutional verification is missing.

    This is a transparent greedy compiler, not an optimality proof.
    """

    completed = set(profile.completed_courses)
    required_missing = set(profile.required_missing)
    desired_axes = set(profile.desired_axes)
    warnings: List[str] = []
    eligible: List[CourseCandidate] = []
    by_code: Dict[str, CourseCandidate] = {}

    for course in candidates:
        by_code[course.code] = course
        if course.code in completed:
            continue
        if course.evidence_state == EvidenceState.BLOCKED:
            warnings.append(f"{course.code}: blocked source/policy state; excluded.")
            continue
        if not _term_is_eligible(course, profile.target_term):
            continue
        if not _prerequisites_met(course, completed):
            missing = sorted(set(course.prerequisites) - completed)
            warnings.append(f"{course.code}: unmet prerequisite(s): {', '.join(missing)}.")
            continue
        eligible.append(course)

    selected: List[PlannedCourse] = []
    selected_codes: set[str] = set()
    covered_axes: set[str] = set()
    used_credits = 0

    def add(course: CourseCandidate) -> bool:
        nonlocal used_credits
        if course.code in selected_codes:
            return False
        if used_credits + course.credits > profile.max_term_credits:
            return False
        score, reasons = _score_course(course, profile, used_credits, covered_axes, weights)
        if score == float("-inf"):
            return False
        selected.append(
            PlannedCourse(
                code=course.code,
                title=course.title,
                credits=course.credits,
                axes=course.axes,
                score=round(score, 4),
                score_per_credit=round(score / course.credits, 4),
                reasons=reasons,
                evidence_state=course.evidence_state,
            )
        )
        selected_codes.add(course.code)
        used_credits += course.credits
        covered_axes.update(set(course.axes) & desired_axes)
        return True

    required_candidates = [
        course for course in eligible if course.required or course.code in required_missing
    ]
    required_candidates.sort(
        key=lambda course: (
            course.code not in required_missing,
            -int(course.repeat_repair),
            course.credits,
            course.code,
        )
    )
    for course in required_candidates:
        if not add(course):
            warnings.append(f"{course.code}: required course did not fit the term credit budget.")

    remaining = [course for course in eligible if course.code not in selected_codes]
    while remaining:
        scored: List[Tuple[float, float, str, CourseCandidate]] = []
        for course in remaining:
            if used_credits + course.credits > profile.max_term_credits:
                continue
            score, _ = _score_course(course, profile, used_credits, covered_axes, weights)
            if score == float("-inf"):
                continue
            scored.append((score / course.credits, score, course.code, course))
        if not scored:
            break
        scored.sort(key=lambda item: (-item[0], -item[1], item[2]))
        best = scored[0][3]
        add(best)
        remaining = [course for course in remaining if course.code != best.code]

    missing_required = tuple(
        sorted(code for code in required_missing if code not in completed and code not in selected_codes)
    )
    if missing_required:
        warnings.append("Required course(s) still missing: " + ", ".join(missing_required) + ".")

    axis_coverage: Dict[str, Tuple[str, ...]] = {}
    for axis in profile.desired_axes:
        codes = tuple(sorted(course.code for course in selected if axis in course.axes))
        axis_coverage[axis] = codes
    uncovered_axes = tuple(axis for axis in profile.desired_axes if not axis_coverage[axis])
    if uncovered_axes:
        warnings.append(
            "Not every desired specialization axis is covered this term: " + ", ".join(uncovered_axes) + "."
        )

    if used_credits < profile.min_full_time_credits:
        warnings.append(
            f"Selected load is {used_credits} credits, below configured full-time threshold "
            f"of {profile.min_full_time_credits}."
        )

    projected_total = profile.earned_credits + used_credits
    if projected_total < profile.target_credits:
        warnings.append(
            f"Projected cumulative credits ({projected_total}) remain below target ({profile.target_credits})."
        )

    selected_states = {course.evidence_state for course in selected}
    has_unverified = bool(selected_states & {EvidenceState.UNVERIFIED, EvidenceState.STALE})
    registration_ready = (
        bool(selected)
        and not missing_required
        and not has_unverified
        and projected_total >= profile.target_credits
    )

    if missing_required:
        oak_status = OAKStatus.BLOCKED
    elif has_unverified:
        oak_status = OAKStatus.PROTOTYPE
    elif registration_ready:
        oak_status = OAKStatus.CANON
    elif selected:
        oak_status = OAKStatus.PROTOTYPE
    else:
        oak_status = OAKStatus.EXPLORATORY

    return MultiSpecializationPlan(
        selected=tuple(selected),
        total_credits=used_credits,
        projected_total_credits=projected_total,
        axis_coverage=axis_coverage,
        uncovered_axes=uncovered_axes,
        missing_required=missing_required,
        warnings=tuple(dict.fromkeys(warnings)),
        oak_status=oak_status,
        registration_ready=registration_ready,
    )


def render_polyspecialist_markdown(plan: MultiSpecializationPlan) -> str:
    """Render a compact auditable Markdown summary."""

    lines = [
        "# Ω-POLYSPECIALIST-T plan",
        "",
        f"- OAK status: `{plan.oak_status.value}`",
        f"- Registration-ready: `{str(plan.registration_ready).lower()}`",
        f"- Selected term credits: **{plan.total_credits}**",
        f"- Projected cumulative credits: **{plan.projected_total_credits}**",
        "",
        "## Selected portfolio",
        "",
    ]
    for course in plan.selected:
        lines.append(
            f"- **{course.code} — {course.title}** ({course.credits} cr): "
            f"axes={', '.join(course.axes)}; density={course.score_per_credit:.4f}; "
            f"evidence={course.evidence_state.value}."
        )
    lines.extend(["", "## Axis coverage", ""])
    for axis, codes in plan.axis_coverage.items():
        lines.append(f"- `{axis}`: {', '.join(codes) if codes else 'not covered this term'}")
    if plan.warnings:
        lines.extend(["", "## OAK warnings", ""])
        lines.extend(f"- {warning}" for warning in plan.warnings)
    return "\n".join(lines) + "\n"
