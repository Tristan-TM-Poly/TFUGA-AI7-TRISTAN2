from omega_prof_poly_t import Evidence, ProfessorSignal, build_project_forge_prompt, rank_signals


def main() -> None:
    signals = [
        ProfessorSignal(
            name="CourseCVCD pilot for signal processing",
            teaching_value=0.9,
            research_value=0.55,
            student_value=0.85,
            industry_value=0.45,
            ip_value=0.2,
            feasibility=0.82,
            reproducibility=0.72,
            ethics_safety=0.88,
            confidentiality_risk=0.15,
            academic_integrity_risk=0.42,
            overclaim_risk=0.25,
            evidence=(
                Evidence("course_plan_signal_processing.md", "Existing course plan with learning objectives.", 0.8),
                Evidence("past_exam_errors.csv", "Repeated misconception patterns can seed M-minus.", 0.7),
            ),
        ),
        ProfessorSignal(
            name="Patent-sensitive lab prototype with industry partner",
            teaching_value=0.55,
            research_value=0.82,
            student_value=0.65,
            industry_value=0.9,
            ip_value=0.85,
            feasibility=0.58,
            reproducibility=0.38,
            ethics_safety=0.63,
            confidentiality_risk=0.82,
            academic_integrity_risk=0.25,
            overclaim_risk=0.64,
            evidence=(Evidence("partner_meeting_notes.md", "Prototype interest from partner; confidentiality not yet classified.", 0.6),),
        ),
    ]

    for decision in rank_signals(signals):
        print(f"{decision.status.value:11s} {decision.score:.3f} | {decision.signal_name}")
        for warning in decision.warnings:
            print(f"  - OAK: {warning}")
        print(f"  - Next: {decision.next_actions[0]}")

    print()
    print(
        build_project_forge_prompt(
            disciplines=["genie physique", "genie electrique", "genie logiciel"],
            goal="Create a low-cost photonic sensor lab with reproducible signal analysis.",
            constraints=[
                "one-term undergraduate feasibility",
                "explicit uncertainty analysis",
                "no medical or safety-critical claims",
            ],
        )
    )


if __name__ == "__main__":
    main()
