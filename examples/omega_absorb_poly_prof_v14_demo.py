from omega_prof_poly_t import run_cli


def main() -> None:
    print(run_cli(["version"]).strip())
    print("schema", run_cli(["schema-check", "--source", "combined"]).strip())
    print("claims", run_cli(["claim-oak", "--source", "combined"]).strip())
    print("methods", run_cli(["method-packets", "--source", "combined"]).strip())
    print("mminus", run_cli(["mminus"]).splitlines()[0])
    print("packet", run_cli(["github-packet", "--feature", "claim_oak_plus"]).splitlines()[0])


if __name__ == "__main__":
    main()
