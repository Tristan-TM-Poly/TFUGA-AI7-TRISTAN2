from omega_prof_poly_t import run_cli


def main() -> None:
    print(run_cli(["version"]).strip())
    print(run_cli(["layout-v2"]).splitlines()[0])
    print(run_cli(["report-contract"]).splitlines()[0])
    print(run_cli(["workflow-seed"]).splitlines()[0])
    print(run_cli(["command-groups"]).splitlines()[0])
    print(run_cli(["absorb-os"]).splitlines()[0])


if __name__ == "__main__":
    main()
