from omega_prof_poly_t import (
    GateStatus,
    absorb_public_records,
    atom_from_public_record,
    build_all_professor_genomes,
    build_course_memory_minus,
    build_poly_research_twin,
    demo_public_research_records,
    generate_prior_art_packet,
)


def test_atom_from_public_record_metadata_plus_abstract():
    atom = atom_from_public_record(
        {
            "atom_id": "a1",
            "title": "Demo paper",
            "authors": ["A"],
            "year": "2026",
            "abstract": "Public abstract.",
            "keywords": ["sensor"],
            "claims": ["claim"],
            "methods": ["method"],
            "limitations": ["limit"],
        }
    )
    assert atom.legal_absorption_level() == "metadata_plus_abstract"
    assert atom.oak is not None
    assert atom.oak.status in {GateStatus.SAFE_EXECUTE, GateStatus.AUTO_GENERATE_ONLY}


def test_absorb_public_records_counts_levels():
    report = absorb_public_records(demo_public_research_records())
    assert report.total == 2
    assert report.metadata_plus_abstract_count == 1
    assert report.metadata_only_count == 1
    assert report.next_action == "build_professor_genomes_and_poly_research_twin"


def test_professor_genomes_are_built():
    report = absorb_public_records(demo_public_research_records())
    genomes = build_all_professor_genomes(report.atoms)
    professors = {genome.professor for genome in genomes}
    assert "Professor Demo" in professors
    assert "Professor Demo 2" in professors
    assert any(genome.project_opportunities for genome in genomes)


def test_poly_research_twin_answers_questions():
    report = absorb_public_records(demo_public_research_records())
    twin = build_poly_research_twin(report.atoms)
    answers = twin.answer_questions()
    assert answers["courses_can_absorb_research"]
    assert answers["projects_to_forge"]
    assert answers["grant_clusters"]
    assert twin.next_action == "generate_course_project_grant_ip_packets"


def test_course_memory_minus_builds_anti_errors():
    memory = build_course_memory_minus("Signals", ["FFT: wrong bin interpretation"])
    assert memory.anti_errors[0].concept == "FFT"
    assert "wrong bin" in memory.anti_errors[0].error
    assert memory.next_action == "inject_anti_errors_into_coursecvcd_exercises_and_rubrics"


def test_prior_art_packet_generates_queries():
    report = absorb_public_records(demo_public_research_records())
    packet = generate_prior_art_packet("compiler", ["CourseCVCD", "OAK"], report.atoms)
    assert packet.search_queries
    assert packet.novelty_axes
    assert packet.closest_public_references
    assert packet.next_action == "run_public_prior_art_search_and_update_ip_oak_gate"
