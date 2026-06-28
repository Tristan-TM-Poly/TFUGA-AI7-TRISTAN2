from omega_prof_poly_t import VERSION, build_release_bundle, run_cli


def main() -> None:
    bundle = build_release_bundle()
    print(run_cli(["version"]).strip())
    print("version", VERSION)
    print("bundle", bundle.version)
    print("summary_len", len(bundle.summary_json))
    print("roadmap_len", len(bundle.roadmap_markdown))


if __name__ == "__main__":
    main()
