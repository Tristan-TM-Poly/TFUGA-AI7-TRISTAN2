from omega_prof_poly_t import build_export_payloads, render_documentation_index, run_cli


def main() -> None:
    payloads = build_export_payloads()
    print(run_cli(["version"]).strip())
    print("summary_json_len", len(payloads.summary_json))
    print("validation_json_len", len(run_cli(["validation-json"])))
    print("graph_json_len", len(run_cli(["graph-json"])))
    print(render_documentation_index().splitlines()[0])


if __name__ == "__main__":
    main()
