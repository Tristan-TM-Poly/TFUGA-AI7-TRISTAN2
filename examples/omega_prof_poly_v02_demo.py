from omega_prof_poly_t import (
    CourseInput,
    GrantInput,
    IPInput,
    LabInput,
    ProjectInput,
    classify_ip,
    demo_professor_graph,
    forge_grant,
    forge_project,
    generate_coursecvcd,
    generate_lab_oakbench,
    render_packet_report,
)


def main() -> None:
    course = generate_coursecvcd(
        CourseInput(
            title="Signal processing for intelligent sensors",
            disciplines=("genie physique", "genie electrique", "genie logiciel"),
            objectives=("FFT and spectra", "noise filtering", "uncertainty", "sensor prototype"),
            prerequisites=("linear algebra", "signals", "python"),
        ),
        evidence_count=2,
    )
    lab = generate_lab_oakbench(
        LabInput(
            title="FFT uncertainty lab",
            hypothesis="A noisy sensor signal can be filtered while preserving measurable uncertainty.",
            measurands=("frequency_peak", "noise_floor", "signal_to_noise"),
            instruments=("photodiode", "oscilloscope"),
        ),
        evidence_count=2,
    )
    project = forge_project(
        ProjectInput(
            need="low-cost experimental teaching platform",
            disciplines=("genie physique", "genie electrique", "genie logiciel", "genie mecanique"),
            prototype="photonic sensor bench",
            term_weeks=12,
            equipment=("laser diode", "photodiode", "microcontroller"),
        ),
        evidence_count=2,
    )
    grant = forge_grant(
        GrantInput(
            title="Poly Intelligence Engine for engineering pedagogy",
            problem="fragmented course-lab-project-research pipelines",
            objectives=("CourseCVCD", "LabOAKBench", "ProjectForge", "ProfessorGraph"),
            methods=("hypergraph modeling", "automated OAK scoring", "reproducible packets"),
            team_strength=0.7,
            impact=0.8,
            novelty=0.72,
            feasibility=0.68,
            reproducibility=0.75,
        ),
        evidence_count=2,
    )
    ip = classify_ip(
        IPInput(
            result_name="Course-to-lab zero-touch compiler",
            novelty_score=0.68,
            utility_score=0.82,
            market_score=0.55,
            feasibility_score=0.76,
            disclosure_risk=0.42,
            reproducibility_score=0.78,
        ),
        evidence_count=2,
    )
    graph = demo_professor_graph()

    print(render_packet_report("Omega-PROF-POLY-T v0.2 demo", (course, lab, project, grant, ip)))
    print(graph.answer_auto_questions())


if __name__ == "__main__":
    main()
