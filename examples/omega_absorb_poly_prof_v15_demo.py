from omega_prof_poly_t import run_cli


def main() -> None:
    print(run_cli(["version"]).strip())
    print("tensor", run_cli(["tensor", "--source", "combined"]).strip())
    print("twin", run_cli(["twin-v2", "--source", "combined"]).strip())
    print("bridges", run_cli(["bridge-opt", "--source", "combined"]).strip())
    print(run_cli(["next-actions", "--source", "combined"]).splitlines()[0])
    print("manifest_len", len(run_cli(["oak-manifest", "--source", "combined"])))


if __name__ == "__main__":
    main()
