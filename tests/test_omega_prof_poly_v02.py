from omega_prof_poly_t import (
    CourseInput,
    GateStatus,
    GrantInput,
    IPInput,
    LabInput,
    ProjectInput,
    classify_ip,
    compile_oak,
    demo_professor_graph,
    forge_grant,
    forge_project,
    generate_coursecvcd,
    generate_lab_oakbench,
    render_packet_report,
)


def test_compile_oak_safe_execute():
    result = compile_oak(
        "safe artifact",
        {"teaching": 0.9, "automation": 0.8},
        {"overclaim": 0.1, "privacy": 0.1},
        evidence_count=2,
    )
    assert result.status == GateStatus.SAFE_EXECUTE
    assert result.blocked_action is None
    assert result.score > 0.5


def test_compile_oak_external_lock():
    result = compile_oak(
        "grant submission packet",
        {"impact": 0.8, "feasibility": 0.7},
        {"overclaim": 0.2},
        evidence_count=1,
        external_action=True,
    )
    assert result.status == GateStatus.EXTERNAL_ACTION_LOCKED
    assert result.blocked_action is not None
    assert result.blocked_action.artifact_ready is True


def test_coursecvcd_generates_concepts_and_exercises():
    packet = generate_coursecvcd(
        CourseInput(
            title="Signals",
            disciplines=("physique", "electrique"),
            objectives=("FFT", "filtering"),
        ),
        evidence_count=2,
    )
    assert len(packet.concept_graph) == 2
    assert len(packet.exercise_seeds) == 2
    assert packet.oak.status in {GateStatus.SAFE_EXECUTE, GateStatus.AUTO_GENERATE_ONLY}


def test_lab_oakbench_generates_tests():
    packet = generate_lab_oakbench(
        LabInput(
            title="Sensor lab",
            hypothesis="Filtering preserves signal structure.",
            measurands=("frequency", "amplitude"),
            instruments=("oscilloscope",),
        ),
        evidence_count=2,
    )
    assert "unit_consistency_test" in packet.coherence_tests
    assert any(item.startswith("uncertainty_for_") for item in packet.uncertainty_sources)


def test_project_forge_outputs_potentials():
    packet = forge_project(
        ProjectInput(
            need="teaching prototype",
            disciplines=("physique", "electrique", "logiciel"),
            prototype="sensor bench",
            equipment=("photodiode",),
        ),
        evidence_count=2,
    )
    assert packet.publication_potential > 0
    assert packet.ip_potential > 0
    assert packet.startup_potential > 0


def test_grant_forge_external_action_lock():
    packet = forge_grant(
        GrantInput(
            title="Course-lab compiler",
            problem="fragmented artifacts",
            objectives=("course", "lab", "project"),
            methods=("graph", "oak"),
            team_strength=0.7,
            impact=0.8,
            novelty=0.7,
            feasibility=0.75,
            reproducibility=0.72,
        ),
        evidence_count=2,
    )
    assert packet.score > 0
    assert packet.oak.status == GateStatus.EXTERNAL_ACTION_LOCKED


def test_ip_gate_routes_candidate():
    packet = classify_ip(
        IPInput(
            result_name="new compiler",
            novelty_score=0.8,
            utility_score=0.8,
            market_score=0.75,
            feasibility_score=0.75,
            disclosure_risk=0.35,
            reproducibility_score=0.7,
        ),
        evidence_count=2,
    )
    assert packet.value_score >= 0
    assert packet.commercial_value > 0.6


def test_professor_graph_answers_questions():
    graph = demo_professor_graph()
    answers = graph.answer_auto_questions()
    assert answers["courses_that_can_become_labs"]
    assert answers["prototypes_partner_ready"]


def test_report_renderer_contains_title():
    packet = generate_coursecvcd(
        CourseInput(title="Signals", disciplines=("physique",), objectives=("FFT",)),
        evidence_count=1,
    )
    report = render_packet_report("Demo", (packet,))
    assert "# Demo" in report
    assert "CourseCVCDPacket" in report
