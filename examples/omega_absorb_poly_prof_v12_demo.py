from omega_prof_poly_t import available_demo_sources, build_package_status_report, run_cli


def main() -> None:
    print(run_cli(["version"]).strip())
    print("sources", ",".join(available_demo_sources()))
    print("polypublie_summary_len", len(run_cli(["summary-json", "--source", "polypublie"])))
    print("graphml_len", len(run_cli(["graphml", "--source", "expertise"])))
    print("docs_index", run_cli(["docs-index"]).splitlines()[0])
    print("status", build_package_status_report().version)


if __name__ == "__main__":
    main()
