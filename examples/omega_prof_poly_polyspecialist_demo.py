from omega_prof_poly_t import (
    CourseCandidate,
    EvidenceState,
    StudentProfile,
    compile_polyspecialist_plan,
    render_polyspecialist_markdown,
)


def main() -> None:
    profile = StudentProfile(
        completed_courses=("BASE-Q", "BASE-MATH"),
        earned_credits=96,
        target_credits=120,
        required_missing=("CORE-ETHICS",),
        desired_axes=(
            "quantum",
            "photonics",
            "nano_materials",
            "biomedical",
            "computation_ai",
        ),
        max_term_credits=12,
        min_full_time_credits=12,
        target_term="fall",
    )

    candidates = [
        CourseCandidate(
            "CORE-ETHICS",
            "Engineering ethics",
            3,
            ("entrepreneurship_governance",),
            terms=("fall",),
            required=True,
            evidence_state=EvidenceState.VERIFIED,
            source="fixture://degree-audit",
        ),
        CourseCandidate(
            "QPH-401",
            "Quantum photonic systems",
            3,
            ("quantum", "photonics"),
            prerequisites=("BASE-Q",),
            terms=("fall",),
            evidence_state=EvidenceState.VERIFIED,
            source="fixture://catalog",
        ),
        CourseCandidate(
            "NBI-410",
            "Nano-biomedical instrumentation",
            3,
            ("nano_materials", "biomedical", "electronics_instrumentation"),
            terms=("fall",),
            evidence_state=EvidenceState.VERIFIED,
            source="fixture://catalog",
        ),
        CourseCandidate(
            "SCI-AI-420",
            "Scientific AI for physical systems",
            3,
            ("computation_ai", "quantum", "nano_materials"),
            prerequisites=("BASE-MATH",),
            terms=("fall",),
            evidence_state=EvidenceState.VERIFIED,
            source="fixture://catalog",
        ),
    ]

    plan = compile_polyspecialist_plan(profile, candidates)
    print(render_polyspecialist_markdown(plan))


if __name__ == "__main__":
    main()
