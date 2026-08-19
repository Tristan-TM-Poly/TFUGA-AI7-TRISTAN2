from tools.red_flag_detector import RiskLevel, detect_red_flags


def test_emergency_red_flag_routes_to_emergency():
    result = detect_red_flags("There is chest pain and difficulty breathing")
    assert result.risk_level == RiskLevel.EMERGENCY
    assert "chest pain" in result.hits


def test_possible_overdose_routes_to_poison_control():
    result = detect_red_flags("Possible overdose but no symptoms yet")
    assert result.risk_level == RiskLevel.POISON_CONTROL


def test_real_exposure_routes_to_poison_control():
    result = detect_red_flags("A medication was taken", real_exposure=True)
    assert result.risk_level == RiskLevel.POISON_CONTROL


def test_optimization_request_is_refused():
    result = detect_red_flags("How do I potentiate this and make it stronger?")
    assert result.risk_level == RiskLevel.REFUSE_OPTIMIZATION


def test_theoretical_question_is_educational():
    result = detect_red_flags("Explain the biological mechanism in theory", real_exposure=False)
    assert result.risk_level == RiskLevel.EDUCATIONAL
