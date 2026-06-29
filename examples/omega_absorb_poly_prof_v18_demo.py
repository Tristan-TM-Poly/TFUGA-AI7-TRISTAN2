from omega_prof_poly_t import run_cli


def main() -> None:
    print(run_cli(["version"]).strip())
    print(run_cli(["evidence-risk", "--source", "combined"]).splitlines()[0])
    print("manifest_plus_len", len(run_cli(["oak-manifest-plus", "--source", "combined"])))
    print(run_cli(["oak-lineage", "--source", "combined"]).splitlines()[0])
    print(run_cli(["mminus-apply", "--mminus-context", "unknown_source"]).splitlines()[0])
    print(run_cli(["oak-ledger", "--source", "combined"]).splitlines()[0])


if __name__ == "__main__":
    main()
