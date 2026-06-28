from omega_prof_poly_t import Evidence, OAKStatus, ProfessorSignal, build_project_forge_prompt, evaluate_signal, rank_signals


def test_low_evidence_stays_exploratory_or_prototype():
    signal = ProfessorSignal(
        name="raw idea",
        teaching_value=0.5,
        feasibility=0.4,
        reproducibility=0.2,
        ethics_safety=0.6,
    )
    decision = evaluate_signal(signal)
    assert decision.status in {OAKStatus.EXPLORATORY, OAKStatus.PROTOTYPE}
    assert any("No evidence" in warning for warning in decision.warnings)


def test_high_confidentiality_blocks_or_warns_ip_gate():
    signal = ProfessorSignal(
        name="secret prototype",
        teaching_value=0.7,
        research_value=0.8,
        industry_value=0.9,
        ip_value=0.9,
        feasibility=0.7,
        reproducibility=0.7,
        ethics_safety=0.8,
        confidentiality_risk=0.9,
        evidence=(Evidence("internal-note", "Confidential partner prototype.", 0.8),),
    )
    decision = evaluate_signal(signal)
    assert any("IP" in warning or "confidentiality" in warning for warning in decision.warnings)
    assert decision.risks["confidentiality_risk"] == 0.9


def test_strong_evidenced_reproducible_signal_can_be_canon():
    signal = ProfessorSignal(
        name="validated course lab",
        teaching_value=0.95,
        research_value=0.75,
        student_value=0.9,
        industry_value=0.4,
        ip_value=0.1,
        feasibility=0.92,
        reproducibility=0.88,
        ethics_safety=0.9,
        confidentiality_risk=0.05,
        academic_integrity_risk=0.1,
        overclaim_risk=0.1,
        evidence=(
            Evidence("course-plan", "Learning objectives verified.", 0.9),
            Evidence("lab-results", "Pilot lab reproduced twice.", 0.85),
            Evidence("rubric", "Human-reviewed evaluation rubric.", 0.8),
        ),
    )
    decision = evaluate_signal(signal)
    assert decision.status == OAKStatus.CANON
    assert decision.score >= 0.72


def test_rank_signals_orders_by_score():
    weak = ProfessorSignal(name="weak", ethics_safety=0.5)
    strong = ProfessorSignal(
        name="strong",
        teaching_value=1,
        research_value=1,
        student_value=1,
        feasibility=1,
        reproducibility=1,
        ethics_safety=1,
        evidence=(Evidence("x", "y", 1), Evidence("z", "w", 1)),
    )
    ranked = rank_signals([weak, strong])
    assert ranked[0].signal_name == "strong"


def test_project_forge_prompt_contains_goal_and_disciplines():
    prompt = build_project_forge_prompt(["physique", "logiciel"], "sensor lab")
    assert "physique" in prompt
    assert "logiciel" in prompt
    assert "sensor lab" in prompt
    assert "OAK-safe" in prompt
