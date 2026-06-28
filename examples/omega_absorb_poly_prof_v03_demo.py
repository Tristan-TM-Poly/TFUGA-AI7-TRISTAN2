from omega_prof_poly_t import (
    absorb_public_records,
    build_all_professor_genomes,
    build_course_memory_minus,
    build_poly_research_twin,
    demo_public_research_records,
    generate_prior_art_packet,
    render_packet_report,
)


def main() -> None:
    report = absorb_public_records(demo_public_research_records())
    genomes = build_all_professor_genomes(report.atoms)
    twin = build_poly_research_twin(report.atoms)
    memory_minus = build_course_memory_minus(
        "Signal processing for intelligent sensors",
        (
            "FFT: confusing resolution with accuracy",
            "uncertainty: reporting a number without conditions",
            "filtering: hiding signal distortion",
        ),
    )
    prior_art = generate_prior_art_packet(
        "Course-to-lab zero-touch compiler",
        ("CourseCVCD", "LabOAKBench", "ProfessorGraph", "OAK compiler"),
        report.atoms,
    )
    print(render_packet_report("Ω-ABSORB-POLY-PROF-T v0.3 demo", (report, twin, memory_minus, prior_art)))
    print("genomes", [genome.professor for genome in genomes])
    print("questions", twin.answer_questions())


if __name__ == "__main__":
    main()
