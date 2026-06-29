from omega_prof_poly_t import run_cli


def main() -> None:
    print(run_cli(["version"]).strip())
    print(run_cli(["tensor-weights", "--source", "combined"]).splitlines()[0])
    print(run_cli(["twin-answer", "--source", "combined", "--question", "next-10"]).splitlines()[0])
    print(run_cli(["department-matrix", "--source", "combined"]).splitlines()[0])
    print(run_cli(["route-dashboard", "--source", "combined"]).splitlines()[0])


if __name__ == "__main__":
    main()
