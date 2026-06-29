from omega_prof_poly_t import run_cli


def main() -> None:
    print(run_cli(["version"]).strip())
    print(run_cli(["reports"]).splitlines()[0])
    print(run_cli(["write-reports"]).strip())
    print(run_cli(["release-intel"]).splitlines()[0])
    print(run_cli(["changelog-plus"]).splitlines()[0])
    print(run_cli(["ci-plan"]).splitlines()[0])


if __name__ == "__main__":
    main()
