from omega_prof_poly_t import CourseCandidate, EvidenceState, OAKStatus, StudentProfile, compile_polyspecialist_plan


def test_bridge_course_maximizes_axis_coverage():
    profile = StudentProfile(earned_credits=90, desired_axes=("quantum", "photonics"), max_term_credits=3, min_full_time_credits=0)
    courses = [
        CourseCandidate("ONE", "Single", 3, ("quantum",), evidence_state=EvidenceState.VERIFIED),
        CourseCandidate("BRIDGE", "Bridge", 3, ("quantum", "photonics"), evidence_state=EvidenceState.VERIFIED),
    ]
    plan = compile_polyspecialist_plan(profile, courses)
    assert plan.selected_codes == ("BRIDGE",)
    assert plan.uncovered_axes == ()


def test_required_missing_blocks_when_not_selected():
    profile = StudentProfile(earned_credits=90, required_missing=("REQ",), desired_axes=("quantum",), max_term_credits=3, min_full_time_credits=0)
    plan = compile_polyspecialist_plan(profile, [])
    assert plan.missing_required == ("REQ",)
    assert plan.oak_status == OAKStatus.BLOCKED


def test_unverified_degree_completion_is_not_registration_ready():
    profile = StudentProfile(earned_credits=117, target_credits=120, desired_axes=("photonics",), max_term_credits=3, min_full_time_credits=0)
    plan = compile_polyspecialist_plan(profile, [CourseCandidate("OPT", "Optics", 3, ("photonics",))])
    assert plan.projected_total_credits == 120
    assert plan.oak_status == OAKStatus.PROTOTYPE
    assert not plan.registration_ready


def test_verified_degree_completion_can_be_canon():
    profile = StudentProfile(earned_credits=117, target_credits=120, desired_axes=("biomedical",), max_term_credits=3, min_full_time_credits=0)
    plan = compile_polyspecialist_plan(profile, [CourseCandidate("BIO", "Bio", 3, ("biomedical",), evidence_state=EvidenceState.VERIFIED)])
    assert plan.oak_status == OAKStatus.CANON
    assert plan.registration_ready
