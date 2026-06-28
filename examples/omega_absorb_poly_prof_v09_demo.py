from omega_prof_poly_t import (
    demo_combined_fixture_records,
    run_v09_e2e_pipeline,
    validate_public_records,
    render_roadmap_markdown,
)


def main() -> None:
    records = demo_combined_fixture_records()
    validation = validate_public_records(records)
    result = run_v09_e2e_pipeline()
    print("records", len(records))
    print("validation", validation.valid_count, validation.invalid_count)
    print("artifact_count", len(result.artifact_run.manifest.artifacts))
    print("department_score", result.department_report.score)
    print("roadmap_steps", len(result.roadmap.steps))
    print(render_roadmap_markdown(result.roadmap).splitlines()[0])


if __name__ == "__main__":
    main()
